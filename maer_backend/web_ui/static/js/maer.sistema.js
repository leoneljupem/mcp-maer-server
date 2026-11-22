/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo Sistema
   Estado del servidor, rendimiento, red, consola de log
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.sistema = {

  _perfInterval: null,

  /* ── CERRAR SESIÓN ── */
  logout() {
    document.cookie = "maer_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    try { sessionStorage.clear(); } catch (e) {}
    window.location.href = '/static/login.html';
  },

  /* ── REFRESH COMPLETO ── */
  async refresh() {
    await Promise.all([
      this._checkServer(),
      this._renderPerf(),
      this._renderNet(),
      this._renderLLM(),
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
      hdrStatus.textContent  = MAER.config.backendOK ? '🟢 En línea' : '🔴 Sin conexión';
    }
  },

  _serverOffline(indicator, label, modelEl) {
    MAER.config.backendOK = false;
    if (indicator) indicator.className = 'status-dot offline';
    if (label)     label.textContent   = 'Servidor desconectado';
    if (modelEl)   modelEl.textContent = 'LLM no disponible';
    MAER._log('⚠️ Servidor no disponible. Modo offline activado.');
  },

  /* ── RENDERIZAR ESTADO LLM ── */
  async _renderLLM() {
    const el = document.getElementById('sys-llm');
    if (!el) return;
    el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:10px">🔍 Consultando motores LLM…</div>';
    try {
      const res = await MAER._call('/api/llm-status', null, { timeout: 8000 });
      const d = res.data || {};
      const ollama = d.ollama || {};
      const groq   = d.groq   || {};
      const openai = d.openai || {};

      const motorTag = (nombre, ok) =>
        `<span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;background:${ok ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.12)'};color:${ok ? '#34d399' : '#f87171'};border:1px solid ${ok ? 'rgba(52,211,153,0.35)' : 'rgba(248,113,113,0.3)'}">${ok ? '🟢' : '🔴'} ${nombre}</span>`;

      el.innerHTML = `
        <div style="margin-bottom:14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          ${motorTag('Ollama', ollama.disponible)}
          ${motorTag('Groq', groq.disponible)}
          ${motorTag('OpenAI', openai.disponible)}
          <span style="margin-left:auto;font-size:11px;color:var(--muted)">Motor activo: <strong style="color:var(--accent)">${d.motor_recomendado || '—'}</strong></span>
        </div>

        <div class="sys-info-grid">
          <div class="sys-info-row"><span class="sys-info-label">🦙 Ollama estado</span><span class="sys-info-val">${ollama.disponible ? '✅ Activo' : '❌ No disponible'}</span></div>
          ${ollama.modelo_activo ? `<div class="sys-info-row"><span class="sys-info-label">Modelo activo</span><span class="sys-info-val" style="color:var(--accent)">${ollama.modelo_activo}</span></div>` : ''}
          ${ollama.total_modelos ? `<div class="sys-info-row"><span class="sys-info-label">Modelos instalados</span><span class="sys-info-val">${ollama.total_modelos}</span></div>` : ''}
          ${(ollama.modelos || []).length > 0 ? `
          <div class="sys-info-row"><span class="sys-info-label">Lista modelos</span><span class="sys-info-val" style="font-size:11px">${ollama.modelos.slice(0,6).join(' · ')}</span></div>` : ''}

          <div class="sys-info-row" style="margin-top:6px"><span class="sys-info-label">⚡ Groq estado</span><span class="sys-info-val">${groq.disponible ? '✅ Listo' : groq.clave_configurada ? '⚠️ SDK faltante' : '🔑 Sin clave API'}</span></div>
          <div class="sys-info-row"><span class="sys-info-label">Modelo Groq</span><span class="sys-info-val">${groq.modelo || '—'}</span></div>
          ${!groq.clave_configurada ? `<div class="sys-info-row"><span class="sys-info-label" style="color:#fb923c">Cómo activar Groq</span><span class="sys-info-val" style="font-size:11px">Regístrate gratis en console.groq.com → copia tu API key → pégala en .env como GROQ_API_KEY=sk-...</span></div>` : ''}

          <div class="sys-info-row" style="margin-top:6px"><span class="sys-info-label">🤖 OpenAI estado</span><span class="sys-info-val">${openai.disponible ? '✅ Configurado' : '⚪ No configurado'}</span></div>
          <div class="sys-info-row"><span class="sys-info-label">Modelo OpenAI</span><span class="sys-info-val">${openai.modelo || '—'}</span></div>
        </div>

        <div style="margin-top:10px;padding:8px 12px;background:var(--bg);border-radius:8px;font-size:11px;color:var(--muted)">
          ℹ️ Prioridad: Ollama (local, gratis) → Groq (nube gratuita) → OpenAI → Diccionario IMSS
        </div>`;
    } catch(e) {
      el.innerHTML = `<div class="alert alert-warning">⚠️ No se pudo obtener estado LLM — el servidor debe estar activo (python -m maer_backend.web_ui.server)</div>`;
    }
  },

  /* ── PROBAR OLLAMA ── */
  async _probarOllama() {
    const el = document.getElementById('sys-llm-test');
    if (el) el.textContent = '🦙 Probando Ollama con pregunta de prueba…';
    try {
      const res = await MAER._call('/api/llm-chat', {
        prompt: '¿Qué es el IMSS en una sola oración?',
        motor: 'ollama',
      }, { timeout: 60000 });
      const txt = res.data?.respuesta || res.text || JSON.stringify(res).substring(0, 200);
      if (el) el.innerHTML = `<strong style="color:#34d399">✅ Ollama respondió:</strong><br>${txt.substring(0,300)}`;
    } catch(e) {
      if (el) el.innerHTML = `<span style="color:#f87171">❌ Ollama no disponible: ${e.message}</span>`;
    }
  },

  /* ── PROBAR GROQ ── */
  async _probarGroq() {
    const el = document.getElementById('sys-llm-test');
    if (el) el.textContent = '⚡ Probando Groq con pregunta de prueba…';
    try {
      const res = await MAER._call('/api/llm-chat', {
        prompt: '¿Qué es el IMSS en una sola oración?',
        motor: 'groq',
      }, { timeout: 30000 });
      const txt = res.data?.respuesta || res.text || JSON.stringify(res).substring(0, 200);
      if (el) el.innerHTML = `<strong style="color:#34d399">✅ Groq respondió:</strong><br>${txt.substring(0,300)}`;
    } catch(e) {
      if (el) el.innerHTML = `<span style="color:#f87171">❌ Groq no disponible: ${e.message}</span>`;
    }
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

  /* ── TASKER: CARGAR URL DEL SERVIDOR ── */
  async _cargarUrlTasker() {
    const input = document.getElementById('tasker-url-display');
    if (!input) return;
    try {
      const res = await MAER._call('/api/server-info', null, { timeout: 5000 });
      if (res.ok && res.data) {
        const d = res.data;
        // Preferir URL ngrok si existe
        input.value = d.tasker_url || `http://${d.ip_local}:${d.puerto}/api/tasker-receive`;
        // Mostrar badge ngrok si está activo
        const badge = document.getElementById('tasker-ngrok-badge');
        if (badge) {
          badge.style.display = d.url_ngrok ? 'inline' : 'none';
          badge.textContent = d.url_ngrok ? `🌐 ngrok activo: ${d.url_ngrok}` : '';
        }
        MAER._log(`📱 URL Tasker detectada: ${input.value}`);
      }
    } catch(e) {
      // Mantener localhost como fallback si el servidor no responde
    }
  },

  /* ── TASKER: VER MENSAJES ── */
  async _checkTasker() {
    const el = document.getElementById('sys-tasker-msgs');
    if (!el) return;
    if (!MAER.config.backendOK) {
      el.innerHTML = '<div style="color:var(--muted);font-size:13px">Servidor no disponible. Los mensajes Tasker se guardan cuando el servidor esté activo.</div>';
      return;
    }
    try {
      const res = await MAER._call('/api/tasker-messages', null, { timeout: 5000 });
      const msgs = res.data?.mensajes || [];
      if (!msgs.length) {
        el.innerHTML = '<div style="color:var(--muted);font-size:13px">Sin mensajes Tasker todavía. Configura Tasker con la URL del servidor.</div>';
        return;
      }
      el.innerHTML = msgs.slice().reverse().map(m => `
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px 12px;margin-bottom:6px;display:flex;gap:10px;align-items:flex-start">
          <span style="font-size:18px;flex-shrink:0">📱</span>
          <div style="flex:1">
            <div style="font-size:11px;color:var(--muted);margin-bottom:3px">${m.ts || ''} · ${m.fuente || 'tasker'} · ${m.device || ''}</div>
            <div style="font-size:13px;color:var(--text)">${String(m.mensaje||'').substring(0,200)}</div>
          </div>
        </div>`).join('');
    } catch(e) {
      el.innerHTML = `<div class="alert alert-warning">Error obteniendo mensajes: ${e.message}</div>`;
    }
  },

  async _enviarPruebaTasker() {
    try {
      const res = await MAER._call('/api/tasker-receive', {
        mensaje:    'MAER prueba de conexión exitosa.',
        fuente:     'maer_ui',
        dispositivo: 'panel_sistema',
      });
      if (res.ok) {
        MAER.chat._addMsg('sys', '📱 Prueba Tasker enviada correctamente al servidor.');
        MAER.voz?.hablar('Prueba de Tasker enviada.');
        await this._checkTasker();
      }
    } catch(e) {
      alert(`Error: ${e.message}`);
    }
  },

  /* ── CREAR RESPALDO ── */
  async crearRespaldo() {
    const btn = document.getElementById('btn-respaldo');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Creando respaldo...'; }

    try {
      const res = await MAER._call('/api/backup', null, { timeout: 30000 });
      if (res.ok) {
        MAER.chat._addMsg('sys', `💾 Respaldo creado: <strong>${res.data?.ruta || 'respaldo_maer/'}</strong>`);
        MAER.voz?.hablar('Respaldo creado correctamente.');
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
      MAER.voz?.hablar('Respaldo exportado localmente.');
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

  /* ── SISTEMA DE EVOLUCIÓN (PLUGINS) ── */
  async loadPlugin() {
    const input = document.getElementById('plugin-input');
    const status = document.getElementById('plugin-status');
    if (!input.files.length) return alert('Selecciona un archivo .py o .js');
    
    const file = input.files[0];
    status.textContent = `⏳ Cargando evolución: ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await MAER._upload('/api/load-plugin', formData);
      if (res.ok) {
        status.innerHTML = `<span style="color:#34d399">✅ MAER Evolucionó: ${file.name} integrado.</span>`;
        MAER._log(`🧬 Evolución: Módulo ${file.name} cargado.`);
        MAER.voz?.hablar('Sistema evolucionado correctamente.');
      } else {
        status.innerHTML = `<span style="color:#f87171">❌ Falló: ${res.msg}</span>`;
      }
    } catch(e) {
      status.textContent = '❌ Error de conexión.';
    }
  },

  /* ── AUTO-REPARACIÓN MAESTRA ── */
  async repararMaestro() {
    MAER._log('🔧 Iniciando Auto-Reparación Maestra...');
    try {
      const res = await MAER._call('/api/force-repair');
      if (res.ok) {
        MAER._log('✅ Reparación exitosa. Reiniciando UI...');
        alert('Reparación completada. Se recargará la página.');
        location.reload();
      } else {
        MAER._log('❌ Error en reparación: ' + res.msg);
      }
    } catch(e) {
      MAER._log('❌ No se pudo contactar al motor de reparación.');
    }
  }
};

