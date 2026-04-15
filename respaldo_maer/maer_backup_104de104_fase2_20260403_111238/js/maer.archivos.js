/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo de Archivos
   Vista previa, análisis de CURP/RFC/NSS, detección de datos
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.archivos = {

  archivosActuales: [],
  previewActual: null,

  /* ── MANEJAR INPUT DE ARCHIVOS ── */
  handleInputFiles(files) {
    if (!files || !files.length) return;
    this.archivosActuales = Array.from(files);
    this._renderArchivos();
  },

  /* ── RENDERIZAR LISTA DE ARCHIVOS ── */
  _renderArchivos() {
    const lista = document.getElementById('archivos-lista');
    if (!lista) return;
    lista.innerHTML = '';

    if (!this.archivosActuales.length) {
      lista.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:12px">Sin archivos cargados.</div>';
      return;
    }

    this.archivosActuales.forEach((file, i) => {
      const ext = file.name.split('.').pop().toLowerCase();
      const icons = {pdf:'📄',txt:'📝',json:'📋',js:'📜',py:'🐍',docx:'📄',xlsx:'📊',
                     csv:'📊',md:'📝',png:'🖼️',jpg:'🖼️',jpeg:'🖼️',gif:'🖼️',
                     mp3:'🎵',mp4:'🎬',zip:'📦',xml:'📋',html:'🌐'};
      const icon = icons[ext] || '📁';
      const size = this._fmtSize(file.size);

      const item = document.createElement('div');
      item.className = 'archivo-item';
      item.innerHTML = `
        <div class="archivo-icon">${icon}</div>
        <div class="archivo-info">
          <div class="archivo-nombre">${file.name}</div>
          <div class="archivo-meta">${ext.toUpperCase()} · ${size}</div>
        </div>
        <div style="display:flex;gap:6px;flex-shrink:0">
          <button class="btn btn-secondary btn-sm" onclick="MAER.archivos._previsualizar(${i})">👁️ Ver</button>
          <button class="btn btn-primary btn-sm" onclick="MAER.archivos._analizar(${i})">🔍 Analizar</button>
        </div>`;
      lista.appendChild(item);
    });
  },

  /* ── PREVISUALIZAR ARCHIVO ── */
  async _previsualizar(idx) {
    const file = this.archivosActuales[idx];
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    const area = document.getElementById('archivo-preview');
    if (!area) return;

    area.innerHTML = `<div style="color:var(--muted);font-size:12px;margin-bottom:8px">📎 <strong>${file.name}</strong> · ${this._fmtSize(file.size)}</div>`;

    if (['png','jpg','jpeg','gif','webp','bmp'].includes(ext)) {
      const url = URL.createObjectURL(file);
      area.innerHTML += `<img src="${url}" style="max-width:100%;max-height:400px;border-radius:8px;border:1px solid var(--border)">`;
    }
    else if (['txt','md','csv','json','js','py','html','css','xml'].includes(ext)) {
      try {
        const texto = await file.text();
        const preview = texto.substring(0, 2000) + (texto.length > 2000 ? '\n\n...[truncado]' : '');
        area.innerHTML += `<pre style="white-space:pre-wrap;font-size:12px;line-height:1.7;color:var(--text);background:var(--surface);padding:12px;border-radius:8px;overflow:auto;max-height:380px">${this._escHTML(preview)}</pre>`;
      } catch(e) {
        area.innerHTML += `<div class="alert alert-danger">Error leyendo archivo: ${e.message}</div>`;
      }
    }
    else if (ext === 'pdf') {
      area.innerHTML += `<div style="color:var(--muted);font-size:13px;padding:12px">
        📄 Archivo PDF. Para ver su contenido completo, usa el botón <strong>Analizar</strong> (requiere servidor activo).
        <br><br><em>Previsualización de PDF disponible en el navegador:</em>
        <br><object data="${URL.createObjectURL(file)}" type="application/pdf" width="100%" height="400px" style="border-radius:8px;margin-top:8px"></object>
      </div>`;
    }
    else {
      area.innerHTML += `<div style="color:var(--muted);font-size:13px;padding:12px">
        Vista previa no disponible para este tipo de archivo (<strong>${ext.toUpperCase()}</strong>).
        Usa <strong>Analizar</strong> para extraer información con el servidor.
      </div>`;
    }
  },

  /* ── ANALIZAR ARCHIVO ── */
  async _analizar(idx) {
    const file = this.archivosActuales[idx];
    if (!file) return;

    const area = document.getElementById('archivo-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px">🔍 Analizando...</div>';

    const ext = file.name.split('.').pop().toLowerCase();

    // 1. Intentar con backend
    if (MAER.config.backendOK) {
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await MAER._upload('/api/learn-file', fd);
        if (res.ok && res.data?.text) {
          this._mostrarAnalisis(file.name, res.data.text, area);
          return;
        }
      } catch(e) {}
    }

    // 2. Leer localmente si es texto
    const textExts = ['txt','md','csv','json','js','py','html','css','xml'];
    if (textExts.includes(ext)) {
      try {
        const texto = await file.text();
        this._mostrarAnalisis(file.name, texto, area);
      } catch(e) {
        area.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
      }
    } else {
      area.innerHTML = `<div class="alert alert-warning">
        ⚠️ Para analizar archivos <strong>${ext.toUpperCase()}</strong> necesitas el servidor activo.
        <br>Inicia el servidor MAER y vuelve a intentarlo.
      </div>`;
    }
  },

  /* ── MOSTRAR ANÁLISIS ── */
  _mostrarAnalisis(nombre, texto, area) {
    const datos = this._extraerDatos(texto);
    let html = `<h4 style="color:var(--accent);margin-bottom:12px">📊 Análisis: ${nombre}</h4>`;

    // Datos encontrados
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">';
    if (datos.curp.length)  html += this._badgeList('CURP', datos.curp, 'var(--green)');
    if (datos.rfc.length)   html += this._badgeList('RFC',  datos.rfc,  'var(--accent)');
    if (datos.nss.length)   html += this._badgeList('NSS',  datos.nss,  'var(--yellow)');
    if (datos.fechas.length) html += this._badgeList('Fechas', datos.fechas.slice(0,5), 'var(--muted)');
    if (datos.montos.length) html += this._badgeList('Montos', datos.montos.slice(0,5), 'var(--green)');
    html += '</div>';

    if (!datos.curp.length && !datos.rfc.length && !datos.nss.length) {
      html += '<div style="color:var(--muted);font-size:12px;margin-bottom:10px">No se encontraron CURP, RFC ni NSS en este archivo.</div>';
    }

    html += `<div style="font-size:11px;color:var(--muted)">Caracteres: ${texto.length.toLocaleString()} · Líneas: ${texto.split('\n').length.toLocaleString()}</div>`;
    area.innerHTML = html;
  },

  _badgeList(label, items, color) {
    return `<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 12px;min-width:120px">
      <div style="font-size:10px;color:${color};font-weight:600;margin-bottom:4px">${label}</div>
      ${items.map(v => `<div style="font-size:12px;color:var(--text);font-family:monospace">${v}</div>`).join('')}
    </div>`;
  },

  /* ── EXTRAER DATOS CLAVE ── */
  _extraerDatos(texto) {
    return {
      curp:   (texto.match(/[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      rfc:    (texto.match(/[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      nss:    (texto.match(/\b\d{11}\b/g) || []).filter((v,i,a) => a.indexOf(v)===i).slice(0, 5),
      fechas: (texto.match(/\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      montos: (texto.match(/\$[\d,]+\.?\d{0,2}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
    };
  },

  /* ── SUBIR A APRENDIZAJE ── */
  async aprenderArchivo(idx) {
    const file = this.archivosActuales[idx];
    if (!file) return;
    await MAER.aprendizaje.subirArchivo(file);
  },

  /* ── FORMATO TAMAÑO ── */
  _fmtSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes/1024).toFixed(1) + ' KB';
    return (bytes/1048576).toFixed(1) + ' MB';
  },

  _escHTML(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  },
};
