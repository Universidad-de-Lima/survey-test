"""
SURVEY ETL CONFIG — Configuración centralizada del pipeline ETL.

Centraliza todos los mapeos, catálogos y configuraciones para encuestas
de pregrado y graduados.

Para añadir soporte a nuevas carreras, dimensiones o tópicos:
1. Editar este archivo.
2. Los scripts de procesamiento y validación leerán estos valores automáticamente.
"""

from typing import Dict, List, Set

# ============================================================
# 1. RENOMBRADO DE COLUMNAS (Zoho Survey → nombres internos)
# ============================================================

COLUMN_RENAME_PREGRADO: Dict[str, str] = {
    "ID de respuesta": "ID",
    "Start time": "Inicio",
    "Hora de finalización": "Fin",
    "Net Promoter Score (de un total de 10)": "Recomiendas la Universidad de Lima",
    "¿Qué carrera profesional estudias?": "Carrera",
    "¿Qué ciclo es el que cursas?; considera el ciclo donde más cursos llevas": "Ciclo",
    "El perfil de egreso de tu carrera": "Perfil del egreso de la carrera",
    "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera": "Plan curricular y perfil de egreso",
    "Los cursos y contenidos de tu carrera": "Cursos del programa y contenidos",
    "La calidad del servicio de enseñanza en tu carrera": "Calidad de la enseñanza en la carrera",
    "La claridad, precisión y actualización de los materiales de estudio de tu carrera": "Claridad de los recursos académicos",
    "La calidad de la formación académica": "Calidad de la formación académica",
    "La evaluación del aprendizaje en tu carrera": "Evaluación del aprendizaje",
    "El proceso de intercambio estudiantil": "Intercambio estudiantil",
    "La información sobre tu récord académico": "Información sobre el récord académico",
    "El material bibliográfico físico o digital disponible en la biblioteca": "Material bibliográfico en la biblioteca",
    "El servicio recibido por el personal administrativo de tu carrera": "Atención del personal administrativo",
    "Los procedimientos de los servicios administrativos de tu carrera": "Procedimientos administrativos",
    "El servicio social: ayuda financiera": "Ayuda financiera",
    "El servicio médico y su infraestructura": "Servicio médico y su infraestructura",
    "El servicio de atención psicopedagógica": "Servicio de atención psicopedagógica",
    "Los talleres de actividades artísticas y culturales": "Talleres de actividades artísticas y culturales",
    "Las actividades deportivas": "Actividades deportivas",
    "Empleabilidad, vinculación profesional y ALUMNI": "Empleabilidad, vinculación y ALUMNI",
    "Las aulas de clase": "Aulas de clase",
    "Los ambientes y salas para estudio": "Ambientes y salas para estudio",
    "Los laboratorios en lo referido a equipamiento, tecnología y programas": "Equipamiento tecnológico en laboratorios",
    "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad": "Condiciones ambientales en laboratorios",
    "El software especializado empleado en la carrera": "Software especializado empleado en la carrera",
    "El portal web de la universidad: Mi Ulima": "Portal web de la Universidad (Mi Ulima)",
    "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)": "Aula virtual",
    "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual": "Conexión Wi-Fi en el campus",
    "El soporte técnico brindado ante las fallas del sistema informático": "Soporte técnico del sistema informático",
    "Tu carrera": "La carrera",
    "La Universidad de Lima": "La Universidad de Lima",
    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Comentario NPS",
}

