/* ============================================================
   Portal v5.0 Console — Orquestador (adelgazado).
   Conserva: init, openPhase, switchFile, showDashboard,
   renderSidebar, PORTAL_PHASES, REPO_TARGET,
   ICONS, svg, state, $, el, escapeHtml, renderInline,
   renderMarkdown, highlightEvidence, toggleMobileNav, refresh,
   renderArtifactViewer, renderUnderConstruction,
   renderPendingArtifact, renderPending, fetchArtifact,
   loadActiveFile y wiring de eventos.
   La lógica de datos/dashboard/survey/radar/filtros vive en
   shared/js/portal/portal-*.js (cargados ANTES que este archivo).
   ============================================================ */

// ---------- Phase definitions ----------
let PORTAL_PHASES = [
  { id: "1.0", order: 0, name: "Estudiantes Pregrado", fullName: "Estudiantes Pregrado", grupo: "Estudiantes",
    role: "Experiencia de pregrado", predecessor: null, successor: "1.1",
    icon: "book-open" },
  { id: "1.1", order: 1, name: "Estudiantes Posgrado", fullName: "Estudiantes Posgrado", grupo: "Estudiantes",
    role: "Experiencia de posgrado", predecessor: "1.0", successor: "1.2",
    icon: "book-open" },
  { id: "1.2", order: 2, name: "Graduados Pregrado", fullName: "Graduados Pregrado", grupo: "Graduados y egresados",
    role: "Vinculación con graduados", predecessor: "1.1", successor: "1.3",
    icon: "graduation-cap" },
  { id: "1.3", order: 3, name: "Egresados Pregrado", fullName: "Egresados Pregrado", grupo: "Graduados y egresados",
    role: "Inserción laboral", predecessor: "1.2", successor: "1.4",
    icon: "graduation-cap" },
  { id: "1.4", order: 4, name: "Egresados Posgrado", fullName: "Egresados Posgrado", grupo: "Graduados y egresados",
    role: "Seguimiento de egresados", predecessor: "1.3", successor: "1.5",
    icon: "graduation-cap" },
  { id: "1.5", order: 5, name: "Docentes Pregrado", fullName: "Docentes Pregrado", grupo: "Colaboradores y empleadores",
    role: "Experiencia del profesorado", predecessor: "1.4", successor: "1.6",
    icon: "marker" },
  { id: "1.6", order: 6, name: "Docentes Posgrado", fullName: "Docentes Posgrado", grupo: "Colaboradores y empleadores",
    role: "Clima académico", predecessor: "1.5", successor: "1.7",
    icon: "marker" },
  { id: "1.7", order: 7, name: "Personal No Docente", fullName: "Personal No Docente", grupo: "Colaboradores y empleadores",
    role: "Satisfacción del personal", predecessor: "1.6", successor: "1.8",
    icon: "users" },
  { id: "1.8", order: 8, name: "Empleadores", fullName: "Empleadores", grupo: "Colaboradores y empleadores",
    role: "Vinculación con empleadores", predecessor: "1.7", successor: "1.9",
    icon: "briefcase" },
  { id: "1.9", order: 9, name: "Preguntas", fullName: "Preguntas (IA)",
    role: "Asistente IA", predecessor: "1.8", successor: null,
    optional: true, icon: "help-circle" }
];

const REPO_TARGET = {
  summary: "El nivel de satisfacción se obtiene a partir de la pregunta <strong>¿Cuál es tu nivel de satisfacción con la Universidad de Lima?</strong>. Se calcula dividiendo la suma de las respuestas <strong>Totalmente satisfecho</strong>, <strong>Muy satisfecho</strong> y <strong>Satisfecho</strong> entre el total de respuestas de la escala de satisfacción de 5 puntos, excluyendo las opciones <strong>No conozco</strong>, <strong>No utilizo</strong> y las <strong>respuestas vacías</strong>."
};

