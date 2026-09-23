"""
IA CLIENT — Cliente de los motores del análisis cualitativo.

El análisis cualitativo usa una CADENA DE MOTORES ordenada: se intenta el
primero y, si falla o devuelve una respuesta inválida, se pasa al siguiente.
Servicios soportados:

    google     Google Gemini    (clave GOOGLE_API_KEY)
    nvidia     NVIDIA NIM       (clave NVIDIA_API_KEY)
    opencode   OpenCode         (clave OPENCODE_API_KEY)

El orden y los modelos se cambian SIN tocar código con la variable de entorno
IA_CUALITATIVO_CADENA, en formato "servicio:modelo" separado por comas:

    opencode:deepseek-v4.1-flash,google:gemini-3.8-flash,nvidia:moonshotai/kimi-k3

Si la variable no está definida se usa CADENA_DEFECTO. Los motores cuya clave
no esté configurada se omiten con un aviso, de modo que se puede arrancar con
una sola clave y añadir las demás después.

El cliente usa urllib de la stdlib (sin dependencias externas) e incluye
reintentos con backoff, rate limiting por motor y acumulación de tokens.
"""

import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

DEFAULT_MAX_RPM = int(os.environ.get("IA_CUALITATIVO_MAX_RPM", "60"))
DEFAULT_TIMEOUT = int(os.environ.get("IA_CUALITATIVO_TIMEOUT", "60"))
DEFAULT_MAX_RETRIES = 3
DEFAULT_WORKERS = int(os.environ.get("IA_CUALITATIVO_WORKERS", "15"))

# NVIDIA en su plan gratuito tolera ~30 req/min; se limita a 15 para no
# provocar tormentas de 429/timeout cuando todos los comentarios caen ahí.
NVIDIA_MAX_RPM = 15

# Cadena por defecto: OpenCode (deepseek-v4.1-flash) → Google → NVIDIA (4
# modelos, en ese orden). El motor mas actual va primero; los demas quedan como
# respaldo si falla o devuelve una respuesta invalida.
CADENA_DEFECTO = ",".join([
    "opencode:deepseek-v4.1-flash",
    "google:gemini-3.8-flash",
    "nvidia:moonshotai/kimi-k3",
    "nvidia:deepseek-ai/deepseek-v4-pro-0813",
    "nvidia:nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia:meta/muse-glimmer-30b",
])

# Cada servicio: cómo se le habla, con qué clave y con qué límite de ritmo.
SERVICIOS: Dict[str, Dict[str, Any]] = {
    "google": {
        "formato": "google",
        "url": ("https://generativelanguage.googleapis.com/v1beta/"
                "models/{modelo}:generateContent"),
        "clave_env": "GOOGLE_API_KEY",
        "max_rpm": DEFAULT_MAX_RPM,
    },
    "nvidia": {
        "formato": "openai",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "clave_env": "NVIDIA_API_KEY",
        "max_rpm": NVIDIA_MAX_RPM,
    },
    "opencode": {
        "formato": "openai",
        # La clave sirve para los dos planes de OpenCode (Go, por suscripción,
        # y Zen, por uso); lo que cambia es la dirección. Por defecto se apunta
        # al plan Go. Para el plan Zen, definir:
        #   IA_CUALITATIVO_OPENCODE_URL=https://opencode.ai/zen/v1/chat/completions
        "url": os.environ.get(
            "IA_CUALITATIVO_OPENCODE_URL",
            "https://opencode.ai/zen/go/v1/chat/completions",
        ),
        "clave_env": "OPENCODE_API_KEY",
        "max_rpm": DEFAULT_MAX_RPM,
    },
}


# ============================================================
# LECTURA Y VALIDACIÓN DE LA CADENA
# ============================================================

def leer_cadena() -> str:
    """Texto de la cadena: IA_CUALITATIVO_CADENA o la cadena por defecto."""
    return (os.environ.get("IA_CUALITATIVO_CADENA", "") or CADENA_DEFECTO).strip()


