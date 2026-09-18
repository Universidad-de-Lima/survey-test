/* ============================================================
   PORTAL UPLOAD — Validacion y carga de encuestas (Fase 3.8.2/3.8.3).
   Arquitectura A: GitHub-native + PAT del usuario en runtime.
   PAT en closure JS unicamente; nunca se persiste ni imprime.
   ============================================================ */
(function () {
  'use strict';

  var MAX_CSV = 10;
  var MAX_FILE_BYTES = 5 * 1024 * 1024;
  var MAX_TOTAL_BYTES = 50 * 1024 * 1024;

  var CATEGORIES = [
    'ESTUDIANTIL', 'GRADUADOS', 'POSGRADO', 'DOCENTES', 'DOCENTE',
    'EGRESADOS', 'EMPLEADORES'
  ];
  var NO_DOCENTE = 'NO DOCENTES';

  var PERIODICIDAD = {
    'ESTUDIANTIL': 'semestral',
    'GRADUADOS': 'anual',
    'POSGRADO': 'anual',
    'DOCENTES': 'anual',
    'EGRESADOS': 'anual',
    'NO DOCENTES': 'anual',
    'EMPLEADORES': 'anual'
  };

  // Columna carrera/programa/dependencia por encuesta EXACTA.
  var CARRERA_HEADER = {
    'ESTUDIANTIL|PREGRADO': '\u00bfQu\u00e9 carrera profesional estudias?',
    'ESTUDIANTIL|POSGRADO': '\u00bfQu\u00e9 programa de posgrado estudias?',
    'GRADUADOS|PREGRADO':   '\u00bfQu\u00e9 carrera profesional estudiaste?',
    'EGRESADOS|PREGRADO':   '\u00bfQu\u00e9 carrera profesional estudiaste?',
    'EGRESADOS|POSGRADO':   '\u00bfQu\u00e9 programa de posgrado estudiaste?',
    'DOCENTES|PREGRADO':    '\u00bfQu\u00e9 carrera o programa dedicas la mayor cantidad de horas en la Universidad de Lima?',
    'DOCENTES|POSGRADO':    '\u00bfQu\u00e9 programa de posgrado dictas en la Universidad de Lima?',
    'NO DOCENTES|':         '\u00bfA qu\u00e9 dependencia perteneces?',
    'EMPLEADORES|PREGRADO': '\u00bfQu\u00e9 carrera es la que procede el profesional de la Universidad de Lima contratado por su organizaci\u00f3n?',
    'EMPLEADORES|POSGRADO': '\u00bfCu\u00e1l posgrado es el que procede el profesional de la Universidad de Lima contratado por su organizaci\u00f3n?'
  };

  function detectNivel(name) {
    var up = String(name).toUpperCase();
    if (up.indexOf('NO DOCENTE') !== -1) return 'nonfaculty';
    if (up.indexOf('EMPLEADORES') !== -1) return 'employers';
    if (up.indexOf('EGRESADOS') !== -1) return up.indexOf('POSGRADO') !== -1 ? 'alumni-pg' : 'alumni-ug';
    if (up.indexOf('DOCENTE') !== -1) return up.indexOf('POSGRADO') !== -1 ? 'faculty-pg' : 'faculty-ug';
    if (up.indexOf('GRADUADOS') !== -1) return 'graduate';
    if (up.indexOf('ESTUDIANTIL') !== -1 || up.indexOf('ESTUDIANTES') !== -1)
      return up.indexOf('POSGRADO') !== -1 ? 'postgraduate' : 'undergraduate';
    return null;
  }

  function requiredHeaders(categoria, nivelRaw) {
    var base = ['ID de respuesta', 'Net Promoter Score (de un total de 10)'];
    var key = categoria + '|' + (nivelRaw || '');
    var extra = CARRERA_HEADER[key];
    if (extra) base.push(extra);
    return base;
  }

  function formatBytes(bytes) {
    if (bytes >= 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB';
    if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return bytes + ' B';
  }

  function computeSHA256(file) {
    return file.arrayBuffer().then(function (buf) {
      return crypto.subtle.digest('SHA-256', buf).then(function (digest) {
        var arr = Array.from(new Uint8Array(digest));
        return arr.map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      });
    });
  }

  function readHeaders(file) {
    return new Promise(function (resolve) {
      var reader = new FileReader();
      reader.onload = function () {
        try {
          var bytes = new Uint8Array(reader.result);
          var text = new TextDecoder('utf-8').decode(bytes);
          if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
          if (text.indexOf('\uFFFD') !== -1) {
            text = new TextDecoder('latin-1').decode(bytes);
            if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
          }
          var nl = text.indexOf('\n');
          var firstLine = (nl >= 0 ? text.slice(0, nl) : text).replace(/\r$/, '');
          resolve(parseCsvLine(firstLine));
        } catch (e) {
          resolve([]);
        }
      };
      reader.onerror = function () { resolve([]); };
      reader.readAsArrayBuffer(file.slice(0, 65536));
    });
  }

  function parseCsvLine(line) {
    var out = [], cur = '', inQ = false;
    for (var i = 0; i < line.length; i++) {
      var ch = line[i];
      if (inQ) {
        if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
        else if (ch === '"') inQ = false;
        else cur += ch;
      } else {
        if (ch === '"') inQ = true;
        else if (ch === ',') { out.push(cur.trim()); cur = ''; }
        else cur += ch;
      }
    }
    out.push(cur.trim());
    return out;
  }

  // Parser tolerante: separadores espacio/guion equivalentes;
  // periodo extraido con regex (no se parte 20XX-1).
  function parseFilename(name) {
    var low = String(name).toLowerCase();
    if (low.indexOf('encuesta de satisfacci') === -1)
      return { ok: false, error: 'Nombre no inicia con ENCUESTA DE SATISFACCION' };
    if (!low.endsWith('.csv'))
      return { ok: false, error: 'Extension no es .csv' };

    var body = name.slice(0, -4);
    var pm = body.match(/(20\d{2}(?:-[12])?)/);
    var periodo = pm ? pm[1] : null;
    var bodyNop = periodo ? body.replace(periodo, '') : body;

    var tokens = bodyNop.split(/[\s\-]+/).filter(function (t) { return t.length > 0; });
    var i = 0;
    while (i < tokens.length && CATEGORIES.indexOf(tokens[i].toUpperCase()) === -1 && tokens[i].toUpperCase() !== 'NO') i++;
    if (i >= tokens.length) return { ok: false, error: 'No se encontro categoria en el nombre' };

    var tok = tokens[i].toUpperCase();
    var categoria;
    if (tok === 'NO') {
      if (i + 1 < tokens.length && tokens[i + 1].toUpperCase().indexOf('DOCENTE') === 0) {
        categoria = NO_DOCENTE; i += 2;
      } else return { ok: false, error: 'NO sin DOCENTE/DOCENTES' };
    } else {
      categoria = (tok === 'DOCENTE') ? 'DOCENTES' : tok;
      i++;
    }

    var nivelRaw = null;
    if (i < tokens.length && (tokens[i].toUpperCase() === 'PREGRADO' || tokens[i].toUpperCase() === 'POSGRADO')) {
      nivelRaw = tokens[i].toUpperCase();
      i++;
    }
    if (categoria === NO_DOCENTE && nivelRaw)
      return { ok: false, error: 'NO DOCENTE no debe llevar nivel', categoria: categoria, nivelRaw: nivelRaw };
    if (categoria !== NO_DOCENTE && !nivelRaw)
      return { ok: false, error: 'Falta nivel (PREGRADO/POSGRADO) en ' + categoria, categoria: categoria };
    if (i < tokens.length)
      return { ok: false, error: 'Elemento inesperado: ' + tokens[i], categoria: categoria, nivelRaw: nivelRaw, periodo: periodo };
    return { ok: true, categoria: categoria, nivelRaw: nivelRaw, periodo: periodo };
  }

  function validateFile(file) {
    return Promise.resolve().then(function () {
      var result = { name: file.name, size: file.size, ok: false, errors: [], warnings: [], parsed: null };
      if (file.size > MAX_FILE_BYTES) {
        result.errors.push('Tama\u00f1o excede 5 MB');
        return result;
      }
      var parsed = parseFilename(file.name);
      if (parsed.error) {
        result.errors.push(parsed.error);
        return result;
      }
      var nivel = detectNivel(file.name);
      result.parsed = { cat: parsed.categoria, nivel: nivel, nivelRaw: parsed.nivelRaw, periodo: parsed.periodo };
      return readHeaders(file).then(function (headers) {
        if (!headers.length) {
          result.errors.push('No se pudieron leer cabeceras (encoding?)');
          return result;
        }
        var req = requiredHeaders(parsed.categoria, parsed.nivelRaw);
        var missing = req.filter(function (h) { return headers.indexOf(h) === -1; });
        if (missing.length) {
          result.errors.push('Faltan columnas requeridas: ' + missing.join(', '));
          return result;
        }
        var seen = {};
        var dupes = [];
        for (var k = 0; k < headers.length; k++) {
          if (seen[headers[k]]) dupes.push(headers[k]);
          seen[headers[k]] = true;
        }
        if (dupes.length) result.warnings.push('Cabeceras duplicadas: ' + dupes.join(', '));
        result.ok = true;
        return result;
      });
    });
  }

  function ghFetch(repo, endpoint, token, method, body) {
    var url = 'https://api.github.com/repos/' + repo + '/' + endpoint;
    var headers = { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json' };
    if (body) headers['Content-Type'] = 'application/json';
    return fetch(url, {
      method: method, headers: headers,
      body: body ? JSON.stringify(body) : undefined
    }).then(function (res) {
      if (!res.ok) {
        return res.text().then(function (txt) {
          throw new Error('GitHub API ' + res.status + ': ' + txt.slice(0, 300));
        });
      }
      return res.json();
    });
  }

  function uploadToServer(files, token) {
    return Promise.resolve().then(function () {
      var uploadId = (crypto.randomUUID ? crypto.randomUUID() : 'su_' + Date.now());
      var repo = parseRepo();

      // Regla del proyecto: el flujo es SIEMPRE GitHub (Release DRAFT temporal
      // + repository_dispatch). No hay servidor local ni modo de desarrollo
      // local, por lo que no existe rama alternativa.
      return createRelease(repo, token, uploadId).then(function (release) {
        var releaseId = release.id;
        return Promise.all(files.map(function (file) {
          return uploadAsset(release, file, token);
        })).then(function () {
          return dispatchWorkflow(repo, token, uploadId, releaseId, files);
        });
      });
    });
  }

  function checkJobStatus(jobId) {
    // No hay servidor propio: el estado del job solo existe en GitHub Actions,
    // que se supervisa en la pestaña Actions del repositorio.
    return Promise.resolve({ status: 'unknown', message: 'El estado del job no está disponible en el cliente. Verifica GitHub Actions.', output_files: [] });
  }

  function parseRepo() {
    var host = window.location.hostname;
    var path = window.location.pathname || '';
    var parts = path.split('/').filter(function (s) { return s; });
    // GitHub Pages: <owner>.github.io/<repo>
    var m = host.match(/^([^.]+)\.github\.io$/);
    if (m) {
      return m[1] + '/' + (parts[0] || 'survey-test');
    }
    // Fallback: repositorio canónico del proyecto.
    return 'Universidad-de-Lima/survey-test';
  }

  function createRelease(repo, token, uploadId) {
    return ghFetch(repo, 'releases', token, 'POST', {
      tag_name: 'csv-upload-' + uploadId,
      name: 'CSV Upload ' + uploadId,
      draft: true, prerelease: true,
      body: 'Release temporal para upload_id=' + uploadId
    });
  }

  function deleteRelease(repo, token, releaseId) {
    return fetch('https://api.github.com/repos/' + repo + '/releases/' + releaseId, {
      method: 'DELETE',
      headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json' }
    }).then(function (res) {
      if (!res.ok) throw new Error('Delete release failed ' + res.status);
      return { ok: true };
    });
  }

  function uploadAsset(release, file, token) {
    var url = (release.upload_url || '').replace(/\{\?[^}]+\}$/, '');
    if (url.indexOf('?') === -1) url += '?name=' + encodeURIComponent(file.name);
    else url += '&name=' + encodeURIComponent(file.name);
    return fetch(url, {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'text/csv', 'Content-Length': file.size },
      body: file
    }).then(function (res) {
      if (!res.ok) {
        return res.text().then(function (t) {
          throw new Error('Upload failed ' + res.status + ': ' + t.slice(0, 200));
        });
      }
      return res.json();
    });
  }

  function dispatchWorkflow(repo, token, uploadId, releaseId, files) {
    var payload = {
      upload_id: uploadId,
      release_id: releaseId,
      files: files.map(function (f) {
        return {
          name: f.name, sha256: f.sha256, size: f.size,
          category: f.parsed ? f.parsed.cat : null,
          level: f.parsed ? f.parsed.nivel : null,
          period: f.parsed ? f.parsed.periodo : null
        };
      })
    };
    return ghFetch(repo, 'dispatches', token, 'POST', {
      event_type: 'csv_upload',
      client_payload: payload
    }).then(function () { return payload; });
  }

  window.SurveyUpload = {
    MAX_CSV: MAX_CSV,
    MAX_FILE_BYTES: MAX_FILE_BYTES,
    MAX_TOTAL_BYTES: MAX_TOTAL_BYTES,
    PERIODICIDAD: PERIODICIDAD,
    parseFilename: parseFilename,
    detectNivel: detectNivel,
    requiredHeaders: requiredHeaders,
    validateFile: validateFile,
    formatBytes: formatBytes,
    computeSHA256: computeSHA256,
    createRelease: createRelease,
    deleteRelease: deleteRelease,
    uploadAsset: uploadAsset,
    dispatchWorkflow: dispatchWorkflow,
    parseRepo: parseRepo,
    uploadToServer: uploadToServer,
    checkJobStatus: checkJobStatus
  };
})();
