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
# 1. DECLARACION DE LAS PREGUNTAS (identidad de columna)
# ============================================================
# Cada pregunta que procesa el ETL se declara UNA sola vez, aqui:
#
#   id       identificador corto, unico dentro de la encuesta y FIJO. Es lo que
#            el codigo debe usar para comparar columnas (nunca el nombre).
#   nombre   lo que se publica HOY en respuestas.json y en el portal.
#   tipo     'medida' (se mide), 'agrupacion' (agrupa o filtra), 'fecha' o
#            'identificador'.
#   pregunta el texto completo del cuestionario: la llave con la que Zoho manda
#            cada columna (antes, la clave de COLUMN_RENAME_*).
#   escala   solo cuando tipo es 'medida': 'CSAT' (satisfaccion de cinco
#            niveles) o 'NPS' (0 a 10).
#
# Los mapas COLUMN_RENAME_* que consume pandas se DERIVAN de estas listas: el
# texto de la pregunta vive en un solo sitio. Las columnas que el ETL publica
# pero que no son preguntas del formulario (Facultad, y Ciclo en graduados) se
# declaran aparte, en DERIVADAS_*.
#
# El comentario abierto (hoy "Comentario NPS") NO se declara como pregunta: no
# es medida, agrupacion, fecha ni identificador, y no se publica en
# respuestas.json (se analiza y aparece en sentimiento.json). Se conserva en el
# mapa de renombrado porque el ETL necesita renombrarlo.

TIPOS_VALIDOS: Set[str] = {"medida", "agrupacion", "fecha", "identificador"}

