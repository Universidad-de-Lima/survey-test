"""
IA CUALITATIVO — Orquestador del análisis cualitativo por cadena de motores.

Este módulo es la capa de integración entre build_json.py y los submódulos
especializados: ia_client (motores), ia_validacion (validación), ia_filtro_ruido
(pre-filtrado).

Desde v3.9.0 el análisis usa una CADENA DE MOTORES ordenada: se intenta el
primero y, si falla o devuelve una respuesta inválida, se pasa al siguiente.
Sustituye al esquema anterior de "motor primario + un respaldo" (DeepSeek con
respaldo NVIDIA), que quedó obsoleto al incorporar Google y OpenCode.

Uso principal (integrado en build_json.py):
  from lib.ia_cualitativo import generar_salidas_cualitativas_ia
  datos_fragmentos, dataset, metadata = generar_salidas_cualitativas_ia(
      df_sent=df_sent, taxonomia=..., csat_columns_map=...
  )

Variables de entorno (las claves, una por servicio):
  - GOOGLE_API_KEY    (Google Gemini).
  - NVIDIA_API_KEY    (NVIDIA NIM: 4 modelos en la cadena por defecto).
  - OPENCODE_API_KEY  (OpenCode).
  Al menos una es obligatoria: sin ninguna, el ETL falla.

  - IA_CUALITATIVO_CADENA (opcional): orden y modelos de la cadena, en formato
    "servicio:modelo" separado por comas. Sin esta variable se usa la cadena por
    defecto de lib/ia_client.py.
  - IA_CUALITATIVO_MAX_RPM (opcional, default 60): llamadas por minuto y motor.
  Google usa 10 (su plan gratuito tolera ~15) y NVIDIA 8, en lib/ia_client.py.
  - IA_CUALITATIVO_TIMEOUT (opcional, default 60): segundos por llamada.
  - IA_CUALITATIVO_MAX_FALLOS_API_PCT (opcional, default 20): umbral fail-closed.
    Si más de ese porcentaje de comentarios falla por API, el ETL aborta y no se
    publica sentimiento.json. 0 = estricto, 100 = desactivado.
  - (caché IA eliminado — la verificación por ID reemplaza al caché)
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

# CacheManager eliminado — verificación por ID en build_json.py
from .ia_client import MotorIA, construir_motores, DEFAULT_WORKERS
from .ia_filtro_ruido import es_ruido_pre_filtro, generar_unidad_ruido
from .ia_validacion import validar_respuesta_ia
from .io_helper import ofuscar_pii_para_llm
from .prompts_cualitativo import (
    build_system_prompt,
    build_user_prompt,
    RATING_TO_SCORE,
)

try:
    import pandas as _pd
except ImportError:
    _pd = None

logger = logging.getLogger(__name__)


# ============================================================
# UMBRAL FAIL-CLOSED DE FALLOS DE API
# ============================================================

# Motivo que registra la unidad placeholder cuando NINGÚN motor pudo responder.
MOTIVO_FALLO_API = "Error de API (todos los motores fallaron)"

# Muestra mínima para aplicar el umbral: con pocos comentarios una tasa alta no
# es significativa y bloquearía el build sin motivo.
MIN_INTENTOS_UMBRAL = 10

# Workers máximos cuando el PRIMER motor de la cadena es NVIDIA (plan gratuito
# ~30 req/min). Los demás motores de la cadena se autorregulan con su propio
# límite de ritmo (ver lib/ia_client.py).
NVIDIA_MAX_WORKERS = 3

# Valor del campo "motor" para las unidades descartadas por el pre-filtro de
# ruido: no las clasificó ningún motor, y decirlo así es más honesto que
# atribuírselas a uno.
MOTOR_FILTRO_RUIDO = "filtro"


def _umbral_fallos_pct() -> float:
    """Lee el umbral de fallos (porcentaje) desde el entorno. Default 20."""
    try:
        return float(os.environ.get("IA_CUALITATIVO_MAX_FALLOS_API_PCT", "20"))
    except (TypeError, ValueError):
        return 20.0


def evaluar_fallo_masivo(intentos_api: int, fallos_api: int) -> Optional[str]:
    """Evalúa si la tasa de fallos de API obliga a abortar el ETL.

    Fail-closed: si más del `IA_CUALITATIVO_MAX_FALLOS_API_PCT` por ciento de los
    comentarios enviados a la IA no pudo analizarse con NINGÚN motor de la cadena,
    los indicadores cualitativos no son representativos y no deben publicarse.

    Devuelve el mensaje de error si hay que abortar, o None si el build puede
    continuar. `IA_CUALITATIVO_MAX_FALLOS_API_PCT=0` = modo estricto (cualquier
    fallo aborta); un valor alto (p. ej. 100) desactiva el umbral.
    """
    if intentos_api <= 0 or fallos_api <= 0:
        return None
    if intentos_api < MIN_INTENTOS_UMBRAL:
        return None
    umbral = _umbral_fallos_pct()
    tasa = (fallos_api / intentos_api) * 100.0
    if tasa <= umbral:
        return None
    return (
        f"Fallo de API masivo en el analisis cualitativo: "
        f"{fallos_api}/{intentos_api} comentarios ({tasa:.1f}%) no pudieron "
        f"analizarse con ningun motor de la cadena (umbral "
        f"IA_CUALITATIVO_MAX_FALLOS_API_PCT={umbral:.0f}%, muestra minima "
        f"{MIN_INTENTOS_UMBRAL}). No se publica sentimiento.json para este "
        "periodo: revisa las claves y cuotas de los servicios de la cadena "
        "(GOOGLE_API_KEY, NVIDIA_API_KEY, OPENCODE_API_KEY) y relanza el ETL."
    )


# ============================================================
# FUNCION PRINCIPAL: analizar un comentario
# ============================================================

def analizar_comentario(comentario: str,
                        nps_score: int,
                        csat_ratings: Dict[str, str],
                        taxonomia: Dict[str, str],
                        categorias_padre: List[str],
                        motores: List[MotorIA],
                        id_encuesta: str = "",
                        carrera: str = "",
                        ciclo: str = "",
                        facultad: str = "") -> Dict[str, Any]:
    """Analiza un comentario completo y devuelve {unidades: [...]}.

    Recorre la cadena de motores en orden. Se pasa al siguiente motor en DOS
    casos:
      1. Error de API (RuntimeError) en el motor actual.
      2. Respuesta del motor actual no valida (validar_respuesta_ia -> None).

    Si ningún motor de la cadena responde, devuelve una unidad placeholder no
    válida, que el umbral fail-closed contabiliza como fallo de API.
    """
    system_prompt = build_system_prompt(taxonomia, categorias_padre)
    user_prompt = build_user_prompt(comentario, nps_score, csat_ratings, id_encuesta, carrera, ciclo, facultad)

    def _try_motor(motor: MotorIA) -> Optional[Dict[str, Any]]:
        """Llama a un motor y valida su respuesta. Retorna dict saneado o None."""
        try:
            raw = motor.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=16000,
            )
        except RuntimeError as e:
            logger.error(f"{motor.etiqueta} fallo para {id_encuesta}: {e}")
            return None
        if not raw:
            logger.warning(f"{motor.etiqueta} devolvio respuesta vacia para {id_encuesta}.")
            return None
        sanada, err = validar_respuesta_ia(raw, taxonomia)
        if sanada is None:
            logger.warning(f"{motor.etiqueta} respuesta invalida para {id_encuesta}: {err}")
            return None
        return sanada

    for idx, motor in enumerate(motores):
        if idx > 0:
            logger.warning(f"Intentando el siguiente motor ({motor.etiqueta}) para {id_encuesta}...")
        sanada = _try_motor(motor)
        if sanada is not None:
            if isinstance(sanada, dict) and "unidades" in sanada:
                for u in sanada["unidades"]:
                    if isinstance(u, dict):
                        u["_motor_actual"] = motor.servicio
            return sanada

    # Ningún motor de la cadena respondió
    return _placeholder(
        comentario,
        "Ningun motor de la cadena respondio o devolvio una respuesta invalida.",
        MOTIVO_FALLO_API,
    )


def _placeholder(comentario: str, detalle: str, motivo: str) -> dict:
    """Genera placeholder de unidad no valida."""
    return {
        "unidades": [{
            "orden": 1,
            "texto": comentario[:100],
            "es_valido": False,
            "motivo_invalidez": motivo,
            "sentimiento": "neutro",
            "intensidad": 1,
            "justificacion_sentimiento": detalle,
            "dimension": "Pendiente de Clasificación",
            "categoria_padre": "Pendiente de Clasificación",
            "es_mencion_mejora": False,
            "es_salvavidas": False,
            "dimension_evaluada_rating": None,
            "dimension_evaluada_score": None,
            "sub_aspectos": [],
        }]
    }


# ============================================================
# FUNCION DE ALTO NIVEL: analizar todo el dataset
# ============================================================

def analizar_dataset_cualitativo(
    df_sent,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    motores: Optional[List[MotorIA]] = None,
    progress_every: int = 25,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Analiza cualitativamente todo el dataset de comentarios NPS.

    Si no se pasan motores, construye la cadena desde las variables de entorno
    (IA_CUALITATIVO_CADENA + las claves de cada servicio).

    Returns:
        (dataset_cualitativo, metadata) donde dataset_cualitativo es una
        lista de dicts (uno por unidad) y metadata contiene estadisticas.
    """
    if motores is None:
        motores = construir_motores()
    if not motores:
        raise RuntimeError(
            "Ningun motor del analisis cualitativo tiene su clave configurada. "
            "Configure al menos una de GOOGLE_API_KEY, NVIDIA_API_KEY, "
            "OPENCODE_API_KEY."
        )

    categorias_padre = sorted(set(taxonomia.values()))

    # Cleaning defensivo
    if _pd is not None:
        try:
            df_sent = df_sent.copy()
            df_sent["nps_score"] = _pd.to_numeric(df_sent["nps_score"], errors="coerce")
            df_sent = df_sent.dropna(subset=["nps_score"]).reset_index(drop=True)
            df_sent["comentario"] = df_sent["comentario"].fillna("").astype(str)
            df_sent = df_sent[df_sent["comentario"].str.strip() != ""]
            df_sent = df_sent[df_sent["comentario"].str.strip().str.lower() != "nan"]
        except Exception as clean_err:
            logger.warning(f"Cleaning defensivo fallo: {clean_err}")

    dataset_cualitativo: List[Dict[str, Any]] = []
    total_comentarios = 0
    total_unidades = 0
    errores = 0
    cache_hits = 0
    ruido_filtrado = 0

    total_rows = len(df_sent)
    # NVIDIA (plan gratuito) no tolera 15 llamadas concurrentes: su cliente ya
    # se construye con su propio limite de ritmo (15 llamadas/minuto), asi que
    # reducir el pool evita tormentas de 429/timeouts cuando NVIDIA es el
    # PRIMER motor de la cadena. Si encabeza otro servicio, se usa el pool
    # normal: cada motor de la cadena se autorregula.
    primer_motor = motores[0]
    workers = (NVIDIA_MAX_WORKERS if primer_motor.servicio == "nvidia"
               else DEFAULT_WORKERS)
    logger.info(
        f"Iniciando analisis IA de {total_rows} comentarios. Cadena: "
        + " -> ".join(m.etiqueta for m in motores)
        + f". {workers} workers, timeout={primer_motor.timeout}s."
    )

    # Pre-coleccionar tasks
    tasks: List[Tuple] = []
    for idx, row in df_sent.iterrows():
        comentario_val = row["comentario"]
        if _pd is not None and _pd.isna(comentario_val):
            continue
        if comentario_val is None:
            continue
        comentario = str(comentario_val).strip()
        # Ofuscar PII antes de enviar el comentario al LLM (evita que datos
        # sensibles salgan del repositorio hacia cualquier proveedor).
        comentario, _pii_map = ofuscar_pii_para_llm(comentario)

        if not comentario or comentario.lower() == "nan":
            continue

        nps_val = row["nps_score"]
        if _pd is not None and _pd.isna(nps_val):
            continue
        try:
            nps = int(nps_val)
        except (ValueError, TypeError):
            continue

        res_id = str(row.get("ID", f"R_{idx}"))
        facultad = str(row.get("facultad", ""))
        carrera = str(row.get("carrera", ""))
        ciclo = str(row.get("ciclo", ""))
        satisfaccion_global = str(row.get("satisfaccion_global", "No respondido"))

        csat_ratings: Dict[str, str] = {}
        for dim, col in csat_columns_map.items():
            if col in row.index:
                val = row[col]
                if val and str(val).strip() and str(val).strip() in RATING_TO_SCORE:
                    csat_ratings[dim] = str(val).strip()

        tasks.append((comentario, nps, csat_ratings, res_id,
                      facultad, carrera, ciclo, satisfaccion_global))

    logger.info(f"{len(tasks)} tasks preparados de {total_rows} filas.")
    _start_batch = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        fut_map = {}
        for (comentario, nps, csat_ratings, res_id,
             facultad, carrera, ciclo, satisfaccion_global) in tasks:
            es_ruido, motivo = es_ruido_pre_filtro(comentario)
            if es_ruido:
                ruido_filtrado += 1
                unidad = generar_unidad_ruido(motivo)
                dataset_cualitativo.append(_build_item(
                    res_id, "01", facultad, carrera, ciclo, nps,
                    satisfaccion_global, comentario[:100], "", "",
                    "", [], "neutro", 1, 1.0, comentario,
                    False, motivo, MOTOR_FILTRO_RUIDO
                ))
                continue

            future = executor.submit(
                _analizar_un_comentario, comentario, nps, csat_ratings,
                taxonomia, categorias_padre, motores, res_id,
                facultad, carrera, ciclo, satisfaccion_global,
            )
            fut_map[future] = (res_id, facultad, carrera, ciclo,
                               satisfaccion_global, nps, comentario)

        for i, future in enumerate(as_completed(fut_map)):
            res_id, facultad, carrera, ciclo, satisfaccion_global, nps, \
                comentario = fut_map[future]
            try:
                resultado = future.result()
                unidades = resultado.get("unidades", [])
                total_comentarios += 1
                total_unidades += len(unidades)
                for unidad in unidades:
                    es_valido = unidad.get("es_valido", True)
                    sent = unidad.get("sentimiento", "neutro").lower()
                    motor_real = unidad.get("_motor_actual", primer_motor.servicio)
                    dataset_cualitativo.append(_build_item(
                        res_id, f"{unidad['orden']:02d}",
                        facultad, carrera, ciclo, nps,
                        satisfaccion_global, unidad.get("texto", ""),
                        unidad.get("dimension", ""),
                        unidad.get("dimension", ""),
                        unidad.get("categoria_padre", ""),
                        unidad.get("sub_aspectos", []),
                        sent, unidad.get("intensidad", 3),
                        1.0, comentario, es_valido,
                        unidad.get("motivo_invalidez", ""), motor_real
                    ))
            except Exception as e:
                errores += 1
                logger.error(f"Error procesando {res_id}: {e}")

            if (i + 1) % progress_every == 0:
                elapsed = time.perf_counter() - _start_batch
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(
                    f"Progreso: {i+1}/{len(fut_map)} comentarios "
                    f"({rate:.1f} cmt/s), {total_unidades} unidades, "
                    f"{errores} errores, {ruido_filtrado} ruido."
                )

    _elapsed = time.perf_counter() - _start_batch

    # REND-02: Ordenar dataset para garantizar idempotencia.
    # as_completed produce resultados en orden de finalizacion (no determinista).
    # Ordenar por id_encuesta + id_fragmento asegura que mismo CSV -> mismo JSON.
    dataset_cualitativo.sort(key=lambda x: (x.get("id_encuesta", ""), x.get("id_fragmento", "")))

    cache_hits = 0  # sin cache

    # C-1 (fail-closed): intentos enviados realmente a la IA y cuantos no pudo
    # analizar NINGUN motor de la cadena. Antes quedaban como placeholders
    # invalidos, el run se daba por bueno (errores=0) y se publicaba
    # sentimiento.json calculado sobre una muestra irrelevante
    # (incidente 2026-1: 892 de 898).
    intentos_api = len(fut_map)
    fallos_api = sum(
        1 for d in dataset_cualitativo
        if d.get("motivo_invalidez") == MOTIVO_FALLO_API
    )
    tasa_fallos_api = (
        round((fallos_api / intentos_api) * 100.0, 1) if intentos_api else 0.0
    )

    # Uso agregado de toda la cadena (tokens de todos los motores que
    # respondieron, no solo del primero).
    usage_total = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                   "llamadas": 0}
    for motor in motores:
        _u = motor.usage
        usage_total["input_tokens"] += _u.get("input_tokens", 0)
        usage_total["output_tokens"] += _u.get("output_tokens", 0)
        usage_total["total_tokens"] += _u.get("total_tokens", 0)
        usage_total["llamadas"] += _u.get("llamadas", 0)

    metadata = {
        "total_encuestas": total_comentarios,
        "total_fragmentos": total_unidades,
        "errores": errores,
        "ruido_filtrado": ruido_filtrado,
        "fallos_api": fallos_api,
        "intentos_api": intentos_api,
        "tasa_fallos_api": tasa_fallos_api,
        "cache_hits": cache_hits,
        "tiempo_segundos": round(_elapsed, 2),
        "stats_sentimiento": {
            "total_opinion_units": total_unidades,
            "positivos": sum(1 for d in dataset_cualitativo
                             if d["sentimiento"] == "positivo" and d["es_valido"]),
            "negativos": sum(1 for d in dataset_cualitativo
                             if d["sentimiento"] == "negativo" and d["es_valido"]),
            "neutros": sum(1 for d in dataset_cualitativo
                           if d["sentimiento"] == "neutro" and d["es_valido"]),
        },
        "usage": usage_total,
    }

    logger.info(
        f"Analisis IA completado: {total_comentarios} comentarios, "
        f"{total_unidades} unidades, {errores} errores, "
        f"{ruido_filtrado} ruido pre-filtrado, "
        f"{fallos_api}/{intentos_api} fallos de API ({tasa_fallos_api}%). "
        f"Tiempo: {_elapsed:.1f}s."
    )

    # Umbral fail-closed: se evalua ANTES de escribir nada, de modo que el ETL
    # aborta y no se publica sentimiento.json poco fiable.
    error_umbral = evaluar_fallo_masivo(intentos_api, fallos_api)
    if error_umbral:
        logger.error(error_umbral)
        raise RuntimeError(error_umbral)

    return dataset_cualitativo, metadata


