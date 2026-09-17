# Contratos JSON del dashboard de encuestas

> **Nota:** Este documento es una referencia histórica. La fuente canónica y actualizada de los contratos de datos es `CONTRACTS.md` en la raíz del repositorio.

Este documento define el contrato minimo que debe respetar cada periodo academico en `zoho-survey/students/<nivel>/<periodo>/json/` para que `shared/js/dashboard.js` pueda renderizar sin fallos.

## Archivos obligatorios

| Archivo                   | Tipo raiz | Uso principal                                   |
| ------------------------- | --------: | ----------------------------------------------- |
| `dashboard_data.json`     |    object | KPIs ejecutivos, barras NPS/CSAT y hallazgos    |
| `dimensiones.json`        |     array | Top 3, radar, preguntas y visibilidad           |
| `ids.json`                |     array | Conteos por facultad/carrera/ciclo para detalle |
| `nps_ciclo_carrera.json`  |     array | NPS por carrera y ciclo                         |
| `csat_ciclo_carrera.json` |     array | CSAT por carrera y ciclo                        |
| `filtros.json`            |    object | Opciones de filtros cascada                     |
| `sentimiento.json`        |    object | Visual cualitativo                              |

## Archivos legado

Estos archivos pueden existir por compatibilidad historica, pero no deben considerarse contrato obligatorio para nuevas encuestas:

- `nps.json`
- `csat.json`
- `nps_carrera.json`
- `csat_carrera.json`
- `resumen.json`

El validador permite su presencia y emite advertencias para que la deuda sea visible sin romper periodos existentes.

## `dashboard_data.json`

Claves requeridas:

- `resumen`
- `hallazgos`
- `nps`
- `csat`

`resumen` requiere:

- `año` o `ano`
- `encuestas`
- `fecha_inicio`
- `fecha_fin`
- `nps.score`
- `csat.score`

`hallazgos` requiere:

- `csat_pct`
- `nps_score`
- `nps_tipo`
- `nps_etapas`
- `tendencia`
- `delta`

`nps` debe contener `Promotores`, `Pasivos` y `Detractores`.

`csat` debe contener:

- `Totalmente satisfecho`
- `Muy satisfecho`
- `Satisfecho`
- `Insatisfecho`
- `Totalmente insatisfecho`

## `dimensiones.json`

Cada fila debe incluir:

- `facultad`
- `carrera`
- `ciclo`
- `categoria`
- `dimension`
- `t3b`
- `b2b`
- `total`
- `t3b_pct`
- `no_utilizo`
- `no_conozco`
- `Totalmente satisfecho`
- `Muy satisfecho`
- `Satisfecho`
- `Insatisfecho`
- `Totalmente insatisfecho`
- `No utilizo`
- `No conozco`

Debe existir al menos una fila con `total > 0`.

## `filtros.json`

Claves requeridas:

- `facultades`: lista no vacia de textos
- `carreras`: lista no vacia de textos
- `ciclos`: lista no vacia de textos
- `facultad_carrera`: objeto que mapea cada facultad a sus carreras

Cada facultad listada en `facultades` debe existir como clave en `facultad_carrera`.

## `ids.json`

Cada fila debe incluir:

- `facultad`
- `carrera`
- `ciclo`
- `total`

La suma de `total` debe ser positiva.

## `nps_ciclo_carrera.json`

Cada fila debe incluir:

- `facultad`
- `carrera`
- `ciclo`
- `Promotores`
- `Pasivos`
- `Detractores`

## `csat_ciclo_carrera.json`

Cada fila debe incluir:

- `facultad`
- `carrera`
- `ciclo`
- `Totalmente satisfecho`
- `Muy satisfecho`
- `Satisfecho`
- `Insatisfecho`
- `Totalmente insatisfecho`

## `sentimiento.json`

Claves requeridas:

- `resumen`
- `topicos`
- `por_carrera`
- `por_ciclo`

`resumen` requiere:

- `total_con_comentario`
- `total_analizados`
- `pasivos`
- `detractores`
- `nota`

Cada topico requiere:

- `topico`
- `total_comentarios`
- `positivos`
- `negativos`
- `neutros`

## HTML de periodo

Cada `periodo/index.html` debe conservar los IDs consumidos por `dashboard.js`, especialmente:

- `id="sentimiento"`
- `id="sentimiento-heading"`

La etiqueta visible del visual debe ser `Cualitativo` y el titulo debe ser `ANALISIS CUALITATIVO`.

## Validacion

Ejecutar:

```bash
python zoho-survey/scripts/validate_generated_json.py undergraduate
```

El workflow `.github/workflows/build_zoho_survey.yml` ejecuta `validate_generated_json.py` en cada push que afecte `zoho-survey/students/**`.