# ── Mappings específicos para encuesta de GRADUADOS (Posgrado) ──
# BUG SOLVED: "Comentario NPS" unificado con la columna de pregrado
# para asegurar que el motor cualitativo procese el texto libre correctamente.
COLUMN_RENAME_GRADUADO: Dict[str, str] = {
    "ID de respuesta": "ID",
    "Start time": "Inicio",
    "Hora de finalización": "Fin",
    "Net Promoter Score (de un total de 10)": "Recomiendas la Universidad de Lima",
    "¿Qué carrera profesional estudiaste?": "Carrera",
    "¿Cuál es tu situación laboral actual?": "Situación laboral",
    "¿Cuál es el tiempo dedicado a tu trabajo?": "Tiempo laboral",
    "El perfil de egreso de tu carrera": "Perfil del egreso de la carrera",
    "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera": "Plan curricular y perfil de egreso",
    "Los cursos y contenidos de tu carrera": "Cursos del programa y contenidos",
    "La calidad del servicio de enseñanza de tu carrera": "Calidad de la enseñanza en la carrera",
    "La claridad, precisión y actualización de los materiales de estudio de tu carrera": "Claridad de los recursos académicos",
    "La calidad de la formación académica": "Calidad de la formación académica",
    "La exigencia académica de las asignaturas de tu carrera": "Exigencia académica",
    "La evaluación del aprendizaje de tu carrera": "Evaluación del aprendizaje",
    "El proceso de intercambio estudiantil": "Intercambio estudiantil",
    "El dominio de los conocimientos que transmiten": "Transmisión de conocimientos",
    "La capacidad para transmitir el conocimiento y experiencias que complementan la teoría": "Transmisión de experiencias",
    "Las metodologías y herramientas aplicadas para la enseñanza y aprendizaje": "Metodologías",
    "La actualización de los conocimientos transmitidos": "Conocimientos actualizados",
    "El compromiso con el aprendizaje de los alumnos": "Compromiso",
    "La retroalimentación de las tareas, trabajos y desempeño": "Retroalimentación",
    "La disposición y tiempo para asesorar a los alumnos": "Disponibilidad para asesorias",
    "La disciplina en el cumplimiento de las normas y programas": "Cumplimiento de normas y programas",
    "El desarrollo de tus habilidades de trabajo en equipo": "Habilidades para trabajar en equipo",
    "El desarrollo de tus habilidades de comunicación": "Habilidades de comunicación",
    "La capacidad para aportar y explorar nuevas ideas": "Habilidades para aportar nuevas ideas",
    "La mejora de tu perspectiva de empleo": "Mejora en perspectivas de empleo",
    "La información sobre tu récord académico": "Información sobre el récord académico",
    "El material bibliográfico físico o digital disponible en la biblioteca": "Material bibliográfico en la biblioteca",
    "El servicio recibido por el personal administrativo de tu carrera": "Atención del personal administrativo",
    "Los procedimientos de los servicios administrativos de tu carrera": "Procedimientos administrativos",
    "El servicio social: ayuda financiera": "Ayuda financiera",
    "El servicio médico y su infraestructura": "Servicio médico y su infraestructura",
    "El servicio de atención psicopedagógica": "Servicio de atención psicopedagógica",
    "Los talleres de actividades artísticas y culturales": "Talleres de actividades artísticas y culturales",
    "Las actividades deportivas": "Actividades deportivas",
    "Empleabilidad, vinculación profesional y ALUMNI": "Empleabilidad, vinculación y ALUMNI",
    "Las aulas de clase": "Aulas de clase",
    "Los ambientes y salas para estudio": "Ambientes y salas para estudio",
    "Los laboratorios en lo referido a equipamiento, tecnología y programas": "Equipamiento tecnológico en laboratorios",
    "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad": "Condiciones ambientales en laboratorios",
    "El software especializado empleado en tu carrera": "Software especializado empleado en la carrera",
    "El portal web de la universidad: Mi Ulima": "Portal web de la Universidad (Mi Ulima)",
    "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)": "Aula virtual",
    "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual": "Conexión Wi-Fi en el campus",
    "El soporte técnico brindado ante las fallas del sistema informático": "Soporte técnico del sistema informático",
    "Tu carrera": "La carrera",
    "La Universidad de Lima": "La Universidad de Lima",
    "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)": "Comentario NPS",
}

# ============================================================
# 2. CATÁLOGO CARRERA → FACULTAD
# ============================================================

CARRERA_FACULTAD: Dict[str, str] = {
    "Arquitectura": "Facultad de Arquitectura",
    "Administración": "Facultad de Ciencias Empresariales",
    "Contabilidad y Finanzas": "Facultad de Ciencias Empresariales",
    "Marketing": "Facultad de Ciencias Empresariales",
    "Negocios Internacionales": "Facultad de Ciencias Empresariales",
    "Comunicación": "Facultad de Comunicación",
    "Derecho": "Facultad de Derecho",
    "Economía": "Facultad de Economía",
    "Ingeniería Ambiental": "Facultad de Ingeniería",
    "Ingeniería Civil": "Facultad de Ingeniería",
    "Ingeniería de Sistemas": "Facultad de Ingeniería",
    "Ingeniería Industrial": "Facultad de Ingeniería",
    "Ingeniería Mecatrónica": "Facultad de Ingeniería",
    "Psicología": "Facultad de Psicología",
}

