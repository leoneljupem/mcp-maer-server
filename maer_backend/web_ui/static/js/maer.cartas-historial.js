// 🦁 MAER — Historial de versiones de cartas (Bloque 10)
MAER.cartasHistorial = {
  _historial: [],
  TIPOS: ['semanas', 'recurso', 'amparo', 'pension', 'documentos'],

  init() {
    this._historial = JSON.parse(localStorage.getItem('maer_cartas_historial') || '[]');
  },

  guardar(tipo, nombre, texto, contenido) {
    const cuerpo = (contenido !== undefined && contenido !== null && String(contenido).trim())
      ? String(contenido) : String(texto || '');
    const referencia = cuerpo === String(texto || '') ? '' : String(texto || '');
    const carta = {
      id: Date.now(), tipo, nombre, referencia, texto: cuerpo,
      fecha: new Date().toLocaleDateString('es-MX')
    };
    this._historial.push(carta);
    if (this._historial.length > 50) this._historial.shift();
    this._guardar();
    this.render();
    return carta;
  },

  listar() {
    return this._historial.slice();
  },

  obtener(id) {
    return this._historial.find(c => String(c.id) === String(id)) || null;
  },

  eliminar(id) {
    const antes = this._historial.length;
    this._historial = this._historial.filter(c => String(c.id) !== String(id));
    if (this._historial.length === antes) return false;
    this._guardar();
    this.render();
    return true;
  },

  comparar(idA, idB) {
    const a = this.obtener(idA);
    const b = this.obtener(idB);
    if (!a || !b) return null;
    const panel = document.getElementById('cartas-comparacion');
    if (panel) {
      panel.innerHTML = `
        <div class="card" style="margin-top:10px;padding:12px">
          <div style="font-weight:600;margin-bottom:8px">🔍 Comparación de versiones</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div><div class="sugerencia-cat">${this._escapar(a.tipo)} · ${this._escapar(a.fecha)}</div>
              <pre id="carta-texto" class="carta-texto">${this._escapar(a.texto)}</pre></div>
            <div><div class="sugerencia-cat">${this._escapar(b.tipo)} · ${this._escapar(b.fecha)}</div>
              <pre class="carta-texto">${this._escapar(b.texto)}</pre></div>
          </div>
        </div>`;
      panel.style.display = 'block';
    }
    return { a, b, iguales: a.texto === b.texto };
  },

  reimprimir(id) {
    const carta = this.obtener(id);
    if (!carta) return false;
    const el = document.getElementById('carta-texto');
    if (el) el.textContent = carta.texto;

    const frame = document.createElement('iframe');
    frame.setAttribute('aria-hidden', 'true');
    frame.style.position = 'fixed';
    frame.style.width = '0';
    frame.style.height = '0';
    frame.style.border = '0';
    document.body.appendChild(frame);
    const doc = frame.contentWindow?.document;
    if (doc) {
      doc.open();
      doc.write(`<!doctype html><html><head><meta charset="utf-8"><title>${this._escapar(carta.tipo)}</title></head>
        <body style="font-family:'Courier New',monospace;white-space:pre-wrap;padding:24px">${this._escapar(carta.texto)}</body></html>`);
      doc.close();
      frame.contentWindow.focus();
      frame.contentWindow.print();
    }
    window.setTimeout(() => frame.remove(), 1500);
    MAER.voz?.hablar(`Reimprimiendo carta de ${carta.tipo}.`);
    return true;
  },

  _escapar(t) {
    return String(t ?? '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
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
    lista.innerHTML = this._historial.slice().reverse().map((c) => `
      <div class="card" style="margin-bottom:8px;padding:10px;display:flex;justify-content:space-between;align-items:center;gap:8px">
        <div>
          <div style="font-weight:600;font-size:13px">✉️ ${this._escapar(c.tipo)}</div>
          <div style="font-size:11px;color:var(--muted)">${this._escapar(c.nombre)} · ${this._escapar(c.fecha)}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-secondary btn-sm" title="Ver" onclick="MAER.cartasHistorial._ver(${c.id})">👁️ Ver</button>
          <button class="btn btn-secondary btn-sm" title="Reimprimir" onclick="MAER.cartasHistorial.reimprimir(${c.id})">🖨️</button>
          <button class="btn btn-danger btn-sm" title="Eliminar" onclick="MAER.cartasHistorial.eliminar(${c.id})">🗑️</button>
        </div>
      </div>`).join('');
  },

  _ver(id) {
    const carta = this.obtener(id);
    if (!carta) return;
    const el = document.getElementById('carta-texto');
    if (el) {
      el.textContent = carta.texto;
      el.closest('#carta-resultado')?.style?.setProperty('display', 'block');
    }
    MAER.voz?.hablar(`Carta de ${carta.tipo} del ${carta.fecha}.`);
  },

  _eliminar(id) { return this.eliminar(id); }
};