PREGUNTAS_PREGRADO: List[Dict[str, str]] = [
    {
        "id": "id_respuesta",
        "nombre": "ID",
        "tipo": "identificador",
        "pregunta": "ID de respuesta",
        "escala": "",
    },
    {
        "id": "inicio",
        "nombre": "Fecha de inicio",
        "tipo": "fecha",
        "pregunta": "Start time",
        "escala": "",
    },
    {
        "id": "fin",
        "nombre": "Fecha de fin",
        "tipo": "fecha",
        "pregunta": "Hora de finalización",
        "escala": "",
    },
    {
        "id": "nps",
        "nombre": "Recomendación (0 al 10)",
        "tipo": "medida",
        "pregunta": "Net Promoter Score (de un total de 10)",
        "escala": "NPS",
    },
    {
        "id": "carrera",
        "nombre": "Carrera",
        "tipo": "agrupacion",
        "pregunta": "¿Qué carrera profesional estudias?",
        "escala": "",
    },
    {
        "id": "ciclo",
        "nombre": "Ciclo",
        "tipo": "agrupacion",
        "pregunta": "¿Qué ciclo es el que cursas?; considera el ciclo donde más cursos llevas",
        "escala": "",
    },
    {
        "id": "perfil_del_egreso_de_la_carrera",
        "nombre": "Perfil del egreso de la carrera",
        "tipo": "medida",
        "pregunta": "El perfil de egreso de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "plan_curricular_y_perfil_de_egreso",
        "nombre": "Plan curricular y perfil de egreso",
        "tipo": "medida",
        "pregunta": "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "cursos_del_programa_y_contenidos",
        "nombre": "Cursos del programa y contenidos",
        "tipo": "medida",
        "pregunta": "Los cursos y contenidos de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "calidad_de_la_ensenanza_en_la_carrera",
        "nombre": "Calidad de la enseñanza en la carrera",
        "tipo": "medida",
        "pregunta": "La calidad del servicio de enseñanza en tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "claridad_de_los_recursos_academicos",
        "nombre": "Claridad de los recursos académicos",
        "tipo": "medida",
        "pregunta": "La claridad, precisión y actualización de los materiales de estudio de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "calidad_de_la_formacion_academica",
        "nombre": "Calidad de la formación académica",
        "tipo": "medida",
        "pregunta": "La calidad de la formación académica",
        "escala": "CSAT",
    },
    {
        "id": "evaluacion_del_aprendizaje",
        "nombre": "Evaluación del aprendizaje",
        "tipo": "medida",
        "pregunta": "La evaluación del aprendizaje en tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "intercambio_estudiantil",
        "nombre": "Intercambio estudiantil",
        "tipo": "medida",
        "pregunta": "El proceso de intercambio estudiantil",
        "escala": "CSAT",
    },
    {
        "id": "informacion_sobre_el_record_academico",
        "nombre": "Información sobre el récord académico",
        "tipo": "medida",
        "pregunta": "La información sobre tu récord académico",
        "escala": "CSAT",
    },
    {
        "id": "material_bibliografico_en_la_biblioteca",
        "nombre": "Material bibliográfico en la biblioteca",
        "tipo": "medida",
        "pregunta": "El material bibliográfico físico o digital disponible en la biblioteca",
        "escala": "CSAT",
    },
    {
        "id": "atencion_del_personal_administrativo",
        "nombre": "Atención del personal administrativo",
        "tipo": "medida",
        "pregunta": "El servicio recibido por el personal administrativo de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "procedimientos_administrativos",
        "nombre": "Procedimientos administrativos",
        "tipo": "medida",
        "pregunta": "Los procedimientos de los servicios administrativos de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "ayuda_financiera",
        "nombre": "Ayuda financiera",
        "tipo": "medida",
        "pregunta": "El servicio social: ayuda financiera",
        "escala": "CSAT",
    },
    {
        "id": "servicio_medico_y_su_infraestructura",
        "nombre": "Servicio médico y su infraestructura",
        "tipo": "medida",
        "pregunta": "El servicio médico y su infraestructura",
        "escala": "CSAT",
    },
    {
        "id": "servicio_de_atencion_psicopedagogica",
        "nombre": "Servicio de atención psicopedagógica",
        "tipo": "medida",
        "pregunta": "El servicio de atención psicopedagógica",
        "escala": "CSAT",
    },
    {
        "id": "talleres_de_actividades_artisticas_y_culturales",
        "nombre": "Talleres de actividades artísticas y culturales",
        "tipo": "medida",
        "pregunta": "Los talleres de actividades artísticas y culturales",
        "escala": "CSAT",
    },
    {
        "id": "actividades_deportivas",
        "nombre": "Actividades deportivas",
        "tipo": "medida",
        "pregunta": "Las actividades deportivas",
        "escala": "CSAT",
    },
    {
        "id": "empleabilidad_vinculacion_y_alumni",
        "nombre": "Empleabilidad, vinculación y ALUMNI",
        "tipo": "medida",
        "pregunta": "Empleabilidad, vinculación profesional y ALUMNI",
        "escala": "CSAT",
    },
    {
        "id": "aulas_de_clase",
        "nombre": "Aulas de clase",
        "tipo": "medida",
        "pregunta": "Las aulas de clase",
        "escala": "CSAT",
    },
    {
        "id": "ambientes_y_salas_para_estudio",
        "nombre": "Ambientes y salas para estudio",
        "tipo": "medida",
        "pregunta": "Los ambientes y salas para estudio",
        "escala": "CSAT",
    },
    {
        "id": "equipamiento_tecnologico_en_laboratorios",
        "nombre": "Equipamiento tecnológico en laboratorios",
        "tipo": "medida",
        "pregunta": "Los laboratorios en lo referido a equipamiento, tecnología y programas",
        "escala": "CSAT",
    },
    {
        "id": "condiciones_ambientales_en_laboratorios",
        "nombre": "Condiciones ambientales en laboratorios",
        "tipo": "medida",
        "pregunta": "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad",
        "escala": "CSAT",
    },
    {
        "id": "software_especializado_empleado_en_la_carrera",
        "nombre": "Software especializado empleado en la carrera",
        "tipo": "medida",
        "pregunta": "El software especializado empleado en la carrera",
        "escala": "CSAT",
    },
    {
        "id": "portal_web_de_la_universidad_mi_ulima",
        "nombre": "Portal web de la Universidad (Mi Ulima)",
        "tipo": "medida",
        "pregunta": "El portal web de la universidad: Mi Ulima",
        "escala": "CSAT",
    },
    {
        "id": "aula_virtual",
        "nombre": "Aula virtual",
        "tipo": "medida",
        "pregunta": "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "escala": "CSAT",
    },
    {
        "id": "conexion_wi_fi_en_el_campus",
        "nombre": "Conexión Wi-Fi en el campus",
        "tipo": "medida",
        "pregunta": "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "escala": "CSAT",
    },
    {
        "id": "soporte_tecnico_del_sistema_informatico",
        "nombre": "Soporte técnico del sistema informático",
        "tipo": "medida",
        "pregunta": "El soporte técnico brindado ante las fallas del sistema informático",
        "escala": "CSAT",
    },
    {
        "id": "csat_sujeto",
        "nombre": "Satisfacción con tu carrera",
        "tipo": "medida",
        "pregunta": "Tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "csat_universidad",
        "nombre": "Satisfacción con la Universidad",
        "tipo": "medida",
        "pregunta": "La Universidad de Lima",
        "escala": "CSAT",
    },
]

