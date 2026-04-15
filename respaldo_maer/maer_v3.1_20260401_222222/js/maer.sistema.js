/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo Sistema
   Estado del servidor, rendimiento, red, consola de log
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.sistema = {

  _perfInterval: null,

  /* ── REFRESH COMPLETO ── */
  async refresh() {
    await Promise.all([
      this._checkServer(),
      this._renderPerf(),
      this._renderNet(),
    ]);
  },

  /* ── VERIFICAR SERVIDOR ── */
  async _checkServer() {
    const indicator = document.getElementById('server-status');
    const label     = document.getElementById('server-label');
    const modelEl   = document.getElementById('server-model');

    if (indicator) indicator.className = 'status-dot checking';
    if (label)     label.textContent   = 'Verificando...';

    try {
      const res = await MAER._call('/api/status', null, { timeout: 5000 });
      if (res.ok || res.status === 'ok' || res.model || res.version) {
        MAER.config.backendOK = true;
        if (indicator) indicator.className = 'status-dot online';
        if (label) label.textContent = 'Servidor activo';
        if (modelEl && res.model) modelEl.textContent = `Modelo: ${res.model}`;
        MAER._log('✅ Servidor MAER conectado correctamente.');
      } else {
        this._serverOffline(indicator, label, modelEl);
      }
    } catch(e) {
      this._serverOffline(indicator, label, modelEl);
    }

    // Actualizar indicador de header
    const hdrStatus = document.getElementById('hdr-status');
    if (hdrStatus) {
      hdrStatus.textContent  = MAER.config.backendOK ? '🟢 En línea' : '🔴 Offline';
    }
  },

  _serverOffline(indicator, label, modelEl) {
    MAER.config.backendOK = false;
    if (indicator) indicator.className = 'status-dot offline';
    if (label)     label.textContent   = 'Servidor desconectado';
    if (modelEl)   modelEl.textContent = 'LLM no disponible';
    MAER._log('⚠️ Servidor no disponible. Modo offline activado.');
  },

  /* ── RENDERIZAR NAVEGADOR (INFO) ── */
  _renderBrowser() {
    const el = document.getElementById('sys-browser');
    if (!el) return;
    const ua = navigator.userAgent;
    let browser = 'Desconocido';
    if (ua.includes('Chrome'))  browser = 'Google Chrome';
    else if (ua.includes('Firefox')) browser = 'Mozilla Firefox';
    else if (ua.includes('Safari'))  browser = 'Safari';
    else if (ua.includes('Edge'))    browser = 'Microsoft Edge';

    el.innerHTML = `
      <div class="sys-info-grid">
        ${this._infoRow('Navegador',    browser)}
        ${this._infoRow('Plataforma',   navigator.platform || 'Desconocido')}
        ${this._infoRow('Idioma',       navigator.language || 'es-MX')}
        ${this._infoRow('Pantalla',     `${screen.width}×${screen.height}`)}
        ${this._infoRow('Ventana',      `${window.innerWidth}×${window.innerHeight}`)}
        ${this._infoRow('Conexión',     navigator.onLine ? '🟢 En línea' : '🔴 Sin conexión')}
        ${this._infoRow('Cookies',      navigator.cookieEnabled ? '✅ Habilitadas' : '❌ Deshabilitadas')}
        ${this._infoRow('IndexedDB',    typeof indexedDB !== 'undefined' ? '✅ Disponible' : '❌ No disponible')}
        ${this._infoRow('SpeechSynth',  typeof SpeechSynthesisUtterance !== 'undefined' ? '✅ Disponible' : '❌ No disponible')}
        ${this._infoRow('SpeechRecog',  (typeof SpeechRecognition !== 'undefined' || typeof webkitSpeechRecognition !== 'undefined') ? '✅ Disponible' : '❌ No disponible')}
      </div>`;
  },

  /* ── RENDERIZAR RENDIMIENTO ── */
  _renderPerf() {
    const el = document.getElementById('sys-perf');
    if (!el) return;

    const mem = performance.memory || null;
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    const lsSize = this._localStorageSize();

    el.innerHTML = `
      <div class="sys-info-grid">
        ${mem ? this._infoRow('Mem JS usada',   this._fmtBytes(mem.usedJSHeapSize)) : ''}
        ${mem ? this._infoRow('Mem JS total',   this._fmtBytes(mem.totalJSHeapSize)) : ''}
        ${mem ? this._infoRow('Mem JS límite',  this._fmtBytes(mem.jsHeapSizeLimit)) : ''}
        ${this._infoRow('localStorage',        this._fmtBytes(lsSize))}
        ${this._infoRow('Historial msgs',       hist.length + ' entradas')}
        ${this._infoRow('API URL',              MAER.API)}
        ${this._infoRow('MAER versión',         MAER.version)}
        ${this._infoRow('Backend OK',           MAER.config.backendOK ? '✅ Sí' : '❌ No')}
      </div>`;
  },

  /* ── RENDERIZAR RED ── */
  _renderNet() {
    const el = document.getElementById('sys-net');
    if (!el) return;
    const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection || null;

    el.innerHTML = `
      <div class="sys-info-grid">
        ${this._infoRow('Estado red',      navigator.onLine ? '🟢 Conectado' : '🔴 Sin red')}
        ${conn ? this._infoRow('Tipo conexión', conn.effectiveType || 'desconocido') : ''}
        ${conn ? this._infoRow('Velocidad DL',  conn.downlink ? conn.downlink + ' Mbps' : 'desconocida') : ''}
        ${conn ? this._infoRow('RTT',           conn.rtt ? conn.rtt + ' ms' : 'desconocido') : ''}
        ${this._infoRow('Servidor MAER',   MAER.API)}
      </div>
      <div style="margin-top:12px">
        <button class="btn btn-secondary btn-sm" onclick="MAER.sistema.testConexion()">🔌 Probar conexión</button>
        <span id="ping-result" style="margin-left:10px;font-size:12px;color:var(--muted)"></span>
      </div>`;
  },

  /* ── TEST PING ── */
  async testConexion() {
    const el = document.getElementById('ping-result');
    if (el) el.textContent = 'Probando...';
    const t0 = Date.now();
    try {
      const res = await MAER._call('/api/status', null, { timeout: 5000 });
      const ms = Date.now() - t0;
      if (el) el.textContent = `✅ ${ms}ms — Servidor activo`;
      MAER._log(`🔌 Ping al servidor: ${ms}ms`);
    } catch(e) {
      if (el) el.textContent = '❌ Sin respuesta';
      MAER._log('❌ Sin respuesta del servidor.');
    }
  },

  /* ── LIMPIAR CONSOLA ── */
  limpiarConsola() {
    const c = document.getElementById('sys-console');
    if (c) c.innerHTML = '<span style="color:var(--muted)">Consola limpiada.</span><br>';
  },

  /* ── CREAR RESPALDO ── */
  async crearRespaldo() {
    const btn = document.getElementById('btn-respaldo');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Creando respaldo...'; }

    try {
      const res = await MAER._call('/api/backup', null, { timeout: 30000 });
      if (res.ok) {
        MAER.chat._addMsg('sys', `💾 Respaldo creado: <strong>${res.data?.ruta || 'respaldo_maer/'}</strong>`);
        MAER.voz.hablar('Respaldo creado correctamente.');
        MAER._log(`💾 Respaldo: ${res.data?.ruta || 'completado'}`);
      } else {
        MAER.chat._addMsg('sys', `⚠️ Respaldo: ${res.msg || 'Error desconocido'}`);
      }
    } catch(e) {
      // Fallback: exportar datos locales como JSON
      const data = {
        config:     MAER.config,
        historial:  JSON.parse(localStorage.getItem('maer_history') || '[]'),
        aprendidos: JSON.parse(localStorage.getItem('maer_learned') || '[]'),
        eventos:    JSON.parse(localStorage.getItem('maer_eventos') || '[]'),
        notas:      localStorage.getItem('maer_pension_notas') || '',
        fecha:      new Date().toISOString(),
      };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `respaldo_maer_${Date.now()}.json`;
      a.click();
      MAER.chat._addMsg('sys', '💾 Respaldo local exportado como JSON (servidor no disponible).');
      MAER.voz.hablar('Respaldo exportado localmente.');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '💾 Crear Respaldo'; }
    }
  },

  /* ── HELPERS ── */
  _infoRow(label, val) {
    return `<div class="sys-info-row">
      <span style="color:var(--muted);font-size:12px">${label}</span>
      <span style="color:var(--text);font-size:12px;font-weight:500;text-align:right">${val || '—'}</span>
    </div>`;
  },

  _fmtBytes(b) {
    if (!b) return '—';
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
    return (b/1048576).toFixed(1) + ' MB';
  },

  _localStorageSize() {
    let total = 0;
    for (const key of Object.keys(localStorage)) {
      total += (localStorage.getItem(key) || '').length * 2; // UTF-16
    }
    return total;
  },
};
