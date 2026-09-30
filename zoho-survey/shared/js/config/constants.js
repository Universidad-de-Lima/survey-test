/**
 * SURVEY CONFIG — Constantes de negocio externalizadas.
 * 
 * Este archivo es la fuente canónica de configuración para todos los dashboards.
 * dashboard.js usará estos valores si están disponibles, con fallback a sus
 * hardcodeados internos para mantener compatibilidad backward.
 * 
 * Para modificar metas, ciclos especiales o labels:
 * 1. Editar este archivo
 * 2. El cambio aplica a TODOS los dashboards sin tocar dashboard.js
 * 
 * @module config/constants
 * @version 1.0.0
 */

window.SURVEY_CONFIG = {
  // ── Metas institucionales ──
  META_NPS: 50,
  META_CSAT: 93,
  META_T2B: 70,
  META_PONDERADO: 80,
  META_EMPLEABILIDAD: 85,

  // ── Carreras y facultades con 12 ciclos (en lugar de 10) ──
  CARRERAS_12_CICLOS: ['Derecho', 'Psicología'],
  FACULTADES_12_CICLOS: ['Facultad de Derecho', 'Facultad de Psicología'],

  // ── Programa de Estudios Generales ──
  PROGRAMA_ESTUDIOS_GENERALES: 'Programa de Estudios Generales',
  CICLOS_ESTUDIOS_GENERALES: ['1° Ciclo', '2° Ciclo'],

  // ── Claves de niveles de satisfacción ──
  // NO modificar a menos que Zoho Survey cambie sus etiquetas
  SAT_KEYS: [
    'Totalmente satisfecho',
    'Muy satisfecho',
    'Satisfecho',
    'Insatisfecho',
    'Totalmente insatisfecho',
  ],

  // ── Subset para Top 2 Box (las dos respuestas más positivas) ──
  // Invariante de alineación: debe ser SAT_KEYS.slice(0, 2) y mantener el
  // orden de más positivo a más negativo, igual que CSAT_WEIGHTS.
  SAT_TOP2_KEYS: ['Totalmente satisfecho', 'Muy satisfecho'],

  // ── Pesos de la escala Likert para el Promedio Ponderado ──
  // Debe estar alineado posicionalmente con SAT_KEYS (más positivo → peso mayor).
  CSAT_WEIGHTS: [5, 4, 3, 2, 1],
  CSAT_SCALE_MAX: 5,

  // ── Placeholder texts ──
  FACULTAD_PLACEHOLDER: 'Todas las unidades académicas',
  FACULTAD_PLACEHOLDER_PROG: 'Todas las unidades académicas',

  // ── Ciclos ──
  MAX_CICLOS_DEFAULT: 10,
  MAX_CICLOS_ESPECIALES: 12,

  // ── Umbrales visuales ──
  MIN_BAR_LABEL_PCT: 4,
  MIN_EXTERNAL_LABEL_PCT: 0.5,
  MIN_SEGMENT_WIDTH: 30,
  SEGMENT_LABEL_HIDE_PCT: 0.0001,
  SEGMENT_EXTERNAL_LABEL_PCT: 0.02,

  // ── Visualización ──
  RADAR_LABEL_MAXLEN: 26,
  ANIMATION_FALLBACK_MS: 1200,

};
