"""
SURVEY ETL IO HELPER — Módulo de utilidades de entrada y salida de archivos.

Proporciona funciones para lectura segura de archivos JSON, lectura robusta
de CSVs (con detección específica de encoding), normalización de campos fecha,
y utilidades de hash SHA256 para detección de cambios en CSVs.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def load_json(path: Path) -> any:
    """
    Carga de forma segura un archivo JSON con soporte para UTF-8 BOM.
    Lanza ValueError detallados en caso de fallo.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"no se pudo leer el archivo JSON: {exc}") from exc

    if not text.strip():
        raise ValueError("el archivo JSON está vacío")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"formato JSON inválido: {exc}") from exc


def read_csv_robust(path: Path) -> "pd.DataFrame":
    """
    Intenta leer un archivo CSV en UTF-8 y hace fallback a latin-1
    específicamente en caso de fallos de decodificación (UnicodeDecodeError).
    """
    import pandas as pd  # Lazy import para desacoplar dependencias en validadores
    
    if not path.is_file():
        raise FileNotFoundError(f"El archivo CSV no existe en la ruta: {path}")
        
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback controlado ante problemas de encoding en español
        return pd.read_csv(path, encoding="latin-1")


def normalize_dates(df: "pd.DataFrame", columns: List[str]) -> "pd.DataFrame":
    """
    Normaliza formatos de fecha localizados de Zoho Survey (español) a Datetime.
    Mapea meses en español a inglés y corrige el formato de AM/PM.
    """
    import pandas as pd  # Lazy import para desacoplar dependencias en validadores
    
    meses_es = {
        "ene.": "January", "feb.": "February", "mar.": "March", "abr.": "April",
        "may.": "May", "jun.": "June", "jul.": "July", "ago.": "August",
        "sep.": "September", "oct.": "October", "nov.": "November", "dic.": "December"
    }
    
    df_copy = df.copy()
    for col in columns:
        if col not in df_copy.columns:
            continue
            
        # Reemplazar abreviaciones de meses
        for es, en in meses_es.items():
            df_copy[col] = df_copy[col].str.replace(es, en, regex=False)
            
        # Formatear AM/PM de Zoho: "p. m." -> "PM", "a. m." -> "AM"
        df_copy[col] = df_copy[col].str.replace(r"p.\s*m\.", "PM", regex=True)
        df_copy[col] = df_copy[col].str.replace(r"a.\s*m\.", "AM", regex=True)
        
        # Conversión a datetime
        df_copy[col] = pd.to_datetime(df_copy[col], dayfirst=True, errors="coerce")
        
    return df_copy


# ── Utilidades de hash para detección de cambios ─────────────────


ETL_OUTPUT_VERSION = "ia-validation-normalize-v1"