// Overview metrics — derivados del estado real (fases con datos cargados)
function getOverview() {
  const d = window.SurveyPortalData || {};
  const total = PORTAL_PHASES.length;
  let completedPhases = 0;
  if (d.tieneDatosDeFase) {
    PORTAL_PHASES.forEach(function (p) {
      if (d.tieneDatosDeFase(p.id)) completedPhases++;
    });
  }
  return { completedCount: completedPhases, totalCount: total };
}

// ---------- SVG icons (Lucide-style, 24x24 stroke) ----------
const ICONS = {
  menu: '<line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="18" y2="18"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
  'file-text': '<path d="M15 2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
  lock: '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  'chevron-right': '<path d="m9 18 6-6-6-6"/>',
  'arrow-right': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  'check-circle': '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  'trending-up': '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
  'bar-chart': '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
  'shield-check': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
  'shield-alert': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
  'file-search': '<path d="M14 2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><circle cx="11" cy="13" r="3"/><path d="m14 15 2 2"/>',
  'list-checks': '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
  'alert-triangle': '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  gauge: '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
  map: '<path d="M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z"/><path d="M15 5.764v15"/><path d="M9 3.236v15"/>',
  recycle: '<path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/><path d="M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12"/><path d="m14 16-3 3 3 3"/><path d="M8.293 13.596 7.196 9.5 3.1 10.598"/><path d="m9.344 5.811 1.093-1.892A1.83 1.83 0 0 1 11.985 3a1.784 1.784 0 0 1 1.546.888l3.943 6.843"/><path d="m13.378 9.633 4.096 1.098 1.097-4.096"/>',
  'circle-dot': '<circle cx="12" cy="12" r="10"/><circle class="icono-punto" cx="12" cy="12" r="1.5"/>',
  clock: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  hash: '<line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>',
  'file-type': '<path d="M14.5 2H5a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M9 13h6"/><path d="M9 17h6"/><path d="M9 9h1"/>',
  'alert-circle': '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
  github: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
  boxes: '<path d="M2.97 12.92A2 2 0 0 0 2 14.63v3.24a2 2 0 0 0 .97 1.71l3 1.8a2 2 0 0 0 2.06 0L12 19v-5.5l-5-3-4.03 2.42Z"/><path d="M7 16.5l4 2.5"/><path d="m18 12-5 3v5.5l1.97 1.18a2 2 0 0 0 2.06 0l3-1.8a2 2 0 0 0 .97-1.71v-3.24a2 2 0 0 0-.97-1.71L18 12Z"/><path d="m17 16.5-4 2.5"/><path d="M7 7l5 3 5-3"/>',
  'layout-dashboard': '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
  circle: '<circle cx="12" cy="12" r="10"/>',
  hammer: '<path d="m15 12-8.373 8.373a1 1 0 1 1-3-3L12 9"/><path d="M17.64 15 22 10.64"/><path d="m20.91 11.7-1.25-1.25c-.6-.6-.93-.44-1.5.11L7.41 20.41"/><path d="M6 6l8 8"/>',
  'badge-check': '<path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m9 12 2 2 4-4"/>',
  'drafting-compass': '<path d="M12 3a2 2 0 0 1 2 2c0 .42-.13.81-.35 1.13"/><path d="m14.83 11.83 6.05 6.05"/><path d="M2.97 12.92A10 10 0 0 0 12 22c.7 0 1.39-.07 2.05-.21"/><path d="M2.12 8.36A10 10 0 0 1 12 2c1.32 0 2.59.26 3.74.72"/><path d="m9 13-1.83 5.66"/><path d="M9.13 4a2 2 0 0 1 2.74 0"/>',
  compass: '<path d="m16.24 7.76-1.804 5.411a2 2 0 0 1-1.265 1.265L7.76 16.24l1.804-5.411a2 2 0 0 1 1.265-1.265z"/><circle cx="12" cy="12" r="10"/>',
  'search-check': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="m8 11 2 2 4-4"/>',
  'clipboard-list': '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
  'graduation-cap': '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
  'briefcase': '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/><path d="M2 13h20"/>',
  'book-open': '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
  'users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  'help-circle': '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  'dictating': '<circle cx="12" cy="4" r="2.5"/><path d="M12 7v5"/><rect x="7" y="12" width="10" height="2.5" rx="1"/><path d="M5 15h14v2.5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1z"/>',
  'marker': '<path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/>',
  calendar: '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
  landmark: '<line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/>'
};

