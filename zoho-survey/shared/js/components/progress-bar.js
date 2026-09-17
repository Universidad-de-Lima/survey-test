/**
 * SURVEY PROGRESS BAR — Barra de progreso de lectura.
 *
 * Extraído de dashboard.js (v2.0). Muestra una barra naranja que
 * indica el progreso de scroll en la página.
 *
 * Requiere: elemento #progress-fill en el DOM.
 *
 * @module components/progress-bar
 * @version 1.0.0
 */
window.SurveyProgressBar = (() => {
  'use strict';

  /**
   * Inicializa la barra de progreso.
   * - Observa las secciones para navegación activa
   * - Actualiza el ancho de la barra al hacer scroll
   * - Maneja clicks en nav-links para navegación suave
   *
   * @param {Object} [options]
   * @param {string} [options.fillSelector='#progress-fill'] - Selector del elemento fill
   * @param {string} [options.navSelector='.nav-links a'] - Selector de links de navegación
   * @param {string[]} [options.sectionIds] - IDs de las secciones a observar
   */
  function init(options = {}) {
    const fillSelector = options.fillSelector || '#progress-fill';
    const navSelector = options.navSelector || '.nav-links a';
    const sectionIds = options.sectionIds || ['ejecutivo', 'operativo', 'detallado', 'cualitativo'];

    const fill = document.querySelector(fillSelector);
    const navLinks = document.querySelectorAll(navSelector);
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter((el) => el && el.style.display !== 'none');

    if (!fill || !navLinks.length) return;

    const setActive = (id) => {
      navLinks.forEach((a) => {
        a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
      });
    };

    // Observer para activar link de navegación según sección visible
    const observer = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (e.isIntersecting) setActive(e.target.id);
      }),
      { threshold: 0.1 },
    );
    sections.forEach((s) => observer.observe(s));

    // Click en nav-link: marcar como activo
    navLinks.forEach((a) => {
      a.addEventListener('click', () => {
        setActive(a.getAttribute('href').slice(1));
      });
    });

    // Actualizar ancho de barra al hacer scroll
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
          const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
          if (fill) fill.style.width = `${(scrollTop / scrollHeight) * 100}%`;
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  return { init };
})();
