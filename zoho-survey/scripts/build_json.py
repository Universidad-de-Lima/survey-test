"""
ETL PIPELINE — Transforma y agrega datos de encuestas de Zoho Survey.

Importa mapeos centralizados, calcula métricas de NPS/CSAT,
clasifica tópicos cualitativos y genera archivos JSON de contratos de datos.
"""

import pandas as pd
import json
import os
import re
import logging
import time
from pathlib import Path
from shutil import copyfile
from collections import defaultdict
from typing import Dict, List, Set

# Sin python-dotenv: el proyecto se ejecuta unicamente en GitHub Actions, donde
# las variables llegan por entorno (Secrets). No se lee ningun archivo .env.

# Importar configuración, métricas, nlp e io_helpers modularizados
from lib.config import (
    COLUMN_RENAME_PREGRADO,
    COLUMN_RENAME_GRADUADO,
    CARRERA_FACULTAD,
    CATEGORIA_DIMENSION_PREGRADO,
    CATEGORIA_DIMENSION_UNIFICADA,
    CATEGORIA_DIMENSION_GRADUADO,
    RESPUESTAS_TEXTO,
    CSAT_WEIGHTS,
    CSAT_SCALE_MAX,
    ETAPA_MAP,
    EMPLEABILIDAD_CATEGORIAS,
    resolver_config_etl,
    clasificar_categoria_dimension
)
from lib.metrics import calc_nps, calc_csat, calc_promedio_ponderado, calc_nps_carrera, calc_csat_carrera
from lib.io_helper import read_csv_robust, normalize_dates, hash_csv, csv_cambiado, guardar_hash_csv, enmascarar_pii
from lib.csv_exporter import generar_csvs_y_zip, _sanitizar_nombre_csv
from lib.dashboard_builder import construir_dashboard_data
from lib.periodos_updater import actualizar_periodos

# Configurar logging nativo de Python
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR.parent.parent / "data"
ZOHO_DIR: Path = BASE_DIR.parent
STUDENTS_DIR: Path = ZOHO_DIR / "students"

SURVEY_DIRS: Dict[str, Path] = {
    "undergraduate": STUDENTS_DIR / "undergraduate",
    "graduate": STUDENTS_DIR / "graduate",
    "postgraduate": STUDENTS_DIR / "postgraduate",
    "alumni-ug": ZOHO_DIR / "alumni" / "undergraduate",
    "alumni-pg": ZOHO_DIR / "alumni" / "postgraduate",
    "faculty-ug": ZOHO_DIR / "facultystaff" / "undergraduate",
    "faculty-pg": ZOHO_DIR / "facultystaff" / "postgraduate",
    "nonfaculty": ZOHO_DIR / "nonfacultystaff",
    "employers": ZOHO_DIR / "employers",
}

SUPPORTED_EXTENSIONS: List[str] = [".csv"]


# ============================================================
# FUNCIONES EXTRAÍDAS (Fase 11: refactorización estructural)
# Funciones puras testeables extraídas de main() para mejorar mantenibilidad.
# NO cambian comportamiento: mismo CSV → mismo JSON.
# ============================================================

def _detectar_nivel(filename: str) -> str:
    """Detecta el nivel de encuesta desde el nombre del archivo.
    
    Usa substring matching sobre el filename en mayúsculas.
    Retorna el nivel o None si no se puede determinar.
    """
    filename_upper = filename.upper()
    if "NO DOCENTE" in filename_upper:
        return "nonfaculty"
    elif "EMPLEADORES" in filename_upper:
        return "employers"
    elif "EGRESADOS" in filename_upper:
        return "alumni-pg" if "POSGRADO" in filename_upper else "alumni-ug"
    elif "DOCENTE" in filename_upper:
        return "faculty-pg" if "POSGRADO" in filename_upper else "faculty-ug"
    elif "GRADUADOS" in filename_upper:
        return "graduate"
    elif "ESTUDIANTIL" in filename_upper or "ESTUDIANTES" in filename_upper:
        return "postgraduate" if "POSGRADO" in filename_upper else "undergraduate"
    else:
        return None


def _detectar_dimensiones(df) -> "Dict[str, str]":
    """Detecta dimensiones CSAT por columna (Fase 2).

    Una columna es dimension si sus valores no nulos son subconjunto de
    RESPUESTAS_TEXTO (escala Likert de satisfaccion). Se clasifica en
    categoria padre por palabra clave. Las columnas numericas y PII se
    excluyen. Devuelve {columna_original: categoria_padre}.
    """
    resp = set(RESPUESTAS_TEXTO)
    skip = {"ID de respuesta", "ID", "Start time", "Hora de finalizacion",
            "Net Promoter Score (de un total de 10)", "Recomiendas la Universidad de Lima",
            "La Universidad de Lima", "Carrera", "Facultad", "Ciclo",
            "Comentario NPS", "CSAT Score", "Inicio", "Fin"}
    out = {}
    for col in df.columns:
        if col in skip:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        vals = df[col].dropna().astype(str)
        if len(vals) == 0:
            continue
        if set(vals.unique()).issubset(resp):
            out[col] = clasificar_categoria_dimension(col)
    return out