def hash_csv(csv_path: Path) -> str:
    """Calcula el hash SHA256 del contenido del CSV para detección de cambios."""
    h = hashlib.sha256()
    with open(csv_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_csv_versionado(csv_path: Path) -> str:
    """Calcula la huella de build: versión interna del ETL + hash puro del CSV."""
    return f"{ETL_OUTPUT_VERSION}:{hash_csv(csv_path)}"


def csv_cambiado(csv_path: Path, ruta_salida: Path) -> bool:
    """Detecta si un CSV o la versión interna del ETL cambiaron.

    `hash_csv()` permanece como hash puro del CSV. `.csv_hash` guarda una huella
    versionada para forzar un reproceso controlado cuando cambian reglas internas
    que afectan los JSON generados.
    """
    hash_file = ruta_salida / ".csv_hash"
    current_hash = hash_csv_versionado(csv_path)
    if not hash_file.exists():
        return True
    try:
        saved_hash = hash_file.read_text(encoding="utf-8").strip()
        return saved_hash != current_hash
    except OSError:
        return True


def guardar_hash_csv(csv_path: Path, ruta_salida: Path) -> None:
    """Guarda la huella versionada del CSV para comparación en el próximo build."""
    hash_file = ruta_salida / ".csv_hash"
    try:
        hash_file.write_text(hash_csv_versionado(csv_path), encoding="utf-8")
    except OSError as e:
        logging.warning(f"No se pudo guardar hash de CSV: {e}")


# -- Utilidades de redaccion PII para texto de comentarios --------------

import re as _re


def enmascarar_pii(texto: str) -> str:
    """Detecta y enmascara informacion de identificacion personal (PII) en el texto.

    Patrones redactados:
    - Correos electronicos.
    - Numeros telefonicos peruanos (9 digitos con o sin prefijo +51).
    - Codigos de estudiante de 8 digitos (tipicamente inician con 20 o 19).

    Reemplaza cada coincidencia con un placeholder [TIPO ENMASCARADO].
    Si el input no es string o esta vacio, retorna string vacio.
    """
    if not isinstance(texto, str) or not texto.strip():
        return ""

    # 1. Enmascarar correos electronicos
    patron_correo = r"[\w\.-]+@[\w\.-]+\.\w+"
    t = _re.sub(patron_correo, "[CORREO ENMASCARADO]", texto)

    # 2. Enmascarar numeros telefonicos (Peru, 9 digitos con o sin prefijo +51)
    patron_telefono = r"\b(?:\+?51\s*)?9\d{2}[-\s]?\d{3}[-\s]?\d{3}\b"
    t = _re.sub(patron_telefono, "[TELEFONO ENMASCARADO]", t)

    # 3. Enmascarar codigos de estudiante de 8 digitos (inician con 20 o 19)
    patron_codigo = r"\b(?:20|19)\d{6}\b"
    t = _re.sub(patron_codigo, "[CODIGO ENMASCARADO]", t)

    return t


def ofuscar_pii_para_llm(texto: str):
    """Ofusca PII en texto para enviar a LLM (DeepSeek).

    A diferencia de enmascarar_pii(), usa placeholders numerados para que
    el LLM pueda distinguir multiples ocurrencias del mismo tipo:
    [EMAIL_1], [EMAIL_2], [TELEFONO_1], [CODIGO_1], etc.

    Args:
        texto: Texto original que puede contener PII.

    Returns:
        tuple: (texto_ofuscado, mapping)
        - texto_ofuscado: str con PII reemplazada por placeholders numerados
        - mapping: dict {placeholder: valor_original} para trazabilidad interna
    """
    if not isinstance(texto, str) or not texto.strip():
        return "", {}

    mapping = {}
    t = texto

    # 1. Ofuscar correos electronicos con numeracion
    patron_correo = r"[\w\.-]+@[\w\.-]+\.\w+"
    email_counter = 0

    def _repl_email(m):
        nonlocal email_counter
        email_counter += 1
        placeholder = f"[EMAIL_{email_counter}]"
        mapping[placeholder] = m.group(0)
        return placeholder

    t = _re.sub(patron_correo, _repl_email, t)

    # 2. Ofuscar numeros telefonicos peruanos con numeracion
    patron_telefono = r"\b(?:\+?51\s*)?9\d{2}[-\s]?\d{3}[-\s]?\d{3}\b"
    telefono_counter = 0

    def _repl_telefono(m):
        nonlocal telefono_counter
        telefono_counter += 1
        placeholder = f"[TELEFONO_{telefono_counter}]"
        mapping[placeholder] = m.group(0)
        return placeholder

    t = _re.sub(patron_telefono, _repl_telefono, t)

    # 3. Ofuscar codigos de estudiante (8 digitos, inician con 20 o 19) con numeracion
    patron_codigo = r"\b(?:20|19)\d{6}\b"
    codigo_counter = 0

    def _repl_codigo(m):
        nonlocal codigo_counter
        codigo_counter += 1
        placeholder = f"[CODIGO_{codigo_counter}]"
        mapping[placeholder] = m.group(0)
        return placeholder

    t = _re.sub(patron_codigo, _repl_codigo, t)

    return t, mapping
