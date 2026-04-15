/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Historial de Versiones de Cartas
   BLOQUE 10 — Guardar, listar, comparar y re-imprimir cartas
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.cartasHistorial = {

  STORAGE_KEY: 'maer_cartas_historial',
  datos: [],  // [{ id, tipo, nombre, nss, fecha, contenido, creadoEn }]

  /* ── INICIALIZAR ── */
  init() {
    this.datos = this._cargar();
  },

  /* ── GUARDAR CARTA ── */
  guardar(tipo, nombre, nss, contenido) {
    const carta = {
      id: Date.now(),
      tipo,
      nombre: nombre || 'Sin nombre',
      nss: nss || '',
      fecha: new Date().toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' }),
      contenido,
      creadoEn: new Date().toISOString()
    };

    this.datos.unshift(carta); // Más reciente primero
    // Máximo 50 cartas
    if (this.datos.length > 50) this.datos = this.datos.slice(0, 50);
    this._guardar();
    this.render();
    return carta;
  },

  /* ── LISTAR ── */
  listar() {
    return [...this.datos];
  },

  /* ── OBTENER POR ID ── */
  obtener(id) {
    return this.datos.find(c => c.id === id) || null;
  },

  /* ── ELIMINAR ── */
  eliminar(id) {
    if (!confirm('¿Eliminar esta versión de carta?')) return;
    this.datos = this.datos.filter(c => c.id !== id);
    this._guardar();
    this.render();
    MAER.voz?.hablar('Carta eliminada del historial.');
  },

  /* ── COMPARAR DOS CARTAS ── */
  comparar(id1, id2) {
    const c1 = this.obtener(id1);
    const c2 = this.obtener(id2);
    if (!c1 || !c2) return;

    const panel = document.getElementById('cartas-comparacion');
    if (!panel) return;

    panel.innerHTML = `
      <div class="card" style="margin-top:12px">
        <div class="card-title">📊 Comparación de cartas</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div>
            <strong style="color:var(--primary)">${c1.fecha} — ${this._tipoLabel(c1.tipo)}</strong>
            <div style="background:var(--bg2);padding:10px;border-radius:6px;margin-top:8px;font-size:0.8em;max-height:300px;overflow-y:auto;white-space:pre-wrap">${c1.contenido}</div>
          </div>
          <div>
            <strong style="color:#22c55e">${c2.fecha} — ${this._tipoLabel(c2.tipo)}</strong>
            <div style="background:var(--bg2);padding:10px;border-radius:6px;margin-top:8px;font-size:0.8em;max-height:300px;overflow-y:auto;white-space:pre-wrap">${c2.contenido}</div>
          </div>
        </div>
        <button class="btn btn-secondary btn-sm" style="margin-top:8px" onclick="document.getElementById('cartas-comparacion').innerHTML=''">Cerrar comparación</button>
      </div>`;

    MAER.voz?.hablar('Mostrando comparación de cartas.');
  },

  /* ── RE-IMPRIMIR ── */
  reimprimir(id) {
    const carta = this.obtener(id);
    if (!carta) return;
    // Poner en el textarea de cartas
    const textarea = document.getElementById('carta-texto');
    if (textarea) textarea.textContent = carta.contenido;
    // Cambiar a sub-tab de cartas
    const btn = document.querySelector('[onclick*="pension-cartas"]');
    if (btn) btn.click();
    MAER.voz?.hablar('Carta cargada. Puedes imprimirla o copiarla.');
  },

  /* ── RENDER ── */
  render() {
    const contenedor = document.getElementById('cartas-historial-lista');
    if (!contenedor) return;

    if (this.datos.length === 0) {
      contenedor.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:16px">No hay cartas guardadas. Se guardan automáticamente al generarlas.</p>';
      return;
    }

    let html = `<div style="font-size:0.8em;color:var(--text-secondary);margin-bottom:8px">${this.datos.length} carta${this.datos.length > 1 ? 's' : ''} en historial</div>`;

    this.datos.forEach((carta, i) => {
      const fechaCreacion = new Date(carta.creadoEn).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
      const preview = carta.contenido.replace(/<[^>]+>/g, '').substring(0, 100);
      const tipoLabel = this._tipoLabel(carta.tipo);

      html += `
        <div class="card" style="margin-bottom:6px;padding:10px">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <div style="flex:1">
              <strong>${tipoLabel}</strong>
              <span style="font-size:0.75em;color:var(--text-secondary);margin-left:8px">${fechaCreacion}</span>
              <div style="font-size:0.8em;color:var(--text-secondary);margin-top:4px">${carta.nombre} — NSS: ${carta.nss || 'N/A'}</div>
              <div style="font-size:0.75em;color:var(--muted);margin-top:2px;font-style:italic">${preview}...</div>
            </div>
            <div style="display:flex;gap:4px;flex-shrink:0">
              <button class="btn btn-secondary btn-sm" onclick="MAER.cartasHistorial.reimprimir(${carta.id})" title="Cargar carta">📄</button>
              ${i < this.datos.length - 1 ? `<button class="btn btn-secondary btn-sm" onclick="MAER.cartasHistorial.comparar(${carta.id},${this.datos[i+1].id})" title="Comparar con anterior">🔀</button>` : ''}
              <button class="btn btn-secondary btn-sm" onclick="MAER.cartasHistorial.eliminar(${carta.id})" title="Eliminar">🗑️</button>
            </div>
          </div>
        </div>`;
    });

    contenedor.innerHTML = html;
  },

  /* ── TIPO LABEL ── */
  _tipoLabel(tipo) {
    const labels = {
      'semanas': '📋 Solicitud de semanas',
      'pension': '📜 Solicitud de pensión',
      'recurso': '⚖️ Recurso de inconformidad',
      'amparo': '🏛️ Demanda de amparo',
      'queja': '📢 Queja administrativa',
      'general': '📄 Carta general'
    };
    return labels[tipo] || `📄 ${tipo}`;
  },

  /* ── PERSISTENCIA ── */
  _cargar() {
    try { return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || []; } catch(e) { return []; }
  },
  _guardar() {
    try { localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.datos)); } catch(e) {}
  }
};
