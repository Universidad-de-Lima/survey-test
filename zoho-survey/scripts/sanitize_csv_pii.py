"""
SANITIZADOR DE PII — Redacta columnas de identificación directa en CSVs.

Columnas redactadas:
  - Dirección IP
  - Agente Usuario
  - URL de la encuesta a la que accede el encuestado

Estas columnas contienen datos personales identificables (Ley 29733, GDPR).
Se reemplazan con string vacío para preservar estructura CSV sin datos sensibles.

Uso:
  python zoho-survey/scripts/sanitize_csv_pii.py "data/ENCUESTA...csv"
  python zoho-survey/scripts/sanitize_csv_pii.py --all
  # Modifica el archivo in-place (sobreescribe con columnas redactadas)

Idempotencia:
  Si las columnas PII ya están vacías (CSV previamente sanitizado),
  el script no realiza cambios y retorna exitosamente.
"""

import csv
import sys
from pathlib import Path


# Columnas PII a redactar (búsqueda por nombre exacto, case-sensitive).
# Los nombres deben coincidir con los headers exportados por Zoho Survey.
COLUMNAS_PII = [
    "Dirección IP",
    "Agente Usuario",
    "URL de la encuesta a la que accede el encuestado",
]


def sanitizar_csv(ruta_csv: str) -> bool:
    """Redacta columnas PII en un CSV, modificándolo in-place.

    Retorna True si el archivo fue procesado (o ya estaba limpio).
    Retorna False si el archivo no existe o está vacío.
    """
    ruta = Path(ruta_csv)
    if not ruta.exists():
        print(f"ERROR: archivo no encontrado: {ruta_csv}")
        return False

    # Leer todo el CSV en memoria
    with open(ruta, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        filas = list(reader)

    if not filas:
        print(f"ERROR: archivo vacío: {ruta_csv}")
        return False

    headers = filas[0]

    # Identificar índices de columnas PII por nombre exacto
    indices_pii = {}  # {indice: nombre_columna}
    for i, h in enumerate(headers):
        h_clean = h.strip().strip('"')
        if h_clean in COLUMNAS_PII:
            indices_pii[i] = h_clean

    if not indices_pii:
        print(f"INFO: no se encontraron columnas PII en {ruta_csv}. Saltando.")
        return True  # No es error, el archivo ya está limpio

    # Contar redacciones por columna
    cambios_por_col = {nombre: 0 for nombre in indices_pii.values()}

    for fila in filas[1:]:  # Saltar header
        for idx, nombre in indices_pii.items():
            if idx < len(fila) and fila[idx].strip():
                fila[idx] = ""
                cambios_por_col[nombre] += 1

    # Escribir el CSV sanitizado (sobreescribe original)
    with open(ruta, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(filas)

    total_filas = len(filas) - 1  # Sin contar header
    detalle = ", ".join(f"{v} {k}" for k, v in cambios_por_col.items() if v > 0)
    if detalle:
        print(f"✓ {ruta.name}: {total_filas} filas, {detalle} redactadas")
    else:
        print(f"✓ {ruta.name}: {total_filas} filas, ya sanitizado (sin cambios)")
    return True


def main():
    if len(sys.argv) < 2:
        print("Uso: python zoho-survey/scripts/sanitize_csv_pii.py <ruta_csv1> [ruta_csv2 ...]")
        print("  O: python zoho-survey/scripts/sanitize_csv_pii.py --all  (sanitiza todos los CSVs en data/)")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Desde zoho-survey/scripts/, subir 3 niveles para llegar a la raíz del repo:
        # zoho-survey/scripts/sanitize_csv_pii.py → scripts → zoho-survey → raíz_repo
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        csvs = list(data_dir.glob("*.csv"))
        if not csvs:
            print(f"No se encontraron CSVs en {data_dir}")
            sys.exit(0)
        exitos = 0
        for csv_path in csvs:
            if sanitizar_csv(str(csv_path)):
                exitos += 1
        print(f"\nTotal: {exitos}/{len(csvs)} CSVs sanitizados")
    else:
        for ruta in sys.argv[1:]:
            sanitizar_csv(ruta)


if __name__ == "__main__":
    main()
