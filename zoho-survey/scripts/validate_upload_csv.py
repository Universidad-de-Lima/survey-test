"""
Valida archivos CSV subidos antes de procesarlos en GitHub Actions.

ALCANCE (Fase 3.8.3): el validador ACEPTA las 7 categorias de encuesta
y los 10 CSV reales del proyecto (PDF/). Es la PUERTA DE ENTRADA del
boton: que no rechace archivos validos. build_json.py PROCESA por ahora
solo las categorias con mapeo de columnas; el resto pasa la validacion
pero se omite en el ETL (Nivel 2 futuro).

NO confia en metadata del navegador: valida el archivo real en el runner.

Reglas (Fase 3.8.3, coherentes con los CSV reales):
- Nombre: ENCUESTA DE SATISFACCION {CATEGORIA} [- NIVEL] [- PERIODO].csv
  * Separadores espacio/guion equivalentes (ej 'EGRESADOS PREGRADO 2026'
    vs 'ESTUDIANTIL - PREGRADO - 2026-1').
  * NIVEL solo para categorias con pregrado/posgrado (NO DOCENTE no lleva).
  * PERIODO OPCIONAL: 20XX o 20XX-1/20XX-2.
- Headers obligatorias por encuesta exacta: ID de respuesta + NPS +
  columna propia de carrera/programa/dependencia (la CSAT 'La Universidad
  de Lima' NO es universal; se valida en build_json).
- Encoding UTF-8 / UTF-8-BOM / Latin-1.
- Columnas duplicadas -> rechazo.
- Tamano: <=5 MB por archivo, <=50 MB total por lote.
- Duplicados en lote: mismo nombre+hash -> error; mismo hash+nombre
  distinto -> warning.
"""

import re
import sys
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.io_helper import read_csv_robust  # noqa: E402

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024

PERIOD_RE = re.compile(r"(20\d{2}(?:-[12])?)")

# Categorias (singular y plural de DOCENTE aceptados).
CATEGORIES = (
    "ESTUDIANTIL", "GRADUADOS", "POSGRADO", "DOCENTES", "DOCENTE",
    "EGRESADOS", "EMPLEADORES",
)
NO_DOCENTE = "NO DOCENTES"

BASE_CRITICAS = [
    "ID de respuesta",
    "Net Promoter Score (de un total de 10)",
]

# Columna de carrera/programa/dependencia por encuesta EXACTA
# (categoria normalizada, nivel_raw). Coincide con los CSV en PDF/.
CARRERA_HEADER = {
    ("ESTUDIANTIL", "PREGRADO"): "¿Qué carrera profesional estudias?",
    ("ESTUDIANTIL", "POSGRADO"): "¿Qué programa de posgrado estudias?",
    ("GRADUADOS", "PREGRADO"):   "¿Qué carrera profesional estudiaste?",
    ("EGRESADOS", "PREGRADO"):   "¿Qué carrera profesional estudiaste?",
    ("EGRESADOS", "POSGRADO"):   "¿Qué programa de posgrado estudiaste?",
    ("DOCENTES", "PREGRADO"):    "¿Qué carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?",
    ("DOCENTES", "POSGRADO"):    "¿Qué programa de posgrado dictas en la Universidad de Lima?",
    ("NO DOCENTES", None):        "¿A qué dependencia perteneces?",
    ("EMPLEADORES", "PREGRADO"): "¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización?",
    ("EMPLEADORES", "POSGRADO"): "¿Cuál posgrado es el que procede el profesional de la Universidad de Lima contratado por su organización?",
}


def _normalizar_categoria(cat: str) -> str:
    up = cat.upper()
    if up.startswith("NO DOCENTE"):
        return NO_DOCENTE
    if up.startswith("DOCENTE"):
        return "DOCENTES"
    return up


def _nivel_desde_meta(categoria: str, nivel_raw) -> str:
    cat = _normalizar_categoria(categoria)
    if cat == NO_DOCENTE:
        return "nonfaculty"
    if cat == "EMPLEADORES":
        return "employers"
    if cat == "EGRESADOS":
        return "alumni-pg" if nivel_raw == "POSGRADO" else "alumni-ug"
    if cat == "DOCENTES":
        return "faculty-pg" if nivel_raw == "POSGRADO" else "faculty-ug"
    if cat == "GRADUADOS":
        return "graduate"
    if cat in ("ESTUDIANTIL", "ESTUDIANTES"):
        return "postgraduate" if nivel_raw == "POSGRADO" else "undergraduate"
    return None


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_filename(name: str):
    """Devuelve (ok, categoria, nivel, periodo, error). Parser tolerante:
    separadores espacio/guion equivalentes; periodo extraido con regex."""
    low = name.lower()
    if "encuesta de satisfacci" not in low:
        return (False, None, None, None, "Nombre no inicia con ENCUESTA DE SATISFACCION")
    if not low.endswith(".csv"):
        return (False, None, None, None, "Extension no es .csv")

    body = name[:-4]
    m = PERIOD_RE.search(body)
    periodo = m.group(1) if m else None
    body_nop = body.replace(periodo, "", 1) if periodo else body

    tokens = [t for t in re.split(r"[\s\-]+", body_nop) if t]
    i = 0
    while i < len(tokens) and tokens[i].upper() not in CATEGORIES and tokens[i].upper() != "NO":
        i += 1
    if i >= len(tokens):
        return (False, None, None, None, "No se encontro categoria en el nombre")

    tok = tokens[i].upper()
    if tok == "NO":
        if i + 1 < len(tokens) and tokens[i + 1].upper() in ("DOCENTE", "DOCENTES"):
            categoria = NO_DOCENTE
            i += 2
        else:
            return (False, None, None, None, "NO sin DOCENTE/DOCENTES")
    else:
        categoria = _normalizar_categoria(tok)
        i += 1

    nivel_raw = None
    if i < len(tokens) and tokens[i].upper() in ("PREGRADO", "POSGRADO"):
        nivel_raw = tokens[i].upper()
        i += 1

    if categoria == NO_DOCENTE and nivel_raw:
        return (False, categoria, nivel_raw, periodo,
                "NO DOCENTE no debe llevar nivel (PREGRADO/POSGRADO)")
    if categoria != NO_DOCENTE and not nivel_raw:
        return (False, categoria, None, periodo,
                "Falta nivel (PREGRADO/POSGRADO) en " + categoria)
    if i < len(tokens):
        return (False, categoria, nivel_raw, periodo,
                "Elemento inesperado: " + tokens[i])
    return (True, categoria, nivel_raw, periodo, None)


