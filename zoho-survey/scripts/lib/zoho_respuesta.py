"""
ZOHO RESPUESTA — Normalizacion de las respuestas que llegan por webhook.

Zoho Survey puede empujar cada respuesta a una URL externa (Builder -> Hub ->
Triggers -> Webhook). Este modulo convierte ese envio en el registro interno
que guarda la bandeja de entrada, SIN llamar a ningun servicio externo:

    { "id_respuesta": "...", "encuesta": "...", "recibido_en": "ISO-8601",
      "respuestas": { ...preguntas y valores, ya enmascarados... } }

Reglas de negocio:

  - El identificador de respuesta es obligatorio: es lo que evita guardar dos
    veces la misma respuesta cuando Zoho reintenta el envio.
  - El nombre de la encuesta (categoria + periodo, p. ej. "ESTUDIANTIL 2026-1")
    es obligatorio: define a que grupo y periodo pertenece la respuesta.
  - Los datos personales se enmascaran ANTES de guardar, porque el repositorio
    es publico (se reutiliza enmascarar_pii del modulo io_helper).
  - Los campos desconocidos se conservan tal cual: Zoho puede anadir preguntas
    sin aviso y no conviene perder informacion.
"""

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.io_helper import enmascarar_pii

# Nombres aceptados para el identificador de respuesta y para la encuesta. Zoho
# los nombra como el usuario los escriba al configurar el webhook: se aceptan
# varias formas razonables. La clave "ID" es la que envia el webhook real (llega
# como cuerpo de la incidencia que crea en GitHub).
CLAVES_ID = ("ID", "ID de respuesta", "id_respuesta", "Response ID", "response_id")
CLAVES_ENCUESTA = ("Encuesta", "encuesta", "Survey", "survey")


def _buscar(payload: Dict[str, Any], claves) -> Optional[Any]:
    for clave in claves:
        if clave in payload and str(payload[clave]).strip():
            return payload[clave]
    return None


def _enmascarar_valor(valor: Any) -> Any:
    """Aplica el enmascarado de datos personales a texto, listas y objetos."""
    if isinstance(valor, str):
        return enmascarar_pii(valor)
    if isinstance(valor, list):
        return [_enmascarar_valor(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _enmascarar_valor(v) for k, v in valor.items()}
    return valor


def slug_encuesta(nombre: str) -> str:
    """Nombre de archivo seguro a partir del nombre de la encuesta."""
    base = unicodedata.normalize("NFKD", str(nombre))
    base = base.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()
    return base or "sin-nombre"


def normalizar_respuesta(
    payload: Any,
    momento: Optional[str] = None,
    encuesta_por_defecto: Optional[str] = None,
) -> Dict[str, Any]:
    """Convierte la respuesta recibida de Zoho en el registro interno.

    Args:
        payload: objeto JSON con pares nombre/valor (cuerpo del webhook).
        momento: marca de tiempo ISO-8601; si no se indica, se usa la actual.
        encuesta_por_defecto: nombre de la encuesta cuando el cuerpo no lo trae
            (el webhook lo envia en el titulo de la incidencia).

    Returns:
        dict con id_respuesta, encuesta, recibido_en y respuestas (enmascaradas).

    Raises:
        ValueError: si el payload no es un objeto, o si falta el identificador
            de respuesta o el nombre de la encuesta (fallo explicito, sin
            guardar nada a medias).
    """
    if not isinstance(payload, dict):
        raise ValueError(
            "la respuesta recibida debe ser un objeto JSON de pares nombre/valor"
        )

    id_respuesta = _buscar(payload, CLAVES_ID)
    if id_respuesta is None:
        raise ValueError(
            "falta el identificador de respuesta: agrega un campo llamado "
            + " o ".join(f"'{c}'" for c in CLAVES_ID[:2])
        )

    encuesta = _buscar(payload, CLAVES_ENCUESTA)
    if encuesta is None and encuesta_por_defecto and str(encuesta_por_defecto).strip():
        encuesta = str(encuesta_por_defecto).strip()
    if encuesta is None:
        raise ValueError(
            "falta la encuesta (categoria + periodo, p. ej. 'ESTUDIANTIL 2026-1'): "
            "agrega un campo llamado " + " o ".join(f"'{c}'" for c in CLAVES_ENCUESTA[:2])
        )

    respuestas = {
        clave: _enmascarar_valor(valor)
        for clave, valor in payload.items()
        if clave not in CLAVES_ID + CLAVES_ENCUESTA
    }

    return {
        "id_respuesta": str(id_respuesta).strip(),
        "encuesta": str(encuesta).strip(),
        "recibido_en": momento or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "respuestas": respuestas,
    }


def respuesta_ya_registrada(
    pendientes: List[Dict[str, Any]], id_respuesta: str
) -> bool:
    """True si el identificador ya esta en la bandeja de entrada."""
    return any(p.get("id_respuesta") == id_respuesta for p in pendientes or [])


def agregar_pendiente(
    pendientes: List[Dict[str, Any]], respuesta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Devuelve la lista con la respuesta agregada; si ya estaba, no la duplica."""
    lista = list(pendientes or [])
    if respuesta_ya_registrada(lista, respuesta.get("id_respuesta")):
        return lista
    lista.append(respuesta)
    return lista


def leer_pendientes(ruta: Path) -> List[Dict[str, Any]]:
    """Lee la bandeja de entrada (un JSON por linea). Vacia si no existe."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return []

    pendientes: List[Dict[str, Any]] = []
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip():
            continue
        try:
            pendientes.append(json.loads(linea))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"la linea {numero} del archivo de pendientes no es JSON valido: {exc}"
            ) from exc
    return pendientes


def guardar_pendientes(ruta: Path, pendientes: List[Dict[str, Any]]) -> None:
    """Escribe la bandeja de entrada: un JSON por linea, en UTF-8."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    lineas = [json.dumps(p, ensure_ascii=False, sort_keys=True) for p in pendientes or []]
    ruta.write_text("\n".join(lineas) + ("\n" if lineas else ""), encoding="utf-8")