# ============================================================
# 3. CATÁLOGO DIMENSIÓN → CATEGORÍA
# ============================================================

CATEGORIA_DIMENSION_PREGRADO: Dict[str, str] = {
    # Académico
    "Perfil del egreso de la carrera": "Académico",
    "Plan curricular y perfil de egreso": "Académico",
    "Cursos del programa y contenidos": "Académico",
    "Calidad de la enseñanza en la carrera": "Académico",
    "Claridad de los recursos académicos": "Académico",
    "Calidad de la formación académica": "Académico",
    "Exigencia académica": "Académico",
    "Evaluación del aprendizaje": "Académico",
    "Intercambio estudiantil": "Académico",
    "La carrera": "Académico",
    "Satisfacción estudiantil": "Académico",
    
    # Administrativo y Bienestar
    "Información sobre el récord académico": "Administrativo y Bienestar",
    "Material bibliográfico en la biblioteca": "Administrativo y Bienestar",
    "Atención del personal administrativo": "Administrativo y Bienestar",
    "Procedimientos administrativos": "Administrativo y Bienestar",
    "Ayuda financiera": "Administrativo y Bienestar",
    "Servicio médico y su infraestructura": "Administrativo y Bienestar",
    "Servicio de atención psicopedagógica": "Administrativo y Bienestar",
    "Talleres de actividades artísticas y culturales": "Administrativo y Bienestar",
    "Actividades deportivas": "Administrativo y Bienestar",
    "Empleabilidad, vinculación y ALUMNI": "Administrativo y Bienestar",
    
    # Infraestructura
    "Aulas de clase": "Infraestructura",
    "Ambientes y salas para estudio": "Infraestructura",
    "Equipamiento tecnológico en laboratorios": "Infraestructura",
    "Condiciones ambientales en laboratorios": "Infraestructura",
    "Ubicación": "Infraestructura",
    "Espacios de alimentación": "Infraestructura",
    # Fase IA: dimensión catch-all para referencias genéricas a espacios del campus
    # (no tiene pregunta CSAT directa en Zoho; se infiere del comentario).
    "Espacios comunes": "Infraestructura",
   
    # Tecnología
    "Software especializado empleado en la carrera": "Tecnología",
    "Portal web de la Universidad (Mi Ulima)": "Tecnología",
    "Aula virtual": "Tecnología",
    "Conexión Wi-Fi en el campus": "Tecnología",
    "Soporte técnico del sistema informático": "Tecnología",
}

CATEGORIA_DIMENSION_GRADUADO: Dict[str, str] = {
    # Docencia
    "Transmisión de conocimientos": "Docencia",
    "Transmisión de experiencias": "Docencia",
    "Metodologías": "Docencia",
    "Conocimientos actualizados": "Docencia",
    "Compromiso": "Docencia",
    "Retroalimentación": "Docencia",
    "Disponibilidad para asesorías": "Docencia",
    "Cumplimiento de normas y programas": "Docencia",
    
    # Desarrollo Profesional
    "Habilidades para trabajar en equipo": "Desarrollo Profesional",
    "Habilidades de comunicación": "Desarrollo Profesional",
    "Habilidades para aportar nuevas ideas": "Desarrollo Profesional",
    "Mejora en perspectivas de empleo": "Desarrollo Profesional",

    # Académico
    "Perfil del egreso de la carrera": "Académico",
    "Plan curricular y perfil de egreso": "Académico",
    "Cursos del programa y contenidos": "Académico",
    "Calidad de la enseñanza en la carrera": "Académico",
    "Claridad de los recursos académicos": "Académico",
    "Calidad de la formación académica": "Académico",
    "Exigencia académica": "Académico",
    "Evaluación del aprendizaje": "Académico",
    "Intercambio estudiantil": "Académico",
    "La carrera": "Académico",
    "Satisfacción estudiantil": "Académico",
    
    # Administrativo y Bienestar
    "Información sobre el récord académico": "Administrativo y Bienestar",
    "Material bibliográfico en la biblioteca": "Administrativo y Bienestar",
    "Atención del personal administrativo": "Administrativo y Bienestar",
    "Procedimientos administrativos": "Administrativo y Bienestar",
    "Ayuda financiera": "Administrativo y Bienestar",
    "Servicio médico y su infraestructura": "Administrativo y Bienestar",
    "Servicio de atención psicopedagógica": "Administrativo y Bienestar",
    "Talleres de actividades artísticas y culturales": "Administrativo y Bienestar",
    "Actividades deportivas": "Administrativo y Bienestar",
    "Empleabilidad, vinculación y ALUMNI": "Administrativo y Bienestar",
    
    # Infraestructura
    "Aulas de clase": "Infraestructura",
    "Ambientes y salas para estudio": "Infraestructura",
    "Equipamiento tecnológico en laboratorios": "Infraestructura",
    "Condiciones ambientales en laboratorios": "Infraestructura",
    "Ubicación": "Infraestructura",
    "Espacios de alimentación": "Infraestructura",
    "Espacios comunes": "Infraestructura",
   
    # Tecnología
    "Software especializado empleado en la carrera": "Tecnología",
    "Portal web de la Universidad (Mi Ulima)": "Tecnología",
    "Aula virtual": "Tecnología",
    "Conexión Wi-Fi en el campus": "Tecnología",
    "Soporte técnico del sistema informático": "Tecnología",
}