PREGUNTAS_GRADUADO: List[Dict[str, str]] = [
    {
        "id": "id_respuesta",
        "nombre": "ID",
        "tipo": "identificador",
        "pregunta": "ID de respuesta",
        "escala": "",
    },
    {
        "id": "inicio",
        "nombre": "Fecha de inicio",
        "tipo": "fecha",
        "pregunta": "Start time",
        "escala": "",
    },
    {
        "id": "fin",
        "nombre": "Fecha de fin",
        "tipo": "fecha",
        "pregunta": "Hora de finalización",
        "escala": "",
    },
    {
        "id": "nps",
        "nombre": "Recomendación (0 al 10)",
        "tipo": "medida",
        "pregunta": "Net Promoter Score (de un total de 10)",
        "escala": "NPS",
    },
    {
        "id": "carrera",
        "nombre": "Carrera",
        "tipo": "agrupacion",
        "pregunta": "¿Qué carrera profesional estudiaste?",
        "escala": "",
    },
    {
        "id": "situacion_laboral",
        "nombre": "Situación laboral",
        "tipo": "agrupacion",
        "pregunta": "¿Cuál es tu situación laboral actual?",
        "escala": "",
    },
    {
        "id": "tiempo_laboral",
        "nombre": "Tiempo laboral",
        "tipo": "agrupacion",
        "pregunta": "¿Cuál es el tiempo dedicado a tu trabajo?",
        "escala": "",
    },
    {
        "id": "perfil_del_egreso_de_la_carrera",
        "nombre": "Perfil del egreso de la carrera",
        "tipo": "medida",
        "pregunta": "El perfil de egreso de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "plan_curricular_y_perfil_de_egreso",
        "nombre": "Plan curricular y perfil de egreso",
        "tipo": "medida",
        "pregunta": "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "cursos_del_programa_y_contenidos",
        "nombre": "Cursos del programa y contenidos",
        "tipo": "medida",
        "pregunta": "Los cursos y contenidos de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "calidad_de_la_ensenanza_en_la_carrera",
        "nombre": "Calidad de la enseñanza en la carrera",
        "tipo": "medida",
        "pregunta": "La calidad del servicio de enseñanza de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "claridad_de_los_recursos_academicos",
        "nombre": "Claridad de los recursos académicos",
        "tipo": "medida",
        "pregunta": "La claridad, precisión y actualización de los materiales de estudio de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "calidad_de_la_formacion_academica",
        "nombre": "Calidad de la formación académica",
        "tipo": "medida",
        "pregunta": "La calidad de la formación académica",
        "escala": "CSAT",
    },
    {
        "id": "exigencia_academica",
        "nombre": "Exigencia académica",
        "tipo": "medida",
        "pregunta": "La exigencia académica de las asignaturas de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "evaluacion_del_aprendizaje",
        "nombre": "Evaluación del aprendizaje",
        "tipo": "medida",
        "pregunta": "La evaluación del aprendizaje de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "intercambio_estudiantil",
        "nombre": "Intercambio estudiantil",
        "tipo": "medida",
        "pregunta": "El proceso de intercambio estudiantil",
        "escala": "CSAT",
    },
    {
        "id": "transmision_de_conocimientos",
        "nombre": "Transmisión de conocimientos",
        "tipo": "medida",
        "pregunta": "El dominio de los conocimientos que transmiten",
        "escala": "CSAT",
    },
    {
        "id": "transmision_de_experiencias",
        "nombre": "Transmisión de experiencias",
        "tipo": "medida",
        "pregunta": "La capacidad para transmitir el conocimiento y experiencias que complementan la teoría",
        "escala": "CSAT",
    },
    {
        "id": "metodologias",
        "nombre": "Metodologías",
        "tipo": "medida",
        "pregunta": "Las metodologías y herramientas aplicadas para la enseñanza y aprendizaje",
        "escala": "CSAT",
    },
    {
        "id": "conocimientos_actualizados",
        "nombre": "Conocimientos actualizados",
        "tipo": "medida",
        "pregunta": "La actualización de los conocimientos transmitidos",
        "escala": "CSAT",
    },
    {
        "id": "compromiso",
        "nombre": "Compromiso",
        "tipo": "medida",
        "pregunta": "El compromiso con el aprendizaje de los alumnos",
        "escala": "CSAT",
    },
    {
        "id": "retroalimentacion",
        "nombre": "Retroalimentación",
        "tipo": "medida",
        "pregunta": "La retroalimentación de las tareas, trabajos y desempeño",
        "escala": "CSAT",
    },
    {
        "id": "disponibilidad_para_asesorias",
        "nombre": "Disponibilidad para asesorías",
        "tipo": "medida",
        "pregunta": "La disposición y tiempo para asesorar a los alumnos",
        "escala": "CSAT",
    },
    {
        "id": "cumplimiento_de_normas_y_programas",
        "nombre": "Cumplimiento de normas y programas",
        "tipo": "medida",
        "pregunta": "La disciplina en el cumplimiento de las normas y programas",
        "escala": "CSAT",
    },
    {
        "id": "habilidades_para_trabajar_en_equipo",
        "nombre": "Habilidades para trabajar en equipo",
        "tipo": "medida",
        "pregunta": "El desarrollo de tus habilidades de trabajo en equipo",
        "escala": "CSAT",
    },
    {
        "id": "habilidades_de_comunicacion",
        "nombre": "Habilidades de comunicación",
        "tipo": "medida",
        "pregunta": "El desarrollo de tus habilidades de comunicación",
        "escala": "CSAT",
    },
    {
        "id": "habilidades_para_aportar_nuevas_ideas",
        "nombre": "Habilidades para aportar nuevas ideas",
        "tipo": "medida",
        "pregunta": "La capacidad para aportar y explorar nuevas ideas",
        "escala": "CSAT",
    },
    {
        "id": "mejora_en_perspectivas_de_empleo",
        "nombre": "Mejora en perspectivas de empleo",
        "tipo": "medida",
        "pregunta": "La mejora de tu perspectiva de empleo",
        "escala": "CSAT",
    },
    {
        "id": "informacion_sobre_el_record_academico",
        "nombre": "Información sobre el récord académico",
        "tipo": "medida",
        "pregunta": "La información sobre tu récord académico",
        "escala": "CSAT",
    },
    {
        "id": "material_bibliografico_en_la_biblioteca",
        "nombre": "Material bibliográfico en la biblioteca",
        "tipo": "medida",
        "pregunta": "El material bibliográfico físico o digital disponible en la biblioteca",
        "escala": "CSAT",
    },
    {
        "id": "atencion_del_personal_administrativo",
        "nombre": "Atención del personal administrativo",
        "tipo": "medida",
        "pregunta": "El servicio recibido por el personal administrativo de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "procedimientos_administrativos",
        "nombre": "Procedimientos administrativos",
        "tipo": "medida",
        "pregunta": "Los procedimientos de los servicios administrativos de tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "ayuda_financiera",
        "nombre": "Ayuda financiera",
        "tipo": "medida",
        "pregunta": "El servicio social: ayuda financiera",
        "escala": "CSAT",
    },
    {
        "id": "servicio_medico_y_su_infraestructura",
        "nombre": "Servicio médico y su infraestructura",
        "tipo": "medida",
        "pregunta": "El servicio médico y su infraestructura",
        "escala": "CSAT",
    },
    {
        "id": "servicio_de_atencion_psicopedagogica",
        "nombre": "Servicio de atención psicopedagógica",
        "tipo": "medida",
        "pregunta": "El servicio de atención psicopedagógica",
        "escala": "CSAT",
    },
    {
        "id": "talleres_de_actividades_artisticas_y_culturales",
        "nombre": "Talleres de actividades artísticas y culturales",
        "tipo": "medida",
        "pregunta": "Los talleres de actividades artísticas y culturales",
        "escala": "CSAT",
    },
    {
        "id": "actividades_deportivas",
        "nombre": "Actividades deportivas",
        "tipo": "medida",
        "pregunta": "Las actividades deportivas",
        "escala": "CSAT",
    },
    {
        "id": "empleabilidad_vinculacion_y_alumni",
        "nombre": "Empleabilidad, vinculación y ALUMNI",
        "tipo": "medida",
        "pregunta": "Empleabilidad, vinculación profesional y ALUMNI",
        "escala": "CSAT",
    },
    {
        "id": "aulas_de_clase",
        "nombre": "Aulas de clase",
        "tipo": "medida",
        "pregunta": "Las aulas de clase",
        "escala": "CSAT",
    },
    {
        "id": "ambientes_y_salas_para_estudio",
        "nombre": "Ambientes y salas para estudio",
        "tipo": "medida",
        "pregunta": "Los ambientes y salas para estudio",
        "escala": "CSAT",
    },
    {
        "id": "equipamiento_tecnologico_en_laboratorios",
        "nombre": "Equipamiento tecnológico en laboratorios",
        "tipo": "medida",
        "pregunta": "Los laboratorios en lo referido a equipamiento, tecnología y programas",
        "escala": "CSAT",
    },
    {
        "id": "condiciones_ambientales_en_laboratorios",
        "nombre": "Condiciones ambientales en laboratorios",
        "tipo": "medida",
        "pregunta": "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad",
        "escala": "CSAT",
    },
    {
        "id": "software_especializado_empleado_en_la_carrera",
        "nombre": "Software especializado empleado en la carrera",
        "tipo": "medida",
        "pregunta": "El software especializado empleado en tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "portal_web_de_la_universidad_mi_ulima",
        "nombre": "Portal web de la Universidad (Mi Ulima)",
        "tipo": "medida",
        "pregunta": "El portal web de la universidad: Mi Ulima",
        "escala": "CSAT",
    },
    {
        "id": "aula_virtual",
        "nombre": "Aula virtual",
        "tipo": "medida",
        "pregunta": "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "escala": "CSAT",
    },
    {
        "id": "conexion_wi_fi_en_el_campus",
        "nombre": "Conexión Wi-Fi en el campus",
        "tipo": "medida",
        "pregunta": "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "escala": "CSAT",
    },
    {
        "id": "soporte_tecnico_del_sistema_informatico",
        "nombre": "Soporte técnico del sistema informático",
        "tipo": "medida",
        "pregunta": "El soporte técnico brindado ante las fallas del sistema informático",
        "escala": "CSAT",
    },
    {
        "id": "csat_sujeto",
        "nombre": "Satisfacción con tu carrera",
        "tipo": "medida",
        "pregunta": "Tu carrera",
        "escala": "CSAT",
    },
    {
        "id": "csat_universidad",
        "nombre": "Satisfacción con la Universidad",
        "tipo": "medida",
        "pregunta": "La Universidad de Lima",
        "escala": "CSAT",
    },
]