function svg(name, size) {
  size = size || 14;
  const path = ICONS[name] || ICONS.circle;
  return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" class="icono-svg">' + path + '</svg>';
}

// ---------- State ----------
const state = {
  view: 'dashboard',
  activePhaseId: '1.1',
  activeFile: null,
  refreshing: false,
  mobileNavOpen: false,
  cache: new Map()
};

// ---------- DOM helpers ----------
function $(id) { return document.getElementById(id); }
function el(tag, attrs, html) {
  const e = document.createElement(tag);
  if (attrs) {
    for (const k in attrs) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'html') e.innerHTML = attrs[k];
      else if (k.startsWith('on') && typeof attrs[k] === 'function') {
        e.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
      } else if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    }
  }
  if (html != null) e.innerHTML = html;
  return e;
}

// ---------- Markdown renderer ----------
function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function highlightEvidence(text) {
  return text.replace(/\[(ED|EI|INF|HIP|INC)(:[^\]]+)?\]/g, function(m, code, rest) {
    const cls = code.toLowerCase();
    return '<mark class="' + cls + '">[' + code + (rest || '') + ']</mark>';
  });
}

function renderInline(text) {
  let s = escapeHtml(text);
  const codes = [];
  s = s.replace(/`([^`]+)`/g, function(_, c) {
    codes.push(c);
    return '\u0000CODE' + (codes.length - 1) + '\u0000';
  });
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function(_, t, u) {
    return '<a href="' + u + '" target="_blank" rel="noopener noreferrer">' + t + '</a>';
  });
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[^*])\*([^*\s][^*]*?)\*(?!\*)/g, '$1<em>$2</em>');
  s = s.replace(/\u0000CODE(\d+)\u0000/g, function(_, i) {
    return '<code>' + codes[+i] + '</code>';
  });
  s = highlightEvidence(s);
  return s;
}

function renderMarkdown(md) {
  if (!md) return '<p><em>Sin contenido</em></p>';
  const lines = md.replace(/\r\n/g, '\n').split('\n');
  let html = [];
  let i = 0;
  let inUl = false, inOl = false, inBq = false;
  let paragraph = [];

  function closeParagraph() {
    if (paragraph.length) {
      html.push('<p>' + renderInline(paragraph.join(' ')) + '</p>');
      paragraph = [];
    }
  }
  function closeLists() {
    if (inUl) { html.push('</ul>'); inUl = false; }
    if (inOl) { html.push('</ol>'); inOl = false; }
  }
  function closeBlockquote() {
    if (inBq) { html.push('</blockquote>'); inBq = false; }
  }

  while (i < lines.length) {
    let line = lines[i];

    if (/^```/.test(line)) {
      closeParagraph(); closeLists(); closeBlockquote();
      const lang = line.replace(/^```/, '').trim();
      const buf = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) {
        buf.push(lines[i]); i++;
      }
      i++;
      const code = escapeHtml(buf.join('\n'));
      html.push('<pre><code' + (lang ? ' class="language-' + lang + '"' : '') + '>' + code + '</code></pre>');
      continue;
    }

    if (/^\s*\|/.test(line) && i + 1 < lines.length && /^\s*\|[\s\-:|]+\|\s*$/.test(lines[i + 1])) {
      closeParagraph(); closeLists(); closeBlockquote();
      const headerCells = line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(s => s.trim());
      i += 2;
      const rows = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) {
        const cells = lines[i].trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(s => s.trim());
        rows.push(cells);
        i++;
      }
      let tbl = '<div class="table-wrap"><table><thead><tr>';
      headerCells.forEach(c => { tbl += '<th>' + renderInline(c) + '</th>'; });
      tbl += '</tr></thead><tbody>';
      rows.forEach(r => {
        tbl += '<tr>';
        for (let j = 0; j < headerCells.length; j++) {
          tbl += '<td>' + renderInline(r[j] || '') + '</td>';
        }
        tbl += '</tr>';
      });
      tbl += '</tbody></table></div>';
      html.push(tbl);
      continue;
    }

    if (/^---+\s*$/.test(line) || /^\*\*\*+\s*$/.test(line)) {
      closeParagraph(); closeLists(); closeBlockquote();
      html.push('<hr/>');
      i++;
      continue;
    }

    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      closeParagraph(); closeLists(); closeBlockquote();
      const level = h[1].length;
      html.push('<h' + level + '>' + renderInline(h[2]) + '</h' + level + '>');
      i++;
      continue;
    }

    if (/^>\s?/.test(line)) {
      closeParagraph(); closeLists();
      if (!inBq) { html.push('<blockquote>'); inBq = true; }
      paragraph.push(line.replace(/^>\s?/, ''));
      i++;
      continue;
    } else {
      closeBlockquote();
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      closeParagraph();
      if (inOl) { html.push('</ol>'); inOl = false; }
      if (!inUl) { html.push('<ul>'); inUl = true; }
      html.push('<li>' + renderInline(line.replace(/^\s*[-*+]\s+/, '')) + '</li>');
      i++;
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      closeParagraph();
      if (inUl) { html.push('</ul>'); inUl = false; }
      if (!inOl) { html.push('<ol>'); inOl = true; }
      html.push('<li>' + renderInline(line.replace(/^\s*\d+\.\s+/, '')) + '</li>');
      i++;
      continue;
    }

    if (/^\s*$/.test(line)) {
      closeParagraph(); closeLists();
      i++;
      continue;
    }

    closeLists();
    paragraph.push(line.trim());
    i++;
  }
  closeParagraph(); closeLists(); closeBlockquote();
  return html.join('\n');
}

// ---------- Constantes de artefactos ----------
const UNDER_CONSTRUCTION = ['1.1', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8'];

// Ítems que ya tienen vista de dashboard sobre los datos del periodo.
const FASES_CON_DASHBOARD = ['1.0', '1.2'];

// ---------- Artifact fetching ----------
async function fetchArtifact(filename) {
  if (state.cache.has(filename)) return state.cache.get(filename);
  try {
    const res = await fetch('./portal-workspace/' + encodeURIComponent(filename), { cache: 'no-store' });
    if (!res.ok) {
      const data = { name: filename, exists: false, bytes: 0, words: 0, lines: 0, mtime: null, content: '' };
      state.cache.set(filename, data);
      return data;
    }
    if (filename.endsWith('.zip')) {
      const buf = await res.arrayBuffer();
      const bytes = buf.byteLength;
      const data = { name: filename, exists: true, bytes, words: 0, lines: 0, mtime: null, content: null, isZip: true };
      state.cache.set(filename, data);
      return data;
    }
    const content = await res.text();
    const bytes = new Blob([content]).size;
    const words = content.split(/\s+/).filter(Boolean).length;
    const lines = content.split(/\n/).length;
    const mtime = res.headers.get('last-modified');
    const data = { name: filename, exists: true, bytes, words, lines, mtime, content };
    state.cache.set(filename, data);
    return data;
  } catch (e) {
    const data = { name: filename, exists: false, bytes: 0, words: 0, lines: 0, mtime: null, content: '', error: String(e) };
    state.cache.set(filename, data);
    return data;
  }
}

// ---------- Sidebar ----------
function renderSidebar(container) {
  container.innerHTML = '';
  const nav = el('nav', { 'aria-label': 'Navegación de encuestas' });
  nav.appendChild(el('div', { class: 'sidebar-title', html: '<span class="marca-linea"><span class="marca-insignia">Encuestas de Satisfacción</span></span>' }));
  const ol = el('ol', { class: 'sidebar-list portal-scrollbar' });

  PORTAL_PHASES.forEach((phase, idx) => {
    const li = el('li');
    const isActive = state.view === 'phase' && state.activePhaseId === phase.id;
    const btn = el('button', {
      class: 'sidebar-item' + (isActive ? ' active' : ''),

});
    btn.addEventListener('click', () => openPhase(phase.id));
    if (idx < PORTAL_PHASES.length - 1) {
      btn.appendChild(el('span', { class: 'sidebar-connector' }));
    }
    const badge = el('span', { class: 'sidebar-badge done', html: svg('check', 16) });
    btn.appendChild(badge);

    const content = el('span', { class: 'sidebar-content' });
    const row = el('span', { class: 'sidebar-content-row' });
    row.appendChild(el('span', { class: 'icon', style: 'color:' + (isActive ? 'var(--primary)' : 'var(--muted-foreground)'), html: svg(phase.icon, 14) }));
    row.appendChild(el('span', { class: 'phase-id', html: phase.id }));
    row.appendChild(el('span', { class: 'phase-name', html: phase.name }));
    if (phase.optional) row.appendChild(el('span', { class: 'opt', html: 'IA' }));
    content.appendChild(row);
    content.appendChild(el('span', { class: 'sidebar-role', html: phase.role }));
    btn.appendChild(content);

    li.appendChild(btn);
    ol.appendChild(li);
  });
  nav.appendChild(ol);

  nav.appendChild(el('div', { class: 'sidebar-info', html:
    svg('lock', 12) +
    '<span>Escala de satisfacción de 5 puntos · Escala de percepción de 10 puntos</span>'
  }));
  container.appendChild(nav);
}

// ---------- Artifact viewer ----------
function renderArtifactViewer(phaseId) {
  const phase = PORTAL_PHASES.find(p => p.id === phaseId);
  if (!phase) { renderPending('Item desconocido: ' + phaseId); return; }
  // Pestañas = periodos publicados del grupo de ESTE ítem (mismo criterio para todos).
  const files = window.SurveyPortalData.getPeriodosDeFase(phase.id);
  if (!state.activeFile || files.indexOf(state.activeFile) === -1) {
    state.activeFile = files[0];
  }

  // Decisión del usuario: con un solo periodo también se muestra la pestaña,
  // porque es la forma de saber a qué periodo corresponden los datos.
  const fileTabsHtml = files.length > 0 ?
    '<div class="file-tabs">' +
      files.map(f =>
        '<button class="file-tab' + (state.activeFile === f ? ' active' : '') + '"  data-file="' + f + '">' + f + '</button>'
      ).join('') +
    '</div>' : '';

  const headerHtml =
    '<div class="artifact">' +
      '<header class="artifact-header">' +
        '<div class="artifact-header-row">' +
          '<div class="sin-desborde">' +
            '<div class="artifact-breadcrumb">' +
              '<span class="artifact-phase-tag">Item ' + phase.id + '</span>' +
              svg('chevron-right', 12) +
              '<span>' + phase.role + '</span>' +
            '</div>' +
            '<h1 class="artifact-title">' +
              '<span class="texto-marca">' + svg(phase.icon, 24) + '</span>' +
              phase.fullName +
            '</h1>' +
          '</div>' +
          fileTabsHtml +
        '</div>' +
      '</header>' +
      '<div class="main-scroll portal-scrollbar panel-desplazable">' +
        '<div class="main-inner ancho-lectura" id="artifactBody">' +
          '<div class="state-box"><div class="spinner"></div><p class="texto-carga">Cargando ' + state.activeFile + '…</p></div>' +
        '</div>' +
      '</div>' +
    '</div>';

  $('mainContent').innerHTML = headerHtml;
  // Adjuntar listeners a file-tabs (CAL-05: reemplaza onclick inline)
  document.querySelectorAll('#mainContent .file-tab').forEach(function (btn) {
    btn.addEventListener('click', function () { switchFile(btn.getAttribute('data-file')); });
  });
  loadActiveFile(phase);
}

function renderUnderConstruction() {
  return '<div class="state-box caja-centrada">' +
    '<div class="aviso-construccion">' +
      '<img src="shared/img/todo-posible.webp" alt="En construcción" class="imagen-construccion">' +
      '<div class="raya-naranja"></div>' +
      '<h1 class="titulo-construccion">PÁGINA EN CONSTRUCCIÓN</h1>' +
      '<p class="texto-construccion">Esta sección está siendo desarrollada. Pronto podrás ver los resultados aquí.</p>' +
    '</div>' +
  '</div>';
}

async function loadActiveFile(phase) {
  const body = $('artifactBody');
  if (!body) return;
  const filename = state.activeFile;

  // Fases en construcción declaradas + fases cuyo dashboard todavía no tiene
  // datos publicados: ambas muestran la misma página.
  if (UNDER_CONSTRUCTION.indexOf(phase.id) !== -1 || !window.SurveyPortalData.tieneDatosDeFase(phase.id)) {
    body.innerHTML = renderUnderConstruction();
    return;
  }

  // Estudiantes Pregrado (1.0) / Graduados (1.2): dashboard completo del portal
  if (FASES_CON_DASHBOARD.indexOf(phase.id) !== -1) {
    body.innerHTML = '<div class="state-box"><div class="spinner"></div><p class="texto-carga">Cargando dashboard…</p></div>';
    await window.SurveyPortalData.initSurveyData(window.SurveyPortalData.nivelDeFase(phase.id), filename);
    if (!window.SurveyPortalData.getSurveyData()) {
      // El periodo figura en periodos.json pero sus datos no se pudieron leer
      // (carpeta/JSON ausentes). Sin este aviso la pantalla se quedaba en
      // "Cargando dashboard…" de forma indefinida.
      body.innerHTML = '<div class="state-box error">' + svg('alert-circle', 28) +
        '<p class="texto-carga">No se pudieron cargar los datos del periodo "' + escapeHtml(String(filename)) + '". Revisa que existan los archivos JSON de ese periodo.</p></div>';
      return;
    }
    window.SurveyPortalSurvey.renderSurveyView();
    return;
  }

  body.innerHTML = '<div class="state-box"><div class="spinner"></div><p class="texto-carga">Cargando ' + filename + '…</p></div>';

  const data = await fetchArtifact(filename);

  if (data.error) {
    body.innerHTML = '<div class="state-box error">' + svg('alert-circle', 28) + '<p class="texto-carga">Error al cargar: ' + escapeHtml(data.error) + '</p></div>';
    return;
  }
  if (!data.exists) {
    body.innerHTML = renderPendingArtifact(phase, filename);
    return;
  }

  const isZip = filename.endsWith('.zip');
  const sizeKb = (data.bytes / 1024).toFixed(1).replace('.', ',');
  const mtimeStr = data.mtime
    ? new Date(data.mtime).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' })
    : '';

  let metaBar = '<div class="file-meta-bar">' +
    '<span class="item filename">' + svg('file-text', 14) + data.name + '</span>';
  if (!isZip) {
    metaBar += '<span class="item">' + svg('file-type', 12) + data.words.toLocaleString('es-PE', { useGrouping: false }) + ' palabras</span>' +
      '<span class="item">' + svg('hash', 12) + data.lines.toLocaleString('es-PE', { useGrouping: false }) + ' líneas</span>';
  }
  metaBar += '<span class="item"><span class="dot"></span>' + sizeKb + ' KB</span>';
  if (mtimeStr) {
    metaBar += '<span class="item">' + svg('clock', 12) + mtimeStr + '</span>';
  }
  metaBar += '<a class="btn-download" href="./portal-workspace/' + encodeURIComponent(filename) + '" download="' + filename + '">' + svg('download', 12) + 'Descargar</a>';
  metaBar += '</div>';

  let contentHtml;
  if (isZip) {
    contentHtml = '<div class="zip-box">' +
      '<div class="zip-icono">' + svg('download', 32) + '</div>' +
      '<p class="titulo-paquete">Paquete de cambios binario</p>' +
      '<a class="btn-zip" href="./portal-workspace/' + encodeURIComponent(filename) + '" download="' + filename + '">' + svg('download', 14) + 'Descargar ' + filename + '</a>' +
    '</div>';
  } else {
    contentHtml = '<div class="portal-md">' + renderMarkdown(data.content) + '</div>';
  }

  body.innerHTML = metaBar + contentHtml +
    '<div class="postcondition">' + svg('check-circle', 16) +
      '<span>Postcondición del Item ' + phase.id + ' cumplida. Artefacto entregado conforme a la plantilla del portal v5.0.</span>' +
    '</div>';
}

function renderPendingArtifact(phase, filename) {
  return '<div class="pending-box">' +
    '<div class="pending-circle">' + svg(phase.icon, 28) + '</div>' +
    '<div>' +
      '<p class="pending-title">Item ' + phase.id + ' pendiente de ejecución</p>' +
      '<p class="pending-desc">El artefacto <code class="pending-code">' + escapeHtml(filename) + '</code> aún no ha sido generado. Este item requiere que el item anterior entregue su artefacto.</p>' +
    '</div>' +
    '<div class="pending-role"><span>Rol: </span><span class="role-name">' + phase.role + '</span></div>' +
  '</div>';
}

function renderPending(msg) {
  $('mainContent').innerHTML = '<div class="state-box"><p>' + msg + '</p></div>';
}

// ---------- Navigation ----------
function openPhase(id) {
  state.view = 'phase';
  state.activePhaseId = id;
  state.activeFile = null;
  state.mobileNavOpen = false;
  $('mobileOverlay').style.display = 'none';
  $('dashboardBtn').classList.remove('active');
  renderSidebar($('sidebarDesktop'));
  renderSidebar($('sidebarMobile'));
  renderArtifactViewer(id);
  $('mainScroll').scrollTop = 0;
}

function switchFile(filename) {
  state.activeFile = filename;
  const phase = PORTAL_PHASES.find(p => p.id === state.activePhaseId) || {};
  const nivel = window.SurveyPortalData.nivelDeFase(phase.id);
  // Solo los ítems con vista de dashboard cargan los datos del periodo elegido.
  if (nivel && FASES_CON_DASHBOARD.indexOf(phase.id) !== -1) {
    window.SurveyPortalData.initSurveyData(nivel, filename).then(() => {
      renderArtifactViewer(state.activePhaseId);
    });
    return;
  }
  renderArtifactViewer(state.activePhaseId);
}

function showDashboard() {
  state.view = 'dashboard';
  state.mobileNavOpen = false;
  $('mobileOverlay').style.display = 'none';
  $('dashboardBtn').classList.add('active');
  renderSidebar($('sidebarDesktop'));
  renderSidebar($('sidebarMobile'));
  window.SurveyPortalDashboard.renderDashboard();
  $('mainScroll').scrollTop = 0;
}

function toggleMobileNav() {
  state.mobileNavOpen = !state.mobileNavOpen;
  $('mobileOverlay').style.display = state.mobileNavOpen ? 'block' : 'none';
}

function closeMobileNav() {
  state.mobileNavOpen = false;
  $('mobileOverlay').style.display = 'none';
}

// ---------- Proceso de datos (funcion en Vercel) ----------
// El boton de refrescar hace dos cosas: pide a GitHub que procese las respuestas
// acumuladas y vuelve a leer lo publicado. La llave de GitHub vive en Vercel, no
// aqui: la pagina no guarda ni pide credenciales.
const PROCESAR_URL = 'https://qr-smoky-theta.vercel.app/api/procesar-encuesta';

function mostrarAviso(texto) {
  let aviso = document.getElementById('portalAviso');
  if (!aviso) {
    aviso = document.createElement('div');
    aviso.id = 'portalAviso';
    aviso.setAttribute('role', 'status');
    // Centrado en la pantalla (antes salia pegado al borde inferior).
    // Colores del Manual de Marca: naranja institucional con letras blancas.
    aviso.className = 'aviso-refresco';
    document.body.appendChild(aviso);
  }
  aviso.textContent = texto; // textContent: nunca se inyecta HTML
  aviso.style.display = 'block';
  clearTimeout(aviso.dataset.timer || 0);
  aviso.dataset.timer = setTimeout(() => {
    aviso.style.display = 'none';
  }, 7000);
}

async function pedirProcesamiento() {
  try {
    const respuesta = await fetch(PROCESAR_URL, { method: 'POST' });
    const datos = await respuesta.json().catch(() => null);
    mostrarAviso(
      (datos && datos.message) || (respuesta.ok ? 'Solicitud enviada.' : 'No se pudo solicitar el proceso.'),
    );
  } catch {
    mostrarAviso('Sin conexion con el servicio de procesamiento.');
  }
}

// Cada clic cuesta una peticion al servicio (que a su vez consulta a GitHub): con
// varios clics seguidos solo se gasta cuota sin adelantar nada. Se ignora el clic
// mientras hay una peticion en curso y durante unos segundos despues.
const ESPERA_ENTRE_CLICS_MS = 15000;
let peticionEnCurso = false;
let ultimaPeticion = 0;

function refresh() {
  const boton = $('refreshBtn');
  if (peticionEnCurso) {
    mostrarAviso('La solicitud anterior sigue en curso. Espera un momento.');
    return;
  }
  if (Date.now() - ultimaPeticion < ESPERA_ENTRE_CLICS_MS) {
    mostrarAviso('Acabas de pedir la actualizacion. Prueba en unos segundos.');
    return;
  }
  ultimaPeticion = Date.now();
  peticionEnCurso = true;
  if (boton) boton.disabled = true;

  state.refreshing = true;
  const icon = $('refreshIcon');
  icon.classList.add('girando');
  state.cache.clear();

  pedirProcesamiento().finally(() => {
    peticionEnCurso = false;
    if (boton) boton.disabled = false;
    setTimeout(() => {
      icon.classList.remove('girando');
      state.refreshing = false;
      if (state.view === 'dashboard') window.SurveyPortalDashboard.renderDashboard();
      else renderArtifactViewer(state.activePhaseId);
    }, 500);
  });
}

// Funciones de navegación expuestas globalmente (los file-tabs usan addEventListener, no onclick inline)
window.openPhase = openPhase;
window.switchFile = switchFile;

// ---------- Exponer estado/compartidos vía window para los módulos portal-* ----------
window.state = state;
window.svg = svg;
window.ICONS = ICONS;
window.PORTAL_PHASES = PORTAL_PHASES;
window.REPO_TARGET = REPO_TARGET;
window.escapeHtml = escapeHtml;
window.renderMarkdown = renderMarkdown;
window.$ = $;
window.el = el;

// ---------- Wire up events ----------
$('dashboardBtn').addEventListener('click', showDashboard);
$('refreshBtn').addEventListener('click', refresh);
$('hamburgerBtn').addEventListener('click', toggleMobileNav);
$('closeMobileBtn').addEventListener('click', closeMobileNav);
$('mobileOverlay').addEventListener('click', (e) => {
  if (e.target.id === 'mobileOverlay') closeMobileNav();
});

// ---------- Initial render ----------
async function init() {
  // Load initial data
  await window.SurveyPortalData.loadPeriodosDeNiveles();

  const periodo = state.activeFile || window.SurveyPortalData.getPeriodoDeFase('1.0');
  if (periodo) {
    await window.SurveyPortalData.initSurveyData(window.SurveyPortalData.nivelDeFase('1.0'), periodo);
  }
  await window.SurveyPortalData.loadGraduateData();

  renderSidebar($('sidebarDesktop'));
  renderSidebar($('sidebarMobile'));
  window.SurveyPortalDashboard.renderDashboard();

  // Footer date
  const dateStr = new Date().toLocaleDateString('es-PE', { dateStyle: 'medium' });
  const setFooter = (id, val) => { const el = $(id); if (el) el.textContent = val; };
  setFooter('footerDate', 'Generado ' + dateStr);
  const ov = getOverview();
  setFooter('footerCompleted', ov.completedCount);
  setFooter('footerTotal', ov.totalCount);
}

init();