def parsear_cadena(texto: str) -> List[Tuple[str, str]]:
    """Convierte "servicio:modelo,servicio:modelo" en [(servicio, modelo), ...].

    Ignora espacios, entradas vacías, comas repetidas, entradas sin modelo y
    servicios desconocidos (con aviso): una errata en la variable de entorno no
    debe tumbar el ETL.
    """
    motores: List[Tuple[str, str]] = []
    vistos = set()
    for entrada in texto.split(","):
        entrada = entrada.strip()
        if not entrada:
            continue
        if ":" not in entrada:
            logger.warning(
                f"Entrada de cadena ignorada (falta el formato 'servicio:modelo'): "
                f"{entrada!r}"
            )
            continue
        servicio, modelo = entrada.split(":", 1)
        servicio = servicio.strip().lower()
        modelo = modelo.strip()
        if servicio not in SERVICIOS:
            logger.warning(
                f"Servicio desconocido en la cadena, se ignora: {servicio!r} "
                f"(soportados: {', '.join(sorted(SERVICIOS))})"
            )
            continue
        if not modelo:
            logger.warning(f"Entrada de cadena sin modelo, se ignora: {entrada!r}")
            continue
        if (servicio, modelo) in vistos:
            logger.warning(f"Motor repetido en la cadena, se ignora: {servicio}:{modelo}")
            continue
        vistos.add((servicio, modelo))
        motores.append((servicio, modelo))
    return motores


def construir_motores(cadena: Optional[str] = None) -> List["MotorIA"]:
    """Motores listos para usar, en orden, solo los que tienen su clave.

    Los motores cuya clave no esté configurada se omiten con un aviso.
    """
    texto = leer_cadena() if cadena is None else cadena
    motores: List["MotorIA"] = []
    for servicio, modelo in parsear_cadena(texto):
        clave_env = SERVICIOS[servicio]["clave_env"]
        clave = os.environ.get(clave_env, "")
        if not clave:
            logger.warning(
                f"Motor omitido (falta la clave {clave_env}): {servicio}:{modelo}"
            )
            continue
        motores.append(MotorIA(servicio=servicio, modelo=modelo, api_key=clave))
    return motores


def claves_faltantes(cadena: Optional[str] = None) -> List[str]:
    """Claves de entorno que faltan para los servicios presentes en la cadena."""
    texto = leer_cadena() if cadena is None else cadena
    faltantes = []
    for servicio, _modelo in parsear_cadena(texto):
        clave_env = SERVICIOS[servicio]["clave_env"]
        if not os.environ.get(clave_env, "") and clave_env not in faltantes:
            faltantes.append(clave_env)
    return faltantes


# ============================================================
# CLIENTE DE UN MOTOR
# ============================================================

# ============================================================
# IDENTIFICACIÓN ANTE OPENCODE GO
# ============================================================
# OpenCode Go descarta con 403 (Cloudflare, código 1010) las peticiones cuyo
# agente empieza por "Python-urllib", que es el que urllib envía cuando no se
# declara ninguno. Su documentación pide además que cada cliente se identifique
# con un agente propio y envíe un identificador de sesión estable por
# conversación. Aquí la conversación es la corrida completa del ETL.
OPENCODE_AGENTE = "survey-storytelling-etl/1.0"
OPENCODE_SESION = f"survey-storytelling-{os.getpid()}-{int(time.time())}"
CABECERAS_OPENCODE = {
    "User-Agent": OPENCODE_AGENTE,
    "x-opencode-session": OPENCODE_SESION,
}


