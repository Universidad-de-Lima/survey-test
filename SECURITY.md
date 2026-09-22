# Security Policy — survey-test

## Data Protection

This repository processes survey data **Universidad de Lima**.
The data types handled:

| Type | Example | Status |
|---|---|---|
| **PII directa** | IP address, User Agent | 🟢 **Mitigada por Arquitectura A (Fase 3.8.2):** los CSVs subidos **no se commitean**; se descargan a un runner efímero, se redimen con `sanitize_csv_pii.py` antes del ETL y se borran. El Release temporal se mantiene como **DRAFT** (no público) y se elimina tras procesar. `data/` está en `.gitignore` y el commit de resultados está desactivado para uploads. |
| **PII cuasi-identificadora** | Free-text comments (comentarios NPS abiertos) | 🟢 **Mitigada.** Los comentarios se envían a los motores IA (OpenCode, Google, NVIDIA) después de aplicar `enmascarar_pii` (`zoho-survey/scripts/lib/io_helper.py`). En `sentimiento.json` el campo `comentario_original` se guarda ofuscado (emails, teléfonos y códigos de estudiante reemplazados por placeholders). No hay caché persistente (deduplicación por ID en `sentimiento.json`). Las respuestas que llegan por el webhook de Zoho Survey pasan por `enmascarar_pii` **antes** de guardarse en `data/zoho_pendientes/` (Fase 1 de ingesta por webhook). |
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

See `docs/developer-guide.md` (§ "Configuración del Motor Cualitativo") for required and optional environment variables, including:
- `GOOGLE_API_KEY` (Google Gemini, primero en la cadena)
- `NVIDIA_API_KEY` (NVIDIA NIM, 4 modelos)
- `OPENCODE_API_KEY` (OpenCode)
- `IA_CUALITATIVO_CADENA` (orden y modelos) e `IA_CUALITATIVO_*` (workers, RPM, timeout)

## Flujo de Ingesta y Descarga — Documentación completa

Ver `docs/INGESTA_Y_DESCARGA.md` para el flujo completo de:
- **Recepción de respuestas** (webhook → incidencia → enmascarado → `data/zoho_pendientes/`)
- **Subida de CSVs para procesar** (Release → `workflow_dispatch` → sanitización → ETL → deploy → borrado)
- **Generación de ZIPs** (csv_exporter.py → exports/ → borrado en CI)

## Notas sobre la ingesta

- **Única PII sensible en la ingesta:** dirección IP (`Dirección IP`). `Agente Usuario` y `URL de la encuesta a la que accede el encuestado` también se redimen.
- **Enmascarado antes de guardar:** la respuesta del webhook se enmascara en `zoho_respuesta.py` **antes** de escribirla en `data/zoho_pendientes/` (el repositorio es público).
- **PAT del webhook:** vive en la cabecera del webhook dentro de Zoho (permiso *Issues: write*); nunca entra al repositorio ni al navegador.
- **Release de entrada:** se mantiene como DRAFT mientras se procesa y **no** se elimina (es del owner). Si el proceso falla, se relanza con el mismo tag.
- **Fallos de ingesta:** si el cuerpo de la incidencia no es JSON válido, el flujo falla y la incidencia queda **abierta** como aviso.
