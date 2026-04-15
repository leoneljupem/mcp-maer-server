/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo Modo Compacto
   BLOQUE 11 — UI reducida para tablet/pantalla pequeña
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.compacto = {

  activo: false,
  STORAGE_KEY: 'maer_compacto',

  /* ── INIT ── */
  init() {
    // Cargar estado guardado
    this.activo = localStorage.getItem(this.STORAGE_KEY) === 'true';
    if (this.activo) this._aplicar();
    this._syncToggle();

    // Auto-detectar pantalla pequeña
    if (window.innerWidth < 768 && !localStorage.getItem(this.STORAGE_KEY)) {
      this.activar();
      MAER._log('📱 Modo compacto activado automáticamente (pantalla < 768px).');
    }

    // Listener para resize
    window.addEventListener('resize', () => this._checkResize());
  },

  /* ── TOGGLE ── */
  toggle() {
    if (this.activo) this.desactivar();
    else this.activar();
  },

  /* ── ACTIVAR ── */
  activar() {
    this.activo = true;
    this._aplicar();
    this._guardar();
    MAER.voz?.hablar('Modo compacto activado.');
    this._syncToggle();
  },

  /* ── DESACTIVAR ── */
  desactivar() {
    this.activo = false;
    document.body.classList.remove('compact');
    this._guardar();
    MAER.voz?.hablar('Modo compacto desactivado.');
    this._syncToggle();
  },

  /* ── APLICAR CLASE CSS ── */
  _aplicar() {
    document.body.classList.add('compact');
  },

  /* ── GUARDAR ── */
  _guardar() {
    localStorage.setItem(this.STORAGE_KEY, this.activo.toString());
  },

  /* ── SYNC UI ── */
  _syncToggle() {
    const toggle = document.getElementById('cfg-compacto');
    if (toggle) toggle.checked = this.activo;
  },

  /* ── AUTO-DETECT ── */
  _checkResize() {
    // Sugerir compacto si pantalla se reduce
    if (window.innerWidth < 768 && !this.activo) {
      // No auto-activar, solo sugerir
    }
  },

  /* ── ESTADO ── */
  estado() {
    return {
      activo: this.activo,
      viewport: window.innerWidth + 'x' + window.innerHeight
    };
  }
};
