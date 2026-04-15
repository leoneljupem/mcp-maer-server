/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo de Archivos
   Vista previa, análisis REAL con /api/analizar-documento:
   CURP decodificado, RFC validado, pensión, clasificación,
   OCR en imágenes, detección de semanas cotizadas
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.archivos = {

  archivosActuales: [],
  previewActual:    null,
  _ultimoAnalisis:  null,   // Guardamos el último resultado del backend

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
      const ext  = file.name.split('.').pop().toLowerCase();
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
          <button class="btn btn-primary btn-sm"   onclick="MAER.archivos._analizar(${i})">🔬 Analizar</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.archivos._enviarAlChat(${i})" title="Analizar y enviar al Chat">💬</button>
        </div>`;
      lista.appendChild(item);
    });
  },

  /* ── PREVISUALIZAR ARCHIVO ── */
  async _previsualizar(idx) {
    const file = this.archivosActuales[idx];
    if (!file) return;
    const ext  = file.name.split('.').pop().toLowerCase();
    const area = document.getElementById('archivo-preview');
    if (!area) return;

    area.innerHTML = `<div style="color:var(--muted);font-size:12px;margin-bottom:8px">📎 <strong>${file.name}</strong> · ${this._fmtSize(file.size)}</div>`;

    if (['png','jpg','jpeg','gif','webp','bmp'].includes(ext)) {
      const url = URL.createObjectURL(file);
      area.innerHTML += `<img src="${url}" style="max-width:100%;max-height:400px;border-radius:8px;border:1px solid var(--border)">`;
    } else if (['txt','md','csv','json','js','py','html','css','xml'].includes(ext)) {
      try {
        const texto   = await file.text();
        const preview = texto.substring(0, 3000) + (texto.length > 3000 ? '\n\n...[truncado]' : '');
        area.innerHTML += `<pre style="white-space:pre-wrap;font-size:12px;line-height:1.7;color:var(--text);background:var(--surface);padding:12px;border-radius:8px;overflow:auto;max-height:380px">${this._escHTML(preview)}</pre>`;
      } catch(e) {
        area.innerHTML += `<div class="alert alert-danger">Error leyendo archivo: ${e.message}</div>`;
      }
    } else if (ext === 'pdf') {
      area.innerHTML += `<div style="color:var(--muted);font-size:13px;padding:12px">
        📄 Archivo PDF · Usa <strong>🔬 Analizar</strong> para extraer texto completo, CURP, RFC y datos de pensión.
        <br><br>
        <object data="${URL.createObjectURL(file)}" type="application/pdf" width="100%" height="400px" style="border-radius:8px;margin-top:8px"></object>
      </div>`;
    } else {
      area.innerHTML += `<div style="color:var(--muted);font-size:13px;padding:12px">
        Vista previa no disponible para <strong>${ext.toUpperCase()}</strong>. Usa <strong>🔬 Analizar</strong>.
      </div>`;
    }
  },

  /* ── ANALIZAR ARCHIVO (REAL) ── */
  async _analizar(idx) {
    const file = this.archivosActuales[idx];
    if (!file) return;
    const area = document.getElementById('archivo-resultado');
    if (!area) return;

    area.innerHTML = `<div style="color:var(--accent);font-size:13px;padding:12px">
      <span style="animation:pulse 1s infinite;display:inline-block">⏳</span>
      &nbsp;Analizando <strong>${file.name}</strong>…
    </div>`;

    // ── RUTA 1: Backend real (/api/analizar-documento) ──
    if (MAER.config.backendOK) {
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await MAER._upload('/api/analizar-documento', fd);
        if (res.ok && res.data) {
          this._ultimoAnalisis = res.data;
          this._mostrarAnalisisRico(file.name, res.data, area);
          MAER.voz?.hablar(`Análisis de ${file.name} completado.`);
          return;
        }
      } catch(e) {
        MAER._log(`⚠️ /api/analizar-documento: ${e.message}`);
      }
    }

    // ── RUTA 2: Análisis local (texto plano / imágenes) ──
    const ext = file.name.split('.').pop().toLowerCase();
    const textExts = ['txt','md','csv','json','js','py','html','css','xml'];

    if (textExts.includes(ext)) {
      try {
        const texto = await file.text();
        this._mostrarAnalisisLocal(file.name, texto, area);
      } catch(e) {
        area.innerHTML = `<div class="alert alert-danger">Error leyendo archivo: ${e.message}</div>`;
      }
    } else {
      area.innerHTML = `
        <div class="alert alert-warning" style="font-size:13px">
          ⚠️ Para analizar <strong>${ext.toUpperCase()}</strong> necesitas el servidor MAER activo.<br><br>
          <strong>Inicia el servidor:</strong><br>
          <code style="font-size:11px">cd maer_backend &amp;&amp; python web_ui/server.py</code><br><br>
          El servidor extrae texto de PDFs, imágenes (OCR), Word, y detecta CURP, RFC, NSS y semanas IMSS automáticamente.
        </div>`;
    }
  },

  /* ── MOSTRAR ANÁLISIS RICO (desde backend) ── */
  _mostrarAnalisisRico(nombre, d, area) {
    const tipo     = d.tipo_documento || 'Documento';
    const texto    = d.texto         || '';
    const curps    = d.curps         || [];
    const rfcs     = d.rfcs          || [];
    const nss      = d.nss           || [];
    const emails   = d.emails        || [];
    const telefonos= d.telefonos     || [];
    const fechas   = d.fechas        || [];
    const montos   = d.montos        || [];
    const semanas  = d.semanas_cotizadas ? [String(d.semanas_cotizadas)] : [];
    const pension  = d.pension_info  || null;

    const colorTipo = {
      'Resolución IMSS':        'var(--accent)',
      'Estado de Cuenta IMSS':  'var(--accent)',
      'Carta de Derechos':      'var(--green)',
      'Constancia de Semanas':  'var(--green)',
      'Identificación Oficial': 'var(--yellow)',
      'Acta de Nacimiento':     'var(--yellow)',
    }[tipo] || 'var(--muted)';

    let html = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:14px">
        <div>
          <h4 style="color:var(--accent);margin:0 0 4px">🔬 ${this._escHTML(nombre)}</h4>
          <span style="font-size:12px;color:${colorTipo};background:rgba(255,255,255,0.05);
                       border:1px solid currentColor;border-radius:20px;padding:2px 10px">
            ${tipo}
          </span>
        </div>
        <div style="font-size:11px;color:var(--muted);text-align:right">
          ${texto.length.toLocaleString()} caracteres extraídos
        </div>
      </div>`;

    // ── CURP con tarjeta visual completa ──
    if (curps.length) {
      html += `<div style="margin-bottom:16px">
        <div style="font-size:11px;color:var(--green);font-weight:700;margin-bottom:8px;
                    text-transform:uppercase;letter-spacing:.5px">
          🆔 CURP detectada${curps.length > 1 ? 's' : ''}
        </div>`;
      curps.forEach(c => {
        const info = c.info || {};
        // Usar la tarjeta visual del módulo poder si está disponible
        if (MAER.poder?._tarjetaCURP) {
          const dataObj = {
            curp: c.curp, valida: c.valida,
            fecha_nacimiento: info.fecha_nacimiento || '',
            edad: info.edad || '', sexo: info.sexo || '', estado: info.estado || ''
          };
          // Pasar semanas cotizadas del análisis si existen
          html += MAER.poder._tarjetaCURP(dataObj, d.semanas_cotizadas || null);
        } else {
          // Fallback básico
          html += `<div style="background:rgba(52,211,153,0.07);border:1px solid rgba(52,211,153,0.25);
                               border-radius:8px;padding:10px 14px;margin-bottom:6px">
            <div style="font-family:monospace;font-size:15px;color:var(--green);font-weight:700">${c.curp}</div>
          </div>`;
        }
      });
      html += '</div>';
    }

    // ── RFC con validación ──
    if (rfcs.length) {
      html += `<div style="margin-bottom:12px">
        <div style="font-size:11px;color:var(--accent);font-weight:600;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">📋 RFC detectado${rfcs.length > 1 ? 's' : ''}</div>`;
      rfcs.forEach(r => {
        html += `<div style="background:rgba(56,189,248,0.07);border:1px solid rgba(56,189,248,0.25);
                             border-radius:8px;padding:8px 14px;margin-bottom:6px;
                             display:flex;justify-content:space-between;align-items:center">
          <span style="font-family:monospace;font-size:14px;color:var(--accent);font-weight:700">${r.rfc}</span>
          <span style="font-size:11px;color:${r.valido ? 'var(--green)' : 'var(--yellow)'}">${r.valido ? '✓ Válido' : '⚠ Verificar'}</span>
        </div>`;
      });
      html += '</div>';
    }

    // ── NSS ──
    if (nss.length) {
      html += `<div style="margin-bottom:12px">
        <div style="font-size:11px;color:var(--yellow);font-weight:600;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">🏛️ NSS (Número de Seguridad Social)</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
        ${nss.map(n => `<span style="background:rgba(250,204,21,0.1);border:1px solid rgba(250,204,21,0.3);
                                      border-radius:6px;padding:4px 10px;font-family:monospace;
                                      font-size:13px;color:var(--yellow)">${n}</span>`).join('')}
        </div></div>`;
    }

    // ── Semanas cotizadas: se muestran en la tarjeta CURP si hay CURP.
    //    Si NO hay CURP pero sí hay semanas, mostramos el bloque de pensión aquí. ──
    if ((semanas.length || pension) && !curps.length) {
      const sem  = parseInt(semanas[0] || (pension?.semanas_detectadas || 0));
      const META = 1250;
      const pct  = Math.min(100, Math.round((sem / META) * 100));
      const faltan = Math.max(0, META - sem);
      const BLOQ = 20;
      const bloqLlenos = Math.round((pct / 100) * BLOQ);
      const barra = '█'.repeat(bloqLlenos) + '░'.repeat(BLOQ - bloqLlenos);
      const ley  = pension?.ley || '';

      html += `<div style="margin-bottom:14px;background:rgba(52,211,153,0.05);border:1px solid rgba(52,211,153,0.2);border-radius:12px;padding:14px">
        <div style="font-size:12px;color:var(--green);font-weight:700;margin-bottom:12px">🏛️ SEMANAS COTIZADAS — IMSS</div>
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px">
          <div style="text-align:center;background:rgba(52,211,153,0.1);border-radius:10px;padding:10px 16px;border:1px solid rgba(52,211,153,0.3)">
            <div style="font-size:36px;font-weight:900;color:#34d399;line-height:1">${sem}</div>
            <div style="font-size:10px;color:#64748b;margin-top:2px">de ${META}</div>
          </div>
          <div style="flex:1">
            <div style="font-family:monospace;font-size:11px;color:#34d399;margin-bottom:6px;word-break:break-all">${barra}</div>
            <div style="background:rgba(255,255,255,0.06);border-radius:6px;height:10px;overflow:hidden;margin-bottom:4px">
              <div style="width:${pct}%;height:100%;background:linear-gradient(90deg,#34d399,#38bdf8);border-radius:6px"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10px;color:#64748b">
              <span>0</span><span style="color:#34d399;font-weight:700">${pct}%</span><span>${META}</span>
            </div>
          </div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;font-size:12px">
          ${faltan > 0 ? `<span style="color:var(--yellow)">⏳ Faltan <strong>${faltan}</strong> semanas</span>` : '<span style="color:var(--green)">✅ Meta alcanzada</span>'}
          ${ley ? `<span style="color:var(--muted)">· Ley: <strong style="color:var(--accent)">${ley}</strong></span>` : ''}
        </div>
      </div>`;
    }

    // ── Otros datos ──
    const otros = [];
    if (emails.length)    otros.push({label:'📧 Emails',    items:emails,    color:'var(--muted)'});
    if (telefonos.length) otros.push({label:'📞 Teléfonos', items:telefonos, color:'var(--muted)'});
    if (fechas.length)    otros.push({label:'📅 Fechas',    items:fechas.slice(0,8), color:'var(--muted)'});
    if (montos.length)    otros.push({label:'💰 Montos',    items:montos.slice(0,8), color:'var(--green)'});

    if (otros.length) {
      html += `<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px">`;
      otros.forEach(o => {
        html += `<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 12px;min-width:130px;max-width:220px">
          <div style="font-size:10px;color:${o.color};font-weight:600;margin-bottom:4px">${o.label}</div>
          ${o.items.map(v => `<div style="font-size:11px;color:var(--text);word-break:break-all">${this._escHTML(String(v))}</div>`).join('')}
        </div>`;
      });
      html += '</div>';
    }

    // ── Extracto de texto ──
    if (texto.length > 0) {
      const preview = texto.substring(0, 500);
      html += `<details style="margin-top:6px">
        <summary style="font-size:12px;color:var(--muted);cursor:pointer;user-select:none">
          📄 Ver extracto de texto (${texto.length.toLocaleString()} chars)
        </summary>
        <pre style="white-space:pre-wrap;font-size:11px;line-height:1.6;color:var(--text);
                    background:var(--surface);padding:10px;border-radius:6px;
                    max-height:200px;overflow:auto;margin-top:6px">${this._escHTML(preview)}${texto.length > 500 ? '\n…' : ''}</pre>
      </details>`;
    }

    // ── Botones de acción ──
    html += `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
      <button class="btn btn-primary btn-sm" onclick="MAER.archivos._copiarAnalisisAlChat()">
        💬 Enviar análisis al Chat
      </button>
      <button class="btn btn-secondary btn-sm" onclick="MAER.archivos._aprenderArchivo_idx(${this.archivosActuales.indexOf(this.archivosActuales.find(f=>f.name===nombre))})">
        📚 Memorizar documento
      </button>
    </div>`;

    area.innerHTML = html;
    MAER._log(`🔬 Análisis completo: ${nombre} → ${tipo}, ${curps.length} CURP, ${rfcs.length} RFC, ${nss.length} NSS`);
  },

  /* ── MOSTRAR ANÁLISIS LOCAL (sin servidor) ── */
  _mostrarAnalisisLocal(nombre, texto, area) {
    const datos = this._extraerDatos(texto);
    let html = `<h4 style="color:var(--accent);margin-bottom:12px">📊 Análisis local: ${nombre}</h4>
      <div style="font-size:11px;color:var(--yellow);background:rgba(250,204,21,0.08);border:1px solid rgba(250,204,21,0.25);
                  border-radius:6px;padding:8px 12px;margin-bottom:12px">
        ⚠️ Servidor offline — análisis básico (sin validación de CURP/RFC, sin OCR de imágenes)
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">`;

    if (datos.curp.length)   html += this._badgeList('CURP',   datos.curp,           'var(--green)');
    if (datos.rfc.length)    html += this._badgeList('RFC',    datos.rfc,            'var(--accent)');
    if (datos.nss.length)    html += this._badgeList('NSS',    datos.nss,            'var(--yellow)');
    if (datos.fechas.length) html += this._badgeList('Fechas', datos.fechas.slice(0,5), 'var(--muted)');
    if (datos.montos.length) html += this._badgeList('Montos', datos.montos.slice(0,5), 'var(--green)');

    html += '</div>';

    if (!datos.curp.length && !datos.rfc.length && !datos.nss.length) {
      html += '<div style="color:var(--muted);font-size:12px;margin-bottom:10px">No se encontraron CURP, RFC ni NSS en este archivo.</div>';
    }

    html += `<div style="font-size:11px;color:var(--muted)">
      Caracteres: ${texto.length.toLocaleString()} · Líneas: ${texto.split('\n').length.toLocaleString()}
    </div>`;
    area.innerHTML = html;
  },

  /* ── COPIAR ANÁLISIS AL CHAT ── */
  _copiarAnalisisAlChat() {
    if (!this._ultimoAnalisis) {
      MAER.chat._addMsg('sys', '⚠️ Primero analiza un archivo con el servidor activo.');
      return;
    }
    const d    = this._ultimoAnalisis;
    const tipo = d.tipo_documento || 'Documento';
    const curps= (d.curps || []).map(c => c.curp).join(', ');
    const rfcs = (d.rfcs  || []).map(r => r.rfc).join(', ');
    const nss  = (d.nss   || []).join(', ');
    const sem  = d.semanas_cotizadas || '';

    let resumen = `📋 <strong>Análisis de documento: ${tipo}</strong><br>`;
    if (curps) resumen += `CURP: ${curps}<br>`;
    if (rfcs)  resumen += `RFC: ${rfcs}<br>`;
    if (nss)   resumen += `NSS: ${nss}<br>`;
    if (sem)   resumen += `Semanas cotizadas: ${sem}<br>`;

    MAER.chat._addMsg('sys', resumen + '<br><em>Puedes hacer preguntas sobre este documento.</em>');
    MAER.chat.ctxTexto = JSON.stringify(d).substring(0, 3000);
    MAER.tabs.show('chat-principal');
  },

  /* ── ENVIAR AL CHAT (analizar + pasar contexto) ── */
  async _enviarAlChat(idx) {
    await this._analizar(idx);
    setTimeout(() => this._copiarAnalisisAlChat(), 500);
  },

  /* ── SUBIR A APRENDIZAJE ── */
  _aprenderArchivo_idx(idx) {
    const file = this.archivosActuales[idx];
    if (file) MAER.aprendizaje.subirArchivo(file);
  },

  async aprenderArchivo(idx) {
    const file = this.archivosActuales[idx];
    if (!file) return;
    await MAER.aprendizaje.subirArchivo(file);
  },

  _badgeList(label, items, color) {
    return `<div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:8px 12px;min-width:120px">
      <div style="font-size:10px;color:${color};font-weight:600;margin-bottom:4px">${label}</div>
      ${items.map(v => `<div style="font-size:12px;color:var(--text);font-family:monospace">${v}</div>`).join('')}
    </div>`;
  },

  /* ── EXTRAER DATOS LOCAL ── */
  _extraerDatos(texto) {
    return {
      curp:   (texto.match(/[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      rfc:    (texto.match(/[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      nss:    (texto.match(/\b\d{11}\b/g) || []).filter((v,i,a) => a.indexOf(v)===i).slice(0, 5),
      fechas: (texto.match(/\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
      montos: (texto.match(/\$[\d,]+\.?\d{0,2}/g) || []).filter((v,i,a) => a.indexOf(v)===i),
    };
  },

  _fmtSize(bytes) {
    if (bytes < 1024)    return bytes + ' B';
    if (bytes < 1048576) return (bytes/1024).toFixed(1) + ' KB';
    return (bytes/1048576).toFixed(1) + ' MB';
  },

  _escHTML(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  },
};
