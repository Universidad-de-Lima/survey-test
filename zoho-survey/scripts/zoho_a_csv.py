"""
ZOHO A CSV — Convierte la bandeja de respuestas en el CSV que consume el ETL.

Uso:
    python3 zoho-survey/scripts/zoho_a_csv.py [carpeta-de-destino]

Lo invoca el flujo .github/workflows/build_zoho_survey.yml cuando el portal pide
procesar los datos (repository_dispatch). Lee data/zoho_pendientes/*.jsonl (una
linea por respuesta, ya enmascarada), arma un CSV por encuesta con las cabeceras
que espera build_json.py y lo deja en data/, donde el gate "Detectar CSVs a
procesar" lo recoge.

Reglas:

  - Las claves de la bandeja ya vienen con los nombres de cabecera del CSV: el
    webhook envia cada pregunta con el texto que el ETL espera. El identificador
    viaja aparte (id_respuesta) y aqui se repone en 'ID de respuesta'.
  - El nombre del archivo se deriva del titulo de la encuesta, porque el ETL saca
    de ahi el nivel y el periodo (CONTRACTS.md, "Reglas de nombres CSV").
  - Se escribe SIN BOM por limpieza: el ETL ya limpia el BOM de la primera columna la
    primera columna.
  - NO borra la bandeja: es el acumulado del periodo. Borrarla dejaria el
    dashboard sin las respuestas anteriores (ver docs/INGESTA_Y_DESCARGA.md).
  - Si no hay bandejas, no escribe nada: el flujo se queda sin CSV y solo despliega.

Este modulo usa solo la biblioteca estandar (mas las constantes de lib.config),
a proposito: corre antes de instalar dependencias, en el mismo punto que el gate
de CSVs.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.config import COLUMN_RENAME_GRADUADO, COLUMN_RENAME_PREGRADO  # noqa: E402

CARPETA_PENDIENTES = Path("data") / "zoho_pendientes"
CARPETA_DESTINO = Path("data")
CLAVE_ID = "ID de respuesta"
CLAVE_ESTADO = "Estado"

# Solo pasan al CSV las respuestas completas. Las parciales (Estado = PARTIAL)
# quedan en la bandeja, pero no entran al proceso: no aportan a NPS ni CSAT y
# descuadrarian los conteos. Una respuesta SIN el campo Estado se deja pasar:
# no se puede saber su estado y no conviene descartar datos en silencio.
ESTADO_COMPLETO = "COMPLETED"

# Cabeceras por nivel, en el orden que espera build_json.py. Cubre las nueve
# encuestas del catalogo; si un nivel no esta aqui, la conversion falla con
# aviso explicito en vez de generar un CSV a medias.
CABECERAS_POR_NIVEL: Dict[str, List[str]] = {
    # Las dos encuestas que ya estaban: las columnas que el ETL conoce.
    "undergraduate": list(COLUMN_RENAME_PREGRADO),
    "graduate": list(COLUMN_RENAME_GRADUADO),
    # Encuestas 2026: cabeceras tomadas de la descarga de Zoho Survey.
    # Son una base; si Zoho agrega o quita preguntas, se actualiza aqui.
    # Se excluyen las columnas propias de Zoho (IP, agente, tiempo, etc.).
    # Estudiantil Posgrado
    "postgraduate": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿Qué programa de posgrado estudias?",
        "¿Qué nivel es el que cursas?",
        "El perfil de egreso del programa",
        "La correspondencia entre el perfil de egreso y el plan curricular del programa",
        "Los cursos y contenidos del programa",
        "La calidad del servicio de enseñanza del programa",
        "La claridad, precisión y actualización de los materiales de estudio del programa",
        "La evaluación del aprendizaje del programa",
        "La información sobre tu récord académico",
        "El material bibliográfico físico o digital disponible en la biblioteca",
        "El servicio recibido por los directores o coordinadores de la Escuela de Posgrado",
        "El servicio recibido por las secretarias de la Escuela de Posgrado",
        "Los procedimientos de los servicios administrativos de la Escuela de Posgrado",
        "El servicio médico y su infraestructura",
        "El servicio de consejería",
        "Los talleres de actividades artísticas y culturales",
        "Las actividades deportivas",
        "Las aulas de clase",
        "Los ambientes y salas para estudio",
        "El portal web de la universidad: Mi Ulima",
        "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "El soporte técnico brindado ante las fallas del sistema informático",
        "Empleabilidad, vinculación profesional y ALUMNI",
        "La calidad de la formación académica",
        "La Escuela de Posgrado",
        "La Universidad de Lima",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
    ],
    # Egresados Pregrado
    "alumni-ug": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿Qué carrera profesional estudiaste?",
        "¿Qué año egresaste de tu carrera profesional?",
        "El perfil de egreso tu carrera",
        "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera",
        "Los cursos y contenidos de tu carrera",
        "La calidad del servicio de enseñanza de tu carrera",
        "La claridad, precisión y actualización de los materiales de estudio de tu carrera",
        "La exigencia académica de las asignaturas de tu carrera",
        "La evaluación del aprendizaje de tu carrera",
        "El proceso de intercambio estudiantil",
        "El dominio de los conocimientos que transmiten",
        "Las metodologías y herramientas aplicadas para la enseñanza y aprendizaje",
        "La capacidad para transmitir el conocimiento y experiencias que complementan la teoría",
        "La retroalimentación de las tareas, trabajos y desempeño",
        "La actualización de los conocimientos transmitidos",
        "El compromiso con el aprendizaje de los alumnos",
        "La disciplina en el cumplimiento de las normas y programas",
        "La disposición y tiempo para asesorar a los alumnos",
        "El desarrollo de tus habilidades de trabajo en equipo",
        "La capacidad para aportar y explorar nuevas ideas",
        "El desarrollo de tus habilidades de comunicación",
        "La mejora de tu perspectiva de empleo",
        "La información sobre tu récord académico",
        "El material bibliográfico físico o digital disponible en la biblioteca",
        "El servicio recibido por el personal administrativo de tu carrera",
        "Los procedimientos de los servicios administrativos de tu carrera",
        "El servicio social: ayuda financiera",
        "El servicio médico y su infraestructura",
        "El servicio de atención psicopedagógica",
        "Los talleres de actividades artísticas y culturales",
        "Las actividades deportivas",
        "Las aulas de clase",
        "Los ambientes y salas para estudio",
        "Los laboratorios en lo referido a equipamiento, tecnología y programas",
        "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad",
        "El software especializado empleado en tu carrera",
        "El portal web de la universidad: Mi Ulima",
        "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "El soporte técnico brindado ante las fallas del sistema informático",
        "Empleabilidad, vinculación profesional y ALUMNI",
        "La calidad de la formación académica",
        "Tu carrera",
        "La Universidad de Lima",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
    ],
    # Egresados Posgrado
    "alumni-pg": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿Qué programa de posgrado estudiaste?",
        "¿Qué año egresaste de tu programa de posgrado?",
        "El perfil de egreso del programa",
        "La correspondencia entre el perfil de egreso y el plan curricular del programa",
        "Los cursos y contenidos del programa",
        "La calidad del servicio de enseñanza en el programa",
        "La claridad, precisión y actualización de los materiales de estudio del programa",
        "La exigencia académica de las asignaturas del programa",
        "La evaluación del aprendizaje del programa",
        "El desarrollo del conocimiento de las asignaturas del programa",
        "La secuencia y requisitos de los cursos del programa",
        "La oportunidad de aportar ideas y sugerencias durante el desarrollo de las asignaturas del programa",
        "Su experiencia profesional",
        "El dominio de los conocimientos que transmiten",
        "Las metodologías y herramientas aplicadas para la enseñanza y aprendizaje",
        "La capacidad para transmitir el conocimiento y experiencias que complementan la teoría",
        "La retroalimentación de las tareas, trabajos y desempeño",
        "La actualización de los conocimientos transmitidos",
        "La disposición y tiempo para asesorar a los alumnos",
        "La calidad del material utilizado",
        "El cumplimiento de los plazos acordados",
        "El desarrollo de tus habilidades de trabajo en equipo",
        "El desarrollo de tus habilidades de liderazgo",
        "El explorar o adaptarse a distintos escenarios profesionales",
        "La mejora en tu perspectiva de empleo",
        "La información sobre tu récord académico",
        "El material bibliográfico físico o digital disponible en la biblioteca",
        "El servicio recibido por los directores o coordinadores de la Escuela de Posgrado",
        "El servicio recibido por las secretarias de la Escuela de Posgrado",
        "Los procedimientos de los servicios administrativos de la Escuela de Posgrado",
        "El servicio médico y su infraestructura",
        "El servicio de consejería",
        "Los talleres de actividades artísticas y culturales",
        "Las actividades deportivas",
        "Las aulas de clase",
        "Los ambientes y salas para estudio",
        "El portal web de la universidad: Mi Ulima",
        "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "El soporte técnico brindado ante las fallas del sistema informático",
        "Empleabilidad, vinculación profesional y ALUMNI",
        "La calidad de la formación académica",
        "La Escuela de Posgrado",
        "La Universidad de Lima",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
    ],
    # Docente Pregrado
    "faculty-ug": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿Qué carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?",
        "¿Cuántos años laboras en la Universidad de Lima?",
        "El perfil de egreso de tu carrera",
        "La correspondencia entre el perfil de egreso y el plan curricular de tu carrera",
        "Los cursos y contenidos de tu carrera",
        "La cantidad de horas asignadas para el desarrollo de las asignaturas",
        "La carga de trabajo para el desarrollo de las asignaturas",
        "La distribución de su carga lectiva y no lectiva",
        "La coordinación de las asignaturas a su cargo",
        "La administración del registro de notas de los alumnos",
        "El liderazgo y compromiso de las autoridades de tu facultad o programa",
        "El trato recibido por las autoridades de tu facultad o programa",
        "Los mecanismos de comunicación y coordinación entre las autoridades de la carrera y los docentes",
        "El clima laboral en tu facultad o programa",
        "El proceso de promoción y reconocimiento al docente",
        "Las actividades de internacionalización como congresos, intercambios e investigación",
        "Las actividades de responsabilidad social universitaria como voluntariado, foros e investigación",
        "La retroalimentación de los resultados de la evaluación referencial docente (ERD) por parte de las autoridades de tu facultad o programa",
        "La capacitación y perfeccionamiento para competencias generales",
        "La capacitación para el desarrollo de habilidades específicas en pedagogía",
        "Las políticas y procedimientos establecidos por el IDIC para apoyar la investigación docente",
        "Las políticas y procedimientos establecidos por la carrera para apoyar la investigación docente",
        "Los recursos proporcionados para el desarrollo de los proyectos de investigación docente",
        "Los mecanismos para promover la investigación entre los docentes",
        "Las facilidades para publicar las investigaciones en revistas indexadas",
        "La difusión de los resultados de las investigaciones como sílabos, repositorio institucional, revistas, libros, etc.",
        "El material bibliográfico físico o digital disponible en la biblioteca",
        "El servicio recibido por el personal administrativo",
        "El servicio médico y su infraestructura",
        "El servicio de atención psicopedagógica",
        "Los talleres de actividades artísticas y culturales",
        "Las actividades deportivas",
        "Las aulas de clase",
        "Los ambientes y salas para estudio",
        "Los laboratorios en lo referido a equipamiento, tecnología y programas",
        "Los laboratorios en lo referido a iluminación, ventilación, facilidad de ubicación y señalización de seguridad",
        "Las instalaciones para facilitar la relación social entre los docentes",
        "Las oficinas o cubículos de los docentes",
        "El software especializado empleado en la carrera",
        "El portal web de la universidad: Mi Ulima",
        "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "El soporte técnico brindado ante las fallas del sistema informático",
        "Tu facultad o programa",
        "La Universidad de Lima",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
    ],
    # Docente Posgrado
    "faculty-pg": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿Qué programa de posgrado dictas en la Universidad de Lima?",
        "¿Cuántos años laboras en la Universidad de Lima?",
        "El perfil de egreso del programa",
        "La correspondencia entre el perfil de egreso y el plan curricular del programa",
        "Los cursos y contenidos del programa",
        "La cantidad de horas asignadas para el desarrollo de las asignaturas",
        "La contribución de tu asignatura a alcanzar el perfil de egreso del programa",
        "La ubicación de tu asignatura en el plan curricular del programa",
        "Los criterios utilizados en la definición del sistema de evaluación como las tareas académicas y el examen final",
        "El conocimiento de las normativas de la Escuela de Posgrado como registro de notas, plazos, etc.",
        "El liderazgo y compromiso de las autoridades de la Escuela de Posgrado",
        "Interacción, presencial o virtual, con las autoridades de la Escuela de Posgrado",
        "La comunicación oportuna y clara por parte de las autoridades de la Escuela de Posgrado, en ciertos temas como lineamientos, políticas, reuniones, etc.",
        "La claridad, pertinencia y oportunidad en la comunicación por parte de las autoridades de la Escuela de Posgrado",
        "La interacción con el coordinador de la maestría o doctorado",
        "La oportunidad y eficacia en la solución de los problemas planteados a las autoridades de la Escuela de Posgrado",
        "El clima laboral en la Escuela de Posgrado",
        "La utilidad y pertinencia de los temas tratados en la reunión de docentes",
        "La utilidad y pertinencia de los temas tratados en las reuniones, individuales o grupales, de coordinación con las autoridades de la Escuela de Posgrado",
        "La frecuencia y antelación debida en la convocatoria a las reuniones, individuales o grupales, de coordinación las autoridades de la Escuela de Posgrado",
        "Las actividades de internacionalización como congresos, intercambios e investigación",
        "Las actividades de responsabilidad social universitaria como voluntariado, foros e investigación",
        "La retroalimentación de los resultados de la evaluación referencial docente (ERD) por parte de las autoridades de la Escuela de Posgrado",
        "El seguimiento al plan de mejora coordinado con las autoridades de la Escuela de Posgrado",
        "El programa de capacitación a los cuales ha sido invitado durante el año referido a la variedad de temas, pertinencia de horarios, pertinencia en la Invitación, etc.",
        "Las políticas y procedimientos establecidos por la Escuela de Posgrado para apoyar la investigación",
        "La comunicación de la política de beneficios y promoción de la investigación de la Escuela de Posgrado",
        "Los mecanismos para promover la investigación entre los docentes",
        "El material bibliográfico físico o digital disponible en la biblioteca",
        "El servicio recibido por las secretarias de la Escuela de Posgrado",
        "El servicio brindado por el personal administrativo de la Escuela de Posgrado",
        "El servicio médico y su infraestructura",
        "El servicio de consejería",
        "Los talleres de actividades artísticas y culturales",
        "Las actividades deportivas",
        "Las aulas de clase",
        "Los ambientes y salas para estudio",
        "Las instalaciones para facilitar la relación social entre los docentes",
        "Las oficinas o cubículos para los docentes",
        "El portal web de la universidad: Mi Ulima",
        "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "El soporte técnico brindado ante las fallas del sistema informático",
        "La Escuela de Posgrado",
        "La Universidad de Lima",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
    ],
    # No Docente
    "nonfaculty": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿A qué dependencia perteneces?",
        "¿Cuántos años laboras en la Universidad de Lima?",
        "Misión, visión y valores de la universidad",
        "La organización en tu puesto de trabajo",
        "La claridad en la definición de las funciones y responsabilidades de tu puesto de trabajo",
        "La distribución de carga laboral en tu dependencia",
        "El liderazgo y compromiso del responsable de tu dependencia",
        "La comunicación oportuna y clara por parte de la jefatura de tu dependencia sobre asuntos que afectan tu trabajo",
        "Los mecanismos de comunicación y coordinación de la jefatura de tu dependencia",
        "La oportunidad y eficacia en la solución de los problemas planteados a la jefatura de tu dependencia",
        "El trabajo en equipo para cumplir con las tareas asignadas",
        "La comunicación con tus compañeros de tu dependencia",
        "La coordinación con otras dependencias de la Universidad",
        "La motivación para participar con aportes y sugerencias en tu dependencia",
        "El clima laboral en tu dependencia",
        "El proceso de promoción y reconocimiento al personal no docente",
        "La retroalimentación de los resultados de la evaluación de tu desempeño por parte de tu superior inmediato",
        "El programa de becas internas",
        "El programa de capacitación a los cuales ha sido invitado durante el año referido a la variedad de temas, pertinencia de horarios, pertinencia en la Invitación, etc.",
        "El servicio médico y su infraestructura",
        "Los talleres de actividades artísticas y culturales",
        "Las actividades deportivas",
        "Las instalaciones para facilitar la relación social entre el personal no docente",
        "Las oficinas o cubículos para el personal no docente",
        "El software especializado empleado en tu trabajo",
        "El portal web de la universidad: Mi Ulima",
        "El aula virtual (Blackboard) y las herramientas de videoconferencia (Zoom)",
        "La conexión Wi-Fi del campus para acceder a los recursos institucionales como Mi Ulima, Blackboard, Zoom, correo institucional y biblioteca virtual",
        "El soporte técnico brindado ante las fallas del sistema informático",
        "La dependencia a la que perteneces",
        "La Universidad de Lima",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
    ],
    # Empleadores (pregrado y posgrado)
    "employers": [
        "ID de respuesta",
        "Estado de respuesta",
        "Start time",
        "Hora de finalización",
        "Net Promoter Score (de un total de 10)",
        "¿Cuál posgrado es el que procede el profesional de la Universidad de Lima contratado por su organización?",
        "¿Cuál es el principal tipo de relación contractual con el profesional de la Universidad de Lima contratado por su organización?",
        "¿Cuál es la jornada laboral que tiene el profesional de la Universidad de Lima contratado por su organización?",
        "Liderazgo",
        "Trabajo en equipo ",
        "Proactividad y autonomía",
        "Actitud positiva para la innovación y el emprendimiento",
        "Capacidad de análisis",
        "Comunicación oral",
        "Expresión escrita y su redacción",
        "Comportamiento ético",
        "Compromiso con el desarrollo sostenible",
        "Aplicación de conocimientos prácticos de la especialidad",
        "Resolución de problemas y casos de la especialidad",
        "Capacidad para asumir nuevos retos y responsabilidades",
        "Uso de tecnologías de información y comunicación (TIC)",
        "Capacidad de aprendizaje continuo",
        "Trabajo bajo presión",
        "Logro de objetivos",
        "Eficiencia en su desempeño",
        "Puntualidad en el cumplimiento de tareas",
        "Adaptación a diferentes puestos o áreas relacionadas con su especialidad",
        "Compromiso con la empresa",
        "Respeto a las normas y a la autoridad",
        "Honestidad",
        "Resiliencia",
        "El desempeño de los egresados de la Escuela de Posgrado de la Universidad de Lima en los puestos de trabajo ocupados en su organización",
        "Explica con tus palabras, las razones de la calificación que diste en la pregunta anterior. (máx. 100 caracteres)",
        "¿Qué carrera es la que procede el profesional de la Universidad de Lima contratado por su organización?",
        "Aplicación de conocimientos adquiridos en el puesto",
        "Asertividad y flexibilidad para enfrentar acciones inesperadas",
        "Conocimientos técnicos de acuerdo al puesto que desempeña",
        "Apoyo a la mejora continua e innovación",
        "El desempeño de los egresados de la Universidad de Lima en los puestos de trabajo ocupados en su organización",
    ],
}


def detectar_nivel(nombre_archivo: str) -> Optional[str]:
    """Mismo criterio que build_json._detectar_nivel (las pruebas los comparan).

    Se repite aqui para que este paso no dependa de pandas.
    """
    texto = str(nombre_archivo).upper()
    if "NO DOCENTE" in texto:
        return "nonfaculty"
    if "EMPLEADORES" in texto:
        return "employers"
    if "EGRESADOS" in texto:
        return "alumni-pg" if "POSGRADO" in texto else "alumni-ug"
    if "DOCENTE" in texto:
        return "faculty-pg" if "POSGRADO" in texto else "faculty-ug"
    if "GRADUADOS" in texto:
        return "graduate"
    if "ESTUDIANTIL" in texto or "ESTUDIANTES" in texto:
        return "postgraduate" if "POSGRADO" in texto else "undergraduate"
    return None


def nombre_csv(encuesta: str) -> str:
    """Nombre de archivo que el ETL sabe leer: ...{CATEGORIA}[- NIVEL][- PERIODO].csv"""
    return f"{str(encuesta).strip()}.csv"


def cabeceras_de(encuesta: str) -> List[str]:
    """Columnas del CSV para esa encuesta, en el orden del ETL."""
    nivel = detectar_nivel(nombre_csv(encuesta))
    if nivel is None:
        raise ValueError(
            f"no se pudo deducir el nivel de '{encuesta}': el nombre debe seguir el "
            "formato de CONTRACTS.md (ENCUESTA DE SATISFACCION {CATEGORIA} [- NIVEL] [- PERIODO])"
        )
    if nivel not in CABECERAS_POR_NIVEL:
        raise ValueError(
            f"el nivel '{nivel}' todavia no se convierte desde la bandeja: "
            "agrega sus cabeceras a CABECERAS_POR_NIVEL"
        )
    return CABECERAS_POR_NIVEL[nivel]


def leer_respuestas(ruta: Path) -> List[Dict[str, Any]]:
    """Lee una bandeja (un JSON por linea). Falla si una linea no es JSON valido."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return []

    registros: List[Dict[str, Any]] = []
    for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip():
            continue
        try:
            registros.append(json.loads(linea))
        except json.JSONDecodeError as exc:
            raise ValueError(f"la linea {numero} de {ruta.name} no es JSON valido: {exc}") from exc
    return registros