def _inyectar_html(template_index: Path, index_file: Path, periodo_dir: Path, zoho_dir: Path) -> bool:
    """Copia el template HTML al directorio del periodo, reemplazando {{SHARED_PATH}}.
    
    Retorna True si tuvo éxito con inyección, False si usó fallback (copyfile directo).
    """
    try:
        rel_parent = periodo_dir.relative_to(zoho_dir)
        depth = len(rel_parent.parts)
        shared_path = "/".join([".."] * depth) + "/shared"
        
        html_content = template_index.read_text(encoding="utf-8")
        html_content = html_content.replace("{{SHARED_PATH}}", shared_path)
        # Cache-busting: inject build version (timestamp) for JS/CSS assets.
        # This ensures browsers fetch fresh assets on every build, avoiding
        # stale pages after deploys to GitHub Pages.
        html_content = html_content.replace("{{BUILD_VERSION}}", str(int(time.time())))
        index_file.write_text(html_content, encoding="utf-8")
        logging.info(f"Plantilla HTML copiada e inyectada con shared_path '{shared_path}' para {periodo_dir.relative_to(zoho_dir)}")
        return True
    except Exception as html_err:
        logging.error(f"Error al escribir index.html con shared_path para {periodo_dir}: {html_err}")
        copyfile(template_index, index_file)
        return False


