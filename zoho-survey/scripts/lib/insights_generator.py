"""
INSIGHTS GENERATOR — Generador de insights cualitativos deterministas.

Genera insights_ia (síntesis narrativa) a partir de datos ya procesados por el ETL.
NO usa LLM, NO llama APIs externas, NO reclasifica sentimiento ni aspectos.
Su rol es puramente de SÍNTESIS e INTERPRETACIÓN sobre datos existentes.

Responsabilidades:
  - Generar insights_ia.global: hallazgo principal del periodo.
  - Generar insights_ia.por_categoria_padre: síntesis por cada categoría real.
  - Excluir "Pendiente de Clasificación" de cálculos de temas relevantes.
  - Mantener trazabilidad con datos cuantitativos de origen.

Restricciones:
  - No modificar sentimiento ni intensidad asignados por sentiment_engine.py.
  - No crear categorías paralelas a la taxonomía oficial.
  - No llamar APIs externas ni usar LLM.
  - Determinista: misma entrada → misma salida.

Fase 8: implementado para reemplazar templates hardcodeados en build_json.py.
"""

from typing import Dict, List, Any
from collections import defaultdict


# Categorías padre oficiales (7) que el ETL puede producir.
# "Valoración General" NO está incluida porque es legacy (no existe en
# CATEGORIA_DIMENSION_*). "Pendiente de Clasificación" se maneja por separado.
CATEGORIAS_PADRE_OFICIALES: List[str] = [
    "Académico",
    "Administrativo y Bienestar",
    "Infraestructura",
    "Tecnología",
    "Docencia",
    "Desarrollo Profesional",
]

# Pseudo-categoría que NUNCA debe citarse como insight principal.
PSEUDO_CATEGORIA_EXCLUIR: str = "Pendiente de Clasificación"

# Umbral mínimo de comentarios para generar insight sustantivo por categoría.
# Si una categoría tiene menos comentarios, se genera insight mínimo.
UMBRAL_COMENTARIOS_INSIGHT: int = 3


def _calcular_distribucion_sentimiento(comentarios: List[Dict[str, Any]]) -> Dict[str, int]:
    """Cuenta comentarios por sentimiento (positivo/negativo/neutro)."""
    dist = {"positivo": 0, "negativo": 0, "neutro": 0}
    for c in comentarios:
        sent = c.get("sentimiento", "neutro")
        if sent in dist:
            dist[sent] += 1
    return dist


