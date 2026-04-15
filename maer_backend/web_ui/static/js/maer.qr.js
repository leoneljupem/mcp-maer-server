/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo QR Config
   BLOQUE 15 — Exportar/importar configuración vía QR
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.qr = {

  LIB_URL: 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js',
  _libCargada: false,

  /* ── INIT ── */
  init() {
    this._renderPanel();
    MAER._log('📱 QR Config inicializado.');
  },

  /* ── EXPORTAR CONFIG → JSON STRING ── */
  exportar() {
    const cfg = {};

    try {
      const keys = ['maer_config', 'maer_compacto', 'maer_etiquetas', 'maer_timeline_etapa'];
      keys.forEach(k => {
        const v = localStorage.getItem(k);
        if (v !== null) cfg[k] = v;
      });
    } catch(e) { /* silencioso */ }

    cfg._maer_version = '4.0';
    cfg._exportado = new Date().toISOString();

    return JSON.stringify(cfg);
  },

  /* ── IMPORTAR CONFIG DESDE JSON STRING ── */
  importar(jsonStr) {
    try {
      const cfg = JSON.parse(jsonStr);
      if (!cfg._maer_version) throw new Error('No es config MAER válida');

      const skip = ['_maer_version', '_exportado'];
      let count = 0;
      Object.keys(cfg).forEach(k => {
        if (!skip.includes(k)) {
          localStorage.setItem(k, cfg[k]);
          count++;
        }
      });

      MAER._log(`📱 Config importada: ${count} claves restauradas.`);
      return { ok: true, claves: count };
    } catch(e) {
      MAER._log(`❌ Error importando config: ${e.message}`);
      return { ok: false, error: e.message };
    }
  },

  /* ── GENERAR QR (visual) ── */
  async generarQR(contenedor) {
    const el = typeof contenedor === 'string' ? document.getElementById(contenedor) : contenedor;
    if (!el) return false;

    const data = this.exportar();

    // Si los datos son muy grandes para QR, usar versión reducida
    if (data.length > 2000) {
      el.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:10px">⚠️ Config muy grande para QR. Usa exportar texto.</div>';
      return false;
    }

    // Intentar cargar librería QRCode
    if (!this._libCargada) {
      try {
        await this._cargarLib();
      } catch(e) {
        // Fallback: mostrar texto copiable
        el.innerHTML = this._fallbackTexto(data);
        return true;
      }
    }

    // Generar QR con librería
    try {
      el.innerHTML = '';
      new QRCode(el, {
        text: data,
        width: 200,
        height: 200,
        colorDark: '#07101c',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.M
      });
      return true;
    } catch(e) {
      el.innerHTML = this._fallbackTexto(data);
      return true;
    }
  },

  /* ── CARGAR LIBRERÍA QR ── */
  _cargarLib() {
    return new Promise((resolve, reject) => {
      if (typeof QRCode !== 'undefined') {
        this._libCargada = true;
        resolve();
        return;
      }
      const s = document.createElement('script');
      s.src = this.LIB_URL;
      s.onload = () => { this._libCargada = true; resolve(); };
      s.onerror = () => reject(new Error('No se pudo cargar QRCode.js'));
      document.head.appendChild(s);
    });
  },

  /* ── FALLBACK TEXTO ── */
  _fallbackTexto(data) {
    return `<div style="padding:10px">
      <div style="font-size:12px;color:var(--muted);margin-bottom:8px">📋 Copia este texto para transferir config:</div>
      <textarea id="qr-export-text" readonly style="width:100%;height:80px;font-size:11px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;resize:none">${data}</textarea>
      <button onclick="MAER.qr._copiarTexto()" style="margin-top:6px;padding:4px 12px;font-size:11px;background:var(--accent);color:#fff;border:none;border-radius:4px;cursor:pointer">Copiar</button>
    </div>`;
  },

  /* ── COPIAR TEXTO ── */
  _copiarTexto() {
    const ta = document.getElementById('qr-export-text');
    if (ta) {
      ta.select();
      document.execCommand('copy');
      MAER.voz?.hablar('Config copiada.');
    }
  },

  /* ── RENDER PANEL ── */
  _renderPanel() {
    const panel = document.getElementById('qr-panel');
    if (!panel) return;

    panel.innerHTML = `
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start">
        <div style="flex:1;min-width:200px">
          <button id="btn-qr-generar" style="padding:8px 16px;font-size:13px;background:var(--accent);color:#fff;border:none;border-radius:6px;cursor:pointer;margin-bottom:10px">📱 Generar QR Config</button>
          <div id="qr-output" style="min-height:50px"></div>
        </div>
        <div style="flex:1;min-width:200px">
          <div style="font-size:12px;color:var(--muted);margin-bottom:6px">📥 Importar configuración:</div>
          <textarea id="qr-import-text" placeholder="Pega aquí el JSON de config..." style="width:100%;height:80px;font-size:11px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;resize:none"></textarea>
          <button id="btn-qr-importar" style="margin-top:6px;padding:6px 14px;font-size:12px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:4px;cursor:pointer">📥 Importar</button>
        </div>
      </div>`;

    // Listeners
    document.getElementById('btn-qr-generar')?.addEventListener('click', () => {
      this.generarQR('qr-output');
    });

    document.getElementById('btn-qr-importar')?.addEventListener('click', () => {
      const ta = document.getElementById('qr-import-text');
      if (ta?.value?.trim()) {
        const res = this.importar(ta.value.trim());
        if (res.ok) {
          ta.value = '';
          MAER.chat?._addMsg('sys', `✅ Config importada (${res.claves} claves). Recarga la página para aplicar.`);
        } else {
          MAER.chat?._addMsg('sys', `❌ Error: ${res.error}`);
        }
      }
    });
  },

  /* ── DATOS PARA TESTS ── */
  datosExport() {
    return this.exportar();
  }
};
