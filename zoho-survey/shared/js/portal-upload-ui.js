/* ============================================================
   PORTAL UPLOAD UI - Wiring del modal de carga (Fase 3.8.2).
   Arquitectura A: PAT del usuario en runtime, solo en memoria.

   SEGURIDAD DEL PAT (critical):
   - El PAT vive UNICAMENTE en la variable de closure uploadState.token.
   - Nunca se persiste (no localStorage / no sessionStorage).
   - Nunca se escribe en el DOM (solo se lee del input al iniciar).
   - Nunca se imprime en consola ni en mensajes de error.
   - Se borra (token=null) y se limpia el input al terminar o fallar.
   ============================================================ */
(function () {
  'use strict';

  var U;
  var uploadState = {
    token: null,
    files: [],
    uploadId: null,
    releaseId: null
  };

  var els = {};
  var STATES = {
    IDLE: 'Esperando archivos',
    VALIDATING: 'Validando',
    INVALID: 'Validacion fallida',
    VALID: 'Validado',
    UPLOADING: 'Subiendo',
    QUEUED: 'En cola',
    PROCESSING: 'Procesando',
    GEN: 'Generando resultados',
    PUBLISHING: 'Publicando',
    DONE: 'Completado',
    ERROR: 'Error'
  };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }

  function showState(state, detail) {
    if (!els.status) return;
    els.status.className = 'upload-status upload-status-' + (state === STATES.ERROR ? 'error' : 'info');
    els.status.hidden = false;
    var msg = '<strong>' + esc(state) + '</strong>';
    if (detail) msg += ' - ' + esc(detail);
    els.status.innerHTML = msg;
  }

  function setFilesListUI() {
    if (!els.fileList) return;
    els.fileList.innerHTML = "";
    uploadState.files.forEach(function (f) {
      var div = document.createElement('div');
      div.className = 'upload-file-item';
      var meta = f.parsed ? esc(f.parsed.cat) + ' / ' + esc(f.parsed.nivel) + ' / ' + esc(f.parsed.periodo) : '-';
      div.innerHTML = '<div class="upload-file-name">' + esc(f.name) + '</div>' +
        '<div class="upload-file-meta">' + U.formatBytes(f.size) + ' - ' + meta + '</div>' +
        (f.errors.length ? '<div class="upload-file-errors">' + f.errors.map(esc).join('<br>') + '</div>' : '') +
        (f.warnings && f.warnings.length ? '<div class="upload-file-warnings">' + f.warnings.map(esc).join('<br>') + '</div>' : '');
      div.classList.add(f.errors.length ? 'has-error' : 'has-ok');
      els.fileList.appendChild(div);
    });
    updateSubmitButton();
  }

  function updateSubmitButton() {
    if (!els.submit || !els.token) return;
    var tokenOk = els.token.value.trim().length > 0;
    var allValid = uploadState.files.length >= 1 &&
      uploadState.files.length <= U.MAX_CSV &&
      uploadState.files.every(function (f) { return f.errors.length === 0; });
    els.submit.disabled = !(tokenOk && allValid);
    if (els.summary) {
      if (uploadState.files.length === 0) els.summary.textContent = '';
      else els.summary.innerHTML = '<strong>' + uploadState.files.length + '</strong> archivo(s) - ' +
        (allValid ? '<span class="ok">validacion OK</span>' : '<span class="err">corregir errores</span>');
    }
  }

  async function handleFiles(fileList) {
    if (!U) return;
    var files = Array.from(fileList || []);
    if (files.length === 0) return;
    if (files.length > U.MAX_CSV) {
      showState(STATES.ERROR, 'Maximo ' + U.MAX_CSV + ' archivos por carga.');
      return;
    }
    var totalSize = files.reduce(function (sum, f) { return sum + f.size; }, 0);
    if (totalSize > U.MAX_TOTAL_BYTES) {
      showState(STATES.ERROR, 'Tamaño total excede ' + U.formatBytes(U.MAX_TOTAL_BYTES));
      return;
    }
    showState(STATES.VALIDATING);
    uploadState.files = [];
    for (var i = 0; i < files.length; i++) {
      var res = await U.validateFile(files[i]);
      res.file = files[i];
      uploadState.files.push(res);
    }
    var hasErrors = uploadState.files.some(function (f) { return f.errors.length; });
    setFilesListUI();
    showState(hasErrors ? STATES.INVALID : STATES.VALID, hasErrors ? 'Corrige los errores antes de continuar.' : 'Listo para subir.');
  }

  function openModal() {
    if (els.overlay) els.overlay.hidden = false;
    if (els.token) els.token.value = "";
    uploadState.token = null;
    uploadState.files = [];
    uploadState.uploadId = null;
    uploadState.releaseId = null;
    setFilesListUI();
    showState(STATES.IDLE, 'Selecciona tus CSV y proporciona tu token.');
  }
  function closeModal() {
    if (els.overlay) els.overlay.hidden = true;
    uploadState.token = null;
    if (els.token) els.token.value = "";
  }

  async function runUpload() {
    uploadState.token = (els.token && els.token.value) ? els.token.value.trim() : '';
    if (!uploadState.token) { showState(STATES.ERROR, 'Se requiere un token de acceso.'); return; }
    if (els.token) els.token.value = '';
    if (!uploadState.files.length || uploadState.files.some(function (f) { return f.errors.length; })) {
      showState(STATES.ERROR, 'Corrige los errores antes de subir.');
      uploadState.token = null;
      return;
    }
    var repo = U.parseRepo();
    uploadState.uploadId = (crypto.randomUUID ? crypto.randomUUID() : 'su_' + Date.now());
    uploadState.releaseId = null;
    try {
      showState(STATES.UPLOADING, 'Creando Release temporal...');
      var release = await U.createRelease(repo, uploadState.token, uploadState.uploadId);
      uploadState.releaseId = release.id;
      showState(STATES.UPLOADING, 'Subiendo ' + uploadState.files.length + ' CSV(s)...');
      for (var i = 0; i < uploadState.files.length; i++) {
        await U.uploadAsset(release, uploadState.files[i].file, uploadState.token);
      }
      showState(STATES.QUEUED, 'Disparando GitHub Actions...');
      await U.dispatchWorkflow(repo, uploadState.token, uploadState.uploadId, uploadState.releaseId, uploadState.files);
      showState(STATES.PROCESSING, 'GitHub Actions esta procesando. El Release temporal se elimina automaticamente al finalizar. Puedes cerrar esta ventana.');
    } catch (err) {
      showState(STATES.ERROR, 'Fallo en la carga: ' + (err && err.message ? err.message : 'error desconocido'));
      if (uploadState.releaseId && uploadState.token) {
        try { await U.deleteRelease(repo, uploadState.token, uploadState.releaseId); } catch (_) { /* best effort */ }
      }
    } finally {
      uploadState.token = null;
      if (els.token) els.token.value = "";
    }
  }

  function wire() {
    U = window.SurveyUpload;
    els.overlay = $('uploadModalOverlay');
    els.token = $('uploadToken');
    els.dropzone = $('uploadDropzone');
    els.fileInput = $('uploadFileInput');
    els.fileList = $('uploadFileList');
    els.browse = $('uploadBrowseBtn');
    els.submit = $('uploadSubmitBtn');
    els.summary = $('uploadSummary');
    els.status = $('uploadStatus');
    els.close = $('uploadModalClose');
    var btn = $('uploadBtn');
    if (btn) btn.addEventListener("click", openModal);
    if (els.close) els.close.addEventListener("click", closeModal);
    if (els.overlay) els.overlay.addEventListener("click", function (e) { if (e.target === els.overlay) closeModal(); });
    if (els.browse) els.browse.addEventListener("click", function () { els.fileInput.click(); });
    if (els.fileInput) els.fileInput.addEventListener('change', function (e) { handleFiles(e.target.files); e.target.value = ''; });
    if (els.dropzone) {
      ['dragover', 'dragenter'].forEach(function (ev) { els.dropzone.addEventListener(ev, function (e) { e.preventDefault(); els.dropzone.classList.add('dragover'); }); });
      ['dragleave', 'drop'].forEach(function (ev) { els.dropzone.addEventListener(ev, function (e) { e.preventDefault(); els.dropzone.classList.remove('dragover'); }); });
      els.dropzone.addEventListener('drop', function (e) { handleFiles(e.dataTransfer ? e.dataTransfer.files : null); });
    }
    if (els.token) els.token.addEventListener('input', updateSubmitButton);
    if (els.submit) els.submit.addEventListener("click", runUpload);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();
})();
