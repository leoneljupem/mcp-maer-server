/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Núcleo Principal
   Motor base: config, tabs, API, reloj, tooltips, estadísticas
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

/* ── Objeto MAER global ── */
const MAER = {
  version: '3.1',
  API:     'http://localhost:8765',

  config: {
    vozActiva:   true,
    vozPitch:    0.62,   // Grave y masculina
    vozRate:     0.93,   // Pausado, autoridad
    vozVol:      1.0,
    aprendizaje: true,
    backendOK:   false,
    accentColor: '#38bdf8',
    bgColor:     '#07101c',
  },

  /* ══ INIT ══ */
  async init() {
    this._restoreConfig();
    this._startClock();
    this._setupDropZone();
    this._loadChecklistState();
    this.pension._loadNotas();
    this.pension._loadEventos();
    this.memoria._render();
    this.sistema._renderBrowser();
    this.sistema._renderPerf();
    this.sistema._renderNet();
    this.voz.init();
    await this.sistema.refresh();
    this._updateStats();
    this._log('🦁 MAER 3.1 iniciado correctamente.');
    this._log(`📖 Diccionario: ${MAER_DICCIONARIO.length} patrones cargados.`);
    // Fecha para cartas
    const fc = document.getElementById('carta-fecha');
    if (fc) fc.value = new Date().toLocaleDateString('es-MX', {day:'2-digit', month:'long', year:'numeric'});
    // Fecha evento default
    const fe = document.getElementById('evento-fecha');
    if (fe) fe.value = new Date().toISOString().split('T')[0];
    // Speed slider sync
    const vs = document.getElementById('voz-speed');
    if (vs) vs.addEventListener('input', e => {
      document.getElementById('voz-speed-val').textContent = parseFloat(e.target.value).toFixed(1);
      MAER.config.vozRate = parseFloat(e.target.value);
    });
    // Aplicar colores guardados
    this._applyTheme();
    // Bienvenida en voz — diferida hasta primera interacción del usuario
    // Chrome 71+ bloquea speechSynthesis.speak() sin gesto del usuario
    const _saludar = () => {
      MAER.voz?.hablar('MAER activo. Listo, Leonel.');
      document.removeEventListener('click', _saludar);
      document.removeEventListener('keydown', _saludar);
    };
    document.addEventListener('click', _saludar, { once: true });
    document.addEventListener('keydown', _saludar, { once: true });
  },

  /* ── RESTAURAR CONFIG ── */
  _restoreConfig() {
    try {
      const saved = JSON.parse(localStorage.getItem('maer_config') || '{}');
      Object.assign(this.config, saved);
    } catch(e) {}
    const su = localStorage.getItem('maer_server');
    if (su) { this.API = su; const el=document.getElementById('cfg-server'); if(el) el.value=su; }
    // Sync toggles
    ['cfg-voz','voz-toggle'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.checked = this.config.vozActiva;
    });
    const pp = document.getElementById('voz-pitch');
    if (pp) pp.value = this.config.vozPitch;
    const pv = document.getElementById('voz-speed');
    if (pv) pv.value = this.config.vozRate;
  },

  saveConfig() {
    localStorage.setItem('maer_config', JSON.stringify(this.config));
    const s = document.getElementById('cfg-server')?.value?.trim();
    if (s) { this.API = s; localStorage.setItem('maer_server', s); }
  },

  _applyTheme() {
    if (this.config.accentColor) {
      document.documentElement.style.setProperty('--accent', this.config.accentColor);
    }
    if (this.config.bgColor) {
      document.documentElement.style.setProperty('--bg', this.config.bgColor);
    }
  },

  /* ── RELOJ ── */
  _startClock() {
    const tick = () => {
      const now = new Date();
      const t = now.toLocaleTimeString('es-MX');
      const el1 = document.getElementById('hdr-time');
      const el2 = document.getElementById('sb-time2');
      if (el1) el1.textContent = t;
      if (el2) el2.textContent = t;
    };
    tick();
    setInterval(tick, 1000);
  },

  /* ── LOG ── */
  _log(msg) {
    const c = document.getElementById('sys-console');
    if (c) {
      c.innerHTML += `<span style="color:var(--muted)">${new Date().toLocaleTimeString('es-MX')}</span> ${msg}<br>`;
      c.scrollTop = c.scrollHeight;
    }
    console.log('[MAER]', msg.replace(/<[^>]+>/g,''));
  },

  /* ── ESTADÍSTICAS ── */
  _updateStats() {
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    const today = new Date().toDateString();
    const msgsHoy = hist.filter(h => new Date(h.ts).toDateString() === today).length;
    const setEl = (id, val) => { const el=document.getElementById(id); if(el) el.textContent=val; };
    setEl('stat-msgs', msgsHoy);
    setEl('stat-archivos', localStorage.getItem('maer_files_count') || 0);
    const docs = document.querySelectorAll('#docs-checklist input[type=checkbox]:checked');
    setEl('stat-docs', docs.length);
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    setEl('stat-mem', hist.length + learned.length);
    setEl('sb-mem', `🧠 ${hist.length} msgs`);
  },

  /* ── GUARDAR EN HISTORIAL ── */
  _saveToHistory(q, a) {
    if (!this.config.aprendizaje) return;
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    hist.push({ q, a, ts: Date.now() });
    if (hist.length > 500) hist.splice(0, hist.length - 500);
    localStorage.setItem('maer_history', JSON.stringify(hist));
  },

  /* ── CHECKLIST ESTADO ── */
  _loadChecklistState() {
    for (let i = 1; i <= 11; i++) {
      const el = document.getElementById(`doc${i}`);
      if (el) el.checked = localStorage.getItem(`maer_doc${i}`) === '1';
    }
    if (this.pension) this.pension.updateDocs();
  },

  /* ── DROP ZONE ── */
  _setupDropZone() {
    const dz = document.getElementById('drop-zone');
    if (!dz) return;
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
    dz.addEventListener('drop', e => {
      e.preventDefault(); dz.classList.remove('drag-over');
      MAER.archivos.handleInputFiles(e.dataTransfer.files);
    });
  },

  /* ══ TABS ══ */
  tabs: {
    show(name) {
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      const panel = document.getElementById(`panel-${name}`);
      if (panel) panel.classList.add('active');
      // Activar botón correspondiente
      document.querySelectorAll('.tab-btn').forEach(b => {
        if (b.dataset.tab === name) b.classList.add('active');
      });
      // Hooks especiales
      if (name === 'sistema')     MAER.sistema.refresh();
      if (name === 'memoria')     { MAER.memoria._render(); MAER.memoria._renderAprendizajes(); }
      if (name === 'aprendizaje') MAER.aprendizaje._renderLista();
      if (name === 'whatsapp')    MAER.whatsapp._renderConversaciones();
      if (name === 'ajustes')     { MAER.ajustes.init(); MAER.notificaciones._actualizarUI(); }
      if (name === 'pension')     { MAER.pension._loadNotas(); MAER.pension._loadEventos(); }
      MAER._updateStats();
    }
  },

  /* ══ API ══ */
  async _call(endpoint, payload, opts = {}) {
    const serverUrl = document.getElementById('cfg-server')?.value?.trim() || this.API;
    try {
      const url = serverUrl + endpoint;
      const options = payload
        ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }
        : { method: 'GET' };
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), opts.timeout || 15000);
      const res = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(timeout);
      return await res.json();
    } catch(e) {
      if (e.name === 'AbortError') return { ok: false, msg: 'Tiempo de espera agotado.' };
      return { ok: false, msg: `Sin conexión: ${e.message}` };
    }
  },

  async _upload(endpoint, formData) {
    const serverUrl = document.getElementById('cfg-server')?.value?.trim() || this.API;
    try {
      const res = await fetch(serverUrl + endpoint, { method: 'POST', body: formData });
      return await res.json();
    } catch(e) {
      return { ok: false, msg: `Error de subida: ${e.message}` };
    }
  },

  /* ══ TOOLTIPS ══ */
  tooltip: {
    _data: {
      'chat-principal': {
        titulo: '💬 Chat con MAER',
        desc: 'Habla con MAER en texto o voz. Pregunta sobre pensión IMSS, documentos, procesos legales, o cualquier tema.',
        pasos: ['Escribe tu pregunta y presiona Enter', 'O usa el micrófono 🎤 para hablar', 'Adjunta un archivo para analizarlo', 'Cambia el modo (Pensión, Legal, etc.)']
      },
      'busqueda-principal': {
        titulo: '🔍 Búsqueda Masiva',
        desc: 'Busca palabras, números o datos dentro de TODOS tus archivos, no solo por nombre.',
        pasos: ['Escribe lo que buscas (ej: "CURP", "IMSS", "2024")', 'Selecciona qué tipos de archivo incluir', 'Elige buscar en nombre o dentro del contenido', 'Selecciona resultados y muévelos a una carpeta']
      },
      'archivos-principal': {
        titulo: '📂 Análisis de Archivos',
        desc: 'Sube cualquier archivo y MAER lo analiza: detecta CURP, RFC, fechas, muestra vista previa.',
        pasos: ['Haz clic en "Elegir Archivo" para abrir el Finder', 'O arrastra archivos al área de carga', 'MAER muestra la vista previa al instante', 'Activa las opciones de análisis que necesites']
      },
      'aprendizaje-principal': {
        titulo: '📚 Aprendizaje Permanente',
        desc: 'Dale documentos a MAER para que los memorice. Nunca los olvidará, los usa en el chat.',
        pasos: ['Sube PDF, TXT, Word, JSON, etc.', 'MAER extrae el texto completo', 'El contenido queda guardado permanentemente', 'En el chat, MAER usa lo aprendido como contexto']
      },
      'tareas-principal': {
        titulo: '🤖 Tareas IA',
        desc: 'MAER realiza investigaciones y crea documentos por ti. Investigación legal, cartas, análisis.',
        pasos: ['Elige el tipo de tarea', 'Describe qué necesitas', 'Adjunta documentos relevantes si aplica', 'MAER genera el resultado y lo puedes guardar como archivo']
      },
      'pension-cartas': {
        titulo: '✉️ Generador de Cartas',
        desc: 'Genera cartas oficiales para el IMSS con tus datos personales.',
        pasos: ['Llena tus datos (nombre, NSS, CURP)', 'Elige el tipo de carta', 'Revisa el texto generado', 'Copia o imprime para presentar en el IMSS']
      },
      'organizar-principal': {
        titulo: '🗂️ Organizador de Documentos',
        desc: 'MAER analiza una carpeta y sugiere cómo organizarla por tipo de archivo.',
        pasos: ['Elige la carpeta a organizar', 'MAER analiza todos los archivos', 'Revisa la propuesta de organización', 'MAER crea una COPIA organizada — los originales quedan intactos']
      },
    },

    show(clave, event) {
      event?.stopPropagation();
      const d = this._data[clave];
      if (!d) return;
      const ol = document.createElement('div');
      ol.className = 'tooltip-overlay';
      ol.innerHTML = `
        <div class="tooltip-box">
          <h3>${d.titulo}</h3>
          <p>${d.desc}</p>
          ${d.pasos ? `<ul>${d.pasos.map(p=>`<li>${p}</li>`).join('')}</ul>` : ''}
          <div style="margin-top:14px;text-align:right">
            <button class="btn btn-primary btn-sm" onclick="this.closest('.tooltip-overlay').remove()">Entendido ✓</button>
          </div>
        </div>`;
      ol.addEventListener('click', e => { if(e.target === ol) ol.remove(); });
      document.body.appendChild(ol);
    }
  },
};

/* ── ARRANCAR AL CARGAR ── */
window.addEventListener('load', () => MAER.init());
