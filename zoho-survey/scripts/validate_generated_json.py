"""
SURVEY VALIDATION — Validador de contratos de datos para encuestas.

Valida estructura, tipos y claves de los JSON generados por periodo usando:
  1. JSON Schema Draft-07 (schemas en scripts/schemas/*.schema.json) — fuente canónica de tipos.
  2. Invariantes de negocio cruzadas (no expresables en JSON Schema).

Tambien valida que los index.html tengan las secciones cualitativas requeridas.

Fuentes de verdad:
  - Schemas Draft-07 en scripts/schemas/*.schema.json (unico contrato formal de tipos).
  - ETL (build_json.py) produce los JSONs consumidos por el frontend.
  - CONTRACTS.md documenta los contratos en lenguaje humano.

El validador NO debe ser mas permisivo que el schema. Si el schema rechaza, el validador rechaza.
Las validaciones custom adicionales (suma > 0, facultad_carrera cubre facultades, etc.) son
complementarias y se aplican despues del schema.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Reutilizar I/O helper y configuraciones centrales
from lib.config import RESPUESTAS_TEXTO, CSAT_WEIGHTS, CSAT_SCALE_MAX
from lib.io_helper import load_json
from lib.metrics import calc_promedio_ponderado

# Import opcional de jsonschema (Draft-07). Si no esta instalado, se omite la
# validacion formal y se reporta como warning al usuario.
try:
    import jsonschema
    from jsonschema import Draft7Validator
    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False

BASE_DIR: Path = Path(__file__).resolve().parent
ROOT_DIR: Path = BASE_DIR.parent / "students"
SCHEMAS_DIR: Path = BASE_DIR / "schemas"

# ---------------------------------------------------------------------------
# Mapping de archivo -> schema filename. Solo se validan con schema los archivos
# que tienen uno formal definido. Los archivos legacy no se validan con schema.
# ---------------------------------------------------------------------------
SCHEMA_BY_FILE: Dict[str, str] = {
    "dashboard_data.json": "dashboard_data.schema.json",
    "filtros.json": "filtros.schema.json",
    "sentimiento.json": "sentimiento.schema.json",
    "dimensiones.json": "dimensiones.schema.json",
    "ids.json": "ids.schema.json",
    "nps_ciclo_carrera.json": "nps_ciclo_carrera.schema.json",
    "csat_ciclo_carrera.json": "csat_ciclo_carrera.schema.json",
}

# Archivos obligatorios por periodo (shape minimo; el schema formal vive en SCHEMA_BY_FILE).
REQUIRED_PERIOD_FILES: Dict[str, Dict[str, any]] = {
    "dashboard_data.json": dict(type=dict, non_empty=True),
    "dimensiones.json": dict(type=list, non_empty=True),
    "ids.json": dict(type=list, non_empty=True),
    "nps_ciclo_carrera.json": dict(type=list, non_empty=True),
    "csat_ciclo_carrera.json": dict(type=list, non_empty=True),
    "filtros.json": dict(type=dict, non_empty=True),
    "sentimiento.json": dict(type=dict, non_empty=True),
}

# Archivos legacy: validados si existen, pero su ausencia no genera error.
LEGACY_PERIOD_FILES: Dict[str, Dict[str, any]] = {
    "nps_carrera.json": dict(type=list, non_empty=True),
    "csat_carrera.json": dict(type=list, non_empty=True),
}

# Derivar llaves de respuestas del catalogo central
SAT_KEYS: Set[str] = set(RESPUESTAS_TEXTO[:5])
VISIBILITY_KEYS: Set[str] = set(RESPUESTAS_TEXTO[5:7])
REQUIRED_RESPONSE_KEYS: Set[str] = SAT_KEYS | VISIBILITY_KEYS

REQUIRED_FILTROS_KEYS: Set[str] = {"has_ciclo", "facultades", "carreras", "ciclos", "facultad_carrera"}
REQUIRED_CROSS_KEYS: Set[str] = {"facultad", "carrera", "ciclo"}


# ---------------------------------------------------------------------------
# Carga y cache de schemas
# ---------------------------------------------------------------------------
_SCHEMA_CACHE: Dict[str, dict] = {}


def load_schema(schema_filename: str) -> dict:
    """Carga y cachea un JSON Schema desde scripts/schemas/."""
    if schema_filename in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_filename]
    path = SCHEMAS_DIR / schema_filename
    if not path.exists():
        raise FileNotFoundError(f"Schema no encontrado: {path}")
    schema = load_json(path)
    _SCHEMA_CACHE[schema_filename] = schema
    return schema


def validate_with_schema(value: any, schema_filename: str, json_path: Path) -> List[str]:
    """
    Valida un valor contra un JSON Schema Draft-07.
    Retorna una lista de mensajes de error (vacia si es valido).
    """
    if not HAVE_JSONSCHEMA:
        return [f"[{json_path.name}] validacion JSON Schema omitida: libreria jsonschema no instalada"]

    try:
        schema = load_schema(schema_filename)
    except (FileNotFoundError, ValueError) as exc:
        return [f"[{json_path.name}] no se pudo cargar schema {schema_filename}: {exc}"]

    errors: List[str] = []
    validator = Draft7Validator(schema)
    for err in validator.iter_errors(value):
        # Formatear ruta legible: /resumen/nps/score
        location = "/".join(str(p) for p in err.absolute_path) or "(raiz)"
        errors.append(f"[{json_path.name}] schema {schema_filename}: {location}: {err.message}")

    return errors


# ---------------------------------------------------------------------------
# Validaciones de shape y helpers (mantenidas por retrocompatibilidad)
# ---------------------------------------------------------------------------
def validate_shape(value: any, expected_type: type, non_empty: bool) -> None:
    """Verifica que un valor coincida con el tipo y restriccion de vacio esperados."""
    if not isinstance(value, expected_type):
        raise ValueError(f"se esperaba {expected_type.__name__}, se encontro {type(value).__name__}")
    if non_empty and not value:
        raise ValueError("estructura vacia")


def require_keys(value: any, keys: Set[str], label: str) -> None:
    """Valida la presencia de un set de llaves requeridas dentro de un objeto/diccionario."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} debe ser un objeto")
    missing = keys - value.keys()
    if missing:
        raise ValueError(f"{label} no contiene las llaves requeridas: {sorted(missing)}")