# ============================================================
# 3a-bis. TAXONOMÍA UNIFICADA (pregrado + graduado)
# ============================================================
# Unión de CATEGORIA_DIMENSION_PREGRADO + CATEGORIA_DIMENSION_GRADUADO.
# Se pasa al system_prompt del motor IA para que este tenga TODAS las
# dimensiones disponibles al clasificar comentarios de cualquier nivel.
#
# Esto resuelve el bug por el cual comentarios de pregrado sobre
# "metodologías", "asesorías" o "perspectivas de empleo" se clasificaban
# en dimensiones incorrectas (porque esas dimensiones solo existían en
# la taxonomía de graduado y la IA no las conocía al analizar pregrado).
#
# Si una dimensión aparece en ambos mapas con la misma categoría padre,
# se incluye una sola vez. Si tuviera categorías padre distintas (no debería),
# gana la de graduado (más específica).
CATEGORIA_DIMENSION_UNIFICADA: Dict[str, str] = {}
CATEGORIA_DIMENSION_UNIFICADA.update(CATEGORIA_DIMENSION_PREGRADO)
CATEGORIA_DIMENSION_UNIFICADA.update(CATEGORIA_DIMENSION_GRADUADO)

# ============================================================
# 3b. DIMENSIONES SIN PREGUNTA CSAT DIRECTA (catch-all)
# ============================================================
# Estas dimensiones se usan en el análisis cualitativo pero NO tienen una
# columna CSV de calificación CSAT asociada. El cross-reference
# dimension_evaluada_rating devolverá null para ellas.
DIMENSIONES_SIN_CSAT: Set[str] = {
    "Satisfacción estudiantil",
    "Espacios comunes",
    "La carrera",
    "La Universidad de Lima",
    "Pendiente de Clasificación",
}

# ============================================================
# 4. RESPUESTAS DE TEXTO ESTÁNDAR
# ============================================================

RESPUESTAS_TEXTO: List[str] = [
    "Totalmente satisfecho",
    "Muy satisfecho",
    "Satisfecho",
    "Insatisfecho",
    "Totalmente insatisfecho",
    "No utilizo",
    "No conozco",
]

# ============================================================
# 4b. PESOS DE LA ESCALA LIKERT PARA EL PROMEDIO PONDERADO
# ============================================================
# Invariante de alineación: CSAT_WEIGHTS debe estar alineado posicionalmente
# con RESPUESTAS_TEXTO[:5] (de más positivo a más negativo). Cualquier
# reorden de RESPUESTAS_TEXTO rompería esta alineación.
CSAT_WEIGHTS: List[int] = [5, 4, 3, 2, 1]
CSAT_SCALE_MAX: int = 5

# ============================================================
# 5. MAPA DE ETAPAS (ciclo numérico → etapa académica)
# ============================================================

ETAPA_MAP: Dict[int, str] = {
    1: "Inicial",
    2: "Inicial",
    3: "Intermedio",
    4: "Intermedio",
    5: "Intermedio",
    6: "Avanzado",
    7: "Avanzado",
    8: "Avanzado",
    9: "Avanzado",
    10: "Avanzado",
    11: "Avanzado",
    12: "Avanzado",
}



# ============================================================
# 6. EMPLEABILIDAD (encuestas de graduados)
# ============================================================

EMPLEABILIDAD_CATEGORIAS: List[str] = [
    "Trabajador dependiente",
    "Prácticas profesionales",
    "Trabajador independiente",
    "Prácticas pre - profesionales"
]




