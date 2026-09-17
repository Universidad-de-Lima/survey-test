"""
SURVEY ETL CSV EXPORTER — Exportación de datos a CSV y ZIP.

Genera dos archivos CSV (análisis cualitativo y respuestas por dimensión)
y los empaqueta en un archivo ZIP. Incluye protección contra formula
injection en celdas con prefijos =, +, -, @.
"""

import logging
import re
import zipfile
from pathlib import Path
from typing import Dict

import pandas as pd

from lib.config import COLUMN_RENAME_PREGRADO, COLUMN_RENAME_GRADUADO
from lib.io_helper import enmascarar_pii


def _sanitizar_nombre_csv(filename: str) -> str:
    """Convierte nombre de archivo CSV a formato limpio con guiones bajos."""
    name = filename.replace(".csv", "").lower()
    name = re.sub(r"[^a-z0-9áéíóúñü]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def _csv_escape(val) -> str:
    """Escapa un valor para CSV protegiendo contra formula injection.

    Defensa en profundidad:
      - Prefijos =, +, -, @: prepende comilla simple (formula injection).
      - Tab y CR dentro de celdas: reemplaza con espacio (evita CSV smuggling).
      - Comas, comillas dobles, newlines: quoting CSV estandar.
    """
    s = str(val) if val is not None else ""
    # Reemplazar tab y CR con espacio (defensa contra CSV smuggling)
    s = s.replace("\t", " ").replace("\r", " ")
    if s and s[0] in ('=', '+', '-', '@'):
        s = "'" + s
    if "," in s or '"' in s or "\n" in s:
        return f'"{s.replace(chr(34), chr(34)+chr(34))}"'
    return s


def generar_csvs_y_zip(
    df: pd.DataFrame,
    comentarios_detallados: list,
    ruta_salida: Path,
    csv_file: Path,
    nivel: str,
    categoria_dim: Dict[str, str],
    nps_col: str,
    csat_col: str,
    comentario_col: str,
) -> None:
    """Genera dos CSVs (analisis_cualitativo + respuestas_dimensiones)
    y los empaqueta en un ZIP dentro del directorio de salida."""
    nombre_base = _sanitizar_nombre_csv(csv_file.name)
    fecha = pd.Timestamp.now().strftime("%Y-%m-%d")

    # Reverse mapping (renombrado → original)
    rev_pregrado = {v: k for k, v in COLUMN_RENAME_PREGRADO.items()}
    rev_graduado = {v: k for k, v in COLUMN_RENAME_GRADUADO.items()}
    rev_map = rev_graduado if nivel == "graduate" else rev_pregrado

    # ── CSV 1: analisis_cualitativo ──
    csv1_headers = [
        "ID", "CID", "Carrera", "Facultad", "Ciclo",
        "NPS Score", "Sentimiento", "Intensidad",
        "Tema", "Tema Padre",
        "Comentario Original", "Comentario Corregido"
    ]
    csv1_rows = []
    for c in comentarios_detallados:
        # Redactar PII en campos de texto libre (comentarios) antes de exportar.
        # Defensa en profundidad: los ZIPs ya no se despliegan en GitHub Pages,
        # pero los CSVs pueden descargarse localmente para auditoria.
        csv1_rows.append([
            (c.get("comentario_id_original", "") or "").rsplit("_", 1)[0] if "_" in (c.get("comentario_id_original", "") or "") else (c.get("comentario_id_original", "") or ""),
            c.get("id", ""),
            c.get("carrera", ""),
            c.get("facultad", ""),
            c.get("ciclo", ""),
            c.get("nps_score", ""),
            c.get("sentimiento", ""),
            c.get("intensidad", ""),
            c.get("aspecto_normalizado", ""),
            c.get("categoria_padre", ""),
            enmascarar_pii(c.get("comentario_original", "")),
            enmascarar_pii(c.get("fragmento_mostrar", "")),
        ])
    csv1_name = f"analisis_cualitativo_{nombre_base}.csv"

    # ── CSV 2: respuestas por dimensión ──
    dim_cols_renamed = [d for d in categoria_dim.keys() if d in df.columns]
    csv2_headers = ["ID", "Carrera"]
    if "Situación laboral" in df.columns:
        csv2_headers.append("Situación laboral")
    if "Tiempo laboral" in df.columns:
        csv2_headers.append("Tiempo laboral")
    csv2_headers.append("Facultad")
    if "Ciclo" in df.columns:
        csv2_headers.append("Ciclo")

    for d_renamed in dim_cols_renamed:
        csv2_headers.append(rev_map.get(d_renamed, d_renamed))

    rev_carrera = rev_map.get("La carrera", "Tu carrera")
    csv2_headers.append(rev_carrera)
    csv2_headers.append(rev_map.get(csat_col, csat_col))
    csv2_headers.append(rev_map.get(nps_col, nps_col))
    csv2_headers.append("Comentario Original")

    csv2_rows = []
    for _, row in df.iterrows():
        r = [
            row.get("ID", ""),
            row.get("Carrera", ""),
        ]
        if "Situación laboral" in df.columns:
            r.append(row.get("Situación laboral", ""))
        if "Tiempo laboral" in df.columns:
            r.append(row.get("Tiempo laboral", ""))
        r.append(row.get("Facultad", ""))
        if "Ciclo" in df.columns:
            r.append(row.get("Ciclo", ""))

        for d_renamed in dim_cols_renamed:
            r.append(row.get(d_renamed, ""))

        r.append(row.get("La carrera", ""))
        r.append(row.get(csat_col, ""))
        r.append(row.get(nps_col, ""))
        r.append(enmascarar_pii(row.get(comentario_col, "")))
        csv2_rows.append(r)

    csv2_name = f"{nombre_base}.csv"
    zip_name = f"data_{nombre_base}.zip"

    # ── Escribir ZIP ──
    # Los ZIPs se guardan en directorio "exports/" (hermano de "json/")
    # para evitar que se desplieguen en GitHub Pages con PII potencial.
    # El directorio exports/ se excluye del artifact de Pages.
    exports_dir = ruta_salida.parent / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    zip_path = exports_dir / zip_name
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            csv1_content = "\ufeff" + ",".join(csv1_headers) + "\n"
            csv1_content += "\n".join(
                ",".join(_csv_escape(v) for v in row) for row in csv1_rows
            )
            zf.writestr(csv1_name, csv1_content.encode("utf-8-sig"))

            csv2_content = "\ufeff" + ",".join(csv2_headers) + "\n"
            csv2_content += "\n".join(
                ",".join(_csv_escape(v) for v in row) for row in csv2_rows
            )
            zf.writestr(csv2_name, csv2_content.encode("utf-8-sig"))

        logging.info(
            f"ZIP generado: {zip_name} ({len(csv1_rows)} comentarios, "
            f"{len(csv2_rows)} encuestados)"
        )
    except (OSError, zipfile.BadZipFile, Exception) as exc:
        # CAL-03: restringido a excepciones de I/O y ZIP.
        logging.warning(f"No se pudo generar ZIP {zip_name}: {exc}")
