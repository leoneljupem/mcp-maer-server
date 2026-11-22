// 🦁 MAER — Módulo de Aprendizaje
MAER.aprendizaje = {
  _docs: [],

  init() {
    this._docs = JSON.parse(localStorage.getItem('maer_learned_docs') || '[]');
    this._renderLista();
    const cnt = document.getElementById('learn-count');
    if (cnt) cnt.textContent = this._docs.length;
    MAER._log(`📚 Aprendizaje: ${this._docs.length} documentos cargados.`);
  },

  async subirArchivo(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('label', file.name);
    MAER.chat._addMsg('sys', `📚 Procesando "${file.name}"...`);
    const r = await MAER._upload('/api/learn-file', fd);
    if (r.ok) {
      const doc = { id: Date.now(), nombre: r.data.filename, label: r.data.label, texto: r.data.text, chars: r.data.chars, fecha: new Date().toLocaleDateString('es-MX') };
      this._docs.push(doc);
      localStorage.setItem('maer_learned_docs', JSON.stringify(this._docs));
      this._renderLista();
      const cnt = document.getElementById('learn-count');
      if (cnt) cnt.textContent = this._docs.length;
      MAER.chat._addMsg('maer', `✅ Aprendido: "${doc.label}" (${doc.chars} caracteres)`);
    } else {
      MAER.chat._addMsg('sys', `❌ Error: ${r.msg}`);
    }
  },

  _renderLista() {
    const lista = document.getElementById('aprendizaje-lista');
    if (!lista) return;
    if (!this._docs.length) {
      lista.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:12px">Sin documentos aprendidos aún.</div>';
      return;
    }
    lista.innerHTML = this._docs.slice().reverse().map((d, i) => `
      <div class="card" style="margin-bottom:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:8px">
        <div>
          <div style="font-weight:600;font-size:13px">📄 ${d.label}</div>
          <div style="font-size:11px;color:var(--muted)">${d.chars?.toLocaleString() || '?'} chars · ${d.fecha || ''}</div>
        </div>
        <button class="btn btn-danger btn-sm" onclick="MAER.aprendizaje._eliminar(${d.id})">🗑️</button>
      </div>`).join('');
  },

  _eliminar(id) {
    this._docs = this._docs.filter(d => d.id !== id);
    localStorage.setItem('maer_learned_docs', JSON.stringify(this._docs));
    this._renderLista();
    const cnt = document.getElementById('learn-count');
    if (cnt) cnt.textContent = this._docs.length;
  },

  exportar() {
    const blob = new Blob([JSON.stringify(this._docs, null, 2)], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'maer_conocimiento.json'; a.click();
  },

  limpiarTodo() {
    if (!confirm('¿Eliminar todo el conocimiento aprendido?')) return;
    this._docs = [];
    localStorage.removeItem('maer_learned_docs');
    this._renderLista();
    const cnt = document.getElementById('learn-count');
    if (cnt) cnt.textContent = 0;
    MAER.chat._addMsg('sys', '🗑️ Conocimiento eliminado.');
  },

  getContexto(query) {
    if (!this._docs.length) return '';
    const q = query.toLowerCase();
    const relevantes = this._docs.filter(d => d.texto?.toLowerCase().includes(q)).slice(0, 2);
    return relevantes.map(d => `[Documento: ${d.label}]
${d.texto?.slice(0, 500)}`).join('\n\n');
  },

  /* ── Compatibilidad IndexedDB / almacenamiento ── */
  async initDB() {
    this._docs = JSON.parse(localStorage.getItem('maer_learned_docs') || '[]');
    return true;
  },

  async guardar(doc) {
    if (!doc) return null;
    const item = {
      id: Date.now(),
      nombre: doc.nombre || doc.label || 'documento',
      label: doc.label || doc.nombre || 'documento',
      texto: doc.texto || '',
      chars: (doc.texto || '').length,
      tipo: doc.tipo || 'doc',
      fecha: new Date().toLocaleDateString('es-MX')
    };
    this._docs.push(item);
    localStorage.setItem('maer_learned_docs', JSON.stringify(this._docs));
    this._renderLista();
    const cnt = document.getElementById('learn-count');
    if (cnt) cnt.textContent = this._docs.length;
    return item;
  },

  async buscarEnConocimiento(query) {
    if (!query || !this._docs.length) return null;
    const q = query.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    let mejor = null, score = 0;
    for (const d of this._docs) {
      const txt = (d.texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      if (!txt) continue;
      const idx = txt.indexOf(q);
      if (idx >= 0) {
        const frag = d.texto.slice(Math.max(0, idx - 220), idx + 480);
        const s = Math.min(frag.length, 999);
        if (s > score) { score = s; mejor = frag; }
      }
    }
    return mejor;
  }
};
