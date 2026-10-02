"""Tabla de respuestas por periodo: una fila por respuesta, con numeros en vez de texto.

Es la hoja que necesita el asistente del item 1.9 para responder cualquier consulta:
filtra las filas que cumplen una condicion y cuenta el resultado, incluidos los cruces
entre dos o mas preguntas (por ejemplo "de los que trabajan a tiempo completo, cuantos
estan satisfechos con la Universidad de Lima").

Forma del documento:

- ``cabeceras``: la lista de preguntas, en orden.
- ``opciones``: por cada pregunta, sus respuestas posibles, ordenadas (una sola vez).
- ``filas``: una lista de numeros por respuesta; cada numero apunta a la opcion de esa
  pregunta en ``opciones``.
- ``excluidas``: lo que quedo fuera y por que.

No incluye identificadores, fechas, estado del webhook ni el texto de la pregunta
abierta: los comentarios siguen en sentimiento.json (ya analizados y con los datos
personales enmascarados) y las fechas del periodo en dashboard_data.json.
"""
import re
import unicodedata
from typing import Dict, List, Optional

import pandas as pd

from .config import RESPUESTAS_TEXTO, RESPUESTAS_VERSION, declaraciones_de
from .io_helper import normalize_dates

VERSION = RESPUESTAS_VERSION

# Columnas que no son preguntas de la encuesta.
NO_VAN = {"Estado de respuesta", "Comentario NPS"}

# Campos que viajan aparte, en paralelo a las filas (no como opciones):
# el ID enlaza con el analisis de los comentarios (sentimiento.json) y la fecha
# permite contar por dia o por semana. Las columnas vacias se declaran en
# `opciones` con "(sin respuesta)".
COLUMNA_ID = "ID"
COLUMNAS_FECHA = ("Inicio", "Fin")

# Tope defensivo: una pregunta de opciones no tiene mas valores distintos que esto.
# Lo que lo supere es texto libre (u otro campo abierto) y se deja fuera.
MAX_OPCIONES = 50

SIN_RESPUESTA = "(sin respuesta)"


def _texto(serie: pd.Series) -> pd.Series:
    """Normaliza a texto sin espacios sobrantes (los vacios quedan como "")."""
    return serie.fillna("").astype(str).str.strip()


