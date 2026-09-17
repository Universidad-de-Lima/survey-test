"""
SURVEY ETL DASHBOARD BUILDER — Construcción del contrato dashboard_data.json.

Ensambla las métricas pre-calculadas en la estructura JSON final
que consume el frontend del dashboard.
"""

from lib.config import RESPUESTAS_TEXTO


def construir_dashboard_data(
    resumen: dict,
    csat_score: float,
    nps_score: float,
    nps_etapas: dict,
    top_dims: list,
    top_facs: list,
    promotores_total: int,
    pasivos_total: int,
    detractores_total: int,
    serie_csat,
) -> dict:
    """Construye el objeto dashboard_data.json desde sus componentes.

    Recibe todas las métricas pre-calculadas y las ensambla en la estructura
    final que consume el frontend.
    """
    return {
        "version": "2.0",
        "resumen": resumen,
        "hallazgos": {
            "csat_pct": int(csat_score),
            "nps_score": int(nps_score),
            "nps_tipo": (
                "Excelente" if nps_score >= 60
                else "Bueno" if nps_score >= 30
                else "Regular" if nps_score >= 0
                else "Pésimo"
            ),
            "nps_etapas": nps_etapas,
            "tendencia": (
                "disminuye" if nps_etapas.get("Inicial", 0) > nps_etapas.get("Avanzado", 0)
                else "aumenta" if nps_etapas.get("Inicial", 0) < nps_etapas.get("Avanzado", 0)
                else "se mantiene"
            ),
            "delta": abs(int(nps_etapas.get("Inicial", 0) - nps_etapas.get("Avanzado", 0))),
            "top_dimensiones": top_dims,
            "top_facultades": top_facs
        },
        "nps": {
            "promotores": promotores_total,
            "pasivos": pasivos_total,
            "detractores": detractores_total,
            "score": nps_score
        },
        "csat": {r: int((serie_csat == r).sum()) for r in RESPUESTAS_TEXTO}
    }
