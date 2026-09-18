/**
 * ESLint 9/10 — configuracion flat en ESM (.mjs).
 *
 * Motivo: el proyecto tenia .eslintrc.json (formato eslintrc) y el workflow lo
 * invocaba con `--no-eslintrc --config .eslintrc.json`. En ESLint 9 ese flag fue
 * ELIMINADO (sustituido por `--no-config-lookup`) y el formato eslintrc esta
 * deprecado, de modo que el paso de lint no analizaba nada y el `|| true`
 * ocultaba el fallo.
 *
 * Se usa .mjs con `export default` (no .js con module.exports) para ser
 * compatible tanto con ESLint 9 como con ESLint 10, que ya no acepta la
 * configuracion flat en formato CommonJS.
 *
 * El paso de CI trata el resultado asi:
 *   - exit 0  -> sin hallazgos
 *   - exit 1  -> hay hallazgos (informativo, no bloquea)
 *   - exit >=2 -> la configuracion no carga: el job FALLA (fail-closed)
 */

const BROWSER_GLOBALS = {
  window: 'readonly',
  document: 'readonly',
  navigator: 'readonly',
  location: 'readonly',
  history: 'readonly',
  localStorage: 'readonly',
  sessionStorage: 'readonly',
  console: 'readonly',
  alert: 'readonly',
  fetch: 'readonly',
  crypto: 'readonly',
  FormData: 'readonly',
  Blob: 'readonly',
  File: 'readonly',
  FileReader: 'readonly',
  URL: 'readonly',
  URLSearchParams: 'readonly',
  AbortController: 'readonly',
  TextEncoder: 'readonly',
  TextDecoder: 'readonly',
  Promise: 'readonly',
  Map: 'readonly',
  Set: 'readonly',
  Date: 'readonly',
  Math: 'readonly',
  JSON: 'readonly',
  Intl: 'readonly',
  Number: 'readonly',
  Object: 'readonly',
  Array: 'readonly',
  String: 'readonly',
  Boolean: 'readonly',
  Error: 'readonly',
  RegExp: 'readonly',
  Symbol: 'readonly',
  isNaN: 'readonly',
  parseInt: 'readonly',
  parseFloat: 'readonly',
  encodeURIComponent: 'readonly',
  decodeURIComponent: 'readonly',
  setTimeout: 'readonly',
  clearTimeout: 'readonly',
  setInterval: 'readonly',
  clearInterval: 'readonly',
  requestAnimationFrame: 'readonly',
  cancelAnimationFrame: 'readonly',
  getComputedStyle: 'readonly',
  matchMedia: 'readonly',
  CustomEvent: 'readonly',
  Event: 'readonly',
  Node: 'readonly',
  Element: 'readonly',
  HTMLElement: 'readonly',
  MutationObserver: 'readonly',
  IntersectionObserver: 'readonly',
  ResizeObserver: 'readonly',
  globalThis: 'readonly',
};

const RULES = {
  'no-unused-vars': ['warn', { args: 'none' }],
  'no-undef': 'error',
  'no-alert': 'warn',
  'no-implied-eval': 'error',
  'no-var': 'warn',
};

export default [
  {
    // Los JSON generados por el ETL y las dependencias no se lintean.
    ignores: ['node_modules/**', 'zoho-survey/**/json/**', 'tests/screenshots/**'],
  },
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'script',
      globals: BROWSER_GLOBALS,
    },
    rules: RULES,
  },
  {
    // Los tests y los runners de Node usan CommonJS (require/module/process).
    files: ['tests/**/*.js'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'commonjs',
      globals: { ...BROWSER_GLOBALS, require: 'readonly', module: 'readonly', process: 'readonly', __dirname: 'readonly', global: 'readonly', Buffer: 'readonly' },
    },
    rules: RULES,
  },
];