# Columnas publicadas por el ETL que no salen del formulario.
DERIVADAS_PREGRADO: List[Dict[str, str]] = [
    {
        "id": "facultad",
        "nombre": "Facultad",
        "tipo": "agrupacion",
        "pregunta": "Facultad (derivada de la carrera)",
        "escala": "",
    },
]

DERIVADAS_GRADUADO: List[Dict[str, str]] = [
    {
        "id": "ciclo",
        "nombre": "Ciclo",
        "tipo": "agrupacion",
        "pregunta": "Ciclo (derivado; la encuesta de graduados no lo pregunta)",
        "escala": "",
    },
    {
        "id": "facultad",
        "nombre": "Facultad",
        "tipo": "agrupacion",
        "pregunta": "Facultad (derivada de la carrera)",
        "escala": "",
    },
]

# Declaracion completa por nivel interno: preguntas del formulario + derivadas.
PREGUNTAS_POR_NIVEL: Dict[str, List[Dict[str, str]]] = {
    "undergraduate": PREGUNTAS_PREGRADO + DERIVADAS_PREGRADO,
    "graduate": PREGUNTAS_GRADUADO + DERIVADAS_GRADUADO,
}

# Texto de la pregunta abierta: el ETL la renombra, pero no se publica.
COMENTARIO_NPS_PREGUNTA: str = "Explica con tus palabras, las razones de la calificaci\u00f3n que diste en la pregunta anterior. (m\u00e1x. 100 caracteres)"


