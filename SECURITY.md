# Security Policy — survey-test

## Data Protection

This repository processes survey data **Universidad de Lima**.
The data types handled:

| Type | Example | Status |
|---|---|---|
| **PII directa** | IP address, User Agent | 🟢 **Mitigada por Arquitectura A (Fase 3.8.2):** los CSVs subidos **no se commitean**; se descargan a un runner efímero, se redimen con `sanitize_csv_pii.py` antes del ETL y se borran. El Release temporal se mantiene como **DRAFT** (no público) y se elimina tras procesar. `data/` está en `.gitignore` y el commit de resultados está desactivado para uploads. |
| **PII cuasi-identificadora** | Free-text comments (comentarios NPS abiertos) | 🟢 **Mitigada.** Los comentarios se envían a DeepSeek/NVIDIA después de aplicar `enmascarar_pii` (`zoho-survey/scripts/lib/io_helper.py`). En `sentimiento.json` el campo `comentario_original` se guarda ofuscado (emails, teléfonos y códigos de estudiante reemplazados por placeholders). No hay caché persistente (deduplicación por ID en `sentimiento.json`). |
| **Aggregated metrics** | NPS, CSAT scores | 🟢 No PII exposure |

## Reporting Vulnerability

If you discover PII exposure or security issue:

1. **Do not** open public issue.
2. Contact repository maintainer directly.
3. Or email: [survey-security@ulima.edu.pe]

## Runtime Security

- Zero runtime dependencies in production (static site on GitHub Pages).
- All processing happens in CI (GitHub Actions).
- CSV exports sanitized formula injection.
- HTML input sanitized via `SurveySanitizer` (allowlist 9 tags).

## Environment Variables

See `.env.example` for required and optional environment variables, including:
- `DEEPSEEK_API_KEY` (principal)
- `NVIDIA_API_KEY` (fallback)
- `IA_CUALITATIVO_*` (workers, RPM, timeout, modelos)

## Flujo de Ingesta y Descarga — Documentación completa

Ver `docs/INGESTA_Y_DESCARGA.md` para el flujo completo de:
- **Subida de CSVs** (Release DRAFT temporal → Actions → sanitización → ETL → deploy → borrado)
- **Generación de ZIPs** (csv_exporter.py → exports/ → borrado en CI)

## Notas sobre la ingesta web ("Subir datos")

- **Única PII sensible en la ingesta:** dirección IP (`Dirección IP`). `Agente Usuario` y `URL de la encuesta a la que accede el encuestado` también se redimen.
- **Release temporal siempre DRAFT:** el frontend ya no publica el Release; se mantiene como borrador y GitHub Actions lo elimina tras procesar exitosamente. En caso de error, el frontend intenta borrar el Release DRAFT.
- **PAT del owner:** se mantiene solo en memoria del navegador; nunca llega a GitHub Actions.
- **Reintento:** si falla, el Release DRAFT persiste para recovery manual; reintentar con un nuevo `upload_id` (tag UUID) evita colisiones de tags.
