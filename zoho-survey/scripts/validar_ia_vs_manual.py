"""
VALIDACIÓN IA vs ANÁLISIS MANUAL — Compara la salida del motor IA (DeepSeek)
contra el análisis manual humano (ground truth) de la encuesta 2026-1.

Métricas calculadas:
  1. Cobertura: cuántos comentarios del manual fueron procesados por la IA.
  2. Segmentación: distribución de fragmentos/comentario (media, mediana, moda).
  3. Sentimiento: matriz de confusión (Positivo/Negativo/Neutro) + accuracy +
     Cohen's Kappa.
  4. Intensidad: correlación de Pearson + MAE (mean absolute error).
  5. Taxonomía: accuracy exacta + accuracy por categoría padre + top mismatch.
  6. Validez: accuracy + recall de inválidos.
  7. Reglas NPS: % de unidades donde la IA respetó la regla de contexto
     (menciones de mejora en promotores, salvavidas en detractores).

Uso:
  # Modo 1: generar salida IA desde el CSV (requiere DEEPSEEK_API_KEY)
  python zoho-survey/scripts/validar_ia_vs_manual.py \\
      --csv "data/ENCUESTA DE SATISFACCIÓN ESTUDIANTIL- PREGRADO - 2026-1.csv" \\
      --xlsx upload/analisis_nps_cualitativo.xlsx \\
      --output reporte_validacion_ia.json

  # Modo 2: usar dataset_cualitativo.json ya generado
  python zoho-survey/scripts/validar_ia_vs_manual.py \\
      --ia-json zoho-survey/students/undergraduate/2026-1/intermediate/dataset_cualitativo.json \\
      --xlsx upload/analisis_nps_cualitativo.xlsx \\
      --output reporte_validacion_ia.json

  # Modo 3: comparar legacy vs IA vs manual (tres vías)
  python zoho-survey/scripts/validar_ia_vs_manual.py \\
      --ia-json .../dataset_cualitativo.json \\
      --legacy-json .../dataset_cualitativo_legacy.json \\
      --xlsx upload/analisis_nps_cualitativo.xlsx
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Any

# Asegurar que el directorio scripts/ está en sys.path para imports relativos
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ============================================================
# CARGA DE DATOS
# ============================================================

def load_manual_xlsx(xlsx_path: Path) -> pd.DataFrame:
    """Carga el análisis manual y normaliza columnas."""
    df = pd.read_excel(xlsx_path)
    # Normalizar sentimiento (mayúscula inicial, corregir typos)
    df["Sentimiento"] = df["Sentimiento"].astype(str).str.strip()
    df["Sentimiento"] = df["Sentimiento"].str.capitalize()
    # Corregir typo conocida
    df["Tema Padre"] = df["Tema Padre"].replace(
        {"Desarrollo Profecional": "Desarrollo Profesional"}
    )
    # Extraer ID base (sin sufijo _NN)
    df["id_encuesta"] = df["ID"].str.rsplit("_", n=1).str[0]
    # Normalizar válido a bool
    df["es_valido"] = df["Válido"].astype(str).str.strip().str.lower() == "sí"
    return df


def load_ia_json(ia_json_path: Path) -> pd.DataFrame:
    """Carga dataset_cualitativo.json (formato IA) a DataFrame."""
    with open(ia_json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    data = payload.get("data", [])
    if not data:
        raise ValueError(f"dataset_cualitativo.json vacío: {ia_json_path}")
    df = pd.DataFrame(data)
    # Normalizar sentimiento a mayúscula inicial para comparar con manual
    if "sentimiento_display" in df.columns:
        df["Sentimiento"] = df["sentimiento_display"]
    else:
        df["Sentimiento"] = df["sentimiento"].astype(str).str.capitalize()
    # Mapear campos IA → nombres comparables
    df["Tema"] = df.get("dimension", df.get("aspecto_normalizado", ""))
    df["Tema Padre"] = df["categoria_padre"]
    df["ID"] = df["id_fragmento"]
    df["id_encuesta"] = df["id_encuesta"]
    df["Intensidad"] = df["intensidad"]
    df["es_valido"] = df.get("es_valido", True)
    df["Frase Analizada"] = df["texto"]
    return df


def load_legacy_json(legacy_json_path: Path) -> pd.DataFrame:
    """Carga dataset_cualitativo.json (formato legacy) a DataFrame."""
    return load_ia_json(legacy_json_path)  # mismo formato


# ============================================================
# MÉTRICAS DE COMPARACIÓN
# ============================================================

def metricas_segmentacion(df_manual: pd.DataFrame, df_ia: pd.DataFrame) -> Dict[str, Any]:
    """Compara la distribución de fragmentos por comentario."""
    frags_manual = df_manual.groupby("id_encuesta").size()
    frags_ia = df_ia.groupby("id_encuesta").size()

    # Alinear por id_encuesta
    common = frags_manual.index.intersection(frags_ia.index)
    m = frags_manual.reindex(common).fillna(0).astype(int)
    i = frags_ia.reindex(common).fillna(0).astype(int)

    return {
        "total_comentarios_manual": int(len(frags_manual)),
        "total_comentarios_ia": int(len(frags_ia)),
        "comentarios_en_comun": int(len(common)),
        "total_fragmentos_manual": int(len(df_manual)),
        "total_fragmentos_ia": int(len(df_ia)),
        "promedio_fragmentos_manual": round(float(frags_manual.mean()), 3),
        "promedio_fragmentos_ia": round(float(frags_ia.mean()), 3),
        "mediana_fragmentos_manual": float(frags_manual.median()),
        "mediana_fragmentos_ia": float(frags_ia.median()),
        "diferencia_absoluta_promedio": round(float((m - i).abs().mean()), 3),
        "comentarios_con_mismo_num_fragmentos": int((m == i).sum()),
        "porcentaje_mismo_num_fragmentos": round(float((m == i).mean() * 100), 2),
    }


def metricas_sentimiento(df_manual: pd.DataFrame,
                         df_ia: pd.DataFrame) -> Dict[str, Any]:
    """Matriz de confusión y métricas de sentimiento."""
    # Merge por id_fragmento (ID)
    merged = df_manual[["ID", "Sentimiento"]].merge(
        df_ia[["ID", "Sentimiento"]],
        on="ID", suffixes=("_manual", "_ia")
    )
    if merged.empty:
        # Fallback: comparar distribuciones globales
        return {
            "nota": "No se pudo mergear por ID. Comparando distribuciones globales.",
            "distribucion_manual": df_manual["Sentimiento"].value_counts().to_dict(),
            "distribucion_ia": df_ia["Sentimiento"].value_counts().to_dict(),
        }

    sentimientos = ["Positivo", "Negativo", "Neutro"]
    # Matriz de confusión: filas=manual, cols=ia
    matriz = {}
    for sm in sentimientos:
        matriz[sm] = {}
        sub = merged[merged["Sentimiento_manual"] == sm]
        for si in sentimientos:
            matriz[sm][si] = int((sub["Sentimiento_ia"] == si).sum())

    total = len(merged)
    correctos = sum(matriz[s][s] for s in sentimientos)
    accuracy = correctos / total if total else 0

    # Cohen's Kappa
    from sklearn.metrics import cohen_kappa_score
    kappa = cohen_kappa_score(merged["Sentimiento_manual"], merged["Sentimiento_ia"])

    return {
        "total_unidades_comparadas": int(total),
        "matriz_confusion": matriz,
        "accuracy": round(accuracy, 4),
        "cohen_kappa": round(kappa, 4),
        "distribucion_manual": merged["Sentimiento_manual"].value_counts().to_dict(),
        "distribucion_ia": merged["Sentimiento_ia"].value_counts().to_dict(),
    }


def metricas_intensidad(df_manual: pd.DataFrame,
                        df_ia: pd.DataFrame) -> Dict[str, Any]:
    """Correlación y MAE de intensidad."""
    merged = df_manual[["ID", "Intensidad"]].merge(
        df_ia[["ID", "Intensidad"]], on="ID", suffixes=("_manual", "_ia")
    )
    if merged.empty:
        return {"nota": "No se pudo mergear por ID."}

    m = merged["Intensidad_manual"].astype(int)
    i = merged["Intensidad_ia"].astype(int)

    # Pearson
    try:
        pearson = float(m.corr(i))
    except (ValueError, TypeError):
        pearson = 0.0

    mae = float((m - i).abs().mean())
    exact_match = float((m == i).mean() * 100)
    within_1 = float(((m - i).abs() <= 1).mean() * 100)

    return {
        "total_unidades_comparadas": int(len(merged)),
        "pearson_correlation": round(pearson, 4),
        "mae_mean_absolute_error": round(mae, 4),
        "exact_match_pct": round(exact_match, 2),
        "within_1_point_pct": round(within_1, 2),
        "distribucion_manual": m.value_counts().sort_index().to_dict(),
        "distribucion_ia": i.value_counts().sort_index().to_dict(),
    }


def metricas_taxonomia(df_manual: pd.DataFrame,
                       df_ia: pd.DataFrame) -> Dict[str, Any]:
    """Accuracy de clasificación taxonómica."""
    merged = df_manual[["ID", "Tema", "Tema Padre"]].merge(
        df_ia[["ID", "Tema", "Tema Padre"]],
        on="ID", suffixes=("_manual", "_ia")
    )
    if merged.empty:
        return {"nota": "No se pudo mergear por ID."}

    # Accuracy dimensión exacta
    acc_dim = float((merged["Tema_manual"] == merged["Tema_ia"]).mean() * 100)
    # Accuracy categoría padre
    acc_cat = float((merged["Tema Padre_manual"] == merged["Tema Padre_ia"]).mean() * 100)

    # Top mismatches (dimensión manual → dimensión IA)
    mismatches = merged[merged["Tema_manual"] != merged["Tema_ia"]]
    mismatch_pairs = mismatches.groupby(
        ["Tema_manual", "Tema_ia"]
    ).size().sort_values(ascending=False).head(15)

    # Pendiente de clasificación: cuántos cayeron ahí en cada motor
    pend_manual = int((merged["Tema_manual"] == "Pendiente de Clasificación").sum())
    pend_ia = int((merged["Tema_ia"] == "Pendiente de Clasificación").sum())

    return {
        "total_unidades_comparadas": int(len(merged)),
        "accuracy_dimension_exacta_pct": round(acc_dim, 2),
        "accuracy_categoria_padre_pct": round(acc_cat, 2),
        "pendiente_clasificacion_manual": pend_manual,
        "pendiente_clasificacion_ia": pend_ia,
        "top_mismatches_dim_manual_to_ia": [
            {"manual": k[0], "ia": k[1], "count": int(v)}
            for k, v in mismatch_pairs.items()
        ],
    }


def metricas_validez(df_manual: pd.DataFrame,
                     df_ia: pd.DataFrame) -> Dict[str, Any]:
    """Accuracy de flag de validez."""
    merged = df_manual[["ID", "es_valido"]].merge(
        df_ia[["ID", "es_valido"]], on="ID", suffixes=("_manual", "_ia")
    )
    if merged.empty:
        return {"nota": "No se pudo mergear por ID."}

    total = len(merged)
    correctos = int((merged["es_valido_manual"] == merged["es_valido_ia"]).sum())
    # Recall de inválidos: del total de inválidos manuales, cuántos detectó la IA
    invalidos_manual = merged[~merged["es_valido_manual"]]
    if len(invalidos_manual) > 0:
        recall_invalidos = float(
            (~invalidos_manual["es_valido_ia"]).sum() / len(invalidos_manual) * 100
        )
    else:
        recall_invalidos = 0.0

    return {
        "total_unidades_comparadas": int(total),
        "accuracy_pct": round(correctos / total * 100, 2),
        "invalidos_manual": int(len(invalidos_manual)),
        "invalidos_ia": int((~merged["es_valido_ia"]).sum()),
        "recall_invalidos_pct": round(recall_invalidos, 2),
    }


def metricas_reglas_nps(df_ia: pd.DataFrame) -> Dict[str, Any]:
    """Verifica que la IA respetó las reglas de contexto NPS."""
    if "nps_score" not in df_ia.columns:
        return {"nota": "Sin NPS score en datos IA."}

    df = df_ia.copy()
    df["segmento"] = df["nps_score"].apply(
        lambda x: "Promotor" if x >= 9 else ("Pasivo" if x >= 7 else "Detractor")
    )

    # Contar unidades por segmento y sentimiento
    stats = {}
    for seg in ["Promotor", "Pasivo", "Detractor"]:
        sub = df[df["segmento"] == seg]
        total = len(sub)
        if total == 0:
            continue
        pos = int((sub["Sentimiento"] == "Positivo").sum())
        neg = int((sub["Sentimiento"] == "Negativo").sum())
        neu = int((sub["Sentimiento"] == "Neutro").sum())

        if seg == "Promotor":
            # Regla: predominio Positivo. Negativos = menciones de mejora.
            cumplio = pos >= neg
            menciones_mejora = int(sub.get("es_mencion_mejora", pd.Series([False]*len(sub))).sum()) if "es_mencion_mejora" in sub.columns else neg
            stats[seg] = {
                "total_unidades": total,
                "positivos": pos, "negativos": neg, "neutros": neu,
                "predominio_esperado": "Positivo",
                "predominio_cumplido": bool(cumplio),
                "menciones_mejora_detectadas": menciones_mejora,
            }
        elif seg == "Detractor":
            # Regla: predominio Negativo. Positivos = salvavidas.
            cumplio = neg >= pos
            salvavidas = int(sub.get("es_salvavidas", pd.Series([False]*len(sub))).sum()) if "es_salvavidas" in sub.columns else pos
            stats[seg] = {
                "total_unidades": total,
                "positivos": pos, "negativos": neg, "neutros": neu,
                "predominio_esperado": "Negativo",
                "predominio_cumplido": bool(cumplio),
                "salvavidas_detectados": salvavidas,
            }
        else:  # Pasivo
            # Regla: Neutro o mixto. Intensidad ≤ 3 general.
            intensidad_prom = float(sub["Intensidad"].mean()) if "Intensidad" in sub.columns else 0
            cumple_intensidad = intensidad_prom <= 3.2  # tolerancia
            stats[seg] = {
                "total_unidades": total,
                "positivos": pos, "negativos": neg, "neutros": neu,
                "predominio_esperado": "Neutro o mixto",
                "intensidad_promedio": round(intensidad_prom, 2),
                "intensidad_techo_3_cumplido": bool(cumple_intensidad),
            }

    return stats


# ============================================================
# REPORTING
# ============================================================

def generar_reporte(df_manual: pd.DataFrame,
                    df_ia: pd.DataFrame,
                    metadata_ia: Optional[Dict] = None) -> Dict[str, Any]:
    """Genera el reporte completo de validación."""
    reporte = {
        "metadata": {
            "manual": {
                "total_fragmentos": int(len(df_manual)),
                "total_comentarios": int(df_manual["id_encuesta"].nunique()),
            },
            "ia": {
                "total_fragmentos": int(len(df_ia)),
                "total_comentarios": int(df_ia["id_encuesta"].nunique()),
            },
            "ia_pipeline_meta": metadata_ia or {},
        },
        "1_segmentacion": metricas_segmentacion(df_manual, df_ia),
        "2_sentimiento": metricas_sentimiento(df_manual, df_ia),
        "3_intensidad": metricas_intensidad(df_manual, df_ia),
        "4_taxonomia": metricas_taxonomia(df_manual, df_ia),
        "5_validez": metricas_validez(df_manual, df_ia),
        "6_reglas_nps": metricas_reglas_nps(df_ia),
    }

    # Resumen ejecutivo
    seg = reporte["1_segmentacion"]
    sent = reporte["2_sentimiento"]
    tax = reporte["4_taxonomia"]
    val = reporte["5_validez"]

    reporte["resumen_ejecutivo"] = {
        "cobertura_comentarios_pct": round(
            seg["comentarios_en_comun"] / max(seg["total_comentarios_manual"], 1) * 100, 2
        ),
        "promedio_fragmentos_manual": seg["promedio_fragmentos_manual"],
        "promedio_fragmentos_ia": seg["promedio_fragmentos_ia"],
        "accuracy_sentimiento_pct": round(
            sent.get("accuracy", 0) * 100, 2
        ) if "accuracy" in sent else None,
        "cohen_kappa_sentimiento": sent.get("cohen_kappa"),
        "accuracy_taxonomia_pct": tax.get("accuracy_dimension_exacta_pct"),
        "accuracy_categoria_padre_pct": tax.get("accuracy_categoria_padre_pct"),
        "accuracy_validez_pct": val.get("accuracy_pct"),
        "pendiente_clasificacion_manual": tax.get("pendiente_clasificacion_manual"),
        "pendiente_clasificacion_ia": tax.get("pendiente_clasificacion_ia"),
    }
    return reporte


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Valida la salida IA contra el análisis manual (ground truth)."
    )
    parser.add_argument(
        "--xlsx", required=True,
        help="Ruta al xlsx con análisis manual (ground truth)."
    )
    parser.add_argument(
        "--ia-json",
        help="Ruta a dataset_cualitativo.json ya generado por la IA."
    )
    parser.add_argument(
        "--legacy-json",
        help="(Opcional) Ruta a dataset_cualitativo.json legacy para comparación 3 vías."
    )
    parser.add_argument(
        "--csv",
        help="(Alternativo a --ia-json) CSV de Zoho para generar salida IA en vivo."
    )
    parser.add_argument(
        "--output", default="reporte_validacion_ia.json",
        help="Archivo de salida para el reporte JSON."
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limitar a N comentarios (0 = todos). Útil para pruebas rápidas."
    )
    args = parser.parse_args()

    # 1. Cargar manual
    logger.info(f"Cargando análisis manual: {args.xlsx}")
    df_manual = load_manual_xlsx(Path(args.xlsx))
    logger.info(f"Manual: {len(df_manual)} fragmentos, {df_manual['id_encuesta'].nunique()} comentarios.")

    if args.limit > 0:
        ids_limit = df_manual["id_encuesta"].unique()[:args.limit]
        df_manual = df_manual[df_manual["id_encuesta"].isin(ids_limit)]
        logger.info(f"Limitado a {len(ids_limit)} comentarios.")

    # 2. Cargar/generar IA
    if args.ia_json:
        logger.info(f"Cargando JSON IA: {args.ia_json}")
        df_ia = load_ia_json(Path(args.ia_json))
        metadata_ia = {}
    elif args.csv:
        # Generar IA en vivo (requiere DEEPSEEK_API_KEY)
        if not os.environ.get("DEEPSEEK_API_KEY"):
            logger.error("DEEPSEEK_API_KEY no configurada. No se puede generar IA en vivo.")
            sys.exit(1)
        logger.info(f"Generando análisis IA desde CSV: {args.csv}")
        from lib.ia_cualitativo import generar_salidas_cualitativas_ia
        from lib.config import (
            COLUMN_RENAME_PREGRADO, CATEGORIA_DIMENSION_PREGRADO,
            DIMENSIONES_SIN_CSAT, RESPUESTAS_TEXTO
        )
        # Cargar CSV con mismo renombrado que build_json.py
        df = pd.read_csv(args.csv, encoding="utf-8")
        df.rename(columns=COLUMN_RENAME_PREGRADO, inplace=True)
        # Construir df_sent (simplificado)
        cols = ["Comentario NPS", "Recomiendas la Universidad de Lima", "Carrera", "Facultad", "Ciclo"]
        csat_global_col = "La Universidad de Lima"
        if csat_global_col in df.columns:
            cols.append(csat_global_col)
        df_sent = df[cols].copy()
        rename = {
            "Comentario NPS": "comentario",
            "Recomiendas la Universidad de Lima": "nps_score",
            "Carrera": "carrera", "Facultad": "facultad", "Ciclo": "ciclo"
        }
        if csat_global_col in df.columns:
            rename[csat_global_col] = "satisfaccion_global"
        df_sent.rename(columns=rename, inplace=True)
        if "ID de respuesta" in df.columns:
            df_sent["ID"] = df["ID de respuesta"]
        df_sent = df_sent.dropna(subset=["comentario", "nps_score"])
        df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
        df_sent["nps_score"] = pd.to_numeric(df_sent["nps_score"], errors="coerce")
        df_sent = df_sent.dropna(subset=["nps_score"])
        df_sent = df_sent[df_sent["comentario"].str.strip() != ""]

        if args.limit > 0:
            df_sent = df_sent.head(args.limit)

        # CSAT columns map
        dim_cols = [d for d in CATEGORIA_DIMENSION_PREGRADO.keys()
                    if d in df.columns and d not in DIMENSIONES_SIN_CSAT]
        for dc in dim_cols:
            if dc not in df_sent.columns:
                df_sent[dc] = df[dc]
        csat_map = {d: d for d in dim_cols}

        _, dataset_cualitativo, metadata_ia = generar_salidas_cualitativas_ia(
            df_sent=df_sent,
            taxonomia=CATEGORIA_DIMENSION_PREGRADO,
            csat_columns_map=csat_map,
        )
        df_ia = pd.DataFrame(dataset_cualitativo)
        df_ia["Sentimiento"] = df_ia.get("sentimiento_display", df_ia["sentimiento"].str.capitalize())
        df_ia["Tema"] = df_ia["dimension"]
        df_ia["Tema Padre"] = df_ia["categoria_padre"]
        df_ia["ID"] = df_ia["id_fragmento"]
        df_ia["Intensidad"] = df_ia["intensidad"]
        df_ia["es_valido"] = df_ia.get("es_valido", True)
        df_ia["Frase Analizada"] = df_ia["texto"]
    else:
        logger.error("Debe especificar --ia-json o --csv.")
        sys.exit(1)

    logger.info(f"IA: {len(df_ia)} fragmentos, {df_ia['id_encuesta'].nunique()} comentarios.")

    # 3. Generar reporte
    reporte = generar_reporte(df_manual, df_ia, metadata_ia=metadata_ia)

    # 4. (Opcional) Comparación 3 vías
    if args.legacy_json:
        logger.info(f"Cargando legacy JSON: {args.legacy_json}")
        df_legacy = load_legacy_json(Path(args.legacy_json))
        reporte["legacy_vs_manual"] = generar_reporte(df_manual, df_legacy)
        reporte["ia_vs_legacy"] = generar_reporte(df_legacy, df_ia)

    # 5. Guardar
    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    # 6. Imprimir resumen
    print("\n" + "=" * 60)
    print("REPORTE DE VALIDACIÓN IA vs MANUAL")
    print("=" * 60)
    r = reporte["resumen_ejecutivo"]
    print(f"Cobertura de comentarios:       {r['cobertura_comentarios_pct']}%")
    print(f"Promedio fragmentos (manual):   {r['promedio_fragmentos_manual']}")
    print(f"Promedio fragmentos (IA):       {r['promedio_fragmentos_ia']}")
    print(f"Accuracy sentimiento:           {r['accuracy_sentimiento_pct']}%")
    print(f"Cohen's Kappa (sentimiento):    {r['cohen_kappa_sentimiento']}")
    print(f"Accuracy taxonomía (dimensión): {r['accuracy_taxonomia_pct']}%")
    print(f"Accuracy categoría padre:       {r['accuracy_categoria_padre_pct']}%")
    print(f"Accuracy validez:               {r['accuracy_validez_pct']}%")
    print(f"Pendiente manual / IA:          {r['pendiente_clasificacion_manual']} / {r['pendiente_clasificacion_ia']}")
    print("=" * 60)
    print(f"Reporte completo: {out_path.resolve()}")


if __name__ == "__main__":
    main()