def require_numeric(value: dict, keys: Set[str], label: str) -> None:
    """Valida que los campos declarados dentro de un diccionario sean valores numericos."""
    for key in keys:
        if not isinstance(value.get(key), (int, float)):
            raise ValueError(f"{label}.{key} debe ser numerico")


# ---------------------------------------------------------------------------
# Validaciones de invariantes de negocio (complementarias al schema)
# ---------------------------------------------------------------------------
def validate_filtros_invariants(value: dict) -> None:
    """Valida invariantes de filtros.json no expresables en JSON Schema."""
    require_keys(value, REQUIRED_FILTROS_KEYS, "filtros.json")
    has_ciclo = value.get("has_ciclo", True)

    for key in ("facultades", "carreras"):
        if not isinstance(value.get(key), list) or not value[key]:
            raise ValueError(f"filtros.{key} debe ser una lista no vacia")
        if not all(isinstance(item, str) and item.strip() for item in value[key]):
            raise ValueError(f"filtros.{key} debe contener unicamente textos no vacios")

    if not isinstance(value.get("ciclos"), list):
        raise ValueError("filtros.ciclos debe ser una lista")
    if has_ciclo and not value["ciclos"]:
        raise ValueError("filtros.ciclos debe ser una lista no vacia cuando has_ciclo=true")
    if value["ciclos"] and not all(isinstance(item, str) and item.strip() for item in value["ciclos"]):
        raise ValueError("filtros.ciclos debe contener unicamente textos no vacios")

    facultad_carrera = value.get("facultad_carrera")
    if not isinstance(facultad_carrera, dict) or not facultad_carrera:
        raise ValueError("filtros.facultad_carrera debe ser un objeto no vacio")

    # Invariante: facultad_carrera debe cubrir TODAS las facultades listadas
    for facultad in value["facultades"]:
        if facultad not in facultad_carrera:
            raise ValueError(f"filtros.facultad_carrera no mapea la facultad: {facultad}")
        if not isinstance(facultad_carrera[facultad], list):
            raise ValueError(f"filtros.facultad_carrera.{facultad} debe ser una lista")