# ============================================================
# 7. MOTOR CUALITATIVO — Configuración (motor legacy eliminado en v3.2.0)
# ============================================================

# El motor legacy (spaCy + sentence-transformers) fue eliminado en v3.2.0.
# El motor IA es una cadena de motores (Google, NVIDIA, OpenCode) desde v3.9.0.
# Al menos UNA clave de motor es obligatoria para ejecutar el ETL.
# Variables de entorno del motor IA:
# - GOOGLE_API_KEY / NVIDIA_API_KEY / OPENCODE_API_KEY: al menos una.
# - IA_CUALITATIVO_WORKERS: workers concurrentes (default: 15).
# - IA_CUALITATIVO_MAX_RPM: rate limit por motor (default: 60; Google: 10, NVIDIA: 8).
# - IA_CUALITATIVO_TIMEOUT: timeout por llamada (default: 60s).

# ============================================================
# 8. CONFIGURACION ETL POR NIVEL (Fase 2: 7 categorias)
# ============================================================
# Resuelve, para cada nivel interno, las columnas clave de negocio
# (carrera/programa/dependencia, CSAT, ciclo, mapeo de facultad) y el
# rename minimo a nombres internos. Mantiene identico el comportamiento
# de undergraduate/graduate (usa COLUMN_RENAME_* y CATEGORIA_DIMENSION_*).
#
# Columnas candidatas de identidad por nivel (la primera presente en el
# CSV gana). Los empleadores tienen PRE/PG con texto distinto.
_NIVEL_CARRERA: Dict[str, List[str]] = {
    "undergraduate": ["\u00bfQu\u00e9 carrera profesional estudias?"],
    "postgraduate": ["\u00bfQu\u00e9 programa de posgrado estudias?"],
    "graduate": ["\u00bfQu\u00e9 carrera profesional estudiaste?"],
    "alumni-ug": ["\u00bfQu\u00e9 carrera profesional estudiaste?"],
    "alumni-pg": ["\u00bfQu\u00e9 programa de posgrado estudiaste?"],
    "faculty-ug": ["\u00bfQu\u00e9 carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?"],
    "faculty-pg": ["\u00bfQu\u00e9 programa de posgrado dictas en la Universidad de Lima?"],
    "nonfaculty": ["\u00bfA qu\u00e9 dependencia perteneces?"],
    "employers": [
        "\u00bfQu\u00e9 carrera es la que procede el profesional de la Universidad de Lima contratado por su organizaci\u00f3n?",
        "\u00bfCu\u00e1l posgrado es el que procede el profesional de la Universidad de Lima contratado por su organizaci\u00f3n?",
    ],
}
# CSAT de texto (escala RESPUESTAS_TEXTO). None => empleadores (sin esa columna)
_NIVEL_CSAT: Dict[str, str] = {
    "undergraduate": "La Universidad de Lima",
    "postgraduate": "La Universidad de Lima",
    "graduate": "La Universidad de Lima",
    "alumni-ug": "La Universidad de Lima",
    "alumni-pg": "La Universidad de Lima",
    "faculty-ug": "La Universidad de Lima",
    "faculty-pg": "La Universidad de Lima",
    "nonfaculty": "La Universidad de Lima",
    "employers": None,
}
_NIVEL_CICLO: Dict[str, str] = {
    "undergraduate": "\u00bfQu\u00e9 ciclo es el que cursas?; considera el ciclo donde m\u00e1s cursos llevas",
}
# Niveles cuya columna de identidad son carreras de pregrado de la Universidad
# de Lima, por lo que se pueden traducir a facultad con CARRERA_FACULTAD.
# Quedan fuera posgrado (programas), no docente (dependencias) y empleadores
# cuando la respuesta es un posgrado.
_NIVEL_FAC_MAP: Set[str] = {
    "undergraduate", "alumni-ug", "graduate", "faculty-ug", "employers",
}

