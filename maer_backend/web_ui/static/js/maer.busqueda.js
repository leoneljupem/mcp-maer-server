/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Búsqueda Masiva + Búsqueda Semántica
   Busca dentro del contenido de archivos por palabras exactas
   o por significado (IA semántica con embeddings multilingüe)
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.busqueda = {

  resultados:     [],
  seleccionados:  new Set(),
  _modoSemantico: false,
  _indexListo:    false,

  /* ── EJECUTAR BÚSQUEDA (despacha al modo correcto) ── */
  async ejecutar() {
    const termino = document.getElementById('busq-termino')?.value?.trim();
    if (!termino) {
      MAER.voz?.hablar('Escribe qué quieres buscar.');
      return;
    }

    this._modoSemantico = document.getElementById('busq-semantico')?.checked === true;
    const enContenido   = document.getElementById('busq-modo-contenido')?.checked === true;

    const btn = document.getElementById('btn-buscar');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Buscando...'; }

    const area = document.getElementById('busq-resultados');
    if (area) area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:12px">
      ${this._modoSemantico ? '🧠 Analizando significado...' : enContenido ? '📚 Buscando dentro de archivos...' : '🔍 Buscando en tus archivos...'}
    </div>`;

    try {
      if (this._modoSemantico) {
        await this._buscarSemantico(termino, area);
      } else if (enContenido) {
        await this._buscarFTS(termino, area);
      } else {
        await this._buscarMasiva(termino, area);
      }
    } catch(e) {
      this._noServidor(termino, area);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🔍 Buscar'; }
    }
  },

  /* ── BÚSQUEDA FTS (SQLite FTS5, dentro del contenido) ── */
  async _buscarFTS(termino, area) {
    const tipos = this._getTiposSeleccionados();
    const res = await MAER._call('/api/search-fts', {
      query:      termino,
      limit:      50,
      fuzzy:      true,
      ext_filter: tipos.length ? tipos : null,
    }, { timeout: 30000 });

    const ftsData = res.data || res;
    if (res.ok && ftsData.results) {
      this.resultados = (ftsData.results || []).map(r => ({
        ruta:      r.path || '',
        nombre:    r.file_name || (r.path || '').split('/').pop(),
        fragmento: r.snippet ? r.snippet.replace(/<[^>]+>/g, '') : '',
        tamaño:    '',
        score:     r.score || 0,
        score_pct: '',
        match_type: r.fuzzy ? 'fuzzy' : 'exacto',
      }));
      this.seleccionados.clear();
      this._renderResultados(termino, false);
      MAER.voz?.hablar(`${this.resultados.length} archivos encontrados.`);
      if (!this.resultados.length) {
        this._mostrarIndexarFTS(area, termino);
      }
    } else {
      this._mostrarIndexarFTS(area, termino);
    }
  },

  /* ── CONSTRUIR ÍNDICE FTS ── */
  async _indexarDirectorio() {
    const carpeta = document.getElementById('busq-carpeta')?.value?.trim()
                  || prompt('📂 Ruta de la carpeta a indexar:', '~/Documents');
    if (!carpeta) return;
    const area = document.getElementById('busq-resultados');
    if (area) area.innerHTML = `<div style="padding:16px;color:var(--muted)">
      <div style="font-size:14px;margin-bottom:8px">⚙️ Indexando archivos de <code>${carpeta}</code>...</div>
      <div style="font-size:12px">Esto puede tardar varios minutos según la cantidad de archivos.</div>
      <div style="margin-top:12px;height:4px;background:var(--border);border-radius:2px;overflow:hidden">
        <div style="height:100%;background:var(--accent);animation:indeterminate 1.5s infinite linear;width:30%"></div>
      </div></div>`;
    const res = await MAER._call('/api/search-index-dir', { dir: carpeta, ocr: false }, { timeout: 300000 });
    if (res.ok) {
      const d = res.data || res;
      MAER.chat._addMsg('sys', `✅ Índice FTS listo: <strong>${d.indexed || 0}</strong> nuevos, <strong>${d.updated || 0}</strong> actualizados en <code>${carpeta}</code>.`);
      if (area) area.innerHTML = `<div class="alert alert-success" style="border-radius:8px;padding:12px">
        ✅ Indexados: <strong>${(d.indexed||0)+(d.updated||0)}</strong> archivos.<br>
        Errores: ${d.errors||0} &nbsp;|&nbsp; Omitidos: ${d.skipped||0}<br><br>
        <button class="btn btn-primary" onclick="MAER.busqueda.ejecutar()">🔍 Buscar ahora</button>
      </div>`;
      this._refrescarStats();
    } else {
      if (area) area.innerHTML = `<div class="alert alert-danger" style="border-radius:8px;padding:12px">Error: ${res.error||res.msg||'desconocido'}</div>`;
    }
  },

  _mostrarIndexarFTS(area, termino) {
    const statsEl = area?.querySelector?.('#fts-stats');
    if (!area) return;
    area.innerHTML = `
      <div style="color:var(--muted);font-size:13px;padding:14px;margin-bottom:10px">
        Sin resultados para "<strong>${this._escHTML(termino)}</strong>" en el índice FTS.
      </div>
      <div class="alert alert-warning" style="border-radius:8px;padding:16px">
        <strong>📚 Índice de contenido vacío o sin coincidencias</strong><br><br>
        Para buscar <em>dentro</em> del contenido de archivos, MAER necesita indexarlos primero.<br><br>
        <button class="btn btn-primary" onclick="MAER.busqueda._indexarDirectorio()">
          ⚡ Indexar carpeta
        </button>
        <button class="btn btn-secondary" style="margin-left:8px" onclick="MAER.busqueda._verEstadisticasFTS()">
          📊 Ver estado del índice
        </button>
        <span style="font-size:11px;color:var(--muted);display:block;margin-top:8px">
          Indexar es rápido (sin OCR). Con OCR activado extrae texto de PDFs e imágenes también.
        </span>
      </div>`;
  },

  /* ── TOGGLE EN CONTENIDO → muestra/oculta panel FTS ── */
  _onContenidoToggle(checked) {
    const panel = document.getElementById('fts-stats-panel');
    if (!panel) return;
    if (checked) {
      panel.style.display = 'block';
      this._refrescarStats();
    } else {
      panel.style.display = 'none';
    }
  },

  /* ── REFRESCAR ESTADÍSTICAS FTS ── */
  async _refrescarStats() {
    const body = document.getElementById('fts-stats-body');
    if (!body) return;
    body.innerHTML = '<span style="color:var(--muted)">Cargando…</span>';

    const res = await MAER._call('/api/search-index-stats', null).catch(() => null);
    const data = res?.data || res;

    if (!res?.ok) {
      body.innerHTML = '<span style="color:var(--muted)">Sin conexión con el servidor o índice vacío.</span>';
      return;
    }

    const total   = data.total_files  || 0;
    const chars   = data.total_chars  || 0;
    const byExt   = (data.by_extension || []).slice(0, 10);
    const byType  = (data.by_doc_type  || []).slice(0, 5);

    const extBars = byExt.map(e => {
      const pct = total ? Math.round((e.n / total) * 100) : 0;
      return `<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
        <code style="width:38px;text-align:right;font-size:11px">.${e.ext||'?'}</code>
        <div style="flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden">
          <div style="height:100%;width:${pct}%;background:var(--accent);border-radius:3px"></div>
        </div>
        <span style="width:28px;font-size:10px;color:var(--muted)">${e.n}</span>
      </div>`;
    }).join('');

    const typePills = byType.map(t =>
      `<span style="background:var(--border);border-radius:8px;padding:2px 7px;font-size:10px">${t.doc_type||'?'}: ${t.n}</span>`
    ).join(' ');

    const kb = chars >= 1_000_000
      ? `${(chars / 1_000_000).toFixed(1)} M`
      : `${(chars / 1000).toFixed(0)} k`;

    body.innerHTML = `
      <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px">
        <div style="text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--accent)">${total.toLocaleString()}</div>
          <div style="font-size:10px;color:var(--muted)">archivos</div>
        </div>
        <div style="text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--accent)">${kb}</div>
          <div style="font-size:10px;color:var(--muted)">caracteres</div>
        </div>
        ${total === 0 ? `<div style="align-self:center;font-size:12px;color:var(--muted)">
          El índice está vacío — indexa una carpeta para empezar.</div>` : ''}
      </div>
      ${byExt.length ? `<div style="margin-bottom:8px">${extBars}</div>` : ''}
      ${typePills ? `<div style="display:flex;gap:4px;flex-wrap:wrap">${typePills}</div>` : ''}`;
  },

  async _verEstadisticasFTS() {
    await this._refrescarStats();
  },

  /* ── BÚSQUEDA CLÁSICA POR NOMBRE ── */
  async _buscarMasiva(termino, area) {
    const carpeta  = document.getElementById('busq-carpeta')?.value?.trim() || '';
    const tipos    = this._getTiposSeleccionados();

    const res = await MAER._call('/api/busqueda-masiva', {
      termino, carpeta, tipos,
      en_nombre:    true,
      en_contenido: false,
    }, { timeout: 30000 });

    if (res.ok && res.data) {
      this.resultados = res.data.resultados || [];
      this.seleccionados.clear();
      this._renderResultados(termino, false);
      MAER.voz?.hablar(`${this.resultados.length} archivos encontrados.`);
    } else {
      this._noServidor(termino, area);
    }
  },

  /* ── BÚSQUEDA SEMÁNTICA POR SIGNIFICADO ── */
  async _buscarSemantico(termino, area) {
    // Verificar si el índice está listo
    const status = await MAER._call('/api/semantic-status', {}).catch(() => null);
    const indexReady = status?.data?.ready === true;

    if (!indexReady) {
      // Mostrar opción para construir el índice
      if (area) area.innerHTML = `
        <div class="alert alert-warning" style="border-radius:8px;padding:16px">
          <strong>🧠 Índice semántico no construido</strong><br><br>
          Para búsqueda inteligente, MAER necesita analizar tus documentos una vez
          y crear un índice de significados.<br><br>
          <button class="btn btn-primary" onclick="MAER.busqueda._construirIndice()">
            ⚡ Construir índice semántico
          </button>
          <span style="font-size:11px;color:var(--muted);margin-left:10px">
            (primera vez ~1-2 min, luego es instantáneo)
          </span>
        </div>`;
      return;
    }

    const res = await MAER._call('/api/semantic-search', {
      query: termino,
      top_k: 15,
      mode: 'hybrid',
    }, { timeout: 30000 });

    if (res.ok && res.data) {
      // Adaptar formato semántico al formato de resultados estándar
      this.resultados = (res.data.results || []).map(r => ({
        ruta:      r.path || '',
        nombre:    r.path ? r.path.split('/').pop() : '',
        fragmento: r.snippet_preview || '',
        tamaño:    r.size_bytes ? this._formatBytes(r.size_bytes) : '',
        score:     r.score || 0,
        score_pct: r.score_pct || '',
        match_type: r.match_type || 'semántico',
      }));
      this.seleccionados.clear();
      this._renderResultados(termino, true);
      MAER.voz?.hablar(`${this.resultados.length} documentos encontrados por significado.`);
    } else if (res.code === 'INDEX_NOT_BUILT') {
      this._mostrarConstruirIndice(area);
    } else {
      this._noServidor(termino, area);
    }
  },

  /* ── CONSTRUIR ÍNDICE SEMÁNTICO ── */
  async _construirIndice() {
    const area = document.getElementById('busq-resultados');
    if (area) area.innerHTML = `
      <div style="padding:16px;color:var(--muted)">
        <div style="font-size:14px;margin-bottom:8px">⚙️ Construyendo índice semántico...</div>
        <div style="font-size:12px">Analizando documentos e indexando significados.
        Esto puede tardar 1-2 minutos la primera vez.</div>
        <div style="margin-top:12px;height:4px;background:var(--border);border-radius:2px;overflow:hidden">
          <div style="height:100%;background:var(--accent);animation:indeterminate 1.5s infinite linear;width:30%"></div>
        </div>
      </div>`;

    try {
      const res = await MAER._call('/api/semantic-index', {}, { timeout: 180000 });
      if (res.ok) {
        this._indexListo = true;
        MAER.chat._addMsg('sys', `✅ Índice semántico listo: <strong>${res.data?.total_docs || 0}</strong> documentos indexados (motor: ${res.data?.engine || 'auto'}).`);
        if (area) area.innerHTML = `
          <div class="alert alert-success" style="border-radius:8px;padding:12px">
            ✅ Índice semántico construido con ${res.data?.total_docs || 0} documentos.<br>
            <small>Motor: ${res.data?.engine || 'auto'}</small><br><br>
            <button class="btn btn-primary" onclick="MAER.busqueda.ejecutar()">
              🔍 Buscar ahora
            </button>
          </div>`;
      } else {
        if (area) area.innerHTML = `<div class="alert alert-danger" style="border-radius:8px;padding:12px">
          Error construyendo índice: ${res.msg || 'Error desconocido'}</div>`;
      }
    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-danger" style="border-radius:8px;padding:12px">
        Error de conexión: ${e.message}</div>`;
    }
  },

  _mostrarConstruirIndice(area) {
    if (area) area.innerHTML = `
      <div class="alert alert-warning" style="border-radius:8px;padding:16px">
        <strong>Índice no disponible</strong><br><br>
        <button class="btn btn-primary" onclick="MAER.busqueda._construirIndice()">
          ⚡ Construir índice semántico
        </button>
      </div>`;
  },

  /* ── SIN SERVIDOR ── */
  _noServidor(termino, area) {
    if (area) area.innerHTML = `
      <div class="alert alert-warning">
        ⚠️ El servidor no está disponible para búsqueda de contenido.<br><br>
        La búsqueda dentro de archivos requiere el servidor MAER activo.<br>
        Inicia el servidor con: <code>python -m maer_backend.web_ui.server</code><br><br>
        <strong>Puedes buscar en archivos</strong> usando las pestañas
        <strong>Archivos</strong> o <strong>Aprendizaje</strong>.
      </div>`;
    MAER.voz?.hablar('El servidor no está disponible para búsqueda masiva.');
  },

  /* ── RENDERIZAR RESULTADOS ── */
  _renderResultados(termino, semantico = false) {
    const area = document.getElementById('busq-resultados');
    if (!area) return;

    if (!this.resultados.length) {
      area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:14px">
        Sin resultados para "<strong>${this._escHTML(termino)}</strong>".
        ${semantico ? 'Prueba con otra frase o construye el índice actualizado.' : 'Prueba con otro término o amplía los tipos de archivo.'}
      </div>`;
      return;
    }

    const icons = {pdf:'📄',txt:'📝',json:'📋',js:'📜',py:'🐍',docx:'📄',
                   xlsx:'📊',csv:'📊',md:'📝',png:'🖼️',jpg:'🖼️',jpeg:'🖼️',
                   gif:'🖼️',mp3:'🎵',mp4:'🎬',zip:'📦'};

    const modeLabel = semantico
      ? `<span style="background:var(--accent);color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;margin-left:8px">🧠 semántica</span>`
      : `<span style="background:var(--border);color:var(--text);padding:2px 8px;border-radius:10px;font-size:11px;margin-left:8px">🔍 exacta</span>`;

    area.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
        <div style="font-size:13px;color:var(--accent)">
          <strong>${this.resultados.length}</strong> resultados para
          "<em>${this._escHTML(termino)}</em>"${modeLabel}
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-secondary btn-sm" onclick="MAER.busqueda._seleccionarTodos()">☑️ Seleccionar todo</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.busqueda._deseleccionarTodos()">⬜ Deseleccionar</button>
          <button class="btn btn-primary btn-sm" id="btn-mover-sel" onclick="MAER.busqueda._moverSeleccionados()" disabled>📁 Mover selección</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.busqueda._exportarCSV()" title="Exportar a CSV">⬇️ CSV</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.busqueda._exportarTXT()" title="Exportar lista de rutas">⬇️ TXT</button>
        </div>
      </div>
      <div id="busq-lista">
      ${this.resultados.map((r, i) => {
        const ext  = (r.nombre || '').split('.').pop().toLowerCase();
        const icon = icons[ext] || '📁';
        const fragmento = r.fragmento
          ? `<div style="font-size:11px;color:var(--muted);margin-top:4px;font-style:italic">"${this._escHTML(r.fragmento.slice(0,200))}"</div>`
          : '';
        const scoreBadge = semantico && r.score_pct
          ? `<div style="font-size:10px;padding:2px 6px;border-radius:8px;background:${this._scoreColor(r.score)};color:#fff;flex-shrink:0" title="Relevancia semántica">
              ${r.score_pct}
            </div>`
          : '';
        const matchBadge = semantico && r.match_type
          ? `<div style="font-size:10px;color:var(--muted);flex-shrink:0">${r.match_type}</div>`
          : '';
        return `<div class="search-result-item" id="sr-${i}">
          <input type="checkbox" class="busq-check" onchange="MAER.busqueda._toggleSel(${i}, this.checked)"
            style="flex-shrink:0;accent-color:var(--accent);width:16px;height:16px">
          <div class="resultado-icon">${icon}</div>
          <div style="flex:1;min-width:0">
            <div class="resultado-nombre">${this._escHTML(r.nombre || '')}</div>
            <div class="resultado-ruta" title="${this._escHTML(r.ruta || '')}">${this._escHTML(r.ruta || '')}</div>
            ${fragmento}
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0">
            ${scoreBadge}
            ${matchBadge}
            <div style="font-size:11px;color:var(--muted)">${r.tamaño || ''}</div>
          </div>
        </div>`;
      }).join('')}
      </div>`;
  },

  _scoreColor(score) {
    if (score >= 0.75) return '#22c55e';
    if (score >= 0.5)  return '#f59e0b';
    if (score >= 0.3)  return '#6366f1';
    return '#94a3b8';
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
        const idxArr = Array.from(this.seleccionados).sort((a,b) => b-a);
        idxArr.forEach(i => this.resultados.splice(i, 1));
        this.seleccionados.clear();
        this._renderResultados(document.getElementById('busq-termino')?.value || '',
                               this._modoSemantico);
      } else {
        alert(`Error al mover archivos: ${res.msg || 'Error desconocido'}`);
      }
    } catch(e) {
      alert(`Error: ${e.message}`);
    } finally {
      if (btn) { btn.disabled = false; }
    }
  },

  /* ── EXPORTAR RESULTADOS ── */
  _exportarCSV() {
    if (!this.resultados.length) return;
    const termino = document.getElementById('busq-termino')?.value || 'busqueda';
    const rows = [['Nombre', 'Ruta', 'Fragmento', 'Tipo', 'Score']];
    this.resultados.forEach(r => {
      rows.push([
        `"${(r.nombre   || '').replace(/"/g,'""')}"`,
        `"${(r.ruta     || '').replace(/"/g,'""')}"`,
        `"${(r.fragmento|| '').replace(/"/g,'""').slice(0,200)}"`,
        `"${(r.match_type||'').replace(/"/g,'""')}"`,
        r.score ? r.score.toFixed(3) : '',
      ]);
    });
    const csv = rows.map(r => r.join(',')).join('\n');
    this._descargar(csv, `maer_busqueda_${termino.replace(/\W/g,'_')}.csv`, 'text/csv');
  },

  _exportarTXT() {
    if (!this.resultados.length) return;
    const termino = document.getElementById('busq-termino')?.value || 'busqueda';
    const txt = this.resultados.map(r => r.ruta || r.nombre || '').filter(Boolean).join('\n');
    this._descargar(txt, `maer_rutas_${termino.replace(/\W/g,'_')}.txt`, 'text/plain');
  },

  _descargar(contenido, nombre, tipo) {
    const blob = new Blob([contenido], { type: tipo + ';charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = nombre; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },

  /* ── WATCHER — vigilar carpeta en tiempo real ── */
  async _toggleWatcher() {
    const dirInput = document.getElementById('busq-carpeta');
    const dir = dirInput?.value?.trim() || prompt('Carpeta a vigilar:', '~/Documents');
    if (!dir) return;

    const statusRes = await MAER._call('/api/watch-status', null).catch(() => null);
    const watching = statusRes?.data?.watching || [];
    const yaVigilada = watching.some(w => w.path === dir || dir.startsWith(w.path));

    if (yaVigilada) {
      const res = await MAER._call('/api/watch-stop', { dir });
      if (res.ok) {
        MAER.chat._addMsg('sys', `⏹ Watcher detenido para <code>${dir}</code>.`);
        this._actualizarBtnWatcher(false);
      }
    } else {
      const res = await MAER._call('/api/watch-start', { dir });
      if (res.ok) {
        MAER.chat._addMsg('sys', `👁 Vigilando <code>${dir}</code> — archivos nuevos se indexarán automáticamente.`);
        this._actualizarBtnWatcher(true);
      } else {
        alert(`Error: ${res.message || res.msg || 'No se pudo iniciar'}`);
      }
    }
  },

  _actualizarBtnWatcher(activo) {
    const btn = document.getElementById('btn-watcher');
    if (!btn) return;
    btn.textContent = activo ? '👁 Vigilando' : '👁 Vigilar carpeta';
    btn.style.background = activo ? 'rgba(52,211,153,0.15)' : '';
    btn.style.borderColor = activo ? 'var(--green)' : '';
    btn.style.color = activo ? 'var(--green)' : '';
  },

  /* ── OBTENER TIPOS SELECCIONADOS ── */
  _getTiposSeleccionados() {
    const tipos = [];
    const checks = document.querySelectorAll('.busq-tipo:checked');
    checks.forEach(cb => tipos.push(cb.value));
    return tipos.length ? tipos : ['pdf','docx','txt','xlsx','csv','json','md','png','jpg','jpeg'];
  },

  _formatBytes(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes/1024).toFixed(1)} KB`;
    return `${(bytes/1024/1024).toFixed(1)} MB`;
  },

  _escHTML(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