def _build_item(res_id, ord_id, facultad, carrera, ciclo, nps,
                sat_global, texto, asp_detectado, asp_normalizado,
                cat_padre, sub_aspectos, sentimiento, intensidad,
                confianza, comentario_orig, es_valido, motivo, motor):
    """Construye un item del dataset cualitativo."""
    return {
        "id_encuesta": res_id,
        "id_fragmento": f"{res_id}_{ord_id}",
        "facultad": facultad,
        "carrera": carrera,
        "ciclo": ciclo,
        "nps_score": nps,
        "segmento_nps": (
            "Promotor" if nps >= 9
            else "Pasivo" if nps >= 7
            else "Detractor"
        ),
        "satisfaccion_global": sat_global,
        "texto": texto,
        "aspecto_detectado": asp_detectado,
        "aspecto_normalizado": asp_normalizado,
        "categoria_padre": cat_padre,
        "sub_aspectos": sub_aspectos,
        "sentimiento": sentimiento,
        "intensidad": intensidad,
        "confianza_sentimiento": confianza,
        "comentario_original": comentario_orig,
        "es_valido": es_valido,
        "motivo_invalidez": motivo,
        "motor": motor,
    }


def _analizar_un_comentario(comentario, nps, csat_ratings, taxonomia,
                            categorias_padre, motores, res_id,
                            facultad, carrera, ciclo, satisfaccion_global):
    """Helper para ejecutar en ThreadPoolExecutor."""
    return analizar_comentario(
        comentario=comentario,
        nps_score=nps,
        csat_ratings=csat_ratings,
        taxonomia=taxonomia,
        categorias_padre=categorias_padre,
        motores=motores,
        id_encuesta=res_id,
        carrera=carrera,
        ciclo=ciclo,
        facultad=facultad,
    )


