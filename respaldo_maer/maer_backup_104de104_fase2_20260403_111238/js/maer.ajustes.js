/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo Ajustes
   Configuración de voz, colores, servidor, UI personalizable
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.ajustes = {

  TEMAS_PRESET: [
    { nombre: '🌊 Azul Profundo (default)', bg: '#07101c', accent: '#38bdf8' },
    { nombre: '🔥 Rojo Fuego',             bg: '#0f0a0a', accent: '#f87171' },
    { nombre: '🌿 Verde Selva',            bg: '#071209', accent: '#34d399' },
    { nombre: '🟡 Ámbar',                  bg: '#0f0d00', accent: '#fbbf24' },
    { nombre: '💜 Violeta',               bg: '#090710', accent: '#a78bfa' },
    { nombre: '🟠 Naranja',               bg: '#0f0800', accent: '#fb923c' },
    { nombre: '⬛ Monocromático',          bg: '#0a0a0a', accent: '#e2e8f0' },
    { nombre: '🩵 Cian',                  bg: '#060f10', accent: '#22d3ee' },
  ],

  /* ── INIT AJUSTES UI ── */
  init() {
    this._syncUI();
    this._renderTemas();
    this._renderVoces();
  },

  /* ── SINCRONIZAR UI CON CONFIG ── */
  _syncUI() {
    const cfg = MAER.config;

    // Voz
    const vozToggle = document.getElementById('cfg-voz');
    if (vozToggle) vozToggle.checked = cfg.vozActiva;
    const vozPitch = document.getElementById('voz-pitch');
    if (vozPitch) vozPitch.value = cfg.vozPitch;
    const vozSpeed = document.getElementById('voz-speed');
    if (vozSpeed) {
      vozSpeed.value = cfg.vozRate;
      const val = document.getElementById('voz-speed-val');
      if (val) val.textContent = parseFloat(cfg.vozRate).toFixed(1);
    }

    // Servidor
    const srv = document.getElementById('cfg-server');
    if (srv) srv.value = MAER.API;

    // Colores
    const accentInput = document.getElementById('cfg-accent');
    if (accentInput) accentInput.value = cfg.accentColor || '#38bdf8';
    const bgInput = document.getElementById('cfg-bg');
    if (bgInput) bgInput.value = cfg.bgColor || '#07101c';
  },

  /* ── APLICAR TEMA PRESET ── */
  _renderTemas() {
    const el = document.getElementById('temas-lista');
    if (!el) return;
    el.innerHTML = this.TEMAS_PRESET.map((t, i) => `
      <button class="btn btn-secondary btn-sm" style="
        display:flex;align-items:center;gap:8px;padding:8px 12px;text-align:left;
        border-left:4px solid ${t.accent};background:${t.bg};color:#e2e8f0"
        onclick="MAER.ajustes.aplicarTema(${i})">
        <span style="font-size:18px">${t.nombre.split(' ')[0]}</span>
        <span style="font-size:12px">${t.nombre.split(' ').slice(1).join(' ')}</span>
      </button>`).join('');
  },

  aplicarTema(idx) {
    const t = this.TEMAS_PRESET[idx];
    if (!t) return;
    MAER.config.accentColor = t.accent;
    MAER.config.bgColor     = t.bg;
    MAER._applyTheme();
    MAER.saveConfig();

    const accentInput = document.getElementById('cfg-accent');
    if (accentInput) accentInput.value = t.accent;
    const bgInput = document.getElementById('cfg-bg');
    if (bgInput) bgInput.value = t.bg;

    MAER.voz?.hablar(`Tema ${t.nombre.replace(/[^\w\s]/g,'')} aplicado.`);
    MAER._log(`🎨 Tema: ${t.nombre}`);
  },

  /* ── COLOR PERSONALIZADO ── */
  aplicarColorPersonalizado() {
    const accent = document.getElementById('cfg-accent')?.value || '#38bdf8';
    const bg     = document.getElementById('cfg-bg')?.value     || '#07101c';
    MAER.config.accentColor = accent;
    MAER.config.bgColor     = bg;
    MAER._applyTheme();
    MAER.saveConfig();
    MAER.voz?.hablar('Colores personalizados aplicados.');
  },

  /* ── LISTAR VOCES DISPONIBLES ── */
  _renderVoces() {
    const el = document.getElementById('voces-lista');
    if (!el) return;

    setTimeout(() => {
      const voces = speechSynthesis.getVoices().filter(v => v.lang.startsWith('es'));
      if (!voces.length) {
        el.innerHTML = '<div style="color:var(--muted);font-size:12px">No se detectaron voces en español.</div>';
        return;
      }
      el.innerHTML = voces.map(v => `
        <div style="display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:6px;background:var(--surface);margin-bottom:4px">
          <span style="font-size:12px;flex:1;font-family:monospace;color:var(--text)">${v.name}</span>
          <span style="font-size:11px;color:var(--muted)">${v.lang}</span>
          <button class="btn btn-secondary btn-sm" onclick="MAER.ajustes._probarVoz('${v.name.replace(/'/g,'')}')">▶</button>
        </div>`).join('');
    }, 800);
  },

  _probarVoz(nombre) {
    const voz = speechSynthesis.getVoices().find(v => v.name === nombre);
    if (!voz) return;
    const utt = new SpeechSynthesisUtterance('MAER activo. Voz grave y segura. Leonel, estoy contigo.');
    utt.lang   = 'es-MX';
    utt.voice  = voz;
    utt.pitch  = parseFloat(MAER.config.vozPitch  || 0.62);
    utt.rate   = parseFloat(MAER.config.vozRate   || 0.93);
    utt.volume = 1.0;
    speechSynthesis.cancel();
    speechSynthesis.speak(utt);
  },

  /* ── GUARDAR CONFIG VOZ ── */
  guardarVoz() {
    MAER.config.vozActiva = document.getElementById('cfg-voz')?.checked ?? true;
    MAER.config.vozPitch  = parseFloat(document.getElementById('voz-pitch')?.value  || 0.62);
    MAER.config.vozRate   = parseFloat(document.getElementById('voz-speed')?.value  || 0.93);
    MAER.saveConfig();
    // Sincronizar toggles del sidebar
    ['voz-toggle'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.checked = MAER.config.vozActiva;
    });
    MAER.voz?.hablar('Configuración de voz guardada.');
    MAER._log('🔊 Config voz guardada.');
  },

  /* ── GUARDAR SERVIDOR ── */
  guardarServidor() {
    MAER.saveConfig();
    MAER.chat._addMsg('sys', `🔌 Servidor configurado: <strong>${MAER.API}</strong>`);
    MAER.sistema._checkServer();
  },

  /* ── RESET FACTORY ── */
  resetFactory() {
    if (!confirm('⚠️ ¿Restablecer MAER a valores por defecto? (NO borra historial ni documentos aprendidos)')) return;
    localStorage.removeItem('maer_config');
    localStorage.removeItem('maer_server');
    location.reload();
  },

  /* ── IMPORTAR BACKUP ── */
  async importarBackup(file) {
    if (!file) return;
    try {
      const texto = await file.text();
      const data  = JSON.parse(texto);
      if (data.historial) localStorage.setItem('maer_history',       JSON.stringify(data.historial));
      if (data.aprendidos) localStorage.setItem('maer_learned',       JSON.stringify(data.aprendidos));
      if (data.eventos)    localStorage.setItem('maer_eventos',       JSON.stringify(data.eventos));
      if (data.notas)      localStorage.setItem('maer_pension_notas', data.notas);
      if (data.config)     { Object.assign(MAER.config, data.config); MAER.saveConfig(); }
      MAER.chat._addMsg('sys', `✅ Backup importado correctamente desde <strong>${file.name}</strong>.`);
      MAER.voz?.hablar('Backup importado. Recargando ajustes.');
      MAER._restoreConfig();
      MAER._applyTheme();
      this._syncUI();
      MAER._updateStats();
    } catch(e) {
      alert(`Error al importar backup: ${e.message}`);
    }
  },

  /* ── INFO DEL SISTEMA ── */
  mostrarInfo() {
    const hist    = JSON.parse(localStorage.getItem('maer_history') || '[]');
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    const ol = document.createElement('div');
    ol.className = 'tooltip-overlay';
    ol.innerHTML = `<div class="tooltip-box">
      <h3>ℹ️ MAER ${MAER.version}</h3>
      <div style="font-size:13px;line-height:1.8;color:var(--text)">
        <strong>Leonel Houssen Mojica</strong><br>
        Ecatepec, Estado de México — 2026<br><br>
        <strong>Motor:</strong> FastAPI + llama.cpp (local)<br>
        <strong>Voz:</strong> Web Speech API (pitch ${MAER.config.vozPitch}, rate ${MAER.config.vozRate})<br>
        <strong>Memoria:</strong> IndexedDB + localStorage<br>
        <strong>Historial:</strong> ${hist.length} mensajes<br>
        <strong>Aprendizajes:</strong> ${learned.length} respuestas personalizadas<br>
        <strong>Diccionario:</strong> ${typeof MAER_DICCIONARIO !== 'undefined' ? MAER_DICCIONARIO.length : 0} patrones<br>
        <strong>Servidor:</strong> ${MAER.config.backendOK ? '🟢 Activo' : '🔴 Offline'} (${MAER.API})<br>
      </div>
      <div style="margin-top:14px;text-align:right">
        <button class="btn btn-primary btn-sm" onclick="this.closest('.tooltip-overlay').remove()">Cerrar</button>
      </div>
    </div>`;
    ol.addEventListener('click', e => { if(e.target===ol) ol.remove(); });
    document.body.appendChild(ol);
  },
};

/* ── Inicializar ajustes cuando el panel se muestre ── */
document.addEventListener('DOMContentLoaded', () => {
  // Retrasar para dar tiempo a que carguen voces del sistema
  setTimeout(() => MAER.ajustes.init(), 1000);
});