# Clasificacion de dimensiones por palabra clave (categoria padre).
# El schema de dimensiones.json NO exige enum; cualquier etiqueta sirve.
_KEYWORD_CAT: List[tuple] = [
    ("infraestruct", "Infraestructura"), ("bibliotec", "Infraestructura"),
    ("aula", "Infraestructura"), ("laborator", "Infraestructura"),
    ("instalac", "Infraestructura"), ("oficina", "Infraestructura"),
    ("cub\u00edculo", "Infraestructura"), ("espacio", "Infraestructura"),
    ("wifi", "Tecnolog\u00eda"), ("blackboard", "Tecnolog\u00eda"),
    ("mi ulima", "Tecnolog\u00eda"), ("portal web", "Tecnolog\u00eda"),
    ("soporte t\u00e9cnico", "Tecnolog\u00eda"), ("tecnolog", "Tecnolog\u00eda"),
    ("software", "Tecnolog\u00eda"),
    ("personal administrativo", "Administrativo y Bienestar"),
    ("procedimientos administrativos", "Administrativo y Bienestar"),
    ("ayuda financiera", "Administrativo y Bienestar"),
    ("servicio m\u00e9dico", "Administrativo y Bienestar"),
    ("psicopedag", "Administrativo y Bienestar"),
    ("taller", "Administrativo y Bienestar"), ("deporte", "Administrativo y Bienestar"),
    ("dependencia", "Administrativo y Bienestar"),
    ("clima laboral", "Administrativo y Bienestar"),
    ("bienestar", "Administrativo y Bienestar"),
    ("ense\u00f1anza", "Acad\u00e9mico"), ("cursos", "Acad\u00e9mico"),
    ("perfil de egreso", "Acad\u00e9mico"), ("plan curricular", "Acad\u00e9mico"),
    ("evaluaci\u00f3n del aprendizaje", "Acad\u00e9mico"),
    ("calidad de la formaci\u00f3n", "Acad\u00e9mico"), ("contenido", "Acad\u00e9mico"),
    ("acad\u00e9m", "Acad\u00e9mico"),
    ("autoridades", "Docencia"), ("coordinador", "Docencia"),
    ("liderazgo", "Docencia"), ("investigaci\u00f3n", "Docencia"),
    ("capacitaci\u00f3n", "Docencia"), ("docente", "Docencia"),
    ("metodolog", "Docencia"),
    ("competencia", "Desarrollo Profesional"),
    ("trabajo en equipo", "Desarrollo Profesional"),
    ("comunicaci\u00f3n", "Desarrollo Profesional"),
    ("an\u00e1lisis", "Desarrollo Profesional"),
    ("honestidad", "Desarrollo Profesional"),
    ("empresa", "Desarrollo Profesional"),
    ("desempe\u00f1o", "Desarrollo Profesional"),
]


def clasificar_categoria_dimension(campo: str) -> str:
    """Mapea el texto de una pregunta de dimension a su categoria padre."""
    c = (campo or "").lower()
    for kw, cat in _KEYWORD_CAT:
        if kw in c:
            return cat
    return "General"


def resolver_config_etl(nivel: str, columnas_df) -> Dict[str, object]:
    """Resuelve la configuracion ETL para un nivel interno.

    Args:
        nivel: nivel interno devuelto por _detectar_nivel.
        columnas_df: iterable con los nombres de columna del CSV.

    Returns:
        dict con carrera, csat, ciclo, facultad_map, rename, requeridas.
        'rename' mapea solo columnas clave a nombres internos
        (ID, Recomiendas la Universidad de Lima, Carrera, La Universidad de
        Lima, Comentario NPS). El resto de columnas conserva su nombre.
    """
    cols = [str(c) for c in columnas_df]
    colset = set(cols)
    carrera = next((c for c in _NIVEL_CARRERA.get(nivel, []) if c in colset), None)
    csat = _NIVEL_CSAT.get(nivel)
    if csat and csat not in colset:
        csat = None
    ciclo = _NIVEL_CICLO.get(nivel)
    if ciclo and ciclo not in colset:
        ciclo = None
    facultad_map = nivel in _NIVEL_FAC_MAP

    rename: Dict[str, str] = {}
    if "ID de respuesta" in colset:
        rename["ID de respuesta"] = "ID"
    if "Net Promoter Score (de un total de 10)" in colset:
        rename["Net Promoter Score (de un total de 10)"] = "Recomiendas la Universidad de Lima"
    if carrera:
        rename[carrera] = "Carrera"
    if csat:
        rename[csat] = "La Universidad de Lima"
    for c in cols:
        if c.startswith("Explica con tus palabras"):
            rename[c] = "Comentario NPS"
            break

    requeridas = ["ID de respuesta", "Net Promoter Score (de un total de 10)"]
    if carrera:
        requeridas.append(carrera)

    return {
        "carrera": carrera,
        "csat": csat,
        "ciclo": ciclo,
        "facultad_map": facultad_map,
        "rename": rename,
        "requeridas": requeridas,
    }
