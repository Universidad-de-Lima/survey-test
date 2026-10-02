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

# ---- Escuela de Posgrado: estudiantil y docente ----
# Los `pregunta` de estas preguntas son EXACTAMENTE las claves con las que Zoho
# manda cada columna en data/zoho_pendientes (los textos de sus cuestionarios),
# y los `nombre` son los nombres publicados que elegimos (cortos) para el portal.
# El estudiantil NO tiene pregunta abierta; el docente si (ver COMENTARIO_POR_NIVEL).
# Ninguno de los dos tiene una pregunta 'Satisfaccion con la Universidad'.
PREGUNTAS_POSTGRADO: List[Dict[str, str]] = [
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
        "pregunta": "Hora inicial de resuestas",
        "escala": "",
    },
    {
        "id": "fin",
        "nombre": "Fecha de fin",
        "tipo": "fecha",
        "pregunta": "Hora final de resuestas",
        "escala": "",
    },
    {
        "id": "nps",
        "nombre": "Recomendación (0 al 10)",
        "tipo": "medida",
        "pregunta": "En una escala del 0 al 10, donde 0 significa ‘Definitivamente no la recomendaría’ y 10 ‘Definitivamente sí la recomendaría’¿Qué tan probable es que recomiendes a la Escuela de Posgrado de la Universidad de Lima a un familiar o amigo como institución para estudiar un posgrado?",
        "escala": "NPS",
    },
    {
        "id": "pg_carrera_profesion",
        "nombre": "Carrera (profesión)",
        "tipo": "agrupacion",
        "pregunta": "Carrera (profesión)",
        "escala": "",
    },
    {
        "id": "pg_edad",
        "nombre": "Edad",
        "tipo": "agrupacion",
        "pregunta": "Edad:",
        "escala": "",
    },
    {
        "id": "pg_grado_academico",
        "nombre": "Grado académico",
        "tipo": "agrupacion",
        "pregunta": "Grado Académico más alto alcanzado:",
        "escala": "",
    },
    {
        "id": "pg_nivel_semestre",
        "nombre": "Nivel / Semestre",
        "tipo": "agrupacion",
        "pregunta": "Nivel  / Semestre actual:",
        "escala": "",
    },
    {
        "id": "carrera",
        "nombre": "Programa",
        "tipo": "agrupacion",
        "pregunta": "Programa:",
        "escala": "",
    },
    {
        "id": "pg_puesto",
        "nombre": "Puesto",
        "tipo": "agrupacion",
        "pregunta": "Puesto que ocupa:",
        "escala": "",
    },
    {
        "id": "pg_residencia",
        "nombre": "Residencia",
        "tipo": "agrupacion",
        "pregunta": "Residencia actual:",
        "escala": "",
    },
    {
        "id": "pg_rubro",
        "nombre": "Rubro",
        "tipo": "agrupacion",
        "pregunta": "Rubro:",
        "escala": "",
    },
    {
        "id": "pg_sector",
        "nombre": "Sector",
        "tipo": "agrupacion",
        "pregunta": "Sector:",
        "escala": "",
    },
    {
        "id": "pg_sexo",
        "nombre": "Sexo",
        "tipo": "agrupacion",
        "pregunta": "Sexo:",
        "escala": "",
    },
    {
        "id": "pg_situacion_laboral",
        "nombre": "Situación laboral",
        "tipo": "agrupacion",
        "pregunta": "Situación laboral actual:",
        "escala": "",
    },
    {
        "id": "pg_competencias",
        "nombre": "Competencias del programa",
        "tipo": "medida",
        "pregunta": "El programa comunica claramente las competencias que se espera que desarrolle.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_liderazgo",
        "nombre": "Desarrollo de liderazgo",
        "tipo": "medida",
        "pregunta": "El programa contribuye al desarrollo de mis habilidades de liderazgo.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_perfil_profesional",
        "nombre": "Fortalecimiento del perfil profesional",
        "tipo": "medida",
        "pregunta": "El programa contribuye al fortalecimiento de mi perfil profesional.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_red_contactos",
        "nombre": "Red de contactos profesionales",
        "tipo": "medida",
        "pregunta": "El programa me ofrece oportunidades para ampliar mi red de contactos profesionales.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_internacionalizacion",
        "nombre": "Oportunidades de internacionalización",
        "tipo": "medida",
        "pregunta": "El programa ofrece oportunidades de internacionalización pertinentes para mi formación.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_secuencia_plan",
        "nombre": "Secuencia del plan de estudios",
        "tipo": "medida",
        "pregunta": "Las asignaturas siguen una secuencia coherente dentro del plan de estudios.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_duracion_asignaturas",
        "nombre": "Duración de las asignaturas",
        "tipo": "medida",
        "pregunta": "La duración de las asignaturas permite desarrollar adecuadamente sus contenidos.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_contenidos_actualizados",
        "nombre": "Contenidos actualizados",
        "tipo": "medida",
        "pregunta": "Los contenidos desarrollados en las asignaturas se encuentran actualizados.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_dominio_docente",
        "nombre": "Dominio de los contenidos por los profesores",
        "tipo": "medida",
        "pregunta": "Los profesores demuestran dominio de los contenidos que enseñan.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_carga_academica",
        "nombre": "Carga de trabajo académico",
        "tipo": "medida",
        "pregunta": "La carga de trabajo académico es adecuada para un programa de posgrado.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_metodologias",
        "nombre": "Metodologías de enseñanza",
        "tipo": "medida",
        "pregunta": "Las metodologías de enseñanza empleadas facilitan mi aprendizaje.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_retroalimentacion",
        "nombre": "Retroalimentación recibida",
        "tipo": "medida",
        "pregunta": "La retroalimentación recibida me ayuda a mejorar mi desempeño académico.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_plazos_academicos",
        "nombre": "Atención de solicitudes académicas",
        "tipo": "medida",
        "pregunta": "Mis solicitudes académicas son atendidas dentro de plazos razonables.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_atencion_administrativa",
        "nombre": "Atención del personal administrativo",
        "tipo": "medida",
        "pregunta": "Las respuestas del personal administrativo son útiles para resolver mis consultas.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_informacion_pagos",
        "nombre": "Información sobre pagos",
        "tipo": "medida",
        "pregunta": "La información sobre pagos y obligaciones económicas se comunica con claridad.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_comunicaciones",
        "nombre": "Comunicaciones de la Escuela",
        "tipo": "medida",
        "pregunta": "Recibo oportunamente las comunicaciones relevantes para el desarrollo de mis estudios.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_recursos_bibliograficos",
        "nombre": "Recursos bibliográficos",
        "tipo": "medida",
        "pregunta": "Los recursos bibliográficos disponibles responden a mis necesidades académicas.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_aulas",
        "nombre": "Aulas de clase",
        "tipo": "medida",
        "pregunta": "Las aulas presentan condiciones físicas apropiadas para el desarrollo de las clases.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_equipamiento_aulas",
        "nombre": "Equipamiento de las aulas",
        "tipo": "medida",
        "pregunta": "El equipamiento de las aulas funciona adecuadamente durante las clases.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_conexion_internet",
        "nombre": "Conexión a internet",
        "tipo": "medida",
        "pregunta": "La conexión a internet del campus permite desarrollar mis actividades académicas.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_aula_virtual",
        "nombre": "Aula virtual",
        "tipo": "medida",
        "pregunta": "El aula virtual facilita el acceso a los recursos académicos de mis asignaturas.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_espacios_limpios",
        "nombre": "Limpieza de los espacios",
        "tipo": "medida",
        "pregunta": "Los espacios del campus que utilizo se mantienen limpios.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_csat_programa",
        "nombre": "Satisfacción con la calidad académica",
        "tipo": "medida",
        "pregunta": "En general, estoy satisfecho(a) con la calidad académica del programa.",
        "escala": "acuerdo",
    },
    {
        "id": "pg_lealtad_programa",
        "nombre": "Volvería a estudiar el programa",
        "tipo": "medida",
        "pregunta": "Si tuviera que elegir nuevamente, volvería a estudiar este programa en la Universidad de Lima.",
        "escala": "acuerdo",
    },
]

