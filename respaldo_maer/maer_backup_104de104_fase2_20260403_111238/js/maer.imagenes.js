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

  _fmtSize(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
    return (b/1048576).toFixed(1) + ' MB';
  },

  _escHTML(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
