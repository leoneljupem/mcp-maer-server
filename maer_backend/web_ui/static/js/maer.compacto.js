// 🦁 MAER — Modo Compacto
MAER.compacto = {
  _activo: false,

  init() {
    const saved = localStorage.getItem('maer_compacto');
    this._activo = saved === 'true' || saved === '1';
    if (this._activo) this._aplicar();
    const cb = document.getElementById('cfg-compacto');
    if (cb) cb.checked = this._activo;
  },

  toggle() {
    if (this._activo) this.desactivar();
    else this.activar();
  },

  get activo() { return this._activo; },

  activar() {
    this._activo = true;
    localStorage.setItem('maer_compacto', 'true');
    this._aplicar();
  },

  desactivar() {
    this._activo = false;
    localStorage.setItem('maer_compacto', 'false');
    this._quitar();
  },

  estado() {
    const w = window.innerWidth;
    const viewport = w < 600 ? 'movil' : w < 1024 ? 'tablet' : 'escritorio';
    return { activo: this._activo, viewport, ancho: w };
  },

  _aplicar() {
    if (!document.getElementById('maer-compact-css')) {
      const link = document.createElement('link');
      link.id = 'maer-compact-css';
      link.rel = 'stylesheet';
      link.href = '/static/css/maer-compact.css';
      document.head.appendChild(link);
    }
    document.body.classList.add('compact');
    const cb = document.getElementById('cfg-compacto');
    if (cb) cb.checked = true;
    MAER.chat?._addMsg?.('sys', '📱 Modo compacto activado.');
  },

  _quitar() {
    document.getElementById('maer-compact-css')?.remove();
    document.body.classList.remove('compact');
    const cb = document.getElementById('cfg-compacto');
    if (cb) cb.checked = false;
    MAER.chat?._addMsg?.('sys', '📱 Modo compacto desactivado.');
  }
};