PREGUNTAS_DOCENTE_PG: List[Dict[str, str]] = [
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
        "pregunta": "Hora inicial de resuestas",
        "escala": "",
    },
    {
        "id": "fin",
        "nombre": "Fecha de fin",
        "tipo": "fecha",
        "pregunta": "Hora final de resuestas",
        "escala": "",
    },
    {
        "id": "nps",
        "nombre": "Recomendación (0 al 10)",
        "tipo": "medida",
        "pregunta": "En una escala del 0 al 10, donde 0 significa ‘Definitivamente no la recomendaría’ y 10 ‘Definitivamente sí la recomendaría’¿Qué tan probable es que recomiendes la Escuela de Posgrado de la Universidad de Lima a un familiar o amigo como institución para trabajar?",
        "escala": "NPS",
    },
    {
        "id": "dpg_modalidad",
        "nombre": "Modalidad de dictado",
        "tipo": "agrupacion",
        "pregunta": "Modalidad de dictado",
        "escala": "",
    },
    {
        "id": "dpg_antiguedad",
        "nombre": "Años en la Universidad",
        "tipo": "agrupacion",
        "pregunta": "Número de años que labora en la Universidad de Lima:",
        "escala": "",
    },
    {
        "id": "carrera",
        "nombre": "Programa",
        "tipo": "agrupacion",
        "pregunta": "Programa:",
        "escala": "",
    },
    {
        "id": "dpg_perfil_egreso",
        "nombre": "Claridad del perfil de egreso",
        "tipo": "medida",
        "pregunta": "Claridad del perfil de egreso del programa de posgrado en el que dicta.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_coherencia_plan",
        "nombre": "Coherencia perfil-plan curricular",
        "tipo": "medida",
        "pregunta": "Coherencia entre el perfil de egreso y el plan curricular del programa.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_contribucion_asignatura",
        "nombre": "Contribución de la asignatura al perfil",
        "tipo": "medida",
        "pregunta": "Contribución de su asignatura al logro del perfil de egreso.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_ubicacion_asignatura",
        "nombre": "Ubicación de la asignatura en el plan",
        "tipo": "medida",
        "pregunta": "Ubicación de su asignatura dentro del plan curricular.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_sistema_evaluacion",
        "nombre": "Sistema de evaluación del aprendizaje",
        "tipo": "medida",
        "pregunta": "Adecuación del sistema de evaluación del aprendizaje establecido para su asignatura.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_lineamientos",
        "nombre": "Claridad de los lineamientos",
        "tipo": "medida",
        "pregunta": "Claridad de los lineamientos académicos y administrativos aplicables a su labor docente.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_informacion_asignatura",
        "nombre": "Información para la asignatura",
        "tipo": "medida",
        "pregunta": "Información recibida para planificar y desarrollar su asignatura.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_soporte_academico",
        "nombre": "Soporte académico recibido",
        "tipo": "medida",
        "pregunta": "Soporte académico recibido durante el desarrollo de su asignatura.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_horas_asignadas",
        "nombre": "Horas asignadas",
        "tipo": "medida",
        "pregunta": "Número de horas asignadas para desarrollar los contenidos de su asignatura.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_gestion_academica",
        "nombre": "Gestión académica de las autoridades",
        "tipo": "medida",
        "pregunta": "Gestión académica realizada por las autoridades del programa.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_material_bibliografico",
        "nombre": "Material bibliográfico",
        "tipo": "medida",
        "pregunta": "Disponibilidad de material bibliográfico relacionado con su asignatura.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_bases_datos",
        "nombre": "Acceso a bases de datos",
        "tipo": "medida",
        "pregunta": "Acceso a bases de datos, libros electrónicos y revistas académicas.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_software",
        "nombre": "Software especializado",
        "tipo": "medida",
        "pregunta": "Disponibilidad del software especializado requerido para la enseñanza.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_aula_virtual",
        "nombre": "Aula virtual",
        "tipo": "medida",
        "pregunta": "Funcionamiento del aula virtual utilizada para desarrollar su asignatura.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_equipamiento_aulas",
        "nombre": "Equipamiento tecnológico de las aulas",
        "tipo": "medida",
        "pregunta": "Funcionamiento del equipamiento tecnológico disponible en las aulas.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_internet",
        "nombre": "Acceso a internet",
        "tipo": "medida",
        "pregunta": "Calidad del acceso a internet en el campus.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_soporte_tecnico",
        "nombre": "Soporte técnico",
        "tipo": "medida",
        "pregunta": "Capacidad del soporte técnico para resolver los problemas reportados.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_condiciones_aulas",
        "nombre": "Condiciones físicas de las aulas",
        "tipo": "medida",
        "pregunta": "Condiciones físicas de las aulas utilizadas para el dictado de clases.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_espacios_academicos",
        "nombre": "Espacios para actividades académicas",
        "tipo": "medida",
        "pregunta": "Disponibilidad de espacios para desarrollar actividades académicas fuera del aula.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_comunicacion_direccion",
        "nombre": "Claridad de la comunicación",
        "tipo": "medida",
        "pregunta": "Claridad de la comunicación recibida de la dirección o coordinación del programa.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_accesibilidad_direccion",
        "nombre": "Accesibilidad de la dirección",
        "tipo": "medida",
        "pregunta": "Accesibilidad de la dirección o coordinación para atender sus consultas.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_respuesta_problemas",
        "nombre": "Respuesta ante problemas",
        "tipo": "medida",
        "pregunta": "Capacidad de respuesta ante los problemas comunicados.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_atencion_secretaria",
        "nombre": "Atención de la secretaría académica",
        "tipo": "medida",
        "pregunta": "Atención brindada por la secretaría académica del programa.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_clima_colaboracion",
        "nombre": "Clima de colaboración",
        "tipo": "medida",
        "pregunta": "Clima de colaboración entre los docentes del programa.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_reuniones_coordinacion",
        "nombre": "Reuniones de coordinación",
        "tipo": "medida",
        "pregunta": "Utilidad de las reuniones de coordinación académica.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_retroalimentacion_docente",
        "nombre": "Retroalimentación de la evaluación docente",
        "tipo": "medida",
        "pregunta": "Utilidad de la retroalimentación recibida sobre los resultados de su evaluación docente.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_capacitacion",
        "nombre": "Actividades de capacitación",
        "tipo": "medida",
        "pregunta": "Pertinencia de las actividades de capacitación docente ofrecidas.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_actividades_academicas",
        "nombre": "Actividades académicas nacionales e internacionales",
        "tipo": "medida",
        "pregunta": "Oportunidades ofrecidas para participar en actividades académicas nacionales e internacionales.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_apoyo_investigacion",
        "nombre": "Apoyo a la investigación",
        "tipo": "medida",
        "pregunta": "Apoyo institucional recibido para desarrollar actividades de investigación.",
        "escala": "satisfaccion",
    },
    {
        "id": "dpg_satisfaccion_general",
        "nombre": "Experiencia general como docente",
        "tipo": "medida",
        "pregunta": "Experiencia general como docente de la Escuela de Posgrado.",
        "escala": "satisfaccion",
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

# Un programa de posgrado NO es una carrera de pregrado: no se traduce con
# CARRERA_FACULTAD (no hay correspondencia). Por eso estas dos encuestas
# publican 'Facultad' como derivada y el ETL las deja en 'Otra' (ver
# _NIVEL_FAC_MAP). El 'Ciclo' tambien se deriva (la encuesta no lo pregunta).
DERIVADAS_POSTGRADO: List[Dict[str, str]] = [
    {
        "id": "ciclo",
        "nombre": "Ciclo",
        "tipo": "agrupacion",
        "pregunta": "Ciclo (derivado; la encuesta de posgrado no lo pregunta)",
        "escala": "",
    },
    {
        "id": "facultad",
        "nombre": "Facultad",
        "tipo": "agrupacion",
        "pregunta": "Facultad (derivada; un programa de posgrado no es una carrera de pregrado)",
        "escala": "",
    },
]

DERIVADAS_DOCENTE_PG: List[Dict[str, str]] = [
    {
        "id": "ciclo",
        "nombre": "Ciclo",
        "tipo": "agrupacion",
        "pregunta": "Ciclo (derivado; la encuesta de posgrado no lo pregunta)",
        "escala": "",
    },
    {
        "id": "facultad",
        "nombre": "Facultad",
        "tipo": "agrupacion",
        "pregunta": "Facultad (derivada; un programa de posgrado no es una carrera de pregrado)",
        "escala": "",
    },
]

# Declaracion completa por nivel interno: preguntas del formulario + derivadas.
PREGUNTAS_POR_NIVEL: Dict[str, List[Dict[str, str]]] = {
    "undergraduate": PREGUNTAS_PREGRADO + DERIVADAS_PREGRADO,
    "graduate": PREGUNTAS_GRADUADO + DERIVADAS_GRADUADO,
    "postgraduate": PREGUNTAS_POSTGRADO + DERIVADAS_POSTGRADO,
    "faculty-pg": PREGUNTAS_DOCENTE_PG + DERIVADAS_DOCENTE_PG,
}

# Solo las preguntas del formulario de cada nivel (sin las derivadas): de aqui
# sale la lista de cabeceras de ingesta de zoho_a_csv, para que deje de ser una
# segunda copia escrita a mano. Si el ETL usara PREGUNTAS_POR_NIVEL completas
# agregaria al CSV columnas derivadas que Zoho no manda.
PREGUNTAS_FORMULARIO: Dict[str, List[Dict[str, str]]] = {
    "undergraduate": PREGUNTAS_PREGRADO,
    "graduate": PREGUNTAS_GRADUADO,
    "postgraduate": PREGUNTAS_POSTGRADO,
    "faculty-pg": PREGUNTAS_DOCENTE_PG,
}

# Texto de la pregunta abierta: el ETL la renombra, pero no se publica.
COMENTARIO_NPS_PREGUNTA: str = "Explica con tus palabras, las razones de la calificaci\u00f3n que diste en la pregunta anterior. (m\u00e1x. 100 caracteres)"

# El texto de la pregunta abierta cambia por encuesta: el estudiantil de posgrado
# no tiene ninguna (queda vacio a proposito) y el docente de posgrado usa su propio
# texto. Los demas niveles heredan COMENTARIO_NPS_PREGUNTA. Es el unico dato del
# comentario: resolverlo aqui evita rastrearlo por el prefijo 'Explica con tus
# palabras', que solo era cierto para pregrado.
COMENTARIO_POR_NIVEL: Dict[str, str] = {
    "postgraduate": "",
    "faculty-pg": "Desde su experiencia, \u00bfqu\u00e9 aspecto deber\u00eda mejorarse prioritariamente en la Escuela de Posgrado? Si lo desea, incluya comentarios o sugerencias adicionales.",
}


def comentario_de(nivel: str) -> str:
    """Texto de la pregunta abierta de ese nivel (vacio si la encuesta no tiene)."""
    return COMENTARIO_POR_NIVEL.get(nivel, COMENTARIO_NPS_PREGUNTA)


def cabeceras_declaradas(nivel: str) -> List[str]:
    """Cabeceras de ingesta de un nivel declarado: el texto de cada pregunta, en el
    orden del formulario, mas el de su pregunta abierta si la tiene.

    Es la unica fuente de la lista que consume zoho_a_csv: agregar un publico nuevo
    ya no obliga a mantener su lista de cabeceras aparte. Vacia si el nivel aun no
    declara sus preguntas (esos niveles conservan su lista literal en zoho_a_csv).
    """
    textos = [d["pregunta"] for d in PREGUNTAS_FORMULARIO.get(nivel, [])]
    if not textos:
        # Nivel aun sin declaracion: no inventa cabeceras (zoho_a_csv usa su lista).
        return []
    comentario = comentario_de(nivel)
    if comentario and comentario not in textos:
        textos.append(comentario)
    return textos


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


# Ids de las medidas de cierre: se miden pero no son dimensiones del cuestionario;
# el detector de dimensiones las ignora. No todos los publicos tienen el par
# csat_sujeto/csat_universidad: posgrado cierra con su propia satisfaccion y con
# lealtad (estudiantil) o experiencia general (docente). Se listan aqui para que
# esas medidas tampoco se confundan con dimensiones.
IDS_MEDIDAS_DE_CIERRE: List[str] = [
    "nps", "csat_sujeto", "csat_universidad",
    "pg_csat_programa", "pg_lealtad_programa", "dpg_satisfaccion_general",
]


def columnas_que_no_son_preguntas() -> Set[str]:
    """Nombres y textos de las columnas publicadas que no son preguntas del formulario.

    Son las de tipo 'fecha' o 'identificador' y las medidas de cierre, mas el
    comentario abierto (que no se declara como pregunta porque no se publica en
    respuestas.json). Sale de la declaracion: renombrar una pregunta no deja este
    conjunto desactualizado.
    """
    fuera: Set[str] = {"Comentario NPS"}
    for declaraciones in PREGUNTAS_POR_NIVEL.values():
        for d in declaraciones:
            if d["tipo"] in ("fecha", "identificador") or d["id"] in IDS_MEDIDAS_DE_CIERRE:
                fuera.add(d["nombre"])
                fuera.add(d["pregunta"])
    return fuera


def _mapa_renombrado(declaraciones: List[Dict[str, str]], comentario: str = COMENTARIO_NPS_PREGUNTA) -> Dict[str, str]:
    """Deriva el mapa {pregunta de Zoho: nombre publicado} de una declaracion."""
    mapa = {d["pregunta"]: d["nombre"] for d in declaraciones}
    if comentario:
        mapa[comentario] = "Comentario NPS"
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

# ---- Catálogo dimensión → categoría, llaveado por el id declarado ----
# Cada entrada es (id de la pregunta, categoría padre). Las dimensiones que no son
# preguntas del formulario (catch-all que el motor IA infiere del comentario) van
# por su nombre publicado. El mapa {nombre publicado: categoría} se deriva de aquí,
# así renombrar una pregunta en la declaración no obliga a tocar este catálogo.
_DIMENSIONES_CATCH_ALL: Set[str] = {
    "Satisfacción estudiantil",
    "Ubicación",
    "Espacios de alimentación",
    "Espacios comunes",
}


def _categoria_dimension(entradas: List[tuple]) -> Dict[str, str]:
    """Deriva {nombre publicado: categoría} de una lista de (id o nombre, categoría).

    Los ids se resuelven contra la declaración vigente (nombre_publicado); las
    entradas que ya son un nombre publicado son dimensiones catch-all sin pregunta
    y se dejan tal cual. Falla si un id no está declarado: un nombre de dimensión
    nunca debe quedar escrito a mano.
    """
    mapa: Dict[str, str] = {}
    for clave, categoria in entradas:
        mapa[clave if clave in _DIMENSIONES_CATCH_ALL else nombre_publicado(clave)] = categoria
    return mapa


DIMENSIONES_PREGRADO: List[tuple] = [
    # Académico
    ("perfil_del_egreso_de_la_carrera", "Académico"),
    ("plan_curricular_y_perfil_de_egreso", "Académico"),
    ("cursos_del_programa_y_contenidos", "Académico"),
    ("calidad_de_la_ensenanza_en_la_carrera", "Académico"),
    ("claridad_de_los_recursos_academicos", "Académico"),
    ("calidad_de_la_formacion_academica", "Académico"),
    ("exigencia_academica", "Académico"),
    ("evaluacion_del_aprendizaje", "Académico"),
    ("intercambio_estudiantil", "Académico"),
    ("csat_sujeto", "Académico"),
    ("Satisfacción estudiantil", "Académico"),

    # Administrativo y Bienestar
    ("informacion_sobre_el_record_academico", "Administrativo y Bienestar"),
    ("material_bibliografico_en_la_biblioteca", "Administrativo y Bienestar"),
    ("atencion_del_personal_administrativo", "Administrativo y Bienestar"),
    ("procedimientos_administrativos", "Administrativo y Bienestar"),
    ("ayuda_financiera", "Administrativo y Bienestar"),
    ("servicio_medico_y_su_infraestructura", "Administrativo y Bienestar"),
    ("servicio_de_atencion_psicopedagogica", "Administrativo y Bienestar"),
    ("talleres_de_actividades_artisticas_y_culturales", "Administrativo y Bienestar"),
    ("actividades_deportivas", "Administrativo y Bienestar"),
    ("empleabilidad_vinculacion_y_alumni", "Administrativo y Bienestar"),

    # Infraestructura
    ("aulas_de_clase", "Infraestructura"),
    ("ambientes_y_salas_para_estudio", "Infraestructura"),
    ("equipamiento_tecnologico_en_laboratorios", "Infraestructura"),
    ("condiciones_ambientales_en_laboratorios", "Infraestructura"),
    ("Ubicación", "Infraestructura"),
    ("Espacios de alimentación", "Infraestructura"),
    # Catch-all para referencias genéricas a espacios del campus (sin pregunta CSAT
    # directa en Zoho; se infiere del comentario).
    ("Espacios comunes", "Infraestructura"),

    # Tecnología
    ("software_especializado_empleado_en_la_carrera", "Tecnología"),
    ("portal_web_de_la_universidad_mi_ulima", "Tecnología"),
    ("aula_virtual", "Tecnología"),
    ("conexion_wi_fi_en_el_campus", "Tecnología"),
    ("soporte_tecnico_del_sistema_informatico", "Tecnología"),
]

CATEGORIA_DIMENSION_PREGRADO: Dict[str, str] = _categoria_dimension(DIMENSIONES_PREGRADO)

DIMENSIONES_GRADUADO: List[tuple] = [
    # Docencia
    ("transmision_de_conocimientos", "Docencia"),
    ("transmision_de_experiencias", "Docencia"),
    ("metodologias", "Docencia"),
    ("conocimientos_actualizados", "Docencia"),
    ("compromiso", "Docencia"),
    ("retroalimentacion", "Docencia"),
    ("disponibilidad_para_asesorias", "Docencia"),
    ("cumplimiento_de_normas_y_programas", "Docencia"),

    # Desarrollo Profesional
    ("habilidades_para_trabajar_en_equipo", "Desarrollo Profesional"),
    ("habilidades_de_comunicacion", "Desarrollo Profesional"),
    ("habilidades_para_aportar_nuevas_ideas", "Desarrollo Profesional"),
    ("mejora_en_perspectivas_de_empleo", "Desarrollo Profesional"),

    # Académico
    ("perfil_del_egreso_de_la_carrera", "Académico"),
    ("plan_curricular_y_perfil_de_egreso", "Académico"),
    ("cursos_del_programa_y_contenidos", "Académico"),
    ("calidad_de_la_ensenanza_en_la_carrera", "Académico"),
    ("claridad_de_los_recursos_academicos", "Académico"),
    ("calidad_de_la_formacion_academica", "Académico"),
    ("exigencia_academica", "Académico"),
    ("evaluacion_del_aprendizaje", "Académico"),
    ("intercambio_estudiantil", "Académico"),
    ("csat_sujeto", "Académico"),
    ("Satisfacción estudiantil", "Académico"),

    # Administrativo y Bienestar
    ("informacion_sobre_el_record_academico", "Administrativo y Bienestar"),
    ("material_bibliografico_en_la_biblioteca", "Administrativo y Bienestar"),
    ("atencion_del_personal_administrativo", "Administrativo y Bienestar"),
    ("procedimientos_administrativos", "Administrativo y Bienestar"),
    ("ayuda_financiera", "Administrativo y Bienestar"),
    ("servicio_medico_y_su_infraestructura", "Administrativo y Bienestar"),
    ("servicio_de_atencion_psicopedagogica", "Administrativo y Bienestar"),
    ("talleres_de_actividades_artisticas_y_culturales", "Administrativo y Bienestar"),
    ("actividades_deportivas", "Administrativo y Bienestar"),
    ("empleabilidad_vinculacion_y_alumni", "Administrativo y Bienestar"),

    # Infraestructura
    ("aulas_de_clase", "Infraestructura"),
    ("ambientes_y_salas_para_estudio", "Infraestructura"),
    ("equipamiento_tecnologico_en_laboratorios", "Infraestructura"),
    ("condiciones_ambientales_en_laboratorios", "Infraestructura"),
    ("Ubicación", "Infraestructura"),
    ("Espacios de alimentación", "Infraestructura"),
    ("Espacios comunes", "Infraestructura"),

    # Tecnología
    ("software_especializado_empleado_en_la_carrera", "Tecnología"),
    ("portal_web_de_la_universidad_mi_ulima", "Tecnología"),
    ("aula_virtual", "Tecnología"),
    ("conexion_wi_fi_en_el_campus", "Tecnología"),
    ("soporte_tecnico_del_sistema_informatico", "Tecnología"),
]

CATEGORIA_DIMENSION_GRADUADO: Dict[str, str] = _categoria_dimension(DIMENSIONES_GRADUADO)


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
def _dimensiones_sin_csat() -> Set[str]:
    """Dimensiones del catálogo que no tienen una columna CSAT propia.

    El cross-reference ``dimension_evaluada_rating`` devuelve null para ellas. Las
    dos medidas de cierre salen de la declaración (renombrarlas no obliga a tocar
    el conjunto); las demás son catch-all sin pregunta.
    """
    return {
        "Satisfacción estudiantil",
        "Espacios comunes",
        nombre_publicado("csat_sujeto"),
        nombre_publicado("csat_universidad"),
        "Pendiente de Clasificación",
    }


DIMENSIONES_SIN_CSAT: Set[str] = _dimensiones_sin_csat()

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
    "postgraduate": ["Programa:"],
    "graduate": ["\u00bfQu\u00e9 carrera profesional estudiaste?"],
    "alumni-ug": ["\u00bfQu\u00e9 carrera profesional estudiaste?"],
    "alumni-pg": ["\u00bfQu\u00e9 programa de posgrado estudiaste?"],
    "faculty-ug": ["\u00bfQu\u00e9 carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?"],
    "faculty-pg": ["Programa:"],
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

    # La tabla {pregunta de Zoho -> nombre publicado} sale de la declaracion del
    # nivel: TODAS las preguntas del formulario se renombran a su nombre publicado
    # (corto). Antes solo se renombraban las columnas clave, asi que una encuesta
    # distinta a pregrado/graduados publicaba el texto largo del cuestionario como
    # nombre de columna y no habia como resolverla por id.
    rename: Dict[str, str] = {
        d["pregunta"]: d["nombre"] for d in declaraciones_de(nivel)
    }
    # La pregunta abierta se reconoce por su texto real (el del nivel), no por el
    # prefijo 'Explica con tus palabras', que solo era cierto para pregrado.
    comentario = comentario_de(nivel)
    if comentario and comentario in colset:
        rename[comentario] = "Comentario NPS"
    else:
        for c in cols:
            if c.startswith("Explica con tus palabras"):
                rename[c] = "Comentario NPS"
                break
    # Columnas clave de los niveles que aun no declaran sus preguntas (egresados,
    # docente pregrado, no docente y empleadores): se resuelven por id declarado.
    for id_col in ("id_respuesta", "nps"):
        declaracion = _declaracion_por_id(id_col)
        if declaracion["pregunta"] in colset:
            rename[declaracion["pregunta"]] = declaracion["nombre"]
    if carrera:
        # La columna de agrupacion toma el nombre del propio nivel: 'Programa' en
        # posgrado, 'Carrera' en pregrado; nunca un literal escrito aqui.
        rename[carrera] = columna(nivel, "carrera")
    if csat:
        # El nombre publicado del CSAT global sale de la declaracion (id
        # csat_universidad): renombrarlo no debe exigir escribirlo a mano aqui.
        rename[csat] = columna(nivel, "csat_universidad")
    # Las fechas tambien viajan como columnas internas declaradas (ids inicio/fin):
    # se renombran desde el texto del formulario igual que el ID, el NPS o el CSAT.
    # Sin esto, build_json pide la fecha por su nombre publicado y no la encuentra.
    for id_fecha in ("inicio", "fin"):
        declaracion_fecha = _declaracion_por_id(id_fecha)
        if declaracion_fecha["pregunta"] in colset:
            rename[declaracion_fecha["pregunta"]] = declaracion_fecha["nombre"]

    requeridas = [pregunta_de(nivel, "id_respuesta"), pregunta_de(nivel, "nps")]
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
