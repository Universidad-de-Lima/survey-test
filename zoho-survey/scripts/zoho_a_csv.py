"""
ZOHO A CSV — Convierte la bandeja de respuestas en el CSV que consume el ETL.

Uso:
    python3 zoho-survey/scripts/zoho_a_csv.py [carpeta-de-destino]

Lo invoca el flujo .github/workflows/build_zoho_survey.yml cuando el portal pide
procesar los datos (repository_dispatch). Lee data/zoho_pendientes/*.jsonl (una
linea por respuesta, ya enmascarada), arma un CSV por encuesta con las cabeceras
que espera build_json.py y lo deja en data/, donde el gate "Detectar CSVs a
procesar" lo recoge.

Reglas:

  - Las claves de la bandeja ya vienen con los nombres de cabecera del CSV: el
    webhook envia cada pregunta con el texto que el ETL espera. El identificador
    viaja aparte (id_respuesta) y aqui se repone en 'ID de respuesta'.
  - El nombre del archivo se deriva del titulo de la encuesta, porque el ETL saca
    de ahi el nivel y el periodo (CONTRACTS.md, "Reglas de nombres CSV").
  - Se escribe SIN BOM por limpieza: el ETL ya limpia el BOM de la primera columna la
    primera columna.
  - NO borra la bandeja: es el acumulado del periodo. Borrarla dejaria el
    dashboard sin las respuestas anteriores (ver docs/INGESTA_Y_DESCARGA.md).
  - Si no hay bandejas, no escribe nada: el flujo se queda sin CSV y solo despliega.

Este modulo usa solo la biblioteca estandar (mas las constantes de lib.config),
a proposito: corre antes de instalar dependencias, en el mismo punto que el gate
de CSVs.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.config import COLUMN_RENAME_GRADUADO, COLUMN_RENAME_PREGRADO  # noqa: E402

CARPETA_PENDIENTES = Path("data") / "zoho_pendientes"
CARPETA_DESTINO = Path("data")
CLAVE_ID = "ID de respuesta"
CLAVE_ESTADO = "Estado"

# Solo pasan al CSV las respuestas completas. Las parciales (Estado = PARTIAL)
# quedan en la bandeja, pero no entran al proceso: no aportan a NPS ni CSAT y
# descuadrarian los conteos. Una respuesta SIN el campo Estado se deja pasar:
# no se puede saber su estado y no conviene descartar datos en silencio.
ESTADO_COMPLETO = "COMPLETED"

# Cabeceras por nivel, en el orden que espera build_json.py. Solo se admiten los
# niveles que hoy pueden llegar por webhook: el resto falla con aviso explicito
# en vez de generar un CSV a medias.
CABECERAS_POR_NIVEL: Dict[str, List[str]] = {
    "undergraduate": list(COLUMN_RENAME_PREGRADO),
    "graduate": list(COLUMN_RENAME_GRADUADO),
}


def detectar_nivel(nombre_archivo: str) -> Optional[str]:
    """Mismo criterio que build_json._detectar_nivel (las pruebas los comparan).

    Se repite aqui para que este paso no dependa de pandas.
    """
    texto = str(nombre_archivo).upper()
    if "NO DOCENTE" in texto:
        return "nonfaculty"
    if "EMPLEADORES" in texto:
        return "employers"
    if "EGRESADOS" in texto:
        return "alumni-pg" if "POSGRADO" in texto else "alumni-ug"
    if "DOCENTE" in texto:
        return "faculty-pg" if "POSGRADO" in texto else "faculty-ug"
    if "GRADUADOS" in texto:
        return "graduate"
    if "ESTUDIANTIL" in texto or "ESTUDIANTES" in texto:
        return "postgraduate" if "POSGRADO" in texto else "undergraduate"
    return None


def nombre_csv(encuesta: str) -> str:
    """Nombre de archivo que el ETL sabe leer: ...{CATEGORIA}[- NIVEL][- PERIODO].csv"""
    return f"{str(encuesta).strip()}.csv"


def cabeceras_de(encuesta: str) -> List[str]:
    """Columnas del CSV para esa encuesta, en el orden del ETL."""
    nivel = detectar_nivel(nombre_csv(encuesta))
    if nivel is None:
        raise ValueError(
            f"no se pudo deducir el nivel de '{encuesta}': el nombre debe seguir el "
            "formato de CONTRACTS.md (ENCUESTA DE SATISFACCION {CATEGORIA} [- NIVEL] [- PERIODO])"
        )
    if nivel not in CABECERAS_POR_NIVEL:
        raise ValueError(
            f"el nivel '{nivel}' todavia no se convierte desde la bandeja: "
            "agrega sus cabeceras a CABECERAS_POR_NIVEL"
        )
    return CABECERAS_POR_NIVEL[nivel]


def leer_respuestas(ruta: Path) -> List[Dict[str, Any]]:
    """Lee una bandeja (un JSON por linea). Falla si una linea no es JSON valido."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return []

    registros: List[Dict[str, Any]] = []
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip():
            continue
        try:
            registros.append(json.loads(linea))
        except json.JSONDecodeError as exc:
            raise ValueError(f"la linea {numero} de {ruta.name} no es JSON valido: {exc}") from exc
    return registros