def es_respuesta_completa(registro: Dict[str, Any]) -> bool:
    """True si la respuesta llego completa (o si no trae el estado, que no se sabe)."""
    respuestas = registro.get("respuestas") or {}
    estado = str(respuestas.get(CLAVE_ESTADO) or "").strip().upper()
    return not estado or estado == ESTADO_COMPLETO


def _valor(valor: Any) -> Any:
    """Deja el valor listo para el CSV, sin romper el archivo."""
    if valor is None:
        return ""
    if isinstance(valor, (str, int, float)):
        return valor
    return json.dumps(valor, ensure_ascii=False)


def escribir_csv(encuesta: str, registros: List[Dict[str, Any]], destino: Path = CARPETA_DESTINO) -> Path:
    """Escribe el CSV de una encuesta a partir de sus respuestas. Devuelve la ruta."""
    cabeceras = cabeceras_de(encuesta)

    vistos = set()
    filas: List[Dict[str, Any]] = []
    omitidas = 0
    for registro in registros:
        identificador = str(registro.get("id_respuesta") or "").strip()
        # Sin identificador no hay forma de evitar duplicados: no entra al CSV.
        if not identificador or identificador in vistos:
            continue
        if not es_respuesta_completa(registro):
            omitidas += 1
            continue
        vistos.add(identificador)
        respuestas = registro.get("respuestas") or {}
        filas.append(
            {
                columna: (identificador if columna == CLAVE_ID else _valor(respuestas.get(columna)))
                for columna in cabeceras
            }
        )
    if not filas:
        raise ValueError(
            f"la encuesta '{encuesta}' no tiene respuestas completas con identificador"
        )

    if omitidas:
        print(f"omitidas {omitidas} respuestas sin completar (Estado distinto de {ESTADO_COMPLETO}): {encuesta}")

    salida = Path(destino) / nombre_csv(encuesta)
    with open(salida, "w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=cabeceras)
        escritor.writeheader()
        escritor.writerows(filas)
    return salida


def convertir_encuesta(ruta: Path, destino: Path = CARPETA_DESTINO) -> Path:
    """Arma el CSV de una sola bandeja. Devuelve la ruta escrita."""
    ruta = Path(ruta)
    registros = leer_respuestas(ruta)
    if not registros:
        raise ValueError(f"la bandeja {ruta.name} esta vacia")
    encuesta = str(registros[0].get("encuesta") or "").strip()
    if not encuesta:
        raise ValueError(f"la bandeja {ruta.name} no trae el nombre de la encuesta")
    return escribir_csv(encuesta, registros, destino)


def convertir(
    carpeta_pendientes: Path = CARPETA_PENDIENTES, destino: Path = CARPETA_DESTINO
) -> List[Path]:
    """Convierte todas las bandejas. Devuelve los CSV escritos.

    Las bandejas de una misma encuesta se juntan en un solo CSV: si no, la ultima
    pisaria a las anteriores y se perderian respuestas.
    """
    por_encuesta: Dict[str, List[Dict[str, Any]]] = {}
    for ruta in sorted(Path(carpeta_pendientes).glob("*.jsonl")):
        registros = leer_respuestas(ruta)
        if not registros:
            continue
        encuesta = str(registros[0].get("encuesta") or "").strip()
        if not encuesta:
            raise ValueError(f"la bandeja {ruta.name} no trae el nombre de la encuesta")
        por_encuesta.setdefault(encuesta, []).extend(registros)

    return [escribir_csv(encuesta, registros, destino) for encuesta, registros in por_encuesta.items()]


def main(argv) -> int:
    destino = Path(argv[1]) if len(argv) > 1 else CARPETA_DESTINO
    try:
        escritos = convertir(CARPETA_PENDIENTES, destino)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1

    if not escritos:
        print(f"sin bandejas en {CARPETA_PENDIENTES}: no hay CSV que armar")
        return 0

    for ruta in escritos:
        print(f"CSV generado desde la bandeja: {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
