"""
IA FILTRO RUIDO — Filtro pre-DeepSeek de comentarios ruidosos.

Detecta comentarios que son claramente ruido (vacíos, solo puntuación,
teclazos, etc.) sin necesidad de llamar a la API de DeepSeek.
Genera unidades placeholder inválidas en el mismo formato que la API.
"""

import re
from typing import Tuple

# ============================================================
# CONSTANTES DE VALIDACIÓN
# ============================================================

SENTIMIENTOS_VALIDOS = {"positivo", "negativo", "neutro"}
MOTIVOS_INVALIDEZ_VALIDOS = {
    "Ruido explícito (pre-filtro)",
    "Comentario vacío o demasiado corto",
    "Respuesta inválida de la IA",
    "Error de análisis",
}

# ============================================================
# PATRONES REGEX DE RUIDO
# ============================================================

_RE_SOLO_PUNTUACION = re.compile(r'^[\s.,;:!¡¿?\-_()\[\]{}"\'/\\@#$%^&*+=\d]+$')
_RE_LETRA_REPETIDA = re.compile(r'^(.)\1{2,}$', re.IGNORECASE)
_RE_SOLO_NUMERO = re.compile(r'^\d+$')
_RE_PUNTUACION_REPETIDA = re.compile(r'^[.,;:!?\-_()]{3,}$')
_RE_RUIDO_TECLADO = re.compile(r'^(?:[asdfghjklñzxcvbnmqwertyuiop]+|[asdfghjklñzxcvbnmqwertyuiop]{3,})$', re.IGNORECASE)
_RE_REPITE_CALIFICACION = re.compile(
    r'^(?:mi\s*)?(?:nota|puntaj[ée]|calificaci[oó]n|punto)\s*(?:es\s*de?\s*)?\d+.*$',
    re.IGNORECASE
)
_RE_PALABRA_REPETIDA = re.compile(r'\b(\w+)\b(?:\s+\1\b){4,}', re.IGNORECASE)
_RE_CHAR_REPETIDO_INTERNO = re.compile(r'(.)\1{4,}')

# ============================================================
# SETS DE RUIDO Y FRASES VÁLIDAS
# ============================================================

_RUIDO_SIN_CONTEXTO = {
    "hola", "hola", "trash", "nada", "jaja", "jajaja", "ok", "okey",
    "no", "si", "xd", "xD", "XD", "jsjs", "jsjsjs", "mmm", "mhh",
    "no se", "no sé", "porque si", "porque no", "quien sabe",
    "sin comentarios", "ninguno", "nada que decir", "todo bien",
    "todo mal", "tal vez", "a veces", "no aplica", "n/a",
    "no mucho", "básicamente", "normal", "regular",
    "no tengo", "no se que decir", "no me acuerdo",
    "no sabría decir", "no opino", "no aplica",
    "no sabría", "no sabria", "npi", "no tengo idea",
    "no tengo opinion", "no sé qué poner",
}

_FRASES_CORTAS_VALIDAS = {
    "bien", "muy bien", "satisfecho", "muy satisfecho",
    "me gusta", "me gustó", "excelente", "bueno", "buena",
    "malo", "mala", "pesimo", "pésimo", "regular",
    "mas o menos", "más o menos", "genial", "perfecto",
    "deficiente", "horrible", "terrible", "increíble",
    "me encanta", "me encantó", "estoy conforme",
    "conforme", "inconforme", "no me gusta", "no me gustó",
}


# ============================================================
# FUNCIÓN DE FILTRO
# ============================================================

def es_ruido_pre_filtro(comentario: str) -> Tuple[bool, str]:
    """Evalúa si un comentario es ruido sin llamar a DeepSeek.

    Retorna (True, motivo) si es ruido, (False, "") si parece válido.
    Aplica 15 criterios en orden de especificidad.
    """
    texto = comentario.strip()
    if not texto:
        return True, "Comentario vacío"

    if _RE_SOLO_PUNTUACION.match(texto):
        return True, "Solo puntuación"

    if _RE_LETRA_REPETIDA.match(texto):
        return True, "Letra repetida"

    if _RE_CHAR_REPETIDO_INTERNO.search(texto):
        return True, "Caracter repetido interno"

    if _RE_SOLO_NUMERO.match(texto):
        return True, "Solo números"

    if _RE_REPITE_CALIFICACION.match(texto):
        return True, "Repite calificación"

    if texto.lower() in _FRASES_CORTAS_VALIDAS:
        return False, ""

    if len(texto) == 1:
        return True, "1 carácter"

    if texto.lower() in _RUIDO_SIN_CONTEXTO:
        return True, "Ruido explícito (pre-filtro)"

    tipos = set()
    for ch in texto:
        if ch.isalpha():
            tipos.add("alpha")
        elif ch.isdigit():
            tipos.add("digit")
        elif ch.isspace():
            tipos.add("space")
        else:
            tipos.add("other")
    if len(tipos) == 1 and "alpha" not in tipos:
        return True, "Solo un tipo de caracter no alfabético"

    if _RE_RUIDO_TECLADO.match(texto):
        return True, "Ruido de teclado"

    consonantes = sum(1 for c in texto.lower() if c.isalpha() and c not in "aeiouáéíóúü")
    vocales = sum(1 for c in texto.lower() if c in "aeiouáéíóúü")
    total_letras = consonantes + vocales
    if total_letras > 0 and (consonantes / total_letras) >= 0.75:
        return True, "Alta proporción de consonantes"

    if _RE_PALABRA_REPETIDA.search(texto):
        return True, "Palabra repetida 5+ veces"

    return False, ""


def generar_unidad_ruido(motivo: str) -> dict:
    """Genera una unidad placeholder inválida (compatible con schema DeepSeek)."""
    return {
        "orden": 1,
        "texto": "[ruido detectado]",
        "es_valido": False,
        "motivo_invalidez": motivo,
        "sentimiento": "neutro",
        "intensidad": 1,
        "dimension": "none",
        "categoria_padre": "none",
        "sub_aspectos": [],
        "justificacion_sentimiento": "Comentario clasificado como ruido.",
    }
