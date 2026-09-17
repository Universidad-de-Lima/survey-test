/**
 * SURVEY TOOLTIP — Componente de tooltip flotante.
 *
 * Extraído de dashboard.js (v2.0). Gestiona la visualización de tooltips
 * en barras, gráficos y segmentos de datos.
 *
 * Dependencias: SurveySanitizer (opcional, fallback a textContent)
 *
 * @module components/tooltip
 * @version 1.1.0
 */
window.SurveyTooltip = (() => {
  'use strict';

  const TOOLTIP_ID = 'tooltip';
  const OFFSET_X = 10;
  const OFFSET_Y = -10;

  /** Obtiene o crea el elemento tooltip en el DOM */
  function getElement() {
    let el = document.getElementById(TOOLTIP_ID);
    if (!el) {
      el = document.createElement('div');
      el.id = TOOLTIP_ID;
      el.className = 'tooltip';
      el.setAttribute('role', 'tooltip');
      el.setAttribute('aria-hidden', 'true');
      document.body.appendChild(el);
    }
    return el;
  }

  /** Sanitiza contenido para el tooltip (delega a SurveySanitizer si disponible) */
  function safeContent(html) {
    const san = window.SurveySanitizer;
    return san ? san.sanitizeHTML(html) : String(html).replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /**
   * Reposiciona el tooltip según las coordenadas del evento.
   * Reutiliza la misma lógica de boundary detection que show().
   * @param {MouseEvent} e - Evento del mouse
   */
  function _position(e) {
    const el = document.getElementById(TOOLTIP_ID);
    if (!el || el.style.display === 'none') return;

    const tooltipWidth = el.offsetWidth;
    const tooltipHeight = el.offsetHeight;
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    let leftPos = e.clientX + OFFSET_X;
    let topPos = e.clientY + OFFSET_Y;

    // Si se sale por la derecha, lo mostramos a la izquierda del cursor
    if (leftPos + tooltipWidth > windowWidth) {
      leftPos = e.clientX - tooltipWidth - OFFSET_X;
    }

    // Si se sale por abajo, lo mostramos más arriba
    if (topPos + tooltipHeight > windowHeight) {
      topPos = e.clientY - tooltipHeight - Math.abs(OFFSET_Y);
    }

    // Evitar que se salga por arriba si el usuario scrollea mucho
    if (topPos < 0) {
      topPos = 10;
    }

    el.style.left = `${leftPos}px`;
    el.style.top = `${topPos}px`;
  }

  /**
   * Muestra el tooltip en la posición del evento.
   * @param {MouseEvent} e - Evento del mouse
   * @param {string} content - Contenido HTML (se sanitiza automáticamente)
   * @param {boolean} [raw=false] - Si es true, no sanitiza (usar solo con contenido controlado)
   */
  function show(e, content, raw = false) {
    const el = getElement();
    el.innerHTML = raw ? content : safeContent(content);
    el.style.display = 'block';
    _position(e);
    // Oculta el tooltip al hacer scroll para que no quede pegado
    window.addEventListener('scroll', hide, { once: true });
  }

  /**
   * Reposiciona el tooltip visible siguiendo al cursor.
   * Útil para listeners mousemove después de un mouseenter con show().
   * @param {MouseEvent} e - Evento del mouse
   */
  function move(e) {
    _position(e);
  }

  /** Oculta el tooltip */
  function hide() {
    const el = document.getElementById(TOOLTIP_ID);
    if (el) el.style.display = 'none';
  }

  /**
   * Agrega listeners de tooltip a segmentos dentro de un contenedor.
   * Los segmentos deben tener data-label y data-value.
   * @param {string} selector - Selector CSS para los segmentos
   */
  function bindToSegments(selector) {
    document.querySelectorAll(selector).forEach((seg) => {
      seg.addEventListener('mousemove', (e) =>
        show(e, `${seg.dataset.label}: ${seg.dataset.value}`),
      );
      seg.addEventListener('mouseleave', hide);
    });
  }

  /**
   * Hace un elemento accesible por teclado con tooltip.
   * Anade tabindex="0", role="img" (si no tiene role), y listeners
   * focus/blur para mostrar/ocultar el tooltip al navegar con Tab.
   * No modifica los listeners mouseenter/mouseleave existentes.
   * @param {HTMLElement} el - Elemento a hacer accesible
   * @param {function} getContent - Funcion que retorna el contenido del tooltip
   * @param {boolean} [raw=false] - Si true, no sanitiza
   */
  function makeAccessible(el, getContent, raw = false) {
    if (!el) return;
    el.setAttribute('tabindex', '0');
    if (!el.getAttribute('role')) {
      el.setAttribute('role', 'img');
    }
    el.addEventListener('focus', (e) => {
      show(e, getContent(), raw);
    });
    el.addEventListener('blur', hide);
  }

  return { show, move, hide, bindToSegments, makeAccessible };
})();