def declaraciones_de(nivel: str) -> List[Dict[str, str]]:
    """Declaracion de las preguntas de un nivel interno (vacia si no esta declarado)."""
    return list(PREGUNTAS_POR_NIVEL.get(nivel, []))


def _declaracion_por_id(id_pregunta: str) -> Dict[str, str]:
    """La declaracion de la pregunta con ese id, venga del nivel que venga."""
    for declaraciones in PREGUNTAS_POR_NIVEL.values():
        for d in declaraciones:
            if d["id"] == id_pregunta:
                return d
    raise KeyError("no hay pregunta declarada con id '%s'" % (id_pregunta,))


def nombre_publicado(id_pregunta: str) -> str:
    """Nombre publicado de la pregunta declarada con ese id (sin depender del nivel).

    Se usa donde no hay un nivel concreto (por ejemplo los prompts, comunes a
    todas las encuestas). Falla si el id no esta declarado: un nombre de columna
    jamas debe quedar escrito a mano.
    """
    return _declaracion_por_id(id_pregunta)["nombre"]


def columna(nivel: str, id_pregunta: str) -> str:
    """Nombre publicado de la columna declarada con ese id en esa encuesta.

    Es la unica via por la que el codigo debe pedir una columna: se identifica
    por el id estable, nunca por el nombre publicado. Si la encuesta aun no
    declara sus preguntas, cae al catalogo comun derivado de las declaraciones
    (esos niveles se renombran a esos mismos nombres en resolver_config_etl).
    """
    for d in declaraciones_de(nivel):
        if d["id"] == id_pregunta:
            return d["nombre"]
    return nombre_publicado(id_pregunta)


