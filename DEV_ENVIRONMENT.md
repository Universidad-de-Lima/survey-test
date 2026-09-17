# Entorno de Desarrollo — survey-test

Este documento describe el flujo de trabajo para editar el proyecto localmente y probar los cambios en GitHub Actions / GitHub Pages.

> **Regla fundamental:** GitHub es el entorno de producción. El primer `push` al repositorio se realiza manualmente; los posteriores se automatizan tras validación y autorización.

## Flujo de trabajo

```
Local (edición + validación estática) → commit → push → GitHub Actions (tests + ETL + deploy) → GitHub Pages
```

### 1. Requisitos locales

- Python 3.11+ (recomendado; CI usa 3.11).
- Node.js 18+ (recomendado; CI usa 18).
- Git.
- Credenciales Git configuradas.

Instalar dependencias:

```bash
pip install -r requirements.txt
npm install   # solo si se requiere jsdom/eslint
```

### 2. Validación local

Antes de cada `push` ejecutar:

```bash
# Tests unitarios JS (no requieren DOM ni API keys)
npm run test:js

# Tests unitarios Python
npm run test:py

# Validación de contratos JSON ya generados
npm run validate:json

# Sintaxis de todos los módulos JS
node -c zoho-survey/shared/js/portal-upload.js
node -c zoho-survey/shared/js/portal-upload-ui.js
# ... (ver .github/workflows/tests.yml)
```

> El ETL completo (`npm run build:json`) no se ejecuta localmente porque requiere `DEEPSEEK_API_KEY` y consume tokens. Su prueba autoritativa ocurre en GitHub Actions.

### 3. Vista estática local (opcional)

Para previsualizar HTML/JS sin JSONs generados:

```bash
npm start
# Abrir http://localhost:8080/zoho-survey/
```

Esta vista estática no ejecuta el ETL ni la ingesta.

### 4. Subida de datos

La carga de CSVs se realiza desde el portal publicado en GitHub Pages (`https://universidad-de-lima.github.io/survey-test`):

1. Abrir el portal.
2. Clic en **"Subir datos"**.
3. Ingresar PAT de GitHub (solo en memoria del navegador).
4. Seleccionar hasta 10 CSVs válidos.
5. El frontend crea un Release **DRAFT** temporal, sube los assets y dispara `repository_dispatch`.
6. GitHub Actions descarga, valida, sanitiza, ejecuta el ETL y elimina el Release temporal.

Ver detalles en `docs/INGESTA_Y_DESCARGA.md` y `SECURITY.md`.

## Seguridad local

- `.env` contiene secretos y está en `.gitignore`. Nunca commitearlo.
- Los CSVs en `data/` están en `.gitignore`. No subirlos a GitHub.
- Sanitizar PII con `python zoho-survey/scripts/sanitize_csv_pii.py --all` antes de cualquier commit accidental.

## Migración / publicación en GitHub

El primer push al repositorio remoto lo realiza el propietario:

```bash
git remote add origin https://github.com/Universidad-de-Lima/survey-test.git
git branch -M main
git push -u origin main
```

Asegurarse de configurar el secreto `DEEPSEEK_API_KEY` en el repositorio de GitHub para que el ETL pueda ejecutarse.
