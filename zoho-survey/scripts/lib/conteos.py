'''Conteos por pregunta que hoy no se cuenta en ningun archivo.

Alimenta conteos.json:
  - las preguntas de perfil (situacion laboral, tiempo laboral y las que traiga cada
    encuesta) con sus opciones contadas, y cada opcion partida por carrera, facultad y
    ciclo;
  - las preguntas de escala que NO estan en el mapa de dimensiones.json (su conteo no
    existe en ningun sitio hoy);
  - el catalogo: que preguntas hay y en que archivo vive el conteo de cada una;
  - la empleabilidad global (igual que dashboard_data.resumen.empleabilidad), por
    carrera y por facultad.

No repite lo ya publicado: las escalas del mapa (dimensiones.json), el NPS
(nps_carrera.json / nps_ciclo_carrera.json), el CSAT (csat_carrera.json /
csat_ciclo_carrera.json), las respuestas por carrera/ciclo (ids.json) ni el texto libre
(sentimiento.json).
'''
from typing import Dict, List

import pandas as pd

from .config import EMPLEABILIDAD_CATEGORIAS, RESPUESTAS_TEXTO

VERSION = "1.0"

# Columnas que no son preguntas de la encuesta: identidad, fechas, ubicacion y los
# campos que agrega el conversor de la bandeja ("Estado de respuesta" marca las
# completas; las parciales no llegan al CSV).
NO_SON_PREGUNTAS = {
    "ID", "ID de respuesta", "Inicio", "Fin", "Start time", "Hora de finalización",
    "Recibido en", "Estado de respuesta",
    "Facultad", "Carrera", "Ciclo", "Comentario NPS",
}

# Cada corte que acompana a las opciones.
CORTES = [("por_carrera", "Carrera"), ("por_facultad", "Facultad"), ("por_ciclo", "Ciclo")]

# Empleabilidad: las mismas reglas que usa build_json.py para el total global.
CLAVE_SITUACION = "Situaci\u00f3n laboral"


def texto(serie: pd.Series) -> pd.Series:
    '''Normaliza a texto sin espacios sobrantes (los vacios quedan como "").'''
    return serie.fillna("").astype(str).str.strip()


def es_pregunta_de_escala(serie: pd.Series) -> bool:
    '''Una pregunta de escala solo tiene como valores el catalogo Likert.'''
    valores = {v for v in texto(serie).unique() if v}
    return bool(valores) and valores.issubset(set(RESPUESTAS_TEXTO))


def opciones_de(serie: pd.Series) -> List[str]:
    return sorted({v for v in texto(serie).unique() if v})


def _ya_publicadas(df: pd.DataFrame, escala: Dict[str, str],
                   nps_col, csat_col) -> set:
    '''Columnas cuyo conteo ya vive en otro archivo.'''
    fuera = set(NO_SON_PREGUNTAS) | set(escala)
    if nps_col:
        fuera.add(nps_col)
    if csat_col:
        fuera.add(csat_col)
    return fuera


def preguntas_de_perfil(df: pd.DataFrame, escala: Dict[str, str],
                        nps_col=None, csat_col=None) -> List[str]:
    fuera = _ya_publicadas(df, escala, nps_col, csat_col)
    return [c for c in df.columns if c not in fuera]


def _corte(df: pd.DataFrame, pregunta: str, opcion: str, columna: str) -> Dict[str, int]:
    sub = df[texto(df[pregunta]) == opcion]
    if sub.empty:
        return {}
    cuenta = texto(sub[columna]).replace("", "No indica").value_counts()
    return {str(k): int(v) for k, v in sorted(cuenta.items())}


def conteo_de_pregunta(df: pd.DataFrame, pregunta: str) -> Dict:
    serie = texto(df[pregunta])
    filas = []
    for opcion in opciones_de(df[pregunta]):
        fila = {"opcion": opcion, "total": int((serie == opcion).sum())}
        for nombre, columna in CORTES:
            if columna in df.columns:
                corte = _corte(df, pregunta, opcion, columna)
                if corte:
                    fila[nombre] = corte
        filas.append(fila)
    salida = {"pregunta": pregunta, "total": int(len(df)), "por_opcion": filas}
    sin_respuesta = int((serie == "").sum())
    if sin_respuesta:
        salida["sin_respuesta"] = sin_respuesta
    return salida


def _empleabilidad(sub: pd.DataFrame, etiqueta: Dict[str, object]) -> Dict:
    if CLAVE_SITUACION not in sub.columns:
        return {}
    serie = texto(sub[CLAVE_SITUACION])
    serie = serie[serie != ""]
    total = int(len(serie))
    if not total:
        return {}
    empleados = int(serie.isin(EMPLEABILIDAD_CATEGORIAS).sum())
    return {**etiqueta, "score": round(empleados / total * 100, 2),
            "empleados": empleados, "total": total}


def empleabilidad(df: pd.DataFrame) -> Dict:
    if CLAVE_SITUACION not in df.columns:
        return {}
    salida = {"total": _empleabilidad(df, {})}
    if "Carrera" in df.columns:
        salida["por_carrera"] = [x for x in
                                 (_empleabilidad(sub, {"carrera": car})
                                  for car, sub in df.groupby("Carrera")) if x]
    if "Facultad" in df.columns:
        salida["por_facultad"] = [x for x in
                                  (_empleabilidad(sub, {"facultad": fac})
                                   for fac, sub in df.groupby("Facultad")) if x]
    return salida


def catalogo(df: pd.DataFrame, escala: Dict[str, str], nps_col=None, csat_col=None) -> List[Dict]:
    '''Que preguntas existen y en que archivo vive el conteo de cada una.'''
    filas = []
    for pregunta in sorted({p for p in (set(escala) | {nps_col, csat_col}) if p}):
        if pregunta not in df.columns:
            continue
        if pregunta == nps_col:
            filas.append({"pregunta": pregunta, "donde": "nps_carrera.json",
                          "tipo": "nps", "opciones": []})
        elif pregunta == csat_col:
            filas.append({"pregunta": pregunta, "donde": "csat_carrera.json",
                          "tipo": "csat", "opciones": list(RESPUESTAS_TEXTO)})
        else:
            filas.append({"pregunta": pregunta, "donde": "dimensiones.json",
                          "tipo": "escala", "opciones": list(RESPUESTAS_TEXTO)})
    if "Comentario NPS" in df.columns:
        filas.append({"pregunta": "Comentario NPS", "donde": "sentimiento.json",
                      "tipo": "texto", "opciones": []})
    for pregunta in preguntas_de_perfil(df, escala, nps_col, csat_col):
        filas.append({"pregunta": pregunta, "donde": "conteos.json",
                      "tipo": "escala" if es_pregunta_de_escala(df[pregunta]) else "perfil",
                      "opciones": opciones_de(df[pregunta])})
    return filas


def construir_conteos(df: pd.DataFrame, nivel: str, escala: Dict[str, str],
                      tiene_ciclo: bool, nps_col=None, csat_col=None) -> Dict:
    '''Arma el documento de conteos.json de un periodo.'''
    salida = {
        "version": VERSION,
        "nivel": nivel,
        "respuestas": int(len(df)),
        "catalogo": catalogo(df, escala, nps_col, csat_col),
        "preguntas": [conteo_de_pregunta(df, p)
                      for p in preguntas_de_perfil(df, escala, nps_col, csat_col)],
    }
    empleo = empleabilidad(df)
    if empleo.get("total"):
        salida["empleabilidad"] = empleo
    return salida
