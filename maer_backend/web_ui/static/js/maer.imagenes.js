/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo de Imágenes y OCR
   Análisis visual, extracción de texto, detección de datos
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.imagenes = {

  imagenActual: null,

  /* ── MANEJAR IMAGEN SUBIDA ── */
  async handleImagen(file) {
    if (!file) return;
    this.imagenActual = file;

    const preview = document.getElementById('img-preview');
    const info    = document.getElementById('img-info');

    if (preview) {
      const url = URL.createObjectURL(file);
      preview.innerHTML = `<img src="${url}" style="max-width:100%;max-height:340px;border-radius:8px;border:1px solid var(--border);display:block;margin:0 auto">`;
    }

    if (info) {
      info.innerHTML = `<div style="font-size:12px;color:var(--muted);margin-top:8px;text-align:center">
        📷 <strong>${file.name}</strong> · ${this._fmtSize(file.size)} · ${file.type || 'imagen'}
      </div>`;
    }

    // Auto-analizar con Canvas
    await this._analizarCanvas(file);
  },

  /* ── ANÁLISIS BÁSICO CON CANVAS ── */
  async _analizarCanvas(file) {
    const area = document.getElementById('img-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔍 Analizando imagen...</div>';

    return new Promise(resolve => {
      const img   = new Image();
      const url   = URL.createObjectURL(file);
      img.onload  = () => {
        const canvas = document.createElement('canvas');
        const ctx    = canvas.getContext('2d');

        // Reducir a 300x300 para análisis rápido
        const MAX = 300;
        const ratio = Math.min(MAX / img.width, MAX / img.height, 1);
        canvas.width  = Math.round(img.width  * ratio);
        canvas.height = Math.round(img.height * ratio);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        const stats = this._colorStats(data);

        area.innerHTML = `
          <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px">
            <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:10px">📊 Análisis de imagen</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:12px">
              ${this._statCard('Dimensiones', `${img.width} × ${img.height} px`)}
              ${this._statCard('Brillo', stats.brightness + '%')}
              ${this._statCard('Contraste', stats.contrast)}
              ${this._statCard('Color dom.', stats.dominante)}
            </div>
            <div style="font-size:12px;color:var(--muted)">${stats.descripcion}</div>
          </div>`;

        URL.revokeObjectURL(url);
        resolve();
      };
      img.onerror = () => {
        area.innerHTML = '<div class="alert alert-danger">No se pudo cargar la imagen.</div>';
        resolve();
      };
      img.src = url;
    });
  },

  /* ── OCR: EXTRAER TEXTO ── */
  async extraerTexto() {
    if (!this.imagenActual) {
      alert('Primero sube una imagen.');
      return;
    }

    const area = document.getElementById('img-ocr');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔍 Extrayendo texto (OCR)...</div>';

    const btn = document.getElementById('btn-ocr');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Procesando...'; }

    // 1. Intentar con backend (OCR real con Tesseract/easyocr)
    if (MAER.config.backendOK) {
      try {
        const fd = new FormData();
        fd.append('file', this.imagenActual);
        const res = await MAER._upload('/api/learn-file', fd);
        if (res.ok && res.data?.text && res.data.text.length > 5) {
          this._mostrarOCR(res.data.text, area);
          if (btn) { btn.disabled = false; btn.textContent = '🔤 Extraer Texto (OCR)'; }
          return;
        }
      } catch(e) {}
    }

    // 2. Fallback: Tesseract.js CDN (si está disponible)
    if (typeof Tesseract !== 'undefined') {
      try {
        area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔤 Tesseract.js procesando...</div>';
        const result = await Tesseract.recognize(this.imagenActual, 'spa+eng', {
          logger: m => {
            if (m.status === 'recognizing text') {
              area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">🔤 OCR: ${Math.round(m.progress * 100)}%</div>`;
            }
          }
        });
        const text = result.data.text.trim();
        if (text.length > 2) {
          this._mostrarOCR(text, area);
        } else {
          area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">No se detectó texto en la imagen.</div>';
        }
      } catch(e) {
        area.innerHTML = `<div class="alert alert-warning">OCR local falló: ${e.message}</div>`;
      }
    } else {
      area.innerHTML = `<div class="alert alert-warning">
        OCR requiere el servidor activo para archivos complejos.<br>
        <small>Para OCR local, carga Tesseract.js en la configuración.</small>
      </div>`;
    }

    if (btn) { btn.disabled = false; btn.textContent = '🔤 Extraer Texto (OCR)'; }
  },

  /* ── MOSTRAR TEXTO OCR ── */
  _mostrarOCR(texto, area) {
    const datos  = this._extraerDatosTexto(texto);
    let html = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px">
        <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:10px">🔤 Texto extraído</div>`;

    if (datos.curp.length || datos.rfc.length || datos.nss.length) {
      html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">';
      if (datos.curp.length)  html += this._badge('CURP',  datos.curp.join(', '),  'var(--green)');
      if (datos.rfc.length)   html += this._badge('RFC',   datos.rfc.join(', '),   'var(--accent)');
      if (datos.nss.length)   html += this._badge('NSS',   datos.nss.join(', '),   'var(--yellow)');
      html += '</div>';
    }

    html += `<pre style="white-space:pre-wrap;font-size:12px;line-height:1.6;color:var(--text);max-height:260px;overflow-y:auto">${this._escHTML(texto.substring(0, 1500))}${texto.length > 1500 ? '\n...' : ''}</pre>`;

    html += `<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
      <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(${JSON.stringify(texto)}).then(()=>MAER.voz?.hablar('Texto copiado.'))">📋 Copiar</button>
      <button class="btn btn-primary btn-sm" onclick="MAER.imagenes._aprenderTexto(${JSON.stringify(texto)})">📚 Memorizar</button>
    </div>
    </div>`;

    area.innerHTML = html;
    MAER.voz?.hablar(`Texto extraído: ${texto.substring(0, 80)}.`);
  },

  /* ── VISION IA: ANÁLISIS COMPLETO ── */
  async analizarConIA() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-ocr');
    if (!area) return;

    const btn = document.getElementById('btn-vision-ia');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Analizando con IA...'; }
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🧠 Claude Vision analizando la imagen...</div>';

    try {
      // 1. Subir imagen al servidor
      const fd = new FormData();
      fd.append('file', this.imagenActual);
      const uploadRes = await MAER._upload('/api/upload', fd);
      if (!uploadRes.ok || !uploadRes.data?.path) throw new Error('No se pudo subir imagen');
      const serverPath = uploadRes.data.path;

      // 2. Análisis completo con Claude Vision
      const res = await MAER._call('/api/vision-analyze', { path: serverPath }, { timeout: 60000 });
      if (res.ok && res.data?.analysis) {
        this._mostrarVisionIA(res.data.analysis, serverPath, area);
        MAER.voz?.hablar('Análisis visual completado.');
      } else {
        area.innerHTML = `<div class="alert alert-danger">Error en análisis visual: ${res.msg || 'Sin respuesta'}</div>`;
      }
    } catch(e) {
      area.innerHTML = `<div class="alert alert-warning">
        🧠 Análisis IA requiere servidor activo y ANTHROPIC_API_KEY configurada.<br>
        <small>${e.message}</small>
      </div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🧠 Analizar con IA'; }
    }
  },

  /* ── VISION IA: OCR AVANZADO ── */
  async extraerTextoIA() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-ocr');
    if (!area) return;

    const btn = document.getElementById('btn-vision-ocr');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Extrayendo...'; }
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🧠 Claude Vision extrayendo texto...</div>';

    try {
      const fd = new FormData();
      fd.append('file', this.imagenActual);
      const uploadRes = await MAER._upload('/api/upload', fd);
      if (!uploadRes.ok || !uploadRes.data?.path) throw new Error('No se pudo subir imagen');

      const res = await MAER._call('/api/vision-ocr', { path: uploadRes.data.path }, { timeout: 60000 });
      if (res.ok && res.data?.text) {
        this._mostrarOCR(res.data.text, area);
        area.querySelector && area.querySelector('pre') &&
          (area.innerHTML += `<div style="font-size:11px;color:var(--muted);margin-top:6px">Motor: Claude Vision · ${res.data.chars} caracteres</div>`);
      } else {
        area.innerHTML = `<div class="alert alert-warning">No se pudo extraer texto: ${res.msg || ''}</div>`;
      }
    } catch(e) {
      area.innerHTML = `<div class="alert alert-warning">Error: ${e.message}</div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🧠 OCR con IA'; }
    }
  },

  /* ── VISION IA: CLASIFICAR DOCUMENTO ── */
  async clasificarDocumento() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-resultado');
    if (!area) return;

    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔍 Clasificando documento...</div>';

    try {
      const fd = new FormData();
      fd.append('file', this.imagenActual);
      const uploadRes = await MAER._upload('/api/upload', fd);
      if (!uploadRes.ok || !uploadRes.data?.path) throw new Error('No se pudo subir');

      const res = await MAER._call('/api/vision-classify', { path: uploadRes.data.path }, { timeout: 30000 });
      if (res.ok && res.data) {
        const d = res.data;
        area.innerHTML = `
          <div style="background:var(--surface);border:1px solid var(--accent);border-radius:8px;padding:14px">
            <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:10px">🔍 Tipo de documento detectado</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px">
              ${d.tipo ? this._statCard('Tipo', d.tipo) : ''}
              ${d.institución ? this._statCard('Institución', d.institución) : ''}
              ${d.nombre_titular ? this._statCard('Titular', d.nombre_titular) : ''}
              ${d.fecha ? this._statCard('Fecha', d.fecha) : ''}
              ${d.legibilidad ? this._statCard('Legibilidad', d.legibilidad) : ''}
            </div>
            ${d.datos_clave ? `<div style="margin-top:10px;font-size:12px;color:var(--muted)">Datos clave: ${this._escHTML(d.datos_clave)}</div>` : ''}
          </div>`;
        MAER.voz?.hablar(`Documento identificado como ${d.tipo || 'desconocido'}.`);
      }
    } catch(e) {
      area.innerHTML = `<div class="alert alert-warning">Error clasificando: ${e.message}</div>`;
    }
  },

  /* ── MOSTRAR RESULTADO VISION IA ── */
  _mostrarVisionIA(analysis, path, area) {
    const datos = this._extraerDatosTexto(analysis);
    area.innerHTML = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px">
        <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:10px">🧠 Análisis Claude Vision</div>
        ${datos.curp.length || datos.nss.length || datos.rfc.length ? `
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          ${datos.curp.length ? this._badge('CURP', datos.curp.join(', '), 'var(--green)') : ''}
          ${datos.rfc.length  ? this._badge('RFC',  datos.rfc.join(', '),  'var(--accent)') : ''}
          ${datos.nss.length  ? this._badge('NSS',  datos.nss.join(', '),  'var(--yellow)') : ''}
        </div>` : ''}
        <div style="font-size:12px;line-height:1.7;color:var(--text);white-space:pre-wrap;max-height:300px;overflow-y:auto">${this._escHTML(analysis)}</div>
        <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
          <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(${JSON.stringify(analysis)})">📋 Copiar</button>
          <button class="btn btn-primary btn-sm" onclick="MAER.imagenes._aprenderTexto(${JSON.stringify(analysis)})">📚 Memorizar</button>
        </div>
      </div>`;
  },

  /* ── MEMORIZAR TEXTO DE IMAGEN ── */
  async _aprenderTexto(texto) {
    if (!this.imagenActual) return;
    await MAER.aprendizaje.guardar({
      nombre:   this.imagenActual.name + ' (OCR)',
      etiqueta: this.imagenActual.name,
      texto:    texto.substring(0, 10000),
      chars:    texto.length,
      tipo:     'ocr',
    });
    MAER.aprendizaje._renderLista();
    MAER.chat._addMsg('sys', `📚 Texto de imagen <strong>${this.imagenActual.name}</strong> guardado en memoria.`);
    MAER.voz?.hablar('Texto de imagen memorizado.');
  },

  /* ── ESTADÍSTICAS DE COLOR ── */
  _colorStats(data) {
    let r = 0, g = 0, b = 0, pixels = data.length / 4;
    for (let i = 0; i < data.length; i += 4) {
      r += data[i]; g += data[i+1]; b += data[i+2];
    }
    r = Math.round(r / pixels);
    g = Math.round(g / pixels);
    b = Math.round(b / pixels);
    const brightness = Math.round((r * 0.299 + g * 0.587 + b * 0.114) / 2.55);

    let dominante = 'Neutro';
    if (r > g && r > b) dominante = 'Rojo/Cálido';
    else if (g > r && g > b) dominante = 'Verde';
    else if (b > r && b > g) dominante = 'Azul/Frío';
    else if (brightness > 70) dominante = 'Blanco/Claro';
    else if (brightness < 30) dominante = 'Negro/Oscuro';

    let contraste = 'Bajo';
    if (brightness > 20 && brightness < 80) contraste = 'Medio';
    if (brightness > 40 && brightness < 70) contraste = 'Bueno';

    let descripcion = '';
    if (brightness > 70) descripcion = 'Imagen clara, fondo probable blanco o claro.';
    else if (brightness < 30) descripcion = 'Imagen oscura, puede contener texto blanco o colores vivos.';
    else descripcion = 'Imagen con contraste equilibrado, buena para OCR.';

    return { brightness, contraste, dominante, descripcion };
  },

  _extraerDatosTexto(texto) {
    return {
      curp:  (texto.match(/[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      rfc:   (texto.match(/[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      nss:   (texto.match(/\b\d{11}\b/g) || []).filter((v,i,a) => a.indexOf(v)===i).slice(0,3),
    };
  },

  _statCard(label, val) {
    return `<div style="background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px;text-align:center">
      <div style="font-size:10px;color:var(--muted);margin-bottom:4px">${label}</div>
      <div style="font-size:13px;font-weight:600;color:var(--text)">${val}</div>
    </div>`;
  },

  _badge(label, val, color) {
    return `<div style="background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:6px 10px">
      <div style="font-size:10px;color:${color};font-weight:600">${label}</div>
      <div style="font-size:12px;color:var(--text);font-family:monospace">${val}</div>
    </div>`;
  },

  /* ── ESCANEAR QR / CÓDIGO DE BARRAS ── */
  async escanearCodigos() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔍 Detectando códigos QR y barras…</div>';
    const fd = new FormData();
    fd.append('file', this.imagenActual);
    const uploadRes = await MAER._upload('/api/upload', fd);
    if (!uploadRes.ok) { area.innerHTML = `<div class="alert alert-warning">Error subiendo: ${uploadRes.msg}</div>`; return; }
    const res = await MAER._call('/api/barcode-scan', { path: uploadRes.data.path }, { timeout: 20000 });
    if (res.ok && res.data?.count > 0) {
      const items = res.data.codes.map(c => `
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:8px;margin-bottom:6px">
          <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
            <span class="badge badge-blue">${c.type}</span>
            ${c.tipo && c.tipo !== 'GENERAL' ? `<span class="badge badge-green">${c.tipo}</span>` : ''}
          </div>
          <code style="font-size:12px;word-break:break-all;color:var(--accent)">${this._escHTML(c.data)}</code>
        </div>`).join('');
      area.innerHTML = `<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px">
        <div style="font-size:13px;font-weight:600;color:var(--green);margin-bottom:10px">✅ ${res.data.count} código(s) detectado(s)</div>
        ${items}</div>`;
    } else {
      area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">📭 No se encontraron códigos QR ni barras en la imagen.</div>`;
    }
  },

  /* ── ANÁLISIS COMPLETO DE IMAGEN ── */
  async analizarCompleto() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔬 Análisis exhaustivo en curso…</div>';
    const fd = new FormData();
    fd.append('file', this.imagenActual);
    const uploadRes = await MAER._upload('/api/upload', fd);
    if (!uploadRes.ok) { area.innerHTML = `<div class="alert alert-warning">Error: ${uploadRes.msg}</div>`; return; }
    const res = await MAER._call('/api/image-intelligence', { path: uploadRes.data.path, ocr: true }, { timeout: 90000 });
    if (!res.ok) { area.innerHTML = `<div class="alert alert-warning">Error: ${res.msg}</div>`; return; }
    const d = res.data || {};
    const datos = this._extraerDatosTexto(d.text || '');
    const exifCount = Object.keys(d.exif || {}).length;
    area.innerHTML = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px">
        <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:10px">🔬 Análisis Exhaustivo</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          ${this._statCard('Motor OCR', d.engine || '-')}
          ${this._statCard('Calidad', d.quality ? (d.quality * 100).toFixed(0) + '%' : '-')}
          ${this._statCard('Tipo doc.', d.doc_type || '-')}
          ${this._statCard('EXIF', exifCount + ' campos')}
          ${this._statCard('Códigos', (d.qr_codes?.length || 0) + (d.barcodes?.length || 0))}
        </div>
        ${datos.curp.length ? `<div style="margin-bottom:8px">${this._badge('CURP', datos.curp.join(', '), 'var(--green)')}</div>` : ''}
        ${datos.nss.length  ? `<div style="margin-bottom:8px">${this._badge('NSS',  datos.nss.join(', '),  'var(--gold)')}</div>` : ''}
        ${d.qr_codes?.length ? `<div style="margin-bottom:8px">${this._badge('QR', d.qr_codes.map(c=>c.data).join(' | '), 'var(--purple)')}</div>` : ''}
        ${d.text ? `<div style="font-size:12px;line-height:1.7;color:var(--text);white-space:pre-wrap;max-height:220px;overflow-y:auto;margin-top:8px">${this._escHTML(d.text.substring(0, 1200))}</div>` : ''}
        <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
          ${d.text ? `<button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(${JSON.stringify(d.text || '')})">📋 Copiar texto</button>` : ''}
          ${d.text ? `<button class="btn btn-primary btn-sm" onclick="MAER.imagenes._aprenderTexto(${JSON.stringify(d.text || '')})">📚 Memorizar</button>` : ''}
        </div>
      </div>`;
    MAER.voz?.hablar(`Análisis completo. Documento tipo ${d.doc_type || 'general'}.`);
  },

  /* ── OCR TURBO (Wand + albumentations) ── */
  async ocrTurbo() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">⚡ OCR Turbo: preprocesado máximo…</div>';
    const fd = new FormData();
    fd.append('file', this.imagenActual);
    const uploadRes = await MAER._upload('/api/upload', fd);
    if (!uploadRes.ok) return;
    const res = await MAER._call('/api/preprocess-turbo', { path: uploadRes.data.path }, { timeout: 60000 });
    if (res.ok && res.data?.text) {
      this._mostrarVisionIA(res.data.text, uploadRes.data.path, area);
    } else {
      area.innerHTML = `<div class="alert alert-warning">OCR Turbo no extrajo texto. ${res.msg || ''}</div>`;
    }
  },

  /* ══════════════════════════════════════════════════════════════
     OCR PRO — Ensemble de motores + Preprocesado Adaptativo
  ══════════════════════════════════════════════════════════════ */

  /* ── OCR PRO: ensemble automático ── */
  async ocrPro(mode) {
    if (!this.imagenActual) { alert('Primero sube una imagen o PDF.'); return; }
    const area = document.getElementById('img-resultado');
    if (!area) return;
    const modeLabel = mode || 'auto';
    area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">🔬 OCR Pro [${modeLabel}]: ensemble en curso…</div>`;

    const fd = new FormData();
    fd.append('file', this.imagenActual);

    const url = `/api/ocr-pro?mode=${modeLabel}&preprocess=true`;
    const res = await MAER._upload(url, fd, { timeout: 120000 });

    if (!res.ok) {
      area.innerHTML = `<div class="alert alert-warning">❌ Error OCR Pro: ${res.msg || 'Sin respuesta'}</div>`;
      return;
    }

    const d = res.data || {};
    const calidad = d.quality ? (d.quality * 100).toFixed(0) + '%' : '-';
    const confianza = d.confidence ? (d.confidence * 100).toFixed(0) + '%' : '-';
    const datos = this._extraerDatosTexto(d.text || '');

    // Tabla de motores usados
    const allRows = (d.all_results || []).map(r => {
      const icono = r.ok ? (r.quality >= 0.72 ? '✅' : r.quality >= 0.45 ? '🟡' : '🔴') : '❌';
      return `<tr>
        <td style="padding:3px 8px;font-weight:600">${icono} ${r.engine}</td>
        <td style="padding:3px 8px;text-align:right">${r.ok ? (r.quality*100).toFixed(0)+'%' : '—'}</td>
        <td style="padding:3px 8px;text-align:right">${r.ok ? (r.confidence*100).toFixed(0)+'%' : '—'}</td>
        <td style="padding:3px 8px;text-align:right">${r.ok ? r.char_count : (r.error||'❌').substring(0,30)}</td>
      </tr>`;
    }).join('');

    const pasos = (d.steps || []).join(' → ') || '-';

    area.innerHTML = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px">
        <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:10px">🔬 OCR Pro — Resultado Ensemble</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          ${this._statCard('Motor final', d.engine_used || '-')}
          ${this._statCard('Calidad', calidad)}
          ${this._statCard('Confianza', confianza)}
          ${this._statCard('Chars', d.char_count || 0)}
          ${this._statCard('Tiempo', (d.elapsed_ms || 0) + 'ms')}
          ${this._statCard('Modo', d.mode_used || mode || 'auto')}
        </div>
        <div style="font-size:11px;color:var(--muted);margin-bottom:10px">⚙️ Pasos: ${this._escHTML(pasos)}</div>
        ${allRows ? `
        <div style="margin-bottom:10px;overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;font-size:12px">
            <thead><tr style="background:var(--bg);color:var(--muted)">
              <th style="padding:3px 8px;text-align:left">Motor</th>
              <th style="padding:3px 8px;text-align:right">Calidad</th>
              <th style="padding:3px 8px;text-align:right">Confianza</th>
              <th style="padding:3px 8px;text-align:right">Chars / Error</th>
            </tr></thead>
            <tbody>${allRows}</tbody>
          </table>
        </div>` : ''}
        ${datos.curp.length ? `<div style="margin-bottom:6px">${this._badge('CURP', datos.curp.join(', '), 'var(--green)')}</div>` : ''}
        ${datos.nss.length  ? `<div style="margin-bottom:6px">${this._badge('NSS',  datos.nss.join(', '),  'var(--gold)')}</div>` : ''}
        ${d.text ? `<div style="font-size:12px;line-height:1.7;color:var(--text);white-space:pre-wrap;max-height:260px;overflow-y:auto;border-top:1px solid var(--border);padding-top:10px;margin-top:8px">${this._escHTML(d.text.substring(0, 2000))}</div>` : '<div style="color:var(--muted);font-size:13px;margin-top:8px">Sin texto extraído.</div>'}
        <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
          ${d.text ? `<button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(${JSON.stringify(d.text||'')})">📋 Copiar texto</button>` : ''}
          ${d.text ? `<button class="btn btn-primary btn-sm" onclick="MAER.imagenes._aprenderTexto(${JSON.stringify(d.text||'')})">📚 Memorizar</button>` : ''}
          <button class="btn btn-secondary btn-sm" onclick="MAER.imagenes.ocrComparar()">🆚 Comparar motores</button>
        </div>
      </div>`;
    if (d.text) MAER.voz?.hablar(`OCR Pro completo. ${d.char_count} caracteres extraídos con ${d.engine_used}.`);
  },

  /* ── OCR COMPARAR: side-by-side de todos los motores ── */
  async ocrComparar() {
    if (!this.imagenActual) { alert('Primero sube una imagen.'); return; }
    const area = document.getElementById('img-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🆚 Comparando todos los motores OCR…</div>';

    const fd = new FormData();
    fd.append('file', this.imagenActual);
    const res = await MAER._upload('/api/ocr-compare?mode=auto&preprocess=true', fd, { timeout: 180000 });

    if (!res.ok) {
      area.innerHTML = `<div class="alert alert-warning">❌ Error: ${res.msg}</div>`;
      return;
    }

    const d = res.data || {};
    const ranking = d.ranking || [];
    const results = d.results || {};

    // Generar cards por motor
    const cards = Object.entries(results).map(([eng, r]) => {
      const rank = ranking.findIndex(x => x.engine === eng);
      const medal = rank === 0 ? '🥇' : rank === 1 ? '🥈' : rank === 2 ? '🥉' : '  ';
      const color = r.ok ? (r.quality >= 0.72 ? 'var(--green)' : r.quality >= 0.45 ? 'var(--gold)' : 'var(--red)') : 'var(--muted)';
      return `
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;flex:1;min-width:200px">
          <div style="font-size:13px;font-weight:700;color:${color};margin-bottom:6px">${medal} ${eng}</div>
          ${r.ok ? `
            <div style="font-size:11px;color:var(--muted);margin-bottom:4px">Calidad: <strong>${(r.quality*100).toFixed(0)}%</strong> · Chars: <strong>${r.char_count}</strong></div>
            <div style="font-size:11px;color:var(--text);white-space:pre-wrap;max-height:120px;overflow-y:auto;word-break:break-word">${this._escHTML(r.text||'').substring(0,300)}</div>
          ` : `<div style="font-size:11px;color:var(--red)">${this._escHTML(r.error||'No disponible')}</div>`}
        </div>`;
    }).join('');

    area.innerHTML = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px">
        <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:4px">🆚 Comparación de Motores OCR</div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:10px">Mejor motor: <strong style="color:var(--green)">${d.best_engine || '?'}</strong> · Pasos: ${(d.steps||[]).join(' → ')||'-'} · Tiempo: ${d.elapsed_ms||0}ms</div>
        <div style="display:flex;flex-wrap:wrap;gap:10px">${cards}</div>
        <button class="btn btn-primary btn-sm" style="margin-top:12px" onclick="MAER.imagenes.ocrPro('${d.best_engine||'auto'}')">
          ✅ Usar ${d.best_engine||'mejor motor'} para este documento
        </button>
      </div>`;
  },

  /* ── ESTADO DE MOTORES OCR PRO ── */
  async mostrarEstadoOCR() {
    const area = document.getElementById('img-resultado');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔍 Verificando motores OCR…</div>';

    const res = await MAER._call('/api/ocr-pro-status', {});
    if (!res.ok) {
      area.innerHTML = `<div class="alert alert-warning">Error: ${res.msg}</div>`;
      return;
    }

    const d = res.data || {};
    const engines = d.engines || {};
    const rows = Object.entries(engines).map(([eng, info]) => {
      const icono = info.available ? '✅' : '❌';
      const ver   = info.version ? `v${info.version}` : '';
      const inst  = info.install ? `<button class="btn btn-secondary btn-sm" style="font-size:10px;padding:2px 6px" onclick="MAER.imagenes._instalarMotor('${eng}')">Instalar</button>` : '';
      return `<tr>
        <td style="padding:4px 8px;font-weight:600">${icono} ${eng}</td>
        <td style="padding:4px 8px;color:var(--muted)">${ver}</td>
        <td style="padding:4px 8px">${inst || (info.available ? '<span style="color:var(--green);font-size:11px">Listo</span>' : '<span style="color:var(--muted);font-size:11px">—</span>')}</td>
      </tr>`;
    }).join('');

    area.innerHTML = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px">
        <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:8px">⚙️ Motores OCR Pro — ${d.available_count}/${d.total} disponibles</div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:10px">Activos: <strong>${(d.ready||[]).join(', ')||'ninguno'}</strong></div>
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead><tr style="background:var(--bg);color:var(--muted)">
            <th style="padding:4px 8px;text-align:left">Motor</th>
            <th style="padding:4px 8px;text-align:left">Versión</th>
            <th style="padding:4px 8px;text-align:left">Acción</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  },

  async _instalarMotor(engine) {
    if (!confirm(`¿Instalar motor OCR '${engine}'?\nEsto ejecutará pip install y puede tardar varios minutos.`)) return;
    const area = document.getElementById('img-resultado');
    if (area) area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">📦 Instalando ${engine}… (puede tardar 2-5 min)</div>`;
    const res = await MAER._call('/api/ocr-install-engine', { engine }, { timeout: 300000 });
    if (res.ok) {
      if (area) area.innerHTML = `<div class="alert alert-success">✅ Motor '${engine}' instalado. Recarga MAER para usarlo.</div>`;
    } else {
      if (area) area.innerHTML = `<div class="alert alert-warning">❌ Error instalando '${engine}': ${res.msg}</div>`;
    }
  },

  _fmtSize(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
    return (b/1048576).toFixed(1) + ' MB';
  },

  _escHTML(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