def validate_dimensiones_invariants(value: List[dict]) -> None:
    """Invariante: al menos una fila con total > 0."""
    rows_with_data = sum(1 for row in value if isinstance(row, dict) and row.get("total", 0) > 0)
    if not rows_with_data:
        raise ValueError("dimensiones.json no contiene filas validas con total > 0")


def validate_id_rows_invariants(value: List[dict], filename: str) -> None:
    """Invariante: la suma total debe ser > 0."""
    total = 0
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{filename}[{index}] debe ser un objeto")
        # Soporta 'total' (canonico) y 'count' (legacy)
        key = "total" if "total" in row else "count"
        if key not in row:
            raise ValueError(f"{filename}[{index}] no contiene 'total' ni 'count'")
        if not isinstance(row.get(key), (int, float)):
            raise ValueError(f"{filename}[{index}].{key} debe ser numerico")
        total += row.get(key, 0)
    if total <= 0:
        raise ValueError(f"{filename} no contiene conteos acumulados positivos")


def validate_sentimiento_invariants(value: dict) -> None:
    """Valida invariantes de sentimiento.json no expresables en JSON Schema."""
    # Validar que cada comentario tenga 'es_valido' booleano (reafirmacion)
    for index, comentario in enumerate(value.get("comentarios", [])):
        if not isinstance(comentario, dict):
            raise ValueError(f"sentimiento.comentarios[{index}] debe ser un objeto")
        if not isinstance(comentario.get("es_valido"), bool):
            raise ValueError(f"sentimiento.comentarios[{index}].es_valido debe ser booleano")


def validate_dashboard_csat_extended(value: dict) -> None:
    """Invariantes de los indicadores extendidos de CSAT (T2B y Promedio Ponderado).

    Son condicionales: solo se validan si los campos están presentes, para
    mantener compatibilidad con periodos generados antes de su incorporación.
    """
    csat = value.get("resumen", {}).get("csat", {})
    if not isinstance(csat, dict):
        return

    t3b = csat.get("t3b")
    total = csat.get("total")

    # Monotonia de boxes anidados: t2b <= t3b <= total
    if "t2b" in csat and t3b is not None and total is not None:
        t2b = csat["t2b"]
        if not (0 <= t2b <= t3b <= total):
            raise ValueError(
                f"dashboard_data.resumen.csat: violates t2b <= t3b <= total (t2b={t2b}, t3b={t3b}, total={total})"
            )

    # Recalculo del promedio ponderado desde la distribucion top-level y verificacion
    csat_dist = value.get("csat")
    if "ponderado" in csat and isinstance(csat_dist, dict):
        counts = [int(csat_dist.get(r, 0)) for r in RESPUESTAS_TEXTO[:5]]
        esperado = calc_promedio_ponderado(counts, CSAT_WEIGHTS, CSAT_SCALE_MAX)
        almacenado = csat["ponderado"]
        if abs(esperado - almacenado) > 1e-6:
            raise ValueError(
                f"dashboard_data.resumen.csat.ponderado={almacenado} no coincide con el recalculo ({esperado:.6f}) desde la distribucion csat"
            )


