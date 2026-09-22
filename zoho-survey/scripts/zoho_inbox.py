"""
ZOHO INBOX — Registra en el repositorio una respuesta recibida por webhook.

Uso:
    python3 zoho-survey/scripts/zoho_inbox.py <archivo-con-la-respuesta.json> [nombre-de-la-encuesta]

Lo invoca el flujo .github/workflows/zoho_inbox.yml cuando Zoho Survey empuja
una respuesta: el webhook crea una incidencia en GitHub cuyo cuerpo es la
respuesta en JSON y cuyo titulo es el nombre de la encuesta. Deja la respuesta
en data/zoho_pendientes/<encuesta>.jsonl, ya enmascarada y sin duplicados.

El nombre de la encuesta es opcional: se usa cuando el cuerpo no lo trae.

NO ejecuta el ETL ni publica nada: el procesamiento se hace despues, agrupado
(por intervalo o cuando se pida expresamente), para no lanzar una corrida de
analisis por cada respuesta recibida.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.zoho_respuesta import (  # noqa: E402  (import tras ajustar sys.path)
    agregar_pendiente,
    guardar_pendientes,
    leer_pendientes,
    normalizar_respuesta,
    slug_encuesta,
)

CARPETA_PENDIENTES = Path("data") / "zoho_pendientes"


def main(argv) -> int:
    if len(argv) not in (2, 3):
        print(
            "uso: zoho_inbox.py <archivo-con-la-respuesta.json> [nombre-de-la-encuesta]"
        )
        return 2

    origen = Path(argv[1])
    if not origen.is_file():
        print(f"error: no existe el archivo con la respuesta recibida: {origen}")
        return 2

    try:
        payload = json.loads(origen.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: la respuesta recibida no es JSON valido: {exc}")
        return 1

    encuesta_por_defecto = argv[2].strip() if len(argv) == 3 else ""
    try:
        respuesta = normalizar_respuesta(
            payload, encuesta_por_defecto=encuesta_por_defecto
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 1

    if encuesta_por_defecto and respuesta["encuesta"] == encuesta_por_defecto:
        print(
            "aviso: el nombre de la encuesta se tomo del titulo de la incidencia: "
            f"'{respuesta['encuesta']}'"
        )

    ruta = CARPETA_PENDIENTES / f"{slug_encuesta(respuesta['encuesta'])}.jsonl"
    pendientes = leer_pendientes(ruta)
    actualizados = agregar_pendiente(pendientes, respuesta)

    if len(actualizados) == len(pendientes):
        print(
            f"respuesta {respuesta['id_respuesta']} ya registrada: sin cambios "
            f"({len(pendientes)} pendientes en {ruta})"
        )
        return 0

    guardar_pendientes(ruta, actualizados)
    print(
        f"respuesta {respuesta['id_respuesta']} registrada en {ruta} "
        f"({len(actualizados)} pendientes)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
