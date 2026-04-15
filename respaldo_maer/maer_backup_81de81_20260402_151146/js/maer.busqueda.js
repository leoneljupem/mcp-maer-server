/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Búsqueda Masiva
   Busca dentro del contenido de archivos, filtra por tipo,
   selecciona resultados y los mueve a una carpeta
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.busqueda = {

  resultados:     [],
  seleccionados:  new Set(),

  /* ── EJECUTAR BÚSQUEDA ── */
  async ejecutar() {
    const termino  = document.getElementById('busq-termino')?.value?.trim();
    if (!termino) {
      MAER.voz?.hablar('Escribe qué quieres buscar.');
      return;
    }

    const carpeta  = document.getElementById('busq-carpeta')?.value?.trim() || '';
    const tipos    = this._getTiposSeleccionados();
    const enNombre = document.getElementById('busq-modo-nombre')?.checked !== false;
    const enContenido = document.getElementById('busq-modo-contenido')?.checked;

    const btn = document.getElementById('btn-buscar');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Buscando...'; }

    const area = document.getElementById('busq-resultados');
    if (area) area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:12px">🔍 Buscando en tus archivos...</div>';

    try {
      const res = await MAER._call('/api/busqueda-masiva', {
        termino,
        carpeta,
        tipos,
        en_nombre:    enNombre,
        en_contenido: enContenido || false,
      }, { timeout: 30000 });

      if (res.ok && res.data) {
        this.resultados = res.data.resultados || [];
        this.seleccionados.clear();
        this._renderResultados(termino);
        MAER.voz?.hablar(`Búsqueda completada. ${this.resultados.length} archivos encontrados.`);
      } else {
        this._noServidor(termino, area);
      }
    } catch(e) {
      this._noServidor(termino, area);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🔍 Buscar'; }
    }
  },

  /* ── SIN SERVIDOR ── */
  _noServidor(termino, area) {
    if (area) area.innerHTML = `
      <div class="alert alert-warning">
        ⚠️ El servidor no está disponible para búsqueda de contenido.
        <br><br>
        La búsqueda masiva dentro de archivos requiere el servidor MAER activo.
        <br>Inicia el servidor con: <code>python server.py</code>
        <br><br>
        <strong>Puedes buscar en archivos que hayas subido manualmente</strong> usando
        la pestaña <strong>Archivos</strong> o <strong>Aprendizaje</strong>.
      </div>`;
    MAER.voz?.hablar('El servidor no está disponible para búsqueda masiva.');
  },

  /* ── RENDERIZAR RESULTADOS ── */
  _renderResultados(termino) {
    const area = document.getElementById('busq-resultados');
    if (!area) return;

    if (!this.resultados.length) {
      area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:14px">
        Sin resultados para "<strong>${this._escHTML(termino)}</strong>".
        Prueba con otro término o amplía los tipos de archivo.
      </div>`;
      return;
    }

    const icons = {pdf:'📄',txt:'📝',json:'📋',js:'📜',py:'🐍',docx:'📄',
                   xlsx:'📊',csv:'📊',md:'📝',png:'🖼️',jpg:'🖼️',jpeg:'🖼️',
                   gif:'🖼️',mp3:'🎵',mp4:'🎬',zip:'📦'};

    area.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
        <div style="font-size:13px;color:var(--accent)"><strong>${this.resultados.length}</strong> archivos encontrados para "<em>${this._escHTML(termino)}</em>"</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-secondary btn-sm" onclick="MAER.busqueda._seleccionarTodos()">☑️ Seleccionar todo</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.busqueda._deseleccionarTodos()">⬜ Deseleccionar</button>
          <button class="btn btn-primary btn-sm" id="btn-mover-sel" onclick="MAER.busqueda._moverSeleccionados()" disabled>📁 Mover selección</button>
        </div>
      </div>
      <div id="busq-lista">
      ${this.resultados.map((r, i) => {
        const ext = (r.nombre || '').split('.').pop().toLowerCase();
        const icon = icons[ext] || '📁';
        const fragmento = r.fragmento ? `<div style="font-size:11px;color:var(--muted);margin-top:4px;font-style:italic">"${this._escHTML(r.fragmento)}"</div>` : '';
        return `<div class="search-result-item" id="sr-${i}">
          <input type="checkbox" class="busq-check" onchange="MAER.busqueda._toggleSel(${i}, this.checked)" style="flex-shrink:0;accent-color:var(--accent);width:16px;height:16px">
          <div class="resultado-icon">${icon}</div>
          <div style="flex:1;min-width:0">
            <div class="resultado-nombre">${this._escHTML(r.nombre || '')}</div>
            <div class="resultado-ruta" title="${this._escHTML(r.ruta || '')}">${this._escHTML(r.ruta || '')}</div>
            ${fragmento}
          </div>
          <div style="font-size:11px;color:var(--muted);flex-shrink:0">${r.tamaño || ''}</div>
        </div>`;
      }).join('')}
      </div>`;
  },

  /* ── SELECCIÓN ── */
  _toggleSel(idx, checked) {
    if (checked) this.seleccionados.add(idx);
    else         this.seleccionados.delete(idx);
    this._updateMoverBtn();
  },

  _seleccionarTodos() {
    this.resultados.forEach((_, i) => {
      this.seleccionados.add(i);
      const cb = document.querySelector(`#sr-${i} .busq-check`);
      if (cb) cb.checked = true;
    });
    this._updateMoverBtn();
  },

  _deseleccionarTodos() {
    this.seleccionados.clear();
    document.querySelectorAll('.busq-check').forEach(cb => cb.checked = false);
    this._updateMoverBtn();
  },

  _updateMoverBtn() {
    const btn = document.getElementById('btn-mover-sel');
    if (btn) {
      btn.disabled = this.seleccionados.size === 0;
      btn.textContent = this.seleccionados.size
        ? `📁 Mover ${this.seleccionados.size} archivo${this.seleccionados.size > 1 ? 's' : ''}`
        : '📁 Mover selección';
    }
  },

  /* ── MOVER SELECCIONADOS ── */
  async _moverSeleccionados() {
    if (!this.seleccionados.size) return;
    const destino = prompt('📁 Carpeta destino (ruta completa o nombre):', 'Resultados_MAER');
    if (!destino) return;

    const rutas = Array.from(this.seleccionados).map(i => this.resultados[i]?.ruta).filter(Boolean);
    if (!rutas.length) return;

    const btn = document.getElementById('btn-mover-sel');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Moviendo...'; }

    try {
      const res = await MAER._call('/api/move-files', { rutas, destino });
      if (res.ok) {
        MAER.chat._addMsg('sys', `✅ <strong>${rutas.length}</strong> archivo${rutas.length > 1 ? 's' : ''} movido${rutas.length > 1 ? 's' : ''} a <strong>${destino}</strong>.`);
        MAER.voz?.hablar(`${rutas.length} archivos movidos correctamente.`);
        // Eliminar de resultados
        const idxArr = Array.from(this.seleccionados).sort((a,b) => b-a);
        idxArr.forEach(i => this.resultados.splice(i, 1));
        this.seleccionados.clear();
        this._renderResultados(document.getElementById('busq-termino')?.value || '');
      } else {
        alert(`Error al mover archivos: ${res.msg || 'Error desconocido'}`);
      }
    } catch(e) {
      alert(`Error: ${e.message}`);
    } finally {
      if (btn) { btn.disabled = false; }
    }
  },

  /* ── OBTENER TIPOS SELECCIONADOS ── */
  _getTiposSeleccionados() {
    const tipos = [];
    const checks = document.querySelectorAll('.busq-tipo:checked');
    checks.forEach(cb => tipos.push(cb.value));
    return tipos.length ? tipos : ['pdf','docx','txt','xlsx','csv','json','md','png','jpg','jpeg'];
  },

  _escHTML(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