# ---------------------------------------------------------------------------
# Despachador principal de validacion por archivo
# ---------------------------------------------------------------------------
def validate_json_file(json_dir: Path, filename: str, spec: Dict[str, any]) -> Tuple[any, List[str]]:
    """
    Carga y valida un archivo JSON individual.
    Retorna (value, lista_de_errores_schema).
    Las validaciones custom lanzan ValueError; los errores de schema se acumulan.
    """
    path = json_dir / filename
    if not path.exists():
        raise ValueError("archivo requerido ausente")
    value = load_json(path)
    validate_shape(value, spec["type"], spec["non_empty"])

    schema_errors: List[str] = []
    if filename in SCHEMA_BY_FILE:
        schema_errors = validate_with_schema(value, SCHEMA_BY_FILE[filename], path)

    # Invariantes de negocio (complementarias al schema)
    if filename == "filtros.json":
        validate_filtros_invariants(value)
    elif filename == "dimensiones.json":
        validate_dimensiones_invariants(value)
    elif filename == "ids.json":
        validate_id_rows_invariants(value, filename)
    elif filename == "sentimiento.json":
        validate_sentimiento_invariants(value)
    elif filename == "dashboard_data.json":
        validate_dashboard_csat_extended(value)

    return value, schema_errors


# ---------------------------------------------------------------------------
# Validacion del HTML del periodo (sin cambios funcionales)
# ---------------------------------------------------------------------------
def validate_period_html(period_dir: Path) -> Tuple[List[str], List[str]]:
    """Verifica que el index.html del periodo contenga los enlaces y contenedores del modulo cualitativo."""
    path = period_dir / "index.html"
    if not path.exists():
        return [f"{path}: archivo index.html requerido ausente"]
    try:
        html = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: no se pudo leer el archivo: {exc}"]

    required_fragments = [
        '<a href="#cualitativo">Cualitativo</a>',
        'ANALISIS CUALITATIVO',
        'id="cualitativo"',
        'id="cualitativo-heading"',
    ]
    normalized = (
        html.replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
    )
    errors = []
    for fragment in required_fragments:
        if fragment not in normalized and fragment not in html:
            errors.append(f"{path}: no contiene fragmento requerido: {fragment}")

    # ── Fase 2: Validación de IDs de filtros (contrato público dashboard.js) ──
    filter_suffixes = ["top3", "radar", "preguntas", "detalle", "visibilidad"]
    for suffix in filter_suffixes:
        if f'id="filter-facultad-{suffix}"' not in html:
            errors.append(f"{path}: falta ID de filtro: filter-facultad-{suffix}")
        if suffix != "detalle":
            if f'id="filter-carrera-{suffix}"' not in html:
                errors.append(f"{path}: falta ID de filtro: filter-carrera-{suffix}")
        if f'id="filter-ciclo-{suffix}"' not in html:
            errors.append(f"{path}: falta ID de filtro: filter-ciclo-{suffix}")
        if f'id="reset-{suffix}"' not in html:
            errors.append(f"{path}: falta ID de filtro: reset-{suffix}")

    # ── Validación de sección cualitativa (warnings, no errores) ──
    # Estos IDs son del template actual y del contrato publico de
    # components/sentiment-view.js. Se reportan como advertencia para no
    # bloquear el pipeline si los HTMLs no se han regenerado.
    warnings = []
    sentimiento_ids = [
        'id="sentiment-kpis"',
        'id="sentimiento-bar-chart"',
        'id="explorador-search"',
        'id="explorador-sentimiento"',
        'id="tabla-explorador-comentarios"',
        'id="insight-cualitativo"',
        'id="insight-cualitativo-categorias"',
    ]
    for sid in sentimiento_ids:
        if sid not in html:
            warnings.append(f"{path}: ID cualitativo no encontrado (requiere regeneración): {sid}")

    return errors, warnings


