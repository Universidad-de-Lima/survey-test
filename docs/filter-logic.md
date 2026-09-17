# Lógica de Filtros en Cascada (Matriz de Negocio)

Este documento describe la lógica de los filtros en cascada implementados en el frontend (`shared/js/dashboard.js`), alineados con las reglas de negocio de la Universidad de Lima para la matriz **Facultad / Carrera / Ciclo**.

## Grupos de Filtros

Cada sección del dashboard utiliza un grupo de filtros específico identificado por su sufijo en el HTML:

| Sufijo | Sección | Elementos Esperados |
| --- | --- | --- |
| `top3` | Operativo - Barras Top 3 | facultad, carrera, ciclo, reset |
| `radar` | Operativo - Radar | facultad, carrera, ciclo, reset |
| `preguntas` | Detallado - Preguntas | facultad, carrera, ciclo, reset |
| `detalle` | Detallado - Carrera | facultad, ciclo, reset |
| `visibilidad` | Detallado - Visibilidad | facultad, carrera, ciclo, reset |

La convención de IDs HTML es:
- `filter-facultad-<sufijo>`
- `filter-carrera-<sufijo>`
- `filter-ciclo-<sufijo>`
- `reset-<sufijo>`

---

## Matriz de Combinaciones Válidas

Los filtros operan de manera independiente en la selección, pero el filtrado de datos (`filtrarDatos`) aplica una intersección tipo **AND** entre todos los criterios activos:

| Facultad | Carrera | Ciclo |
| --- | --- | --- |
| Todas | Todas | Todos |
| Todas | Todas | (ciclo específico) |
| Todas | (carrera específica) | Todos |
| Todas | (carrera específica) | (ciclo específico) |
| (facultad específica) | Todas | Todos |
| (facultad específica) | Todas | (ciclo específico) |
| (facultad específica) | (carrera de esa facultad) | Todos |
| (facultad específica) | (carrera de esa facultad) | (ciclo específico) |
| Programa de Estudios Generales | Todas | Todos |

---

## Comportamiento de Cascada de Selectores

1. **Facultad:** Se llena desde `filtros.facultades` más el `Programa de Estudios Generales` (que siempre se renderiza primero en pregrado).
2. **Carrera:**
   - Sin facultad seleccionada o con Estudios Generales: Muestra la lista global `filtros.carreras`.
   - Con una facultad específica: Muestra únicamente las carreras mapeadas en `filtros.facultad_carrera[facultad]`.
3. **Ciclo (Rangos Dinámicos):**
   - El selector limita dinámicamente las opciones visibles de ciclos para prevenir combinaciones de datos inexistentes en el negocio.

---

## Rangos de Ciclos por Selector (Regla de Negocio)

La visualización de ciclos en el selector sigue las siguientes consideraciones:

| Condición | Ciclos Disponibles en Selector |
| --- | --- |
| Facultad = Programa de Estudios Generales | Solo 1° y 2° |
| Carrera = Derecho o Psicología (o sus respectivas facultades) | Del 1° al 12° |
| Resto de carreras / facultades | Del 1° al 10° |

*Nota:* Al filtrar datos con *Programa de Estudios Generales* seleccionado, el sistema limita automáticamente los datos a los ciclos 1° y 2°, incluso si el usuario no los marca explícitamente.

---

## Particularidad de la Sección Cualitativa (Comentarios de Sentimiento)

Debido a que `sentimiento.json` almacena los conteos agregados por facultad, carrera y ciclo por separado (en lugar de una intersección combinada a nivel de fila individual para preservar privacidad y performance), la sección de comentarios cualitativos prioriza los filtros con el orden de jerarquía: **Carrera > Facultad > Ciclo**. 

El *Programa de Estudios Generales* utiliza la suma de los ciclos 1° y 2° del objeto `por_ciclo` de los sentimientos.

---

## Invariantes Estructurales

- **IDs de Contrato:** Los IDs de los selectores HTML son un contrato público con `dashboard.js` y no deben renombrarse en los templates de HTML.
- **Sección `#sentimiento`:** Se mantiene este ID técnico en JS/HTML por backward compatibility, aunque la etiqueta visible sea "Cualitativo".