class MotorIA:
    """Cliente de un motor concreto (un servicio + un modelo)."""

    def __init__(self,
                 servicio: str,
                 modelo: str,
                 api_key: str,
                 max_rpm: Optional[int] = None,
                 timeout: int = DEFAULT_TIMEOUT,
                 max_retries: int = DEFAULT_MAX_RETRIES):
        if servicio not in SERVICIOS:
            raise ValueError(f"Servicio no soportado: {servicio!r}")
        self.servicio = servicio
        self.modelo = modelo
        self.api_key = api_key
        self.formato = SERVICIOS[servicio]["formato"]
        self.max_rpm = SERVICIOS[servicio]["max_rpm"] if max_rpm is None else max_rpm
        self.timeout = timeout
        self.max_retries = max_retries
        self.url = SERVICIOS[servicio]["url"].format(modelo=modelo)
        self._min_interval = 60.0 / self.max_rpm if self.max_rpm > 0 else 0
        self._last_call_ts = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._llamadas = 0
        self._rate_lock = threading.Lock()
        self._usage_lock = threading.Lock()

    @property
    def etiqueta(self) -> str:
        """Identificación legible del motor, para registros: 'servicio:modelo'."""
        return f"{self.servicio}:{self.modelo}"

    def _wait_rate_limit(self) -> None:
        """Rate limiting thread-safe: espaciado mínimo entre llamadas."""
        if self._min_interval <= 0:
            return
        with self._rate_lock:
            elapsed = time.monotonic() - self._last_call_ts
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call_ts = time.monotonic()

    def _cuerpo(self, system_prompt: str, user_prompt: str,
                max_tokens: int) -> bytes:
        """Cuerpo de la petición, en el formato que entiende cada servicio."""
        if self.formato == "google":
            # Gemini 3.x: NO se envía "temperature". Google desaconseja bajarla
            # (por debajo de 1.0 puede provocar respuestas repetitivas o peores).
            cuerpo: Dict[str, Any] = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": max_tokens,
                },
            }
        else:
            # NVIDIA NIM y OpenCode comparten el formato de OpenAI. Tampoco se
            # envía "temperature": estos modelos publican su valor recomendado
            # y aplicarlo por nuestra cuenta solo degrada la respuesta.
            cuerpo = {
                "model": self.modelo,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "stream": False,
            }
        return json.dumps(cuerpo).encode("utf-8")

    def _cabeceras(self) -> Dict[str, str]:
        """Cabeceras de autenticación de cada servicio."""
        if self.formato == "google":
            return {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            }
        cabeceras = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.servicio == "opencode":
            cabeceras.update(CABECERAS_OPENCODE)
        return cabeceras

    def _sumar_uso(self, entrada: int, salida: int) -> None:
        with self._usage_lock:
            self._total_input_tokens += int(entrada or 0)
            self._total_output_tokens += int(salida or 0)
            self._llamadas += 1

    def _json_de_texto(self, texto: str, razonamiento: str, raw: str) -> Dict[str, Any]:
        """Extrae el objeto JSON de la respuesta del modelo.

        Muchos modelos de razonamiento devuelven su pensamiento aparte y a veces
        dejan el JSON ahí; se intenta en ambas partes antes de fallar.
        """
        if not (texto or "").strip():
            if (razonamiento or "").strip():
                logger.warning(
                    "Respuesta con contenido vacío; se intenta extraer el JSON "
                    "del razonamiento interno."
                )
                coincidencia = re.search(r'(\{.*\})', razonamiento, re.DOTALL)
                if coincidencia:
                    try:
                        return json.loads(coincidencia.group(1))
                    except json.JSONDecodeError:
                        pass
            logger.error(f"Contenido vacío de {self.etiqueta}. Raw: {raw[:300]!r}")
            raise json.JSONDecodeError("Contenido vacío", "", 0)
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            coincidencia = re.search(r'(\{.*\})', texto, re.DOTALL)
            if coincidencia:
                try:
                    return json.loads(coincidencia.group(1))
                except json.JSONDecodeError:
                    pass
            if (razonamiento or "").strip():
                logger.warning(
                    "JSON inválido en el contenido; se intenta extraerlo del "
                    "razonamiento interno."
                )
                coincidencia = re.search(r'(\{.*\})', razonamiento, re.DOTALL)
                if coincidencia:
                    try:
                        return json.loads(coincidencia.group(1))
                    except json.JSONDecodeError:
                        pass
            logger.error(f"JSON inválido de {self.etiqueta}. Content: {texto[:500]!r}")
            raise

    def _interpretar(self, data: Dict[str, Any], raw: str) -> Dict[str, Any]:
        """Saca el JSON y los tokens de la respuesta, según el servicio."""
        if self.formato == "google":
            uso = data.get("usageMetadata", {}) or {}
            self._sumar_uso(uso.get("promptTokenCount", 0),
                            uso.get("candidatesTokenCount", 0))
            candidatos = data.get("candidates") or []
            if not candidatos:
                logger.error(f"Respuesta sin candidatos de {self.etiqueta}. Raw: {raw[:300]!r}")
                raise json.JSONDecodeError("Sin candidatos", "", 0)
            partes = (candidatos[0].get("content") or {}).get("parts") or []
            texto = "".join(p.get("text", "") for p in partes)
            razonamiento = ""
        else:
            uso = data.get("usage", {}) or {}
            self._sumar_uso(uso.get("prompt_tokens", 0),
                            uso.get("completion_tokens", 0))
            elecciones = data.get("choices") or []
            if not elecciones:
                logger.error(f"Respuesta sin opciones de {self.etiqueta}. Raw: {raw[:300]!r}")
                raise json.JSONDecodeError("Sin opciones", "", 0)
            mensaje = elecciones[0].get("message", {}) or {}
            texto = mensaje.get("content", "") or ""
            razonamiento = mensaje.get("reasoning_content", "") or ""
        return self._json_de_texto(texto, razonamiento, raw)

    def chat_completion(self, system_prompt: str, user_prompt: str,
                        max_tokens: int = 10000) -> Dict[str, Any]:
        """Llama al motor y devuelve la respuesta parseada como dict.

        Raises:
            RuntimeError: si todos los reintentos fallan.
        """
        cuerpo = self._cuerpo(system_prompt, user_prompt, max_tokens)
        cabeceras = self._cabeceras()
        last_error: Optional[str] = None

        for attempt in range(1, self.max_retries + 1):
            self._wait_rate_limit()
            req = urllib_request.Request(
                self.url, data=cuerpo, headers=cabeceras, method="POST"
            )
            try:
                with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    return self._interpretar(data, raw)
            except HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code == 429:
                    wait = 2 ** attempt
                    logger.warning(
                        f"{self.etiqueta}: rate limit (429). Reintento "
                        f"{attempt}/{self.max_retries} en {wait}s."
                    )
                    time.sleep(wait)
                    continue
                if 400 <= e.code < 500:
                    try:
                        err_body = e.read().decode("utf-8")
                        last_error = f"HTTP {e.code}: {err_body[:300]}"
                    except (UnicodeDecodeError, IOError):
                        pass
                    break
                wait = 2 ** attempt
                logger.warning(
                    f"{self.etiqueta}: error {e.code}. Reintento "
                    f"{attempt}/{self.max_retries} en {wait}s."
                )
                time.sleep(wait)
            except URLError as e:
                last_error = f"URLError: {e.reason}"
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"{self.etiqueta}: URLError. Reintento "
                        f"{attempt}/{self.max_retries} en {wait}s."
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"{self.etiqueta}: URLError tras {self.max_retries} "
                        f"reintentos: {e.reason}"
                    )
            except (json.JSONDecodeError, OSError, ValueError) as e:
                last_error = str(e)
                if "char 0" in str(e) or "Contenido vacío" in str(e):
                    break
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"{self.etiqueta}: error {e}. Reintento "
                        f"{attempt}/{self.max_retries} en {wait}s."
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"{self.etiqueta}: error tras {self.max_retries} "
                        f"reintentos: {e}"
                    )

        raise RuntimeError(
            f"{self.etiqueta} no respondió tras {self.max_retries} reintentos: "
            f"{last_error}"
        )

    @property
    def usage(self) -> Dict[str, int]:
        with self._usage_lock:
            return {
                "input_tokens": self._total_input_tokens,
                "output_tokens": self._total_output_tokens,
                "total_tokens": self._total_input_tokens + self._total_output_tokens,
                "llamadas": self._llamadas,
            }