def main() -> None:
    if not DATA_DIR.is_dir():
        logging.error(f"El directorio de datos de entrada no existe: {DATA_DIR}")
        return

    csv_files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and "ENCUESTA" in f.name.upper()
    ]

    if not csv_files:
        logging.warning("No se encontraron archivos CSV con el patrón 'ENCUESTA' en data/.")
        return

    periodos_por_nivel = defaultdict(set)
    _build_start = time.perf_counter()
    _timings: Dict[str, float] = {}

    for csv_file in csv_files:
        _csv_start = time.perf_counter()
        filename = csv_file.name.upper()
        logging.info(f"Iniciando procesamiento de: {csv_file.name}")

        # Detección del nivel de encuesta (Fase 11: delegado a _detectar_nivel)
        nivel = _detectar_nivel(filename)
        if nivel is None:
            logging.warning(f"No se pudo determinar el nivel para el archivo: {csv_file.name}")
            continue

        # Detección del periodo académico (año e.g. 2026-1)
        match = re.search(r"(20\d{2}(?:-[12])?)", filename)
        if not match:
            logging.warning(f"Omitiendo archivo: no contiene indicador de periodo en su nombre: {csv_file.name}")
            continue

        periodo: str = match.group()
        survey_dir = SURVEY_DIRS[nivel]
        periodos_por_nivel[nivel].add(periodo)

        ruta_salida: Path = survey_dir / periodo / "json"
        ruta_salida.mkdir(parents=True, exist_ok=True)

        # ── DETECCIÓN DE CSV MODIFICADO ──────────────────────────
        # Si el CSV no cambió desde el último build Y los JSON ya existen,
        # saltar el reprocesamiento completo (ahorra tiempo de CPU y ETL).
        # El caché IA (ia_cache.json) ya evita re-pagar el analisis; esto
        # adicionalmente evita releer el CSV, recalcular métricas y
        # reescribir JSONs idénticos.
        if not csv_cambiado(csv_file, ruta_salida):
            jsons_existen = all(
                (ruta_salida / f"{j}.json").exists()
                for j in ["dashboard_data", "filtros", "dimensiones",
                          "nps_carrera", "nps_ciclo_carrera",
                          "csat_carrera", "csat_ciclo_carrera",
                          "sentimiento", "ids"]
        # fragmentos_nps.json y dataset_cualitativo.json se escriben en intermediate/
        # y no se verifican en el shortcut de idempotencia (son intermedios del ETL).
            )
            if jsons_existen:
                logging.info(f"CSV sin cambios desde último build, saltando: {csv_file.name}")
                continue
            else:
                logging.info(f"CSV sin cambios pero faltan JSONs, reprocesando: {csv_file.name}")
        else:
            logging.info(f"CSV modificado o primer build, procesando: {csv_file.name}")

        periodo_dir: Path = survey_dir / periodo
        index_file: Path = periodo_dir / "index.html"
        template_index: Path = ZOHO_DIR / "template" / "index.html"

        # Inyección dinámica de la ruta a la carpeta shared (Fase 11: delegado a _inyectar_html)
        _inyectar_html(template_index, index_file, periodo_dir, ZOHO_DIR)

        # Lectura robusta de CSV
        try:
            df = read_csv_robust(csv_file)
        except (FileNotFoundError, UnicodeDecodeError, OSError, Exception) as exc:
            # CAL-03: restringido a excepciones de I/O y parsing de CSV.
            logging.error(f"Error crítico al leer {csv_file.name}: {exc}")
            continue

        # Limpiar headers
        df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

        # ── CONFIGURACION POR NIVEL (Fase 2: soporte de las 7 categorias) ──
        etl_cfg = resolver_config_etl(nivel, df.columns)
        columnas_faltantes = [c for c in etl_cfg["requeridas"] if c not in df.columns]
        if columnas_faltantes:
            logging.error(f"Archivo {csv_file.name} omitido: faltan columnas de negocio requeridas: {columnas_faltantes}")
            continue

                # Validacion Temprana de Columnas Criticas (Fase 2: config por nivel)
        columnas_faltantes = [c for c in etl_cfg["requeridas"] if c not in df.columns]
        if columnas_faltantes:
            logging.error(f"Archivo {csv_file.name} omitido: faltan columnas de negocio requeridas: {columnas_faltantes}")
            continue

                # Renombrar columnas: UG/graduate usan el mapeo completo;
        # los nuevos niveles usan solo las claves internas (Fase 2).
        if nivel == "undergraduate":
            df.rename(columns=COLUMN_RENAME_PREGRADO, inplace=True)
        elif nivel == "graduate":
            df.rename(columns=COLUMN_RENAME_GRADUADO, inplace=True)
        else:
            df.rename(columns=etl_cfg["rename"], inplace=True)
        if "Carrera" not in df.columns:
            df["Carrera"] = "General"

        # Manejo de Ciclo
        tiene_ciclo: bool = bool(etl_cfg["ciclo"]) and etl_cfg["ciclo"] in df.columns
        if not tiene_ciclo:
            df["Ciclo"] = "NA"

        # Asignación de Facultad
        if etl_cfg["facultad_map"]:
            df["Facultad"] = df["Carrera"].map(CARRERA_FACULTAD)
        else:
            df["Facultad"] = "Otra"
        # Fallback genérico si alguna carrera no tiene mapeo
        df["Facultad"] = df["Facultad"].fillna("Programa de Estudios Generales" if nivel == "undergraduate" else "Otra")

        # Normalización de fechas de Inicio y Fin
        df = normalize_dates(df, ["Inicio", "Fin"])
        inicio = df["Inicio"].min()
        fin = max(df["Inicio"].max(), df["Fin"].max())
        if pd.isnull(inicio):
            inicio = pd.Timestamp.now()
        if pd.isnull(fin):
            fin = pd.Timestamp.now()

        anio = df["Inicio"].dt.year.mode()[0] if not df["Inicio"].empty else inicio.year
        fechas_unicas = df["Inicio"].dt.date.nunique() if not df["Inicio"].empty else 1

        # metricas NPS y CSAT globales
        nps_col: str = "Recomiendas la Universidad de Lima"
        df_nps = df[[nps_col, "Carrera", "Ciclo", "Facultad"]].dropna()
        df_nps[nps_col] = pd.to_numeric(df_nps[nps_col], errors="coerce")
        df_nps = df_nps.dropna(subset=[nps_col])

        promotores_total = int(df_nps[df_nps[nps_col] >= 9].shape[0])
        pasivos_total = int(df_nps[(df_nps[nps_col] >= 7) & (df_nps[nps_col] <= 8)].shape[0])
        detractores_total = int(df_nps[df_nps[nps_col] <= 6].shape[0])
        nps_score = calc_nps(promotores_total, pasivos_total, detractores_total)

        csat_col: str = etl_cfg["csat"]
        if csat_col and csat_col in df.columns:
            serie_csat = df[csat_col].dropna()
            csat_t3b = int(serie_csat.isin(RESPUESTAS_TEXTO[:3]).sum())
            csat_t2b = int(serie_csat.isin(RESPUESTAS_TEXTO[:2]).sum())
            csat_total = int(serie_csat.isin(RESPUESTAS_TEXTO[:5]).sum())
            csat_score = calc_csat(csat_t3b, csat_total)
            csat_t2b_pct = calc_csat(csat_t2b, csat_total)
            csat_counts = [int((serie_csat == r).sum()) for r in RESPUESTAS_TEXTO[:5]]
            csat_ponderado = calc_promedio_ponderado(csat_counts, CSAT_WEIGHTS, CSAT_SCALE_MAX)
        else:
            # Fallback CSAT numerico (empleadores: columna 'CSAT Score' 1-5)
            serie_csat = pd.Series(dtype=object)
            csat_t3b = csat_t2b = csat_total = 0
            csat_score = csat_t2b_pct = csat_ponderado = 0
            if "CSAT Score" in df.columns:
                num = pd.to_numeric(df["CSAT Score"], errors="coerce").dropna()
                total = int(num.between(1, 5).sum())
                if total:
                    t3b = int((num >= 4).sum())
                    t2b = int((num >= 3).sum())
                    csat_score = round(t3b / total * 100, 2)
                    csat_t3b = t3b
                    csat_total = total
                    csat_t2b = t2b
                    csat_t2b_pct = round(t2b / total * 100, 2)
                    csat_ponderado = round(float(num.mean()), 2)

        # Métrica de Empleabilidad (solo graduados)
        empleabilidad = None
        if "Situación laboral" in df.columns:
            serie_emp = df["Situación laboral"].dropna()
            total_emp = len(serie_emp)
            if total_emp > 0:
                empleados = int(serie_emp.isin(EMPLEABILIDAD_CATEGORIAS).sum())
                empleabilidad = {
                    "score": round((empleados / total_emp) * 100, 2),
                    "empleados": empleados,
                    "total": total_emp
                }

        # NPS Carrera (Fase 11: delegado a _calcular_nps_carrera)
        nps_carrera = calc_nps_carrera(df_nps, nps_col)
        with open(ruta_salida / "nps_carrera.json", "w", encoding="utf-8") as f:
            json.dump(nps_carrera, f, ensure_ascii=False, indent=2)

        # NPS Ciclo Carrera
        nps_ciclo_carrera: List[Dict[str, any]] = []
        if tiene_ciclo:
            for (fac, car, cic), sub in df_nps.groupby(["Facultad", "Carrera", "Ciclo"]):
                p = int((sub[nps_col] >= 9).sum())
                pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
                d = int((sub[nps_col] <= 6).sum())
                nps_ciclo_carrera.append({
                    "facultad": fac,
                    "carrera": car,
                    "ciclo": cic,
                    "promotores": p,
                    "pasivos": pa,
                    "detractores": d,
                    "score": calc_nps(p, pa, d)
                })
        with open(ruta_salida / "nps_ciclo_carrera.json", "w", encoding="utf-8") as f:
            json.dump(nps_ciclo_carrera, f, ensure_ascii=False)

        # CSAT Carrera (Fase 11: delegado a _calcular_csat_carrera)
        csat_carrera = calc_csat_carrera(df, csat_col, RESPUESTAS_TEXTO) if csat_col else []
        with open(ruta_salida / "csat_carrera.json", "w", encoding="utf-8") as f:
            json.dump(csat_carrera, f, ensure_ascii=False, indent=2)

                # CSAT Ciclo Carrera
        csat_ciclo_carrera: List[Dict[str, any]] = []
        if csat_col and tiene_ciclo:
            for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
                serie = sub[csat_col].dropna()
                row = {"facultad": fac, "carrera": car, "ciclo": cic}
                for r in RESPUESTAS_TEXTO:
                    row[r] = int((serie == r).sum())
                t3b = row["Totalmente satisfecho"] + row["Muy satisfecho"] + row["Satisfecho"]
                total = t3b + row["Insatisfecho"] + row["Totalmente insatisfecho"]
                row["score"] = calc_csat(t3b, total)
                csat_ciclo_carrera.append(row)
        with open(ruta_salida / "csat_ciclo_carrera.json", "w", encoding="utf-8") as f:
            json.dump(csat_ciclo_carrera, f, ensure_ascii=False)

        # Dimensiones
        rows: List[Dict[str, any]] = []
        # Análisis Cualitativo Cuantitativo: Heatmap de Categorías (solo para survey)
        if nivel == "undergraduate":
            categoria_dim = dict(CATEGORIA_DIMENSION_PREGRADO)
        elif nivel == "graduate":
            categoria_dim = dict(CATEGORIA_DIMENSION_GRADUADO)
        else:
            # Auto-deteccion: columnas cuyos valores son subconjunto de RESPUESTAS_TEXTO
            categoria_dim = _detectar_dimensiones(df)
        for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
            for dim, cat in categoria_dim.items():
                if dim not in sub.columns:
                    continue
                serie = sub[dim].dropna()
                conteos = {r: int((serie == r).sum()) for r in RESPUESTAS_TEXTO}
                t3b = conteos["Totalmente satisfecho"] + conteos["Muy satisfecho"] + conteos["Satisfecho"]
                b2b = conteos["Insatisfecho"] + conteos["Totalmente insatisfecho"]
                total = t3b + b2b
                rows.append({
                    "facultad": fac,
                    "carrera": car,
                    "ciclo": cic,
                    "categoria": cat,
                    "dimension": dim,
                    "t3b": t3b,
                    "b2b": b2b,
                    "total": total,
                    "t3b_pct": calc_csat(t3b, total),
                    "no_utilizo": conteos["No utilizo"],
                    "no_conozco": conteos["No conozco"],
                    **conteos
                })
        with open(ruta_salida / "dimensiones.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)

        # IDs
        ids_conteo: List[Dict[str, any]] = []
        for (fac, car, cic), sub in df.groupby(["Facultad", "Carrera", "Ciclo"]):
            ids_conteo.append({
                "facultad": fac,
                "carrera": car,
                "ciclo": cic,
                "total": int(len(sub))
            })
        with open(ruta_salida / "ids.json", "w", encoding="utf-8") as f:
            json.dump(ids_conteo, f, ensure_ascii=False, indent=2)

        # Agrupamiento NPS etapas (inicial, intermedio, avanzado)
        etapas: Dict[str, Dict[str, int]] = {}
        if tiene_ciclo:
            for ciclo, sub in df_nps.groupby("Ciclo"):
                p = int((sub[nps_col] >= 9).sum())
                pa = int(((sub[nps_col] >= 7) & (sub[nps_col] <= 8)).sum())
                d = int((sub[nps_col] <= 6).sum())
                ciclo_num = int("".join(filter(str.isdigit, ciclo)) or 0)
                etapa = ETAPA_MAP.get(ciclo_num, "Otro")
                if etapa not in etapas:
                    etapas[etapa] = {"p": 0, "pa": 0, "d": 0}
                etapas[etapa]["p"] += p
                etapas[etapa]["pa"] += pa
                etapas[etapa]["d"] += d

        nps_etapas = {etapa: calc_nps(v["p"], v["pa"], v["d"]) for etapa, v in etapas.items()}

        dim_agg = {}
        for r in rows:
            if r["dimension"] not in dim_agg:
                dim_agg[r["dimension"]] = {"t3b": 0, "total": 0}
            dim_agg[r["dimension"]]["t3b"] += r["t3b"]
            dim_agg[r["dimension"]]["total"] += r["total"]

        top_dims = sorted(
            [{"name": k, "score": calc_csat(v["t3b"], v["total"])} for k, v in dim_agg.items()],
            key=lambda x: x["score"], reverse=True
        )[:2]

        fac_agg = {}
        for item in csat_carrera:
            fac = item["facultad"]
            if fac not in fac_agg:
                fac_agg[fac] = {"t3b": 0, "total": 0}
            t3b = item["Totalmente satisfecho"] + item["Muy satisfecho"] + item["Satisfecho"]
            total = t3b + item["Insatisfecho"] + item["Totalmente insatisfecho"]
            fac_agg[fac]["t3b"] += t3b
            fac_agg[fac]["total"] += total

        top_facs = sorted(
            [{"name": k, "score": calc_csat(v["t3b"], v["total"])} for k, v in fac_agg.items()],
            key=lambda x: x["score"], reverse=True
        )[:2]

        resumen = {
            "encuestas": int(len(df)),
            "carreras": int(df["Carrera"].nunique()),
            "facultades": int(df["Facultad"].nunique()),
            "fecha_inicio": inicio.strftime("%Y-%m-%d"),
            "fecha_fin": fin.strftime("%Y-%m-%d"),
            "dias": int((fin - inicio).days + 1),
            "dias_recoleccion": fechas_unicas,
            "año": int(anio),
            "periodo": periodo,
            "nps": {
                "score": nps_score,
                "promotores": promotores_total,
                "pasivos": pasivos_total,
                "detractores": detractores_total,
                "total": promotores_total + pasivos_total + detractores_total
            },
            "csat": {
                "score": csat_score,
                "t3b": csat_t3b,
                "total": csat_total,
                "t2b": csat_t2b,
                "t2b_pct": csat_t2b_pct,
                "ponderado": csat_ponderado
            }
        }
        if empleabilidad:
            resumen["empleabilidad"] = empleabilidad

        # Generar dashboard_data.json (Fase 11: delegado a _construir_dashboard_data)
        dashboard_data = construir_dashboard_data(
            resumen=resumen,
            csat_score=csat_score,
            nps_score=nps_score,
            nps_etapas=nps_etapas,
            top_dims=top_dims,
            top_facs=top_facs,
            promotores_total=promotores_total,
            pasivos_total=pasivos_total,
            detractores_total=detractores_total,
            serie_csat=serie_csat,
        )
        # Nombre sanitizado del CSV fuente para exportaciones
        dashboard_data["_export"] = {
            "nombre_encuesta": _sanitizar_nombre_csv(csv_file.name),
            "fecha_generacion": pd.Timestamp.now().strftime("%Y-%m-%d")
        }
        with open(ruta_salida / "dashboard_data.json", "w", encoding="utf-8") as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

        # Generar filtros.json
        filtros = {
            "version": "2.0",
            "has_ciclo": tiene_ciclo,
            "facultades": sorted(df["Facultad"].dropna().unique().tolist()),
            "carreras": sorted(df["Carrera"].dropna().unique().tolist()),
            "ciclos": sorted(df["Ciclo"].dropna().unique().tolist(),
                             key=lambda x: int("".join(filter(str.isdigit, x)) or 0)) if tiene_ciclo else [],
            "facultad_carrera": {
                fac: sorted(df[df["Facultad"] == fac]["Carrera"].unique().tolist())
                for fac in df["Facultad"].dropna().unique()
            }
        }
        with open(ruta_salida / "filtros.json", "w", encoding="utf-8") as f:
            json.dump(filtros, f, ensure_ascii=False, indent=2)

        # Análisis Cualitativo (sentimiento.json v3.0)
        comentario_col: str = "Comentario NPS"
        if comentario_col in df.columns:
            # Incluir csat_col (Satisfacción Global) si existe
            cols_to_extract = [comentario_col, nps_col, "Carrera", "Facultad", "Ciclo"]
            if csat_col in df.columns:
                cols_to_extract.append(csat_col)
                
            df_sent = df[cols_to_extract].copy()
            
            rename_dict = {
                comentario_col: "comentario",
                nps_col: "nps_score",
                "Carrera": "carrera",
                "Facultad": "facultad",
                "Ciclo": "ciclo"
            }
            if csat_col in df.columns:
                rename_dict[csat_col] = "satisfaccion_global"
                
            df_sent.rename(columns=rename_dict, inplace=True)
            
            # Si la columna ID de respuesta existe, agregarla
            if "ID de respuesta" in df.columns:
                df_sent["ID"] = df["ID de respuesta"]
            elif "ID" in df.columns:
                df_sent["ID"] = df["ID"]

            df_sent = df_sent.dropna(subset=["comentario", "nps_score"])
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent["nps_score"] = pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"])

            # ================================================================
            # ANALISIS CUALITATIVO CON IA (CADENA DE MOTORES)
            # El motor legacy (spaCy + sentence-transformers) fue eliminado en
            # v3.2.0. Desde v3.9.0 el analisis usa una cadena ordenada de
            # motores: Google (Gemini) -> NVIDIA (4 modelos) -> OpenCode.
            # El orden y los modelos se cambian SIN tocar codigo con la
            # variable IA_CUALITATIVO_CADENA ("servicio:modelo,servicio:modelo").
            # Si ningun motor tiene su clave configurada, el ETL falla.
            # ================================================================
            from lib.config import DIMENSIONES_SIN_CSAT
            from lib.ia_cualitativo import generar_salidas_cualitativas_ia
            from lib.ia_client import construir_motores, claves_faltantes, leer_cadena

            _motores = construir_motores()
            if not _motores:
                raise RuntimeError(
                    "Ningun motor del analisis cualitativo tiene su clave "
                    "configurada. Configure en GitHub Actions Secrets "
                    "(Settings -> Secrets and variables -> Actions) al menos una de: "
                    + ", ".join(claves_faltantes())
                    + f". Cadena pedida: {leer_cadena()}"
                )
            logging.info(
                "Modo IA Cualitativo ACTIVADO. Cadena: "
                + " -> ".join(m.etiqueta for m in _motores)
            )
            _motor_primario = _motores[0].servicio

            # Merge columnas CSAT por dimension en df_sent (para cross-reference)
            _dimension_cols = [d for d in categoria_dim.keys()
                               if d in df.columns and d not in DIMENSIONES_SIN_CSAT]
            for _dc in _dimension_cols:
                if _dc not in df_sent.columns:
                    df_sent[_dc] = df[_dc]
            _csat_cols_map = {d: d for d in _dimension_cols}
            
            # ============================================================
            # VERIFICACIÓN POR ID — SIN CACHÉ IA
            # ============================================================
            # En lugar de un caché oculto (ia_cache.json), usamos el propio
            # sentimiento.json como fuente de verdad: si un comentario ya fue
            # procesado (su ID está en el JSON existente), se salta. Solo se
            # envían a los motores de la cadena los comentarios NUEVOS.
            #
            # Para forzar reprocesamiento (ej: cambiaste el prompt y quieres
            # ver los cambios reflejados): borra el sentimiento.json del
            # periodo y vuelve a ejecutar el ETL.
            # ============================================================
            _sentimiento_path = ruta_salida / "sentimiento.json"
            _dataset_existente = []
            _ids_procesados = set()

            if _sentimiento_path.exists():
                try:
                    _sent_previo = json.load(
                        open(_sentimiento_path, "r", encoding="utf-8-sig")
                    )
                    for _com in _sent_previo.get("comentarios", []):
                        _rid = _com.get("comentario_id_original", "")
                        if _rid and _rid not in _ids_procesados:
                            _ids_procesados.add(_rid)
                            _nps_val = _com.get("nps_score", 0)
                            _dataset_existente.append({
                                "id_encuesta": _rid,
                                "id_fragmento": _com.get("id", ""),
                                "facultad": _com.get("facultad", ""),
                                "carrera": _com.get("carrera", ""),
                                "ciclo": _com.get("ciclo", ""),
                                "nps_score": _nps_val,
                                "segmento_nps": (
                                    "Promotor" if _nps_val >= 9
                                    else "Pasivo" if _nps_val >= 7
                                    else "Detractor"
                                ),
                                "satisfaccion_global": "",
                                "texto": _com.get("fragmento_original",
                                                   _com.get("fragmento_mostrar", "")),
                                "aspecto_detectado": "",
                                "aspecto_normalizado": _com.get("aspecto_normalizado",
                                                                 _com.get("categoria", "")),
                                "categoria_padre": _com.get("categoria_padre", ""),
                                "sub_aspectos": [],
                                "sentimiento": _com.get("sentimiento", "neutro"),
                                "intensidad": _com.get("intensidad", 3),
                                "confianza_sentimiento": 1.0,
                                "comentario_original": enmascarar_pii(_com.get("comentario_original", ""))[0],
                                "es_valido": _com.get("es_valido", True),
                                "motivo_invalidez": _com.get("motivo_invalidez", ""),
                                "motor": "desconocido",
                            })
                    logging.info(
                        f"JSON existente cargado: {len(_ids_procesados)} "
                        f"comentarios ya procesados en {_sentimiento_path.name}"
                    )
                except (json.JSONDecodeError, OSError) as _e:
                    logging.warning(
                        f"No se pudo cargar sentimiento.json existente "
                        f"({_e}). Se procesará todo desde cero."
                    )

            # Filtrar: solo comentarios cuyo ID NO esté ya procesado
            _total_antes = len(df_sent)
            _mask_nuevos = ~df_sent["ID"].astype(str).isin(_ids_procesados)
            _df_nuevos = df_sent[_mask_nuevos].copy()
            _total_nuevos = len(_df_nuevos)
            _total_saltados = _total_antes - _total_nuevos

            logging.info(
                f"Comentarios a procesar: {_total_nuevos} nuevos + "
                f"{_total_saltados} ya existentes (saltados) = {_total_antes} total"
            )

            if _total_nuevos > 0:
                _datos_fragmentos_nuevos, _dataset_nuevo, _ia_metadata = (
                    generar_salidas_cualitativas_ia(
                        df_sent=_df_nuevos,
                        taxonomia=CATEGORIA_DIMENSION_UNIFICADA,
                        csat_columns_map=_csat_cols_map,
                        motores=_motores,
                    )
                )
            else:
                logging.info("No hay comentarios nuevos. Se reutilizan los datos existentes.")
                # M-8: este dict debe tener la MISMA forma que el de un run real
                # (schema dataset_cualitativo -> metadata.additionalProperties=false).
                # Antes omitia 'usage' (KeyError al construir el log de resumen) e
                # incluia 'modelo_ia', que no esta declarado en el schema.
                _datos_fragmentos_nuevos, _dataset_nuevo, _ia_metadata = [], [], {
                    "total_encuestas": 0,
                    "total_fragmentos": 0,
                    "errores": 0,
                    "ruido_filtrado": 0,
                    "fallos_api": 0,
                    "intentos_api": 0,
                    "tasa_fallos_api": 0,
                    "cache_hits": 0,
                    "tiempo_segundos": 0,
                    "stats_sentimiento": {
                        "total_opinion_units": 0,
                        "positivos": 0,
                        "negativos": 0,
                        "neutros": 0,
                    },
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                    },
                }

            dataset_cualitativo = _dataset_existente + _dataset_nuevo
            datos_fragmentos = _datos_fragmentos_nuevos
            
            # Escribir fragmentos_nps.json (formato compatible con el legado)
            _motor_str = _motor_primario
            fragmentos_payload = {
                "metadata": {
                    "version": "2.0",
                    "motor": _motor_str,
                    "total_encuestas": len(datos_fragmentos),
                    "total_fragmentos": sum(len(d["fragmentos"]) for d in datos_fragmentos)
                },
                "data": datos_fragmentos
            }
            # Escribir fragmentos_nps.json en intermediate/ (no desplegado en Pages)
            _intermediate_dir = ruta_salida.parent / "intermediate"
            _intermediate_dir.mkdir(parents=True, exist_ok=True)
            with open(_intermediate_dir / "fragmentos_nps.json", "w", encoding="utf-8") as f_frag:
                json.dump(fragmentos_payload, f_frag, ensure_ascii=False, indent=2)
            
            # Escribir dataset_cualitativo.json en intermediate/
            cualitativo_payload = {"metadata": _ia_metadata, "data": dataset_cualitativo}
            with open(_intermediate_dir / "dataset_cualitativo.json", "w", encoding="utf-8") as f_cual:
                json.dump(cualitativo_payload, f_cual, ensure_ascii=False, indent=2)
            
            # Stats para compatibilidad con codigo downstream
            stats_sentimiento = _ia_metadata["stats_sentimiento"]
            _ia_msg = f"IA Cualitativo: {_ia_metadata['total_encuestas']} encuestas, {_ia_metadata['total_fragmentos']} unidades, {_ia_metadata['cache_hits']} cache hits, {_ia_metadata['usage']['total_tokens']} tokens."
            logging.info(_ia_msg)
            
            # Migración: Conectar el Motor Nuevo (dataset_cualitativo) a la UI
            # Fase IA v3: filtrar unidades inválidas (es_valido=false) para que
            # NO se muestren en el dashboard. Solo se incluyen en dataset_cualitativo.json
            # para trazabilidad, pero no en sentimiento.json (que alimenta la UI).
            comentarios_detallados = []
            topicos_dict = {}

            for item in dataset_cualitativo:
                # Fase IA v3: respetar es_valido del dataset; filtrar inválidas de la UI
                es_valido_item = item.get("es_valido", True)
                if not es_valido_item:
                    continue  # NO se muestra en el dashboard

                frag_sec = int(item["id_fragmento"].split("_")[-1]) if "_" in item["id_fragmento"] else 1
                com_obj = {
                    "id": item["id_fragmento"],
                    "carrera": item["carrera"],
                    "facultad": item["facultad"],
                    "ciclo": item["ciclo"],
                    "nps_score": item["nps_score"],
                    "sentimiento": item["sentimiento"],
                    "intensidad": item["intensidad"],
                    "categoria": item["aspecto_normalizado"],
                    "categoria_padre": item["categoria_padre"],
                    "fragmento_original": item["texto"],
                    "fragmento_mostrar": item["texto"],
                    "es_valido": True,
                    "motivo_invalidez": None,
                    "comentario_original": enmascarar_pii(item.get("comentario_original", ""))[0],
                    "comentario_id_original": item["id_encuesta"],
                    "fragmento_secuencia": frag_sec,
                    "es_fragmento": True,
                    "aspecto_normalizado": item["aspecto_normalizado"]
                }
                comentarios_detallados.append(com_obj)

                t = item["aspecto_normalizado"]
                if t not in topicos_dict:
                    topicos_dict[t] = {"total": 0, "positivo": 0, "negativo": 0, "neutro": 0}
                topicos_dict[t]["total"] += 1
                topicos_dict[t][item["sentimiento"]] += 1

            topicos_globales = []
            for t, stats in topicos_dict.items():
                topicos_globales.append({
                    "topico": t,
                    "total_comentarios": stats["total"],
                    "positivos": stats["positivo"],
                    "negativos": stats["negativo"],
                    "neutros": stats["neutro"]
                })
            topicos_globales.sort(key=lambda x: x["total_comentarios"], reverse=True)

            # Contadores
            total_con_com = int(len(df_sent))
            valid_comments = comentarios_detallados
            ids_con_comentarios_validos = set([c["comentario_id_original"] for c in valid_comments])
            total_invalidos = total_con_com - len(ids_con_comentarios_validos)
            
            total_analizados = len(valid_comments)
            
            pasivos_con_com = sum(1 for c in valid_comments if 7 <= c["nps_score"] <= 8)
            detractores_con_com = sum(1 for c in valid_comments if c["nps_score"] <= 6)
            
            # Distribución sentiment/intensity
            dist_sent = {"positivo": 0, "neutro": 0, "negativo": 0}
            for c in valid_comments:
                dist_sent[c["sentimiento"]] += 1
                
            dist_int = {"alta": 0, "media": 0, "baja": 0}
            for c in valid_comments:
                val = c["intensidad"]
                if val >= 4.0:
                    dist_int["alta"] += 1
                elif val >= 2.5:
                    dist_int["media"] += 1
                else:
                    dist_int["baja"] += 1

            # Distribución por carrera
            por_carrera: List[Dict[str, any]] = []
            for car, sub in df_sent.groupby("carrera"):
                valid_sub = [c for c in comentarios_detallados if c["carrera"] == car and c["es_valido"]]
                invalid_sub = [c for c in comentarios_detallados if c["carrera"] == car and not c["es_valido"]]
                por_carrera.append({
                    "carrera": car,
                    "facultad": sub["facultad"].iloc[0] if not sub.empty else "",
                    "total": len(valid_sub),
                    "pasivos": sum(1 for c in valid_sub if 7 <= c["nps_score"] <= 8),
                    "detractores": sum(1 for c in valid_sub if c["nps_score"] <= 6),
                    "comentarios_invalidos": len(invalid_sub)
                })
            por_carrera.sort(key=lambda x: x["total"], reverse=True)

            # Distribución por ciclo
            por_ciclo: List[Dict[str, any]] = []
            for cic, sub in df_sent.groupby("ciclo"):
                valid_sub = [c for c in comentarios_detallados if c["ciclo"] == cic and c["es_valido"]]
                por_ciclo.append({
                    "ciclo": cic,
                    "total": len(valid_sub),
                    "pasivos": sum(1 for c in valid_sub if 7 <= c["nps_score"] <= 8),
                    "detractores": sum(1 for c in valid_sub if c["nps_score"] <= 6)
                })
            por_ciclo.sort(key=lambda x: int("".join(filter(str.isdigit, x["ciclo"])) or 0))

            # Generar Insights Narrativos (Fase 8: vía lib/insights_generator.py)
            # Reemplaza templates hardcodeados por heurísticas deterministas.
            # Excluye "Pendiente de Clasificación" de temas relevantes.
            # Cubre las 7 categorías padre oficiales (no 4 como antes).
            from lib.insights_generator import generar_insights_ia
            insights_ia = generar_insights_ia(
                valid_comments=valid_comments,
                topicos_globales=topicos_globales,
                dist_sent=dist_sent,
                total_analizados=total_analizados,
            )

            sentimiento = {
                "version": "3.0",
                "resumen": {
                    "total_respuestas": int(len(df)),
                    "total_con_comentario": total_con_com,
                    "total_analizados": total_analizados,
                    "comentarios_invalidos": total_invalidos,
                    "distribucion_sentimiento": dist_sent,
                    "distribucion_intensidad": dist_int,
                    "pasivos": pasivos_con_com,
                    "detractores": detractores_con_com,
                    "nota": "Se analizan y clasifican semánticamente todos los comentarios libres ingresados en la encuesta."
                },
                "insights_ia": insights_ia,
                "topicos": topicos_globales,
                "comentarios": comentarios_detallados,
                "por_carrera": por_carrera,
                "por_ciclo": por_ciclo
            }
        else:
            sentimiento = {
                "version": "3.0",
                "resumen": {
                    "total_respuestas": int(len(df)),
                    "total_con_comentario": 0,
                    "total_analizados": 0,
                    "comentarios_invalidos": 0,
                    "distribucion_sentimiento": {"positivo": 0, "neutro": 0, "negativo": 0},
                    "distribucion_intensidad": {"alta": 0, "media": 0, "baja": 0},
                    "pasivos": 0,
                    "detractores": 0,
                    "nota": "No se encontró la columna de comentarios NPS en los datos."
                },
                "insights_ia": {
                    "global": "No hay datos de comentarios disponibles.",
                    "por_categoria_padre": {}
                },
                "topicos": [],
                "comentarios": [],
                "por_carrera": [],
                "por_ciclo": []
            }

        # Guardar únicamente en sentimiento.json (formato v3.0 consolidado y minificado)
        with open(ruta_salida / "sentimiento.json", "w", encoding="utf-8") as f:
            json.dump(sentimiento, f, ensure_ascii=False)

        # Generar CSVs y ZIP (solo si hay datos cualitativos)
        if comentario_col in df.columns and len(comentarios_detallados) > 0:
            try:
                generar_csvs_y_zip(
                    df=df,
                    comentarios_detallados=comentarios_detallados,
                    ruta_salida=ruta_salida,
                    csv_file=csv_file,
                    nivel=nivel,
                    categoria_dim=categoria_dim,
                    nps_col=nps_col,
                    csat_col=csat_col,
                    comentario_col=comentario_col,
                )
            except Exception as exc:
                logging.warning(f"No se pudieron generar los CSVs de exportación: {exc}")

        logging.info(f"Procesamiento finalizado con éxito para {nivel}/{periodo}.")
        _csv_elapsed = time.perf_counter() - _csv_start
        _timings[f"{nivel}/{periodo}"] = _csv_elapsed
        logging.info(f"⏱️ Tiempo de procesamiento para {nivel}/{periodo}: {_csv_elapsed:.1f}s")

        # Guardar hash del CSV para saltar reprocesamiento en el próximo build
        # si el CSV no cambia. Solo se guarda si el procesamiento fue exitoso.
        guardar_hash_csv(csv_file, ruta_salida)

    # =========================================================
    # Actualizar periodos.json automáticamente por nivel
    # =========================================================
    _total_elapsed = time.perf_counter() - _build_start
    logging.info(f"Build completado en {_total_elapsed:.1f}s | {len(_timings)} archivos procesados")
    for _k, _v in sorted(_timings.items(), key=lambda x: x[1], reverse=True):
        logging.info(f"   {_k}: {_v:.1f}s")

    actualizar_periodos(periodos_por_nivel, SURVEY_DIRS)


if __name__ == "__main__":
    main()