# ============================================================
# CAPA DE INTEGRACION CON build_json.py
# ============================================================

def generar_salidas_cualitativas_ia(
    df_sent,
    taxonomia: Dict[str, str],
    csat_columns_map: Dict[str, str],
    motores: Optional[List[MotorIA]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Capa de integracion con build_json.py.

    Retorna (datos_fragmentos, dataset_cualitativo, metadata) en formato
    compatible con el pipeline legacy.
    """
    dataset_cualitativo, metadata = analizar_dataset_cualitativo(
        df_sent=df_sent,
        taxonomia=taxonomia,
        csat_columns_map=csat_columns_map,
        motores=motores,
    )

    from collections import defaultdict
    grupos: Dict[str, List[Dict]] = defaultdict(list)
    for item in dataset_cualitativo:
        grupos[item["id_encuesta"]].append(item)

    datos_fragmentos = []
    for res_id, unidades in grupos.items():
        primera = unidades[0]
        fragmentos = []
        for u in unidades:
            fragmentos.append({
                "id_fragmento": u["id_fragmento"],
                "texto": u["texto"],
                "sentimiento": u.get("sentimiento", "neutro"),
                "intensidad": u.get("intensidad", 3),
                "aspecto_normalizado": u.get("aspecto_normalizado", ""),
                "categoria_padre": u.get("categoria_padre", ""),
                "es_valido": u.get("es_valido", True),
                "motivo_invalidez": u.get("motivo_invalidez", ""),
            })

        datos_fragmentos.append({
            "id_encuesta": res_id,
            "facultad": primera.get("facultad", ""),
            "carrera": primera.get("carrera", ""),
            "ciclo": primera.get("ciclo", ""),
            "nps_score": primera.get("nps_score", 0),
            "segmento_nps": primera.get("segmento_nps", ""),
            "satisfaccion_global": primera.get("satisfaccion_global", ""),
            "comentario_original": primera.get("comentario_original", ""),
            "fragmentos": fragmentos,
        })

    return datos_fragmentos, dataset_cualitativo, metadata
