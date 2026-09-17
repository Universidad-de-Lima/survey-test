"""
SURVEY ETL PERIODOS UPDATER — Actualización del archivo periodos.json.

Gestiona la lectura, ordenamiento y escritura de periodos.json para
cada nivel académico, asegurando que exactamente un periodo tenga
la marca `isNew: true` (el más reciente).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Set


def clave_periodo(p: str) -> tuple:
    """Convierte un string de periodo en tupla ordenable (año, semestre).

    Ejemplos:
        '2026-1' → (2026, 1)
        '2026'   → (2026, 0)  # periodos anuales ordenan después
    """
    parts = p.split("-")
    year = int(parts[0])
    sem = int(parts[1]) if len(parts) > 1 else -1
    return (year, sem)


def actualizar_periodos(periodos_por_nivel: Dict[str, Set[str]], survey_dirs: Dict[str, Path]) -> None:
    """Actualiza periodos.json para cada nivel académico.

    Para cada nivel, ordena los periodos cronológicamente y marca
    exactamente el más reciente con `isNew: true`.
    """
    for nivel, periodos in periodos_por_nivel.items():
        if nivel not in survey_dirs:
            continue
        periodo_dir = survey_dirs[nivel]
        periodos_sorted = sorted(periodos, key=clave_periodo, reverse=True)
        periodos_list = []
        for i, p in enumerate(periodos_sorted):
            periodos_list.append({
                "id": p,
                "isNew": (i == 0)
            })
        try:
            dest = periodo_dir / "periodos.json"
            dest.write_text(
                json.dumps(periodos_list, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logging.info(
                f"periodos.json actualizado para '{nivel}' "
                f"({len(periodos_list)} periodos)"
            )
        except Exception as e:
            logging.error(
                f"No se pudo escribir periodos.json para '{nivel}': {e}"
            )