def es_respuesta_completa(registro: Dict[str, Any]) -> bool:
    """True si la respuesta llego completa (o si no trae el estado, que no se sabe)."""
    respuestas = registro.get("respuestas") or {}
    estado = str(respuestas.get(CLAVE_ESTADO) or "").strip().upper()
    return not estado or estado == ESTADO_COMPLETO


def _valor(valor: Any) -> Any:
    """Deja el valor listo para el CSV, sin romper el archivo."""
    if valor is None:
        return ""
    if isinstance(valor, (str, int, float)):
        return valor
    return json.dumps(valor, ensure_ascii=False)


def escribir_csv(encuesta: str, registros: List[Dict[str, Any]], destino: Path = CARPETA_DESTINO) -> Path:
    """Escribe el CSV de una encuesta a partir de sus respuestas. Devuelve la ruta."""
    cabeceras = cabeceras_de(encuesta)

    vistos = set()
    filas: List[Dict[str, Any]] = []
    omitidas = 0
    for registro in registros:
        identificador = str(registro.get("id_respuesta") or "").strip()
        # Sin identificador no hay forma de evitar duplicados: no entra al CSV.
        if not identificador or identificador in vistos:
            continue
        if not es_respuesta_completa(registro):
            omitidas += 1
            continue
        vistos.add(identificador)
        respuestas = registro.get("respuestas") or {}
        filas.append(
            {
                columna: (identificador if columna == CLAVE_ID else _valor(respuestas.get(columna)))
                for columna in cabeceras
            }
        )
    if not filas:
        raise ValueError(
            f"la encuesta '{encuesta}' no tiene respuestas completas con identificador"
        )

    if omitidas:
        print(f"omitidas {omitidas} respuestas sin completar (Estado distinto de {ESTADO_COMPLETO}): {encuesta}")

    salida = Path(destino) / nombre_csv(encuesta)
    with open(salida, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=cabeceras)
        escritor.writeheader()
        escritor.writerows(filas)
    return salida


def convertir_encuesta(ruta: Path, destino: Path = CARPETA_DESTINO) -> Path:
    """Arma el CSV de una sola bandeja. Devuelve la ruta escrita."""
    ruta = Path(ruta)
    registros = leer_respuestas(ruta)
    if not registros:
        raise ValueError(f"la bandeja {ruta.name} esta vacia")
    encuesta = str(registros[0].get("encuesta") or "").strip()
    if not encuesta:
        raise ValueError(f"la bandeja {ruta.name} no trae el nombre de la encuesta")
    return escribir_csv(encuesta, registros, destino)


def convertir(
    carpeta_pendientes: Path = CARPETA_PENDIENTES, destino: Path = CARPETA_DESTINO
) -> List[Path]:
    """Convierte todas las bandejas. Devuelve los CSV escritos.

    Las bandejas de una misma encuesta se juntan en un solo CSV: si no, la ultima
    pisaria a las anteriores y se perderian respuestas.
    """
    por_encuesta: Dict[str, List[Dict[str, Any]]] = {}
    for ruta in sorted(Path(carpeta_pendientes).glob("*.jsonl")):
        registros = leer_respuestas(ruta)
        if not registros:
            continue
        encuesta = str(registros[0].get("encuesta") or "").strip()
        if not encuesta:
            raise ValueError(f"la bandeja {ruta.name} no trae el nombre de la encuesta")
        por_encuesta.setdefault(encuesta, []).extend(registros)

    return [escribir_csv(encuesta, registros, destino) for encuesta, registros in por_encuesta.items()]


def main(argv) -> int:
    destino = Path(argv[1]) if len(argv) > 1 else CARPETA_DESTINO
    try:
        escritos = convertir(CARPETA_PENDIENTES, destino)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1

    if not escritos:
        print(f"sin bandejas en {CARPETA_PENDIENTES}: no hay CSV que armar")
        return 0

    for ruta in escritos:
        print(f"CSV generado desde la bandeja: {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