# ---------------------------------------------------------------------------
# Orquestacion por periodo y por nivel
# ---------------------------------------------------------------------------
def validate_period(period_dir: Path) -> Tuple[List[str], List[str]]:
    """Valida por completo un directorio de periodo (JSONs y index.html)."""
    errors: List[str] = []
    warnings: List[str] = []
    json_dir = period_dir / "json"
    if not json_dir.is_dir():
        return [f"{period_dir}: no existe carpeta json"], warnings

    html_errors, html_warnings = validate_period_html(period_dir)
    errors.extend(html_errors)
    warnings.extend(html_warnings)

    # Descubrir has_ciclo leyendo filtros.json primero
    has_ciclo = True
    filtros_path = json_dir / "filtros.json"
    if filtros_path.exists():
        try:
            filtros_val = load_json(filtros_path)
            has_ciclo = filtros_val.get("has_ciclo", True)
        except (ValueError, FileNotFoundError):
            pass

    required = dict(REQUIRED_PERIOD_FILES)
    if not has_ciclo:
        # Si no hay ciclos escolares, estos archivos pueden estar vacios
        required["nps_ciclo_carrera.json"] = dict(type=list, non_empty=False)
        required["csat_ciclo_carrera.json"] = dict(type=list, non_empty=False)

    for filename, spec in required.items():
        path = json_dir / filename
        try:
            _, schema_errors = validate_json_file(json_dir, filename, spec)
            errors.extend(schema_errors)
        except ValueError as exc:
            errors.append(f"{path}: {exc}")

    for filename, spec in LEGACY_PERIOD_FILES.items():
        path = json_dir / filename
        if not path.exists():
            continue
        try:
            value = load_json(path)
            validate_shape(value, spec["type"], spec["non_empty"])
        except ValueError as exc:
            errors.append(f"{path}: archivo legado invalido: {exc}")
        else:
            warnings.append(f"{path}: archivo legado/deprecado; no debe ser contrato obligatorio")

    return errors, warnings


def read_periods(level_dir: Path) -> List[str]:
    """Lee y valida el catalogo periodos.json de un nivel academico."""
    periodos_path = level_dir / "periodos.json"
    periodos = load_json(periodos_path)
    if not isinstance(periodos, list) or not periodos:
        raise ValueError(f"{periodos_path}: debe ser una lista no vacia")

    ids = []
    seen = set()
    new_count = 0
    for item in periodos:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError(f"{periodos_path}: cada periodo debe tener la llave id")
        period_id = str(item["id"])
        if period_id in seen:
            raise ValueError(f"{periodos_path}: periodo duplicado detectado: {period_id}")
        seen.add(period_id)
        ids.append(period_id)
        if item.get("isNew") is True:
            new_count += 1

    if new_count != 1:
        raise ValueError(f"{periodos_path}: debe existir exactamente un periodo con la propiedad isNew=true")

    return ids


def main() -> int:
    if not HAVE_JSONSCHEMA:
        print("ADVERTENCIA: la libreria 'jsonschema' no esta instalada; la validacion formal Draft-07 se omitira.")
        print("             Instalar con: pip install jsonschema")
        print()

    levels = sys.argv[1:] or ["undergraduate", "graduate"]
    all_errors: List[str] = []
    all_warnings: List[str] = []

    for level in levels:
        level_dir = ROOT_DIR / level
        if not level_dir.is_dir():
            all_errors.append(f"{level_dir}: nivel academico inexistente")
            continue

        try:
            period_ids = read_periods(level_dir)
        except ValueError as exc:
            all_errors.append(str(exc))
            continue

        for period_id in period_ids:
            period_dir = level_dir / period_id
            # Skip placeholder periods (e.g., "proximamente" pointing to
            # underconstruction.html) that don't have a real folder with JSONs.
            # These are valid entries in periodos.json but have no data to validate.
            if not period_dir.is_dir():
                continue
            errors, warnings = validate_period(period_dir)
            all_errors.extend(errors)
            all_warnings.extend(warnings)

    if all_warnings:
        print("Advertencias de contrato JSON:")
        for warning in all_warnings:
            print(f"- {warning}")
        print()

    if all_errors:
        print("Errores de contrato JSON:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print("Contratos JSON validos (schema Draft-07 + invariantes de negocio).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