def _filtrar_pendiente(comentarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Excluye comentarios con categoria_padre == 'Pendiente de Clasificación'."""
    return [c for c in comentarios if c.get("categoria_padre") != PSEUDO_CATEGORIA_EXCLUIR]


def _topico_mas_frecuente(comentarios: List[Dict[str, Any]], campo: str = "categoria") -> str:
    """Encuentra el tema/dimensión más mencionado en una lista de comentarios."""
    if not comentarios:
        return ""
    freq = defaultdict(int)
    for c in comentarios:
        val = c.get(campo, "")
        if val and val != PSEUDO_CATEGORIA_EXCLUIR:
            freq[val] += 1
    if not freq:
        return ""
    return max(freq, key=freq.get)


def _contar_por_categoria_padre(comentarios: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa comentarios por categoria_padre, excluyendo Pendiente de Clasificación."""
    grupos = defaultdict(list)
    for c in comentarios:
        cat = c.get("categoria_padre", "")
        if cat and cat != PSEUDO_CATEGORIA_EXCLUIR:
            grupos[cat].append(c)
    return dict(grupos)


def _generar_insight_global(
    topicos_globales: List[Dict[str, Any]],
    dist_sent: Dict[str, int],
    total_analizados: int,
) -> str:
    """Genera el insight global del periodo.

    Reglas:
      - Excluir 'Pendiente de Clasificación' del top tópico.
      - Incluir datos cuantitativos (conteos, distribución).
      - Evitar frases genéricas sin respaldo numérico.
    """
    # Filtrar Pendiente de Clasificación de los tópicos
    topicos_reales = [
        t for t in topicos_globales
        if t.get("topico") != PSEUDO_CATEGORIA_EXCLUIR
    ]

    total_pos = dist_sent.get("positivo", 0)
    total_neg = dist_sent.get("negativo", 0)
    total_neu = dist_sent.get("neutro", 0)

    if not topicos_reales:
        return (
            f"El análisis cualitativo procesó {total_analizados} comentarios en este período. "
            f"La distribución general muestra {total_pos} comentarios positivos, "
            f"{total_neu} neutros y {total_neg} negativos. "
            f"No se identificaron temas específicos con clasificación válida; "
            f"se recomienda revisar manualmente los comentarios marcados como "
            f"'Pendiente de Clasificación'."
        )

    top_topico = topicos_reales[0]
    nombre_topico = top_topico.get("topico", "")
    menciones_top = top_topico.get("total_comentarios", 0)

    # Calcular porcentaje del top tópico sobre el total
    pct_topico = (menciones_top / total_analizados * 100) if total_analizados > 0 else 0

    # Determinar tono predominante
    if total_pos > total_neg and total_pos > total_neu:
        tono = f"predominio de opiniones favorables ({total_pos} positivos)"
    elif total_neg > total_pos and total_neg > total_neu:
        tono = f"predominio de opiniones críticas ({total_neg} negativos)"
    else:
        tono = f"distribución balanceada ({total_pos} positivos, {total_neu} neutros, {total_neg} negativos)"

    return (
        f"El análisis cualitativo revela que el tema más relevante en este período es "
        f"'{nombre_topico}' con {menciones_top} menciones ({pct_topico:.1f}% del total analizado). "
        f"La distribución general muestra {tono} "
        f"sobre un total de {total_analizados} comentarios procesados."
    )


def _generar_insight_por_categoria(
    cat_padre: str,
    comentarios_cat: List[Dict[str, Any]],
) -> str:
    """Genera insight narrativo para una categoría padre específica.

    Reglas:
      - Si no hay comentarios: mensaje explícito de ausencia.
      - Si hay < UMBRAL_COMENTARIOS_INSIGHT: insight mínimo con advertencia.
      - Si hay suficientes: insight sustantivo con top tópico y distribución.
    """
    total_cat = len(comentarios_cat)

    if total_cat == 0:
        return f"No se registran comentarios en la categoría '{cat_padre}' para este período."

    # Calcular distribución de sentimiento en esta categoría
    dist_cat = _calcular_distribucion_sentimiento(comentarios_cat)
    pos_cat = dist_cat["positivo"]
    neg_cat = dist_cat["negativo"]
    neu_cat = dist_cat["neutro"]

    # Encontrar el sub-tópico más mencionado
    sub_topico = _topico_mas_frecuente(comentarios_cat, campo="categoria")

    if total_cat < UMBRAL_COMENTARIOS_INSIGHT:
        return (
            f"La categoría '{cat_padre}' registra {total_cat} comentario(s) en este período, "
            f"insuficiente para análisis estadístico robusto. "
            f"Tema mencionado: '{sub_topico}'." if sub_topico else
            f"La categoría '{cat_padre}' registra {total_cat} comentario(s) en este período, "
            f"insuficiente para análisis estadístico robusto."
        )

    # Determinar tono predominante en esta categoría
    if pos_cat > neg_cat and pos_cat >= neu_cat:
        tono = f"predominio de opiniones favorables ({pos_cat} positivas"
        if neu_cat > 0:
            tono += f", {neu_cat} neutras"
        tono += ")"
    elif neg_cat > pos_cat and neg_cat >= neu_cat:
        tono = f"predominio de opiniones críticas ({neg_cat} negativas"
        if neu_cat > 0:
            tono += f", {neu_cat} neutras"
        tono += ")"
    else:
        tono = f"distribución balanceada ({pos_cat} positivas, {neu_cat} neutras, {neg_cat} negativas)"

    # Plantilla sustantiva con datos cuantitativos
    insight = (
        f"La categoría '{cat_padre}' concentra {total_cat} menciones, "
        f"con {tono}. "
    )

    if sub_topico:
        # Calcular qué porcentaje del total de la categoría representa el sub-tópico
        pct_sub = 0
        freq_sub = defaultdict(int)
        for c in comentarios_cat:
            val = c.get("categoria", "")
            if val and val != PSEUDO_CATEGORIA_EXCLUIR:
                freq_sub[val] += 1
        if freq_sub and sub_topico in freq_sub:
            pct_sub = (freq_sub[sub_topico] / total_cat * 100) if total_cat > 0 else 0
        insight += f"El tema más mencionado es '{sub_topico}' ({pct_sub:.0f}% de la categoría). "

    # Añadir nota sobre sentimiento negativo si aplica
    if neg_cat > 0 and neg_cat >= (pos_cat * 0.3):  # al menos 30% de negativos respecto a positivos
        insight += (
            f"Se identifican {neg_cat} comentario(s) con sentimiento negativo que "
            f"requieren atención para acciones de mejora. "
        )

    return insight.strip()


def generar_insights_ia(
    valid_comments: List[Dict[str, Any]],
    topicos_globales: List[Dict[str, Any]],
    dist_sent: Dict[str, int],
    total_analizados: int,
) -> Dict[str, Any]:
    """Función principal: genera el objeto insights_ia completo.

    Args:
        valid_comments: Lista de comentarios con campos categoria, categoria_padre,
                        sentimiento, intensidad. (de dataset_cualitativo en memoria)
        topicos_globales: Lista de tópicos agregados con campo topico, total_comentarios.
        dist_sent: Diccionario con conteos {positivo, negativo, neutro}.
        total_analizados: Total de comentarios analizados (incluye Pendiente de Clasificación).

    Returns:
        Dict con claves:
          - global: str (insight global del periodo)
          - por_categoria_padre: Dict[str, str] (insight por cada categoría oficial)
    """
    # 1. Generar insight global (excluye Pendiente de Clasificación automáticamente)
    insight_global = _generar_insight_global(topicos_globales, dist_sent, total_analizados)

    # 2. Filtrar Pendiente de Clasificación de comentarios para insights por categoría
    comentarios_filtrados = _filtrar_pendiente(valid_comments)

    # 3. Agrupar por categoría padre
    grupos_por_cat = _contar_por_categoria_padre(comentarios_filtrados)

    # 4. Generar insight para cada categoría oficial (7 categorías)
    insights_por_cat = {}
    for cat_padre in CATEGORIAS_PADRE_OFICIALES:
        comentarios_cat = grupos_por_cat.get(cat_padre, [])
        insights_por_cat[cat_padre] = _generar_insight_por_categoria(cat_padre, comentarios_cat)

    # 5. Incluir categorías no oficiales que aparezcan en los datos (defensivo)
    # Esto captura cualquier categoría que el ETL produzca pero no esté en
    # CATEGORIAS_PADRE_OFICIALES (por ejemplo, si se agrega una nueva).
    for cat_extra, comentarios_cat in grupos_por_cat.items():
        if cat_extra not in insights_por_cat and cat_extra != PSEUDO_CATEGORIA_EXCLUIR:
            insights_por_cat[cat_extra] = _generar_insight_por_categoria(cat_extra, comentarios_cat)

    return {
        "global": insight_global,
        "por_categoria_padre": insights_por_cat,
    }
