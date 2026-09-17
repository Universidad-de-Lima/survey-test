/**
 * Bridge script for local development mode.
 * This file runs FIRST and intercepts the upload button logic
 * before the rest of the portal loads.
 */
(function () {
  'use strict';

  var IS_LOCAL = (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  );

  if (!IS_LOCAL) return;

  // ============================================================
  // Override window.SurveyUpload to use LOCAL API only
  // ============================================================
  var LOCAL_API_BASE = '/api';

  var SurveyUploadOverride = {
    MAX_CSV: 10,
    MAX_FILE_BYTES: 5 * 1024 * 1024,
    MAX_TOTAL_BYTES: 50 * 1024 * 1024,
    PERIODICIDAD: {},
    parseFilename: function(n){ return {ok:false,error:'parse disabled in local'}; },
    detectNivel: function(){ return null; },
    requiredHeaders: function(){ return []; },
    validateFile: function(f){
      return Promise.resolve().then(function(){
        if (f.size > 5*1024*1024) return {ok:false,errors:['Excede 5MB']};
        return {ok:true, warnings:[]};
      });
    },
    formatBytes: function(b){
      if(b>=1024*1024) return (b/1024/1024).toFixed(1)+' MB';
      if(b>=1024) return (b/1024).toFixed(1)+' KB';
      return b+' B';
    },
    computeSHA256: function(f){
      return f.arrayBuffer().then(function(buf){
        return crypto.subtle.digest('SHA-256', buf).then(function(digest){
          var arr = Array.from(new Uint8Array(digest));
          return arr.map(function(b){return b.toString(16).padStart(2,'0');}).join('');
        });
      });
    },

    /** Main upload entry point for local mode */
    uploadToServer: function(files, progressCb) {
      var formData = new FormData();
      files.forEach(function(file){
        formData.append('files', file);
      });

      return fetch(LOCAL_API_BASE + '/upload', {
        method: 'POST',
        body: formData
      }).then(function(res){
        if(!res.ok){
          return res.text().then(function(txt){ throw new Error('API error '+res.status+': '+txt.slice(0,300)); });
        }
        return res.json();
      }).then(function(data){
        progressCb({status:'accepted', message:data.message});
        return data.job_id;
      });
    },

    checkJobStatus: function(jobId, statusCb) {
      var interval = setInterval(function(){
        fetch(LOCAL_API_BASE + '/jobs/' + jobId)
          .then(function(res){
            if(!res.ok) throw new Error('Failed to get job status');
            return res.json();
          })
          .then(function(data){
            statusCb(data);
            if(data.status === 'completed' || data.status === 'failed'){
              clearInterval(interval);
            }
          })
          .catch(function(){
            clearInterval(interval);
          });
      }, 2000);
    }
  };

  // Replace global reference BEFORE portal-upload-ui runs
  window.SurveyUpload = SurveyUploadOverride;
  window.SurveyUpload.useLocalMode = true;

})();
