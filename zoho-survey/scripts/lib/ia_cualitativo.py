"""
IA CUALITATIVO — Orquestador del analisis cualitativo basado en DeepSeek.

Este modulo es la capa de integracion entre build_json.py y los 4 submodulos
especializados: ia_client (cliente DeepSeek), ia_validacion (validacion),
ia_filtro_ruido (pre-filtrado), e ia_validacion (validacion de respuestas).

Reemplaza a los 3 modulos locales (segmentacion_nps.py, aspect_extraction.py,
sentiment_engine.py) por una unica llamada a DeepSeek que ejecuta las 5 tareas
en conjunto, con coherencia de contexto y reglas de sesgo NPS aplicadas.

Uso principal (integrado en build_json.py):
  from lib.ia_cualitativo import generar_salidas_cualitativas_ia
  datos_fragmentos, dataset, metadata = generar_salidas_cualitativas_ia(
      df_sent=df_sent, taxonomia=..., csat_columns_map=...
  )

Variables de entorno:
  - DEEPSEEK_API_KEY (obligatorio para modo IA).
  - IA_CUALITATIVO_MODEL (opcional, default "deepseek-v4-flash").
  - IA_CUALITATIVO_MAX_RPM (opcional, default 60).
  - (caché IA eliminado — la verificación por ID reemplaza al caché)
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# CacheManager eliminado — verificación por ID en build_json.py
from .ia_client import DeepSeekClient, DEFAULT_WORKERS
from .ia_filtro_ruido import es_ruido_pre_filtro, generar_unidad_ruido
from .ia_validacion import validar_respuesta_ia
from .io_helper import ofuscar_pii_para_llm
from .prompts_cualitativo import (
    build_system_prompt,
    build_user_prompt,
    RATING_TO_SCORE,
)

try:
    import pandas as _pd
except ImportError:
    _pd = None

logger = logging.getLogger(__name__)


# ============================================================
# FUNCION PRINCIPAL: analizar un comentario
# ============================================================

def analizar_comentario(comentario: str,
                        nps_score: int,
                        csat_ratings: Dict[str, str],
                        taxonomia: Dict[str, str],
                        categorias_padre: List[str],
                        client: DeepSeekClient,
                        fallback_client: Optional[DeepSeekClient] = None,
                        id_encuesta: str = "",
                        carrera: str = "",
                        ciclo: str = "",
                        facultad: str = "") -> Dict[str, Any]:
    """Analiza un comentario completo y devuelve {unidades: [...]}.

    El fallback se activa en DOS casos:
      1. Error de API (RuntimeError) en el cliente primario.
      2. Respuesta del primario no valida (validar_respuesta_ia -> None).

    Si ambos clientes fallan, devuelve una unidad placeholder no valida.
    """
    system_prompt = build_system_prompt(taxonomia, categorias_padre)
    user_prompt = build_user_prompt(comentario, nps_score, csat_ratings, id_encuesta, carrera, ciclo, facultad)

    def _try_client(active_client: DeepSeekClient) -> Optional[Dict[str, Any]]:
        """Llama a un cliente y valida su respuesta. Retorna dict saneado o None."""
        provider_label = "NVIDIA" if active_client.provider == "nvidia" else "DeepSeek"
        try:
            raw = active_client.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=10000,
            )
        except RuntimeError as e:
            logger.error(f"{provider_label} fallo para {id_encuesta}: {e}")
            return None
        if not raw:
            logger.warning(f"{provider_label} devolvio respuesta vacia para {id_encuesta}.")
            return None
        sanada, err = validar_respuesta_ia(raw, taxonomia)
        if sanada is None:
            logger.warning(f"{provider_label} respuesta invalida para {id_encuesta}: {err}")
            return None
        return sanada

    clients_to_try: List[Tuple[DeepSeekClient, str]] = [(client, client.provider)]
    if fallback_client is not None:
        clients_to_try.append((fallback_client, fallback_client.provider))

    for idx, (active_client, provider_name) in enumerate(clients_to_try):
        if idx > 0:
            logger.warning(f"Intentando fallback ({provider_name}) para {id_encuesta}...")
        sanada = _try_client(active_client)
        if sanada is not None:
            if provider_name != "deepseek":
                if isinstance(sanada, dict) and "unidades" in sanada:
                    for u in sanada["unidades"]:
                        if isinstance(u, dict):
                            u["_motor_actual"] = provider_name
            return sanada

    # Ambos fallaron
    return _placeholder(comentario, "Ambos motores (DeepSeek + fallback) fallaron o devolvieron respuesta invalida.",
                       "Error de API (todos los motores fallaron)")


def _placeholder(comentario: str, detalle: str, motivo: str) -> dict:
    """Genera placeholder de unidad no valida."""
    return {
        "unidades": [{
            "orden": 1,
            "texto": comentario[:100],
            "es_valido": False,
            "motivo_invalidez": motivo,
            "sentimiento": "neutro",
            "intensidad": 1,
            "justificacion_sentimiento": detalle,
            "dimension": "Pendiente de Clasificación",
            "categoria_padre": "Pendiente de Clasificación",
            "es_mencion_mejora": False,
            "es_salvavidas": False,
            "dimension_evaluada_rating": None,
            "dimension_evaluada_score": None,
            "sub_aspectos": [],
        }]
    }


# ============================================================
# FUNCION DE ALTO NIVEL: analizar todo el dataset
# ============================================================

def analizar_dataset_cualitativo(
    df_sent,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    progress_every: int = 25,
    fallback_client: Optional[DeepSeekClient] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Analiza cualitativamente todo el dataset de comentarios NPS.

    Returns:
        (dataset_cualitativo, metadata) donde dataset_cualitativo es una
        lista de dicts (uno por unidad) y metadata contiene estadisticas.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key and fallback_client is None:
        raise RuntimeError("DEEPSEEK_API_KEY no configurada y no hay fallback_client.")

    client = DeepSeekClient(api_key=api_key) if api_key else None
    if client is None:
        # Si no hay DeepSeek, usar el fallback como primario
        client = fallback_client
        fallback_client = None

    if fallback_client is None:
        nvidia_api_key = os.environ.get("NVIDIA_API_KEY", "")
        if nvidia_api_key and client.provider != "nvidia":
            nvidia_model = os.environ.get("IA_CUALITATIVO_FALLBACK_MODEL", "nemotron-3-ultra-550b-a55b")
            fallback_client = DeepSeekClient(api_key=nvidia_api_key, model=nvidia_model, provider="nvidia")
            logger.info(f"Cliente NVIDIA fallback configurado (modelo: {nvidia_model}).")
        else:
            logger.warning("NVIDIA_API_KEY no configurada; no hay fallback disponible.")

    categorias_padre = sorted(set(taxonomia.values()))

    # Cleaning defensivo
    if _pd is not None:
        try:
            df_sent = df_sent.copy()
            df_sent["nps_score"] = _pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"]).reset_index(drop=True)
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent = df_sent[df_sent["comentario"].str.strip() != ""]
            df_sent = df_sent[df_sent["comentario"].str.strip().str.lower() != "nan"]
        except Exception as clean_err:
            logger.warning(f"Cleaning defensivo fallo: {clean_err}")

    dataset_cualitativo: List[Dict[str, Any]] = []
    total_comentarios = 0
    total_unidades = 0
    errores = 0
    cache_hits = 0
    ruido_filtrado = 0

    total_rows = len(df_sent)
    workers = DEFAULT_WORKERS
    logger.info(
        f"Iniciando analisis IA de {total_rows} comentarios "
        f"(modelo: {client.model}, {workers} workers, timeout={client.timeout}s)."
    )

    # Pre-coleccionar tasks
    tasks: List[Tuple] = []
    for idx, row in df_sent.iterrows():
        comentario_val = row["comentario"]
        if _pd is not None and _pd.isna(comentario_val):
            continue
        if comentario_val is None:
            continue
        comentario = str(comentario_val).strip()
        # Ofuscar PII antes de enviar a DeepSeek (evita que datos sensibles lleguen al LLM)
        comentario, _pii_map = ofuscar_pii_para_llm(comentario)

        if not comentario or comentario.lower() == "nan":
            continue

        nps_val = row["nps_score"]
        if _pd is not None and _pd.isna(nps_val):
            continue
        try:
            nps = int(nps_val)
        except (ValueError, TypeError):
            continue

        res_id = str(row.get("ID", f"R_{idx}"))
        facultad = str(row.get("facultad", ""))
        carrera = str(row.get("carrera", ""))
        ciclo = str(row.get("ciclo", ""))
        satisfaccion_global = str(row.get("satisfaccion_global", "No respondido"))

        csat_ratings: Dict[str, str] = {}
        for dim, col in csat_columns_map.items():
            if col in row.index:
                val = row[col]
                if val and str(val).strip() and str(val).strip() in RATING_TO_SCORE:
                    csat_ratings[dim] = str(val).strip()

        tasks.append((comentario, nps, csat_ratings, res_id,
                      facultad, carrera, ciclo, satisfaccion_global))

    logger.info(f"{len(tasks)} tasks preparados de {total_rows} filas.")
    _start_batch = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        fut_map = {}
        for (comentario, nps, csat_ratings, res_id,
             facultad, carrera, ciclo, satisfaccion_global) in tasks:
            es_ruido, motivo = es_ruido_pre_filtro(comentario)
            if es_ruido:
                ruido_filtrado += 1
                unidad = generar_unidad_ruido(motivo)
                dataset_cualitativo.append(_build_item(
                    res_id, "01", facultad, carrera, ciclo, nps,
                    satisfaccion_global, comentario[:100], "", "",
                    "", [], "neutro", 1, 1.0, comentario,
                    False, motivo, "deepseek"
                ))
                continue

            future = executor.submit(
                _analizar_un_comentario, comentario, nps, csat_ratings,
                taxonomia, categorias_padre, client, res_id,
                facultad, carrera, ciclo, satisfaccion_global,
                fallback_client=fallback_client
            )
            fut_map[future] = (res_id, facultad, carrera, ciclo,
                               satisfaccion_global, nps, comentario)

        for i, future in enumerate(as_completed(fut_map)):
            res_id, facultad, carrera, ciclo, satisfaccion_global, nps, \
                comentario = fut_map[future]
            try:
                resultado = future.result()
                unidades = resultado.get("unidades", [])
                total_comentarios += 1
                total_unidades += len(unidades)
                for unidad in unidades:
                    es_valido = unidad.get("es_valido", True)
                    sent = unidad.get("sentimiento", "neutro").lower()
                    motor_real = unidad.get("_motor_actual", "deepseek")
                    dataset_cualitativo.append(_build_item(
                        res_id, f"{unidad['orden']:02d}",
                        facultad, carrera, ciclo, nps,
                        satisfaccion_global, unidad.get("texto", ""),
                        unidad.get("dimension", ""),
                        unidad.get("dimension", ""),
                        unidad.get("categoria_padre", ""),
                        unidad.get("sub_aspectos", []),
                        sent, unidad.get("intensidad", 3),
                        1.0, comentario, es_valido,
                        unidad.get("motivo_invalidez", ""), motor_real
                    ))
            except Exception as e:
                errores += 1
                logger.error(f"Error procesando {res_id}: {e}")

            if (i + 1) % progress_every == 0:
                elapsed = time.perf_counter() - _start_batch
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Progreso: {i+1}/{len(fut_map)} comentarios "
                    f"({rate:.1f} cmt/s), {total_unidades} unidades, "
                    f"{errores} errores, {ruido_filtrado} ruido."
                )

    _elapsed = time.perf_counter() - _start_batch

    # REND-02: Ordenar dataset para garantizar idempotencia.
    # as_completed produce resultados en orden de finalizacion (no determinista).
    # Ordenar por id_encuesta + id_fragmento asegura que mismo CSV -> mismo JSON.
    dataset_cualitativo.sort(key=lambda x: (x.get("id_encuesta", ""), x.get("id_fragmento", "")))

    cache_hits = 0  # sin cache

    metadata = {
        "total_encuestas": total_comentarios,
        "total_fragmentos": total_unidades,
        "errores": errores,
        "ruido_filtrado": ruido_filtrado,
        "cache_hits": cache_hits,
        "tiempo_segundos": round(_elapsed, 2),
        "stats_sentimiento": {
            "total_opinion_units": total_unidades,
            "positivos": sum(1 for d in dataset_cualitativo
                             if d["sentimiento"] == "positivo" and d["es_valido"]),
            "negativos": sum(1 for d in dataset_cualitativo
                             if d["sentimiento"] == "negativo" and d["es_valido"]),
            "neutros": sum(1 for d in dataset_cualitativo
                           if d["sentimiento"] == "neutro" and d["es_valido"]),
        },
        "usage": client.usage,
    }

    logger.info(
        f"Analisis IA completado: {total_comentarios} comentarios, "
        f"{total_unidades} unidades, {errores} errores, "
        f"{ruido_filtrado} ruido pre-filtrado. "
        f"Tiempo: {_elapsed:.1f}s."
    )

    return dataset_cualitativo, metadata


def _build_item(res_id, ord_id, facultad, carrera, ciclo, nps,
                sat_global, texto, asp_detectado, asp_normalizado,
                cat_padre, sub_aspectos, sentimiento, intensidad,
                confianza, comentario_orig, es_valido, motivo, motor):
    """Construye un item del dataset cualitativo."""
    return {
        "id_encuesta": res_id,
        "id_fragmento": f"{res_id}_{ord_id}",
        "facultad": facultad,
        "carrera": carrera,
        "ciclo": ciclo,
        "nps_score": nps,
        "segmento_nps": (
            "Promotor" if nps >= 9
            else "Pasivo" if nps >= 7
            else "Detractor"
        ),
        "satisfaccion_global": sat_global,
        "texto": texto,
        "aspecto_detectado": asp_detectado,
        "aspecto_normalizado": asp_normalizado,
        "categoria_padre": cat_padre,
        "sub_aspectos": sub_aspectos,
        "sentimiento": sentimiento,
        "intensidad": intensidad,
        "confianza_sentimiento": confianza,
        "comentario_original": comentario_orig,
        "es_valido": es_valido,
        "motivo_invalidez": motivo,
        "motor": motor,
    }


def _analizar_un_comentario(comentario, nps, csat_ratings, taxonomia,
                            categorias_padre, client, res_id,
                            facultad, carrera, ciclo, satisfaccion_global,
                            fallback_client=None):
    """Helper para ejecutar en ThreadPoolExecutor."""
    return analizar_comentario(
        comentario=comentario,
        nps_score=nps,
        csat_ratings=csat_ratings,
        taxonomia=taxonomia,
        categorias_padre=categorias_padre,
        client=client,
        fallback_client=fallback_client,
        id_encuesta=res_id,
        carrera=carrera,
        ciclo=ciclo,
        facultad=facultad,
    )


# ============================================================
# CAPA DE INTEGRACION CON build_json.py
# ============================================================

def generar_salidas_cualitativas_ia(
    df_sent,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    fallback_client: Optional[DeepSeekClient] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Capa de integracion con build_json.py.

    Retorna (datos_fragmentos, dataset_cualitativo, metadata) en formato
    compatible con el pipeline legacy.
    """
    dataset_cualitativo, metadata = analizar_dataset_cualitativo(
        df_sent=df_sent,
        taxonomia=taxonomia,
        csat_columns_map=csat_columns_map,
        fallback_client=fallback_client,
    )

    from collections import defaultdict
    grupos: Dict[str, List[Dict]] = defaultdict(list)
    for item in dataset_cualitativo:
        grupos[item["id_encuesta"]].append(item)

    datos_fragmentos = []
    for res_id, unidades in grupos.items():
        primera = unidades[0]
        fragmentos = []
        for u in unidades:
            fragmentos.append({
                "id_fragmento": u["id_fragmento"],
                "texto": u["texto"],
                "sentimiento": u.get("sentimiento", "neutro"),
                "intensidad": u.get("intensidad", 3),
                "aspecto_normalizado": u.get("aspecto_normalizado", ""),
                "categoria_padre": u.get("categoria_padre", ""),
                "es_valido": u.get("es_valido", True),
                "motivo_invalidez": u.get("motivo_invalidez", ""),
            })

        datos_fragmentos.append({
            "id_encuesta": res_id,
            "facultad": primera.get("facultad", ""),
            "carrera": primera.get("carrera", ""),
            "ciclo": primera.get("ciclo", ""),
            "nps_score": primera.get("nps_score", 0),
            "segmento_nps": primera.get("segmento_nps", ""),
            "satisfaccion_global": primera.get("satisfaccion_global", ""),
            "comentario_original": primera.get("comentario_original", ""),
            "fragmentos": fragmentos,
        })

    return datos_fragmentos, dataset_cualitativo, metadata
