// 🦁 MAER — Módulo QR
MAER.qr = {
  init() {
    this._renderPanel();
  },

  _renderPanel() {
    const panel = document.getElementById('qr-panel');
    if (!panel) return;
    panel.innerHTML = `
      <div style="font-size:12px;color:var(--muted);margin-bottom:10px">Genera un QR con la URL del servidor para acceder desde tu celular.</div>
      <button class="btn btn-secondary btn-sm" onclick="MAER.qr.generar()">📱 Generar QR de acceso</button>
      <div id="qr-output" style="margin-top:10px"></div>`;
  },

  async generar() {
    const r = await MAER._call('/api/server-info');
    const url = r.ok ? (r.data?.url_local || r.data?.url_ngrok || MAER.API) : MAER.API;
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(url)}`;
    const out = document.getElementById('qr-output');
    if (out) out.innerHTML = `
      <img src="${qrUrl}" alt="QR MAER" style="border-radius:8px;border:2px solid var(--border)">
      <div style="font-size:11px;color:var(--muted);margin-top:6px">${url}</div>`;
  },

  exportar() {
    const datos = { _maer_version: '4.0', _exportado: new Date().toISOString() };
    try {
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k && (k.startsWith('maer_') || k.startsWith('_maer'))) datos[k] = localStorage.getItem(k);
      }
    } catch (e) {}
    datos.server = MAER.API;
    datos.tema = document.documentElement.style.getPropertyValue('--accent') || MAER.config.accentColor || '';
    return JSON.stringify(datos);
  },

  importar(texto) {
    try {
      const cfg = typeof texto === 'string' ? JSON.parse(texto) : texto;
      if (!cfg || typeof cfg !== 'object' || Array.isArray(cfg)) {
        return { ok: false, error: 'Configuración inválida' };
      }
      let claves = 0;
      for (const [k, v] of Object.entries(cfg)) {
        if (k === '_maer_version' || k === '_exportado' || k === 'server' || k === 'tema') continue;
        try { localStorage.setItem(k, typeof v === 'string' ? v : JSON.stringify(v)); claves++; } catch (e) {}
      }
      if (cfg.server) {
        localStorage.setItem('maer_server', cfg.server);
        MAER.API = MAER._normServer(cfg.server) || cfg.server;
        const el = document.getElementById('cfg-server');
        if (el) el.value = MAER.API;
      }
      if (cfg.tema) {
        document.documentElement.style.setProperty('--accent', cfg.tema);
        MAER.config.accentColor = cfg.tema;
      }
      MAER._applyTheme?.();
      return { ok: true, claves, msg: `Configuración importada (${claves} claves)` };
    } catch (e) {
      return { ok: false, error: 'JSON inválido: ' + e.message };
    }
  }
};