def pregunta_de(nivel: str, id_pregunta: str) -> str:
    """Texto del cuestionario de la pregunta declarada con ese id.

    Inverso de `columna`: el texto al que el ETL renombra vive en la declaracion.
    Se usa donde el archivo exportado debe mostrar la pregunta de la encuesta y
    no el nombre publicado.
    """
    for d in declaraciones_de(nivel):
        if d["id"] == id_pregunta:
            return d["pregunta"]
    return _declaracion_por_id(id_pregunta)["pregunta"]


def _mapa_renombrado(declaraciones: List[Dict[str, str]]) -> Dict[str, str]:
    """Deriva el mapa {pregunta de Zoho: nombre publicado} de una declaracion."""
    mapa = {d["pregunta"]: d["nombre"] for d in declaraciones}
    mapa[COMENTARIO_NPS_PREGUNTA] = "Comentario NPS"
    return mapa


COLUMN_RENAME_PREGRADO: Dict[str, str] = _mapa_renombrado(PREGUNTAS_PREGRADO)
COLUMN_RENAME_GRADUADO: Dict[str, str] = _mapa_renombrado(PREGUNTAS_GRADUADO)

# Version del contrato de respuestas.json. Desde 1.1 el archivo trae el bloque
# 'preguntas' (id, nombre, tipo, pregunta y escala de cada columna publicada);
# los archivos 1.0 anteriores no lo llevan y siguen siendo validos.
RESPUESTAS_VERSION: str = "1.1"

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
    "Satisfacción con tu carrera": "Académico",
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
    "Satisfacción con tu carrera": "Académico",
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
    "Satisfacción con tu carrera",
    "Satisfacción con la Universidad",
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
        (ID, Recomendación (0 al 10), Carrera, Satisfacción con la
        Universidad, Comentario NPS). El resto de columnas conserva su nombre.
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
        rename["Net Promoter Score (de un total de 10)"] = "Recomendación (0 al 10)"
    if carrera:
        rename[carrera] = "Carrera"
    if csat:
        # El nombre publicado del CSAT global sale de la declaracion (id
        # csat_universidad): renombrarlo no debe exigir escribirlo a mano aqui.
        rename[csat] = nombre_publicado("csat_universidad")
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