def _fechas_iso(df: pd.DataFrame, col: str) -> List[str]:
    """La fecha de cada respuesta, en formato AAAA-MM-DD.

    Las bandejas traen el formato de Zoho en espanol ("abr. 16, 2026 05:54:43 p. m."),
    asi que se usa el mismo normalizador del ETL. Si viniera ya como fecha, se formatea
    directo; si no se pudiera leer ninguna, se conserva el texto original.
    """
    serie = df[col]
    if not pd.api.types.is_datetime64_any_dtype(serie):
        # Primero el camino directo (una fecha ya en formato de maquina). Solo si casi
        # nada se puede leer, se usa el normalizador de Zoho (meses en espanol), que
        # interpreta el dia primero y por eso no debe aplicarse a una fecha ISO.
        directo = pd.to_datetime(_texto(serie), errors="coerce")
        if directo.notna().sum() >= max(1, len(df) // 2):
            serie = directo
        else:
            try:
                serie = normalize_dates(df[[col]], [col])[col]
            except Exception:
                serie = pd.to_datetime(_texto(serie), errors="coerce", dayfirst=True)
    if serie.isna().all():
        return [v for v in _texto(df[col])]
    return ["" if pd.isna(v) else v.strftime("%Y-%m-%d") for v in serie]


def _slug(nombre: str) -> str:
    """Identificador estable para una columna sin declaración (sin acentos, en minúsculas)."""
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", plano).strip("_") or "pregunta"


def _declaracion_de_cada_columna(cabeceras: List[str], df: pd.DataFrame,
                                 declaraciones: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Declaración (id, nombre, tipo, pregunta, escala) de cada columna publicada.

    Las preguntas declaradas en lib/config.py se copian tal cual; una columna sin
    declaración (un nivel todavía sin declarar) se describe con lo que se sabe de
    sus valores: medida CSAT si solo trae el catálogo de satisfacción, y
    agrupación en caso contrario. El id se mantiene único dentro del archivo.
    """
    por_nombre = {d["nombre"]: d for d in declaraciones}
    publicadas: List[Dict[str, str]] = []
    usados = set()
    for nombre in cabeceras:
        d = por_nombre.get(nombre)
        if d is None:
            valores = {v for v in _texto(df[nombre]).unique() if v}
            es_medida = bool(valores) and valores.issubset(set(RESPUESTAS_TEXTO))
            d = {"id": _slug(nombre), "nombre": nombre,
                 "tipo": "medida" if es_medida else "agrupacion",
                 "pregunta": nombre, "escala": "CSAT" if es_medida else ""}
        id_unico = d["id"]
        sufijo = 2
        while id_unico in usados:
            id_unico = "%s_%d" % (d["id"], sufijo)
            sufijo += 1
        usados.add(id_unico)
        publicadas.append({
            "id": id_unico,
            "nombre": d["nombre"],
            "tipo": d["tipo"],
            "pregunta": d["pregunta"],
            "escala": d["escala"],
        })
    return publicadas


def construir_tabla(df: pd.DataFrame, nivel: str, periodo: str,
                    declaraciones: Optional[List[Dict[str, str]]] = None) -> Dict:
    """Arma la tabla de respuestas de un periodo."""
    if declaraciones is None:
        declaraciones = declaraciones_de(nivel)
    cabeceras: List[str] = []
    opciones: Dict[str, List[str]] = {}
    excluidas: List[Dict[str, str]] = []

    for col in df.columns:
        nombre = str(col)
        if nombre == COLUMNA_ID or nombre in COLUMNAS_FECHA:
            continue  # viajan aparte, en `ids` y `fechas`
        if nombre in NO_VAN:
            excluidas.append({"pregunta": nombre, "motivo": "no es una pregunta"})
            continue
        valores = sorted({v for v in _texto(df[col]).unique() if v})
        if len(valores) > MAX_OPCIONES:
            excluidas.append({"pregunta": nombre, "motivo": "texto libre"})
            continue
        # El hueco solo se declara como opcion cuando de verdad hay respuestas en blanco.
        hay_blancos = bool((_texto(df[col]) == "").any())
        lista = ([SIN_RESPUESTA] if hay_blancos else []) + valores
        opciones[nombre] = lista
        cabeceras.append(nombre)

    indices = {c: {o: i for i, o in enumerate(opciones[c])} for c in cabeceras}
    por_columna = []
    for c in cabeceras:
        mapa = indices[c]
        hueco = mapa.get(SIN_RESPUESTA, 0)
        por_columna.append([mapa.get(v, hueco) for v in _texto(df[c])])
    filas = [list(fila) for fila in zip(*por_columna)] if cabeceras else []

    tabla: Dict = {
        "version": VERSION,
        "nivel": nivel,
        "periodo": str(periodo),
        "respuestas": int(len(df)),
        "cabeceras": cabeceras,
        "preguntas": _declaracion_de_cada_columna(cabeceras, df, declaraciones),
        "opciones": opciones,
        "filas": filas,
    }
    # El ID y la fecha viajan en paralelo a las filas (misma posicion = misma respuesta).
    if COLUMNA_ID in df.columns:
        tabla["ids"] = [v for v in _texto(df[COLUMNA_ID])]
    col_fecha = next((c for c in COLUMNAS_FECHA if c in df.columns), None)
    if col_fecha:
        tabla["fechas"] = _fechas_iso(df, col_fecha)
    if excluidas:
        tabla["excluidas"] = excluidas
    return tabla
