// 🦁 MAER — Módulo de Etiquetas
MAER.etiquetas = {
  _etiquetas: {},

  init() {
    this._etiquetas = JSON.parse(localStorage.getItem('maer_etiquetas') || '{}');
  },

  render() {
    const panel = document.getElementById('etiquetas-panel');
    if (!panel) return;
    const todas = Object.keys(this._etiquetas);
    if (!todas.length) {
      panel.innerHTML = '<div style="color:var(--muted);font-size:12px">Sin etiquetas creadas. Se generan automáticamente al clasificar documentos.</div>';
      return;
    }
    panel.innerHTML = todas.map(tag => `
      <span style="display:inline-block;background:rgba(56,189,248,0.15);color:var(--accent);border:1px solid var(--accent);border-radius:20px;padding:3px 10px;font-size:11px;margin:2px;cursor:pointer" onclick="MAER.etiquetas.filtrar('${tag}')">
        🏷️ ${tag} (${this._etiquetas[tag]?.length || 0})
      </span>`).join('');
  },

  agregar(archivo, etiqueta) {
    if (!this._etiquetas[etiqueta]) this._etiquetas[etiqueta] = [];
    if (!this._etiquetas[etiqueta].includes(archivo)) this._etiquetas[etiqueta].push(archivo);
    localStorage.setItem('maer_etiquetas', JSON.stringify(this._etiquetas));
    this.render();
  },

  filtrar(etiqueta) {
    const archivos = this._etiquetas[etiqueta] || [];
    MAER.chat._addMsg('sys', `🏷️ Archivos con etiqueta "${etiqueta}": ${archivos.length ? archivos.join(', ') : 'ninguno'}`);
  },

  PREDEFINIDAS: ['IMSS', 'INFONAVIT', 'CURP', 'RFC', 'Acta', 'Pensión', 'Ley 73', 'Ley 97', 'Demanda', 'Amparo', 'Afore', 'Semanas', 'Identificación', 'Expediente', 'Carta'],

  asignar(archivo, etiqueta) {
    return this.agregar(archivo, etiqueta);
  },

  obtener(archivo) {
    return Object.keys(this._etiquetas).filter(t => this._etiquetas[t].includes(archivo));
  },

  quitar(archivo, etiqueta) {
    if (this._etiquetas[etiqueta]) {
      this._etiquetas[etiqueta] = this._etiquetas[etiqueta].filter(a => a !== archivo);
      if (!this._etiquetas[etiqueta].length) delete this._etiquetas[etiqueta];
    }
    this._guardar();
    this.render();
  },

  buscarPorEtiqueta(etiqueta) {
    return [...(this._etiquetas[etiqueta] || [])];
  },

  _guardar() {
    localStorage.setItem('maer_etiquetas', JSON.stringify(this._etiquetas));
  }
};
