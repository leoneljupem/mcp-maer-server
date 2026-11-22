// 🦁 MAER — Historial de cartas generadas
MAER.cartasHistorial = {
  _historial: [],

  init() {
    this._historial = JSON.parse(localStorage.getItem('maer_cartas_historial') || '[]');
  },

  guardar(tipo, nombre, texto) {
    const carta = { id: Date.now(), tipo, nombre, texto, fecha: new Date().toLocaleDateString('es-MX') };
    this._historial.push(carta);
    if (this._historial.length > 50) this._historial.shift();
    localStorage.setItem('maer_cartas_historial', JSON.stringify(this._historial));
    this.render();
    return carta;
  },

  listar() {
    return this._historial.slice();
  },

  _guardar() {
    localStorage.setItem('maer_cartas_historial', JSON.stringify(this._historial));
  },

  get datos() { return this._historial; },
  set datos(v) { this._historial = v || []; },

  render() {
    const lista = document.getElementById('cartas-historial-lista');
    if (!lista) return;
    if (!this._historial.length) {
      lista.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px">Sin cartas generadas aún.</div>';
      return;
    }
    lista.innerHTML = this._historial.slice().reverse().map((c, i) => `
      <div class="card" style="margin-bottom:8px;padding:10px;display:flex;justify-content:space-between;align-items:center">
        <div>
          <div style="font-weight:600;font-size:13px">✉️ ${c.tipo}</div>
          <div style="font-size:11px;color:var(--muted)">${c.nombre} · ${c.fecha}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-secondary btn-sm" onclick="MAER.cartasHistorial._ver(${c.id})">👁️ Ver</button>
          <button class="btn btn-danger btn-sm" onclick="MAER.cartasHistorial._eliminar(${c.id})">🗑️</button>
        </div>
      </div>`).join('');
  },

  _ver(id) {
    const carta = this._historial.find(c => c.id === id);
    if (!carta) return;
    const el = document.getElementById('carta-texto');
    if (el) { el.textContent = carta.texto; el.closest('#carta-resultado')?.style?.setProperty('display','block'); }
  },

  _eliminar(id) {
    this._historial = this._historial.filter(c => c.id !== id);
    localStorage.setItem('maer_cartas_historial', JSON.stringify(this._historial));
    this.render();
  }
};
