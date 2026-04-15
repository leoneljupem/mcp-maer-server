/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo de Etiquetas en Documentos
   BLOQUE 14 — Clasificación y filtrado por etiquetas
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.etiquetas = {

  datos: {},       // { docId: ['etiqueta1', 'etiqueta2'] }
  STORAGE_KEY: 'maer_etiquetas',

  /* ── Etiquetas predefinidas para documentos de pensión ── */
  PREDEFINIDAS: [
    { nombre: 'IMSS',          color: '#38bdf8', icon: '🏛️' },
    { nombre: 'Urgente',       color: '#f87171', icon: '🔴' },
    { nombre: 'Ley 73',        color: '#a78bfa', icon: '⚖️' },
    { nombre: 'Ley 97',        color: '#818cf8', icon: '⚖️' },
    { nombre: 'INFONAVIT',     color: '#34d399', icon: '🏠' },
    { nombre: 'PROFEDET',      color: '#fbbf24', icon: '🏢' },
    { nombre: 'Carta',         color: '#fb923c', icon: '📝' },
    { nombre: 'Acuse',         color: '#94a3b8', icon: '📋' },
    { nombre: 'Resolución',    color: '#e879f9', icon: '📄' },
    { nombre: 'Semanas',       color: '#2dd4bf', icon: '📊' },
    { nombre: 'Recurso',       color: '#f472b6', icon: '⚡' },
    { nombre: 'Personal',      color: '#60a5fa', icon: '👤' },
  ],

  /* ── INIT ── */
  init() {
    this._cargar();
  },

  /* ── ASIGNAR etiqueta a documento ── */
  asignar(docId, etiqueta) {
    if (!docId || !etiqueta) return false;
    const norm = etiqueta.trim();
    if (!this.datos[docId]) this.datos[docId] = [];
    if (this.datos[docId].includes(norm)) return false; // ya existe
    this.datos[docId].push(norm);
    this._guardar();
    return true;
  },

  /* ── QUITAR etiqueta de documento ── */
  quitar(docId, etiqueta) {
    if (!this.datos[docId]) return false;
    const idx = this.datos[docId].indexOf(etiqueta.trim());
    if (idx === -1) return false;
    this.datos[docId].splice(idx, 1);
    if (this.datos[docId].length === 0) delete this.datos[docId];
    this._guardar();
    return true;
  },

  /* ── OBTENER etiquetas de un documento ── */
  obtener(docId) {
    return this.datos[docId] || [];
  },

  /* ── BUSCAR documentos por etiqueta ── */
  buscarPorEtiqueta(etiqueta) {
    const norm = etiqueta.trim().toLowerCase();
    const resultados = [];
    for (const [docId, tags] of Object.entries(this.datos)) {
      if (tags.some(t => t.toLowerCase() === norm)) {
        resultados.push(docId);
      }
    }
    return resultados;
  },

  /* ── LISTAR todas las etiquetas usadas ── */
  listarUsadas() {
    const set = new Set();
    for (const tags of Object.values(this.datos)) {
      tags.forEach(t => set.add(t));
    }
    return Array.from(set).sort();
  },

  /* ── ESTADÍSTICAS ── */
  stats() {
    const usadas = this.listarUsadas();
    const totalDocs = Object.keys(this.datos).length;
    const conteo = {};
    for (const tags of Object.values(this.datos)) {
      tags.forEach(t => { conteo[t] = (conteo[t] || 0) + 1; });
    }
    return { totalDocs, totalEtiquetas: usadas.length, conteo };
  },

  /* ── RENDER: generar HTML de etiquetas para un documento ── */
  renderTags(docId, editable = true) {
    const tags = this.obtener(docId);
    let html = '<div class="etiquetas-wrap">';

    tags.forEach(tag => {
      const pre = this.PREDEFINIDAS.find(p => p.nombre.toLowerCase() === tag.toLowerCase());
      const color = pre ? pre.color : '#64748b';
      const icon = pre ? pre.icon : '🏷️';
      html += `<span class="etiqueta-badge" style="--tag-color:${color}" title="${tag}">
        ${icon} ${tag}
        ${editable ? `<button class="etiqueta-remove" onclick="MAER.etiquetas._quitarUI('${docId}','${tag}')" title="Quitar">&times;</button>` : ''}
      </span>`;
    });

    if (editable) {
      html += `<button class="etiqueta-add-btn" onclick="MAER.etiquetas._mostrarSelector('${docId}')" title="Agregar etiqueta">+ Etiqueta</button>`;
    }

    html += '</div>';
    return html;
  },

  /* ── RENDER: panel de etiquetas en pestaña Aprendizaje ── */
  render() {
    const panel = document.getElementById('etiquetas-panel');
    if (!panel) return;

    const stats = this.stats();
    let html = `
      <div style="margin-bottom:12px">
        <span style="color:var(--muted);font-size:12px">
          📊 ${stats.totalDocs} documentos etiquetados · ${stats.totalEtiquetas} etiquetas en uso
        </span>
      </div>`;

    // Etiquetas predefinidas
    html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px">';
    this.PREDEFINIDAS.forEach(p => {
      const count = stats.conteo[p.nombre] || 0;
      html += `<span class="etiqueta-badge etiqueta-clickable" style="--tag-color:${p.color}"
        onclick="MAER.etiquetas._filtrarUI('${p.nombre}')" title="Filtrar por ${p.nombre}">
        ${p.icon} ${p.nombre} <small>(${count})</small>
      </span>`;
    });
    html += '</div>';

    // Documentos etiquetados
    if (stats.totalDocs > 0) {
      html += '<div class="etiquetas-lista">';
      for (const [docId, tags] of Object.entries(this.datos)) {
        html += `<div class="etiqueta-doc-item">
          <span class="etiqueta-doc-name" title="${docId}">${docId.length > 30 ? docId.substring(0,30)+'...' : docId}</span>
          ${this.renderTags(docId, true)}
        </div>`;
      }
      html += '</div>';
    } else {
      html += '<div style="color:var(--muted);font-size:13px;text-align:center;padding:20px">No hay documentos etiquetados aún. Usa el botón "+ Etiqueta" al ver archivos.</div>';
    }

    panel.innerHTML = html;
  },

  /* ── UI helpers ── */
  _mostrarSelector(docId) {
    // Crear un mini-dropdown con etiquetas predefinidas
    const existing = this.obtener(docId);
    const disponibles = this.PREDEFINIDAS.filter(p => !existing.includes(p.nombre));

    if (!disponibles.length) {
      MAER.voz?.hablar('Este documento ya tiene todas las etiquetas disponibles.');
      return;
    }

    // Prompt simple (en futuro: dropdown visual)
    const opciones = disponibles.map((p, i) => `${i+1}. ${p.icon} ${p.nombre}`).join('\n');
    const sel = prompt(`Selecciona etiqueta para "${docId}":\n\n${opciones}\n\nEscribe el nombre o número:`);
    if (!sel) return;

    // Buscar por número o nombre
    const num = parseInt(sel);
    let etiqueta;
    if (!isNaN(num) && num >= 1 && num <= disponibles.length) {
      etiqueta = disponibles[num - 1].nombre;
    } else {
      etiqueta = sel.trim();
    }

    if (etiqueta) {
      this.asignar(docId, etiqueta);
      this.render();
      MAER.voz?.hablar(`Etiqueta ${etiqueta} asignada.`);
    }
  },

  _quitarUI(docId, etiqueta) {
    this.quitar(docId, etiqueta);
    this.render();
  },

  _filtrarUI(etiqueta) {
    const docs = this.buscarPorEtiqueta(etiqueta);
    if (!docs.length) {
      MAER.chat?._addMsg('maer', `🏷️ No hay documentos con la etiqueta "<strong>${etiqueta}</strong>".`);
    } else {
      const lista = docs.map(d => `• ${d}`).join('<br>');
      MAER.chat?._addMsg('maer', `🏷️ Documentos con etiqueta "<strong>${etiqueta}</strong>":<br>${lista}`);
    }
  },

  /* ── PERSISTENCIA ── */
  _guardar() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.datos));
    } catch(e) {}
  },

  _cargar() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (raw) this.datos = JSON.parse(raw);
    } catch(e) {
      this.datos = {};
    }
  }
};