def required_headers(categoria: str, nivel_raw) -> list:
    cols = list(BASE_CRITICAS)
    extra = CARRERA_HEADER.get((categoria, nivel_raw))
    if extra:
        cols.append(extra)
    return cols


def read_headers(path: Path):
    df = read_csv_robust(path)
    return list(df.columns)


def validate_file(path: Path):
    errors = []
    warnings = []
    name = path.name
    size = path.stat().st_size

    if size > MAX_FILE_BYTES:
        errors.append(f"Archivo excede {MAX_FILE_BYTES} bytes ({size})")

    ok, categoria, nivel_raw, periodo, err = parse_filename(name)
    if err:
        errors.append(err)
    if not ok:
        return {"errors": errors, "warnings": warnings,
                "meta": {"name": name, "size": size, "category": categoria,
                         "level": nivel_raw, "period": periodo, "nivel": None,
                         "headers": 0}}

    nivel = _nivel_desde_meta(categoria, nivel_raw)
    if nivel is None:
        errors.append("No se pudo determinar el nivel de la encuesta")

    headers = read_headers(path)
    if len(headers) != len(set(headers)):
        dupes = [h for h in headers if headers.count(h) > 1]
        errors.append(f"Columnas duplicadas: {sorted(set(dupes))}")

    faltantes = [c for c in required_headers(categoria, nivel_raw) if c not in headers]
    if faltantes:
        errors.append(f"Faltan columnas obligatorias: {faltantes}")

    meta = {"name": name, "size": size, "category": categoria,
            "level": nivel_raw, "period": periodo, "nivel": nivel,
            "headers": len(headers)}
    return {"errors": errors, "warnings": warnings, "meta": meta}


def validate_batch(paths: list):
    errors = []
    warnings = []
    total = 0
    seen_hash_name = set()
    seen_hash_names = {}

    if not paths:
        return {"ok": False, "errors": ["Lote vacio"], "warnings": [], "files": []}
    if len(paths) > 10:
        return {"ok": False, "errors": [f"Maximo 10 archivos, recibidos {len(paths)}"],
                "warnings": [], "files": []}

    files = []
    for p in paths:
        res = validate_file(p)
        total += res["meta"].get("size", 0)
        sha = hash_file(p)
        res["meta"]["sha256"] = sha
        files.append(res)

        nm = p.name
        key_hn = f"{sha}|{nm}"
        if key_hn in seen_hash_name:
            res["errors"].append("Archivo duplicado en la seleccion (mismo hash y nombre)")
        seen_hash_name.add(key_hn)

        if sha in seen_hash_names:
            prev_name = seen_hash_names[sha]
            warnings.append(f"Archivo {nm} tiene el mismo contenido que {prev_name}")
        else:
            seen_hash_names[sha] = nm

    for f in files:
        errors.extend(f["errors"])
        warnings.extend(f["warnings"])

    if total > MAX_TOTAL_BYTES:
        errors.append(f"Tamano total excede {MAX_TOTAL_BYTES} bytes ({total})")

    ok = not errors
    return {"ok": ok, "errors": errors, "warnings": warnings, "files": files}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    paths = []
    for arg in argv:
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(
                f for f in p.iterdir()
                if f.is_file() and f.suffix.lower() == ".csv"
                and "ENCUESTA" in f.name.upper()
            ))
        elif p.is_file():
            paths.append(p)

    result = validate_batch(paths)
    for f in result["files"]:
        status = "OK" if not f["errors"] else "ERROR"
        print(f"[{status}] {f['meta']['name']} ({f['meta'].get('size', 0)} bytes)")
        for e in f["errors"]:
            print(f"  ERROR: {e}")
        for w in f["warnings"]:
            print(f"  WARN: {w}")

    if result["errors"]:
        print(f"\nVALIDACION FALLIDA: {len(result['errors'])} error(es)")
        return 1
    print(f"\nVALIDACION EXITOSA: {len(result['files'])} archivo(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
