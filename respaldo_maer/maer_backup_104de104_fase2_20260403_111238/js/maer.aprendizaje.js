/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Aprendizaje Permanente con IndexedDB
   Lo que MAER aprende NUNCA se borra (a menos que el usuario lo pida)
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.aprendizaje = {

  DB_NAME:    'MAER_Conocimiento',
  DB_VERSION: 1,
  STORE:      'documentos',
  db:         null,

  /* ── INICIALIZAR IndexedDB ── */
  async initDB() {
    return new Promise((resolve, reject) => {
      if (this.db) { resolve(this.db); return; }
      const req = indexedDB.open(this.DB_NAME, this.DB_VERSION);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this.STORE)) {
          const store = db.createObjectStore(this.STORE, { keyPath: 'id', autoIncrement: true });
          store.createIndex('nombre', 'nombre', { unique: false });
          store.createIndex('fecha',  'fecha',  { unique: false });
        }
      };
      req.onsuccess = (e) => { this.db = e.target.result; resolve(this.db); };
      req.onerror   = (e) => reject(e.target.error);
    });
  },

  /* ── GUARDAR DOCUMENTO APRENDIDO ── */
  async guardar(item) {
    // item = { nombre, etiqueta, texto, chars, tipo, fecha }
    const db = await this.initDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE, 'readwrite');
      const st = tx.objectStore(this.STORE);
      const req = st.add({ ...item, fecha: Date.now() });
      req.onsuccess = () => resolve(req.result);
      req.onerror   = () => reject(req.error);
    });
  },

  /* ── OBTENER TODOS ── */
  async obtenerTodos() {
    const db = await this.initDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE, 'readonly');
      const st = tx.objectStore(this.STORE);
      const req = st.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror   = () => reject(req.error);
    });
  },

  /* ── ELIMINAR POR ID ── */
  async eliminar(id) {
    const db = await this.initDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.STORE, 'readwrite');
      const st = tx.objectStore(this.STORE);
      const req = st.delete(id);
      req.onsuccess = () => resolve();
      req.onerror   = () => reject(req.error);
    });
  },

  /* ── BUSCAR EN CONOCIMIENTO (para el chat) ── */
  async buscarEnConocimiento(consulta) {
    try {
      const todos = await this.obtenerTodos();
      const palabras = consulta.toLowerCase().normalize('NFD')
        .replace(/[\u0300-\u036f]/g,'').split(/\s+/).filter(p => p.length > 3);
      let mejor = null;
      let mejorScore = 0;
      for (const doc of todos) {
        // Normalizar texto almacenado para búsqueda tolerante a acentos
        const textoNorm = (doc.texto || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
        let score = 0;
        for (const palabra of palabras) {
          const ocurrencias = (textoNorm.match(new RegExp(palabra, 'gi')) || []).length;
          score += ocurrencias;
        }
        if (score > mejorScore) { mejorScore = score; mejor = doc; }
      }
      if (mejor && mejorScore >= 1) {
        // Extraer fragmento relevante
        const fragmento = this._extractoRelevante(mejor.texto, palabras[0]);
        return `De <strong>${mejor.nombre}</strong>:<br><br><em>"${fragmento}"</em>`;
      }
    } catch(e) {}
    return null;
  },

  _extractoRelevante(texto, palabra) {
    if (!palabra || !texto) return texto?.substring(0, 300) || '';
    // Buscar en versión normalizada, pero extraer del texto original
    const textoNorm = texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    const idx = textoNorm.indexOf(palabra);
    if (idx < 0) return texto.substring(0, 300);
    const start = Math.max(0, idx - 100);
    const end   = Math.min(texto.length, idx + 250);
    return (start > 0 ? '...' : '') + texto.substring(start, end) + (end < texto.length ? '...' : '');
  },

  /* ── SUBIR Y PROCESAR ARCHIVO ── */
  async subirArchivo(file) {
    const btn = document.getElementById('btn-learn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loader"></span> Procesando...'; }

    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('label', file.name);
      const res = await MAER._upload('/api/learn-file', fd);

      if (res.ok && res.data?.text) {
        await this.guardar({
          nombre:   res.data.filename || file.name,
          etiqueta: res.data.label    || file.name,
          texto:    res.data.text,
          chars:    res.data.chars,
          tipo:     file.type || file.name.split('.').pop(),
        });
        this._renderLista();
        MAER._updateStats();
        MAER.chat._addMsg('sys', `✅ <strong>${file.name}</strong> aprendido. ${res.data.chars.toLocaleString()} caracteres en memoria permanente.`);
        MAER.voz?.hablar(`Documento ${file.name} aprendido. Lo recordaré siempre.`);
      } else {
        // Fallback: leer localmente si no hay servidor
        await this._aprenderLocal(file);
      }
    } catch(e) {
      await this._aprenderLocal(file);
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '📚 Enseñar a MAER'; }
    }
  },

  /* ── APRENDIZAJE LOCAL (sin servidor) ── */
  async _aprenderLocal(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    const textExts = ['txt','md','csv','json','js','py','html','css','xml'];
    if (!textExts.includes(ext)) {
      MAER.chat._addMsg('sys', `⚠️ Para leer <strong>${ext.toUpperCase()}</strong> necesitas el servidor activo. Solo puedo leer archivos de texto localmente.`);
      return;
    }
    const texto = await file.text();
    await this.guardar({
      nombre:   file.name,
      etiqueta: file.name,
      texto:    texto.substring(0, 10000),
      chars:    texto.length,
      tipo:     ext,
    });
    this._renderLista();
    MAER._updateStats();
    MAER.chat._addMsg('sys', `✅ <strong>${file.name}</strong> aprendido localmente. ${texto.length.toLocaleString()} caracteres en memoria permanente.`);
  },

  /* ── RENDERIZAR LISTA ── */
  async _renderLista() {
    const el = document.getElementById('aprendizaje-lista');
    if (!el) return;
    try {
      const todos = await this.obtenerTodos();
      // Actualizar contador
      const cnt = document.getElementById('learn-count');
      if (cnt) cnt.textContent = todos.length;

      if (!todos.length) {
        el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:12px">Sin documentos aprendidos todavía. Sube tu primer documento.</div>';
        return;
      }
      const icons = {pdf:'📄',txt:'📝',json:'📋',js:'📜',py:'🐍',docx:'📄',xlsx:'📊',csv:'📊',md:'📝',png:'🖼️',jpg:'🖼️'};
      el.innerHTML = [...todos].reverse().map(doc => {
        const icon = icons[doc.tipo?.toLowerCase()] || '📁';
        const fecha = doc.fecha ? new Date(doc.fecha).toLocaleDateString('es-MX') : '';
        const preview = (doc.texto || '').replace(/\n/g,' ').substring(0, 80) + '...';
        return `<div class="conocimiento-item">
          <div class="conocimiento-icon">${icon}</div>
          <div class="conocimiento-info">
            <div class="conocimiento-nombre">${doc.nombre}</div>
            <div class="conocimiento-meta">${doc.chars?.toLocaleString() || '?'} caracteres · ${fecha}</div>
            <div class="conocimiento-meta" style="margin-top:4px;font-style:italic">"${preview}"</div>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px;flex-shrink:0">
            <button class="btn btn-secondary btn-sm" onclick="MAER.aprendizaje._verDoc(${doc.id})">👁️</button>
            <button class="btn btn-danger btn-sm" onclick="MAER.aprendizaje._borrarDoc(${doc.id},'${doc.nombre.replace(/'/g,'')}')">🗑️</button>
          </div>
        </div>`;
      }).join('');
    } catch(e) {
      el.innerHTML = `<div class="alert alert-danger">Error cargando documentos: ${e.message}</div>`;
    }
  },

  async _verDoc(id) {
    const db = await this.initDB();
    const doc = await new Promise(r => db.transaction(this.STORE,'readonly').objectStore(this.STORE).get(id).onsuccess = e => r(e.target.result));
    if (!doc) return;
    const ol = document.createElement('div');
    ol.className = 'tooltip-overlay';
    ol.innerHTML = `<div class="tooltip-box" style="max-width:700px;max-height:80vh;overflow-y:auto">
      <h3>📄 ${doc.nombre}</h3>
      <div style="font-size:11px;color:var(--muted);margin-bottom:12px">${doc.chars?.toLocaleString()} chars · ${new Date(doc.fecha).toLocaleString('es-MX')}</div>
      <pre style="white-space:pre-wrap;font-size:12px;line-height:1.7;color:var(--text)">${(doc.texto||'').substring(0,3000)}${doc.texto?.length > 3000 ? '\n...[truncado]' : ''}</pre>
      <div style="margin-top:14px;text-align:right">
        <button class="btn btn-primary btn-sm" onclick="this.closest('.tooltip-overlay').remove()">Cerrar</button>
      </div>
    </div>`;
    ol.addEventListener('click', e => { if(e.target===ol) ol.remove(); });
    document.body.appendChild(ol);
  },

  async _borrarDoc(id, nombre) {
    if (!confirm(`¿Borrar "${nombre}" de la memoria de MAER?`)) return;
    await this.eliminar(id);
    this._renderLista();
    MAER.chat._addMsg('sys', `🗑️ <strong>${nombre}</strong> eliminado de la memoria.`);
  },

  /* ── EXPORTAR CONOCIMIENTO ── */
  async exportar() {
    const todos = await this.obtenerTodos();
    const blob = new Blob([JSON.stringify(todos, null, 2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `maer_conocimiento_${Date.now()}.json`;
    a.click();
  },

  /* ── LIMPIAR TODO ── */
  async limpiarTodo() {
    if (!confirm('⚠️ ¿Borrar TODO el conocimiento aprendido? Esta acción no se puede deshacer.')) return;
    const db = await this.initDB();
    await new Promise((res, rej) => {
      const tx = db.transaction(this.STORE, 'readwrite');
      const req = tx.objectStore(this.STORE).clear();
      req.onsuccess = res; req.onerror = rej;
    });
    this._renderLista();
    alert('✅ Conocimiento limpiado.');
  },
};
