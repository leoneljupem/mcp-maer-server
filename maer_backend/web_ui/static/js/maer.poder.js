/* ══════════════════════════════════════════════════════════
   MAER 4.0 — PODER REAL
   Módulo de capacidades reales del backend:
   - Análisis completo de documentos (PDF, imágenes, DOCX)
   - OCR potente con preprocesamiento
   - Validación CURP + decodificación completa
   - Validación RFC con dígito verificador
   - Buscador de duplicados (por hash SHA-256)
   - Buscador de imágenes similares (perceptual hash)
   - Análisis de expediente IMSS
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.poder = {

  /* ── INIT ── */
  init() {
    this._renderPanel();
    MAER._log('🔬 MAER Poder Real inicializado.');
  },

  /* ══════════════════════════════════════════════
     1. ANÁLISIS COMPLETO DE DOCUMENTO
  ══════════════════════════════════════════════ */

  async analizarDocumento(archivo) {
    const panel = document.getElementById('poder-resultado');
    if (!panel) return;
    panel.innerHTML = `<div class="poder-loading">🔬 Analizando <strong>${archivo.name}</strong>...<br><small>Extrayendo texto, detectando CURP/NSS/RFC, clasificando...</small></div>`;

    const form = new FormData();
    form.append('file', archivo);

    try {
      const res = await fetch(`${MAER.API}/api/analizar-documento`, { method: 'POST', body: form });
      const data = await res.json();
      if (!data.ok) {
        panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${data.message}</div>`;
        return;
      }
      this._mostrarResultadoAnalisis(data.data, panel);
    } catch(e) {
      panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ Error: ${e.message}<br><small>¿El servidor MAER está corriendo? (localhost:8765)</small></div>`;
    }
  },

  _mostrarResultadoAnalisis(d, panel) {
    const verde = '#34d399', rojo = '#f87171', amarillo = '#fbbf24', azul = '#38bdf8';

    let html = `
      <div class="poder-card">
        <div class="poder-tipo">${d.tipo_documento}</div>
        <div class="poder-stats">
          <span>📄 ${d.chars_total} caracteres</span>
          <span>🔍 ${d.curps?.length || 0} CURP(s)</span>
          <span>💼 ${d.rfcs?.length || 0} RFC(s)</span>
          <span>🔢 ${d.nss?.length || 0} NSS</span>
        </div>
      </div>`;

    // CURPs encontradas
    if (d.curps?.length) {
      html += `<div class="poder-seccion">
        <div class="poder-seccion-titulo">🆔 CURP(s) Detectadas</div>`;
      d.curps.forEach(c => {
        const color = c.valida ? verde : rojo;
        const info = c.info || {};
        html += `<div class="poder-item">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span style="font-family:monospace;font-size:13px;color:${color};font-weight:700">${c.curp}</span>
            <span style="font-size:11px;padding:2px 8px;border-radius:20px;background:${c.valida?'rgba(52,211,153,0.15)':'rgba(248,113,113,0.15)'};color:${color}">${c.valida ? '✅ Válida' : '❌ Inválida'}</span>
          </div>
          ${c.valida && info.fecha_nacimiento ? `
          <div class="poder-detail">
            📅 <strong>Nacimiento:</strong> ${info.fecha_nacimiento} &nbsp;|&nbsp;
            ${info.edad ? `🎂 <strong>${info.edad} años</strong> &nbsp;|&nbsp;` : ''}
            ${info.sexo ? `👤 <strong>${info.sexo}</strong> &nbsp;|&nbsp;` : ''}
            📍 <strong>${info.estado || '—'}</strong>
          </div>` : ''}
        </div>`;
      });
      html += `</div>`;
    }

    // RFCs
    if (d.rfcs?.length) {
      html += `<div class="poder-seccion">
        <div class="poder-seccion-titulo">💼 RFC(s) Detectados</div>`;
      d.rfcs.forEach(r => {
        const color = r.valido ? verde : rojo;
        html += `<div class="poder-item">
          <span style="font-family:monospace;font-size:13px;color:${color};font-weight:700">${r.rfc}</span>
          <span style="font-size:11px;margin-left:8px;color:${color}">${r.valido ? '✅ Válido' : '❌ Inválido'}</span>
        </div>`;
      });
      html += `</div>`;
    }

    // NSS
    if (d.nss?.length) {
      html += `<div class="poder-seccion">
        <div class="poder-seccion-titulo">🔢 Número(s) de Seguridad Social</div>
        <div class="poder-item">
          ${d.nss.map(n => `<span style="font-family:monospace;font-size:13px;color:${azul};font-weight:700;margin-right:12px">${n}</span>`).join('')}
        </div>
      </div>`;
    }

    // Semanas cotizadas (CLAVE para pensión)
    if (d.semanas?.length) {
      const pi = d.pension_info || {};
      html += `<div class="poder-seccion" style="border-color:rgba(251,191,36,0.4)">
        <div class="poder-seccion-titulo">🏛️ Información de Pensión IMSS</div>
        <div class="poder-item">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:8px">
            <div class="poder-stat-box" style="border-color:${amarillo}">
              <div style="font-size:24px;font-weight:700;color:${amarillo}">${pi.semanas_detectadas || d.semanas[0]}</div>
              <div style="font-size:11px;color:var(--muted)">Semanas cotizadas</div>
            </div>
            ${pi.faltan_semanas !== undefined ? `
            <div class="poder-stat-box" style="border-color:${pi.faltan_semanas === 0 ? verde : rojo}">
              <div style="font-size:24px;font-weight:700;color:${pi.faltan_semanas === 0 ? verde : rojo}">${pi.faltan_semanas}</div>
              <div style="font-size:11px;color:var(--muted)">${pi.faltan_semanas === 0 ? '¡Listo para pensión!' : 'Semanas faltantes'}</div>
            </div>
            <div class="poder-stat-box">
              <div style="font-size:24px;font-weight:700;color:${azul}">${pi.porcentaje_completado}%</div>
              <div style="font-size:11px;color:var(--muted)">Completado (meta: 1250)</div>
            </div>` : ''}
          </div>
          ${pi.ley_aplicable ? `<div style="font-size:12px;color:var(--muted)">📋 Ley aplicable: <strong>${pi.ley_aplicable}</strong></div>` : ''}
        </div>
      </div>`;
    }

    // Otros datos
    const otros = [];
    if (d.emails?.length)    otros.push(`📧 <strong>Emails:</strong> ${d.emails.join(', ')}`);
    if (d.telefonos?.length) otros.push(`📞 <strong>Teléfonos:</strong> ${d.telefonos.join(', ')}`);
    if (d.montos?.length)    otros.push(`💰 <strong>Montos:</strong> ${d.montos.join(' · ')}`);
    if (d.salarios?.length)  otros.push(`💵 <strong>Salario(s):</strong> ${d.salarios.join(' · ')}`);
    if (d.fechas?.length)    otros.push(`📅 <strong>Fechas:</strong> ${d.fechas.slice(0,6).join(' · ')}`);

    if (otros.length) {
      html += `<div class="poder-seccion">
        <div class="poder-seccion-titulo">📊 Otros Datos Detectados</div>
        <div class="poder-item">
          ${otros.map(o => `<div style="font-size:12px;color:var(--text);padding:2px 0">${o}</div>`).join('')}
        </div>
      </div>`;
    }

    // Texto extraído
    if (d.texto_extraido?.trim()) {
      html += `<div class="poder-seccion">
        <div class="poder-seccion-titulo" style="display:flex;justify-content:space-between">
          <span>📝 Texto Extraído</span>
          <button onclick="document.getElementById('poder-texto-full').style.display=document.getElementById('poder-texto-full').style.display==='none'?'block':'none'" style="font-size:11px;background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:2px 8px;cursor:pointer;color:var(--text)">Ver/Ocultar</button>
        </div>
        <div id="poder-texto-full" style="display:none;margin-top:8px">
          <pre style="font-size:11px;color:var(--muted);white-space:pre-wrap;max-height:300px;overflow-y:auto;background:var(--bg);padding:10px;border-radius:6px;border:1px solid var(--border)">${d.texto_extraido.replace(/</g,'&lt;')}</pre>
          <button onclick="MAER.poder._copiarTexto('${encodeURIComponent(d.texto_extraido)}')" style="margin-top:6px;font-size:11px;background:var(--accent);color:#fff;border:none;border-radius:4px;padding:4px 12px;cursor:pointer">📋 Copiar texto</button>
        </div>
      </div>`;
    }

    // Enviar al chat
    html += `<div style="margin-top:12px">
      <button onclick="MAER.poder._enviarAnalisisAlChat()" style="padding:8px 18px;background:var(--accent);color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600">💬 Enviar análisis al Chat →</button>
    </div>`;

    panel.innerHTML = html;

    // Guardar último resultado para enviar al chat
    MAER.poder._ultimoAnalisis = d;
  },

  _copiarTexto(encoded) {
    const texto = decodeURIComponent(encoded);
    navigator.clipboard?.writeText(texto).then(() => MAER.voz?.hablar('Texto copiado.'));
  },

  _enviarAnalisisAlChat() {
    const d = this._ultimoAnalisis;
    if (!d) return;
    let resumen = `📄 **Documento analizado:** ${d.tipo_documento}\n\n`;
    if (d.curps?.length) resumen += `🆔 CURP: ${d.curps.map(c=>`${c.curp} (${c.valida?'✅':'❌'})`).join(', ')}\n`;
    if (d.nss?.length) resumen += `🔢 NSS: ${d.nss.join(', ')}\n`;
    if (d.rfcs?.length) resumen += `💼 RFC: ${d.rfcs.map(r=>r.rfc).join(', ')}\n`;
    if (d.semanas?.length) resumen += `📋 Semanas cotizadas: ${d.pension_info?.semanas_detectadas || d.semanas[0]}\n`;
    if (d.pension_info?.faltan_semanas !== undefined) resumen += `🏛️ Faltan ${d.pension_info.faltan_semanas} semanas para pensión\n`;
    const inp = document.getElementById('chat-input');
    if (inp) {
      inp.value = `Analicé este documento: ${resumen}\n¿Qué me recomiendas hacer con esta información para mi trámite de pensión IMSS?`;
      MAER.tabs.show('chat');
    }
  },

  /* ══════════════════════════════════════════════
     2. VALIDADOR CURP — con tarjeta visual completa
  ══════════════════════════════════════════════ */

  async validarCURP(curp) {
    const panel = document.getElementById('curp-resultado');
    if (!panel) return;
    curp = (curp || '').trim().toUpperCase();
    const nss = (document.getElementById('curp-nss-input')?.value || '').trim().replace(/\D/g, '');

    if (curp.length < 18) {
      panel.innerHTML = `<div style="color:var(--muted);font-size:12px;padding:8px">Ingresa una CURP de 18 caracteres</div>`;
      return;
    }

    panel.innerHTML = `<div class="poder-loading">
      ${nss ? '🏛️ Consultando IMSS con CURP + NSS…' : '🔍 Decodificando CURP…'}
      <br><small>${nss ? 'Buscando semanas cotizadas en el portal IMSS…' : 'Análisis local sin API externa'}</small>
    </div>`;

    try {
      if (nss) {
        // Consulta completa: CURP + NSS → IMSS portal + decodificación
        const res = await MAER._call('/api/imss-consulta', { curp, nss }, { timeout: 15000 });
        if (res.ok) {
          panel.innerHTML = this._tarjetaCURPCompleta(res.data);
        } else {
          // Fallback a decodificación local
          panel.innerHTML = this._tarjetaCURP(this._decodificarCURPLocal(curp), null, nss);
        }
      } else {
        // Solo CURP: decodificar con servidor o local
        try {
          const res = await MAER._call('/api/curp-decodificar', { curp }, { timeout: 8000 });
          if (res.ok) {
            panel.innerHTML = this._tarjetaCURP(res.data, null, '');
          } else {
            panel.innerHTML = this._tarjetaCURP(this._decodificarCURPLocal(curp), null, '');
          }
        } catch(e) {
          panel.innerHTML = this._tarjetaCURP(this._decodificarCURPLocal(curp), null, '');
        }
      }
    } catch(e) {
      panel.innerHTML = this._tarjetaCURP(this._decodificarCURPLocal(curp), null, nss);
    }
  },

  /* ══════════════════════════════════════════════
     TARJETA VISUAL CURP — desglose + pensión
     También la llama maer.archivos.js
  ══════════════════════════════════════════════ */

  /* ── TARJETA COMPLETA desde /api/imss-consulta (CURP + NSS + semanas) ── */
  _tarjetaCURPCompleta(data) {
    const ci  = data.curp_info    || {};
    const ni  = data.nss_info     || {};
    const ne  = data.nss_estimado || {};
    const sem = data.semanas_imss;
    const url = data.portal_imss_url || 'https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/semanascotizadas';
    const nssVal = ni.nss || '';

    // Renderizar la tarjeta visual con todos los datos
    let html = this._tarjetaCURP(ci, sem, nssVal);

    // Si el portal no dio semanas, mostrar guía y botón
    if (sem === null || sem === undefined) {
      const err = data.semanas_error || '';
      html += `<div style="background:rgba(251,191,36,0.07);border:1px solid rgba(251,191,36,0.3);
                           border-radius:10px;padding:12px;font-size:12px;margin-bottom:12px">
        <div style="font-weight:700;color:#fbbf24;margin-bottom:6px">📋 Semanas cotizadas</div>
        <div style="color:var(--muted);margin-bottom:10px">
          ${err ? `⚠️ ${err}<br><br>` : ''}
          El portal IMSS requiere autenticación para ver tus semanas exactas.<br>
          Con tu CURP <strong>${ci.curp || ''}</strong> y NSS <strong>${nssVal}</strong> puedes consultarlas en:
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <a href="${url}" target="_blank"
             style="display:inline-block;padding:8px 16px;background:linear-gradient(135deg,#0ea5e9,#38bdf8);
                    color:#fff;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none">
            🌐 Ir a IMSS Digital
          </a>
          <button onclick="MAER.poder._consultarIMSSDirecto('${url}','${ci.curp||''}','${nssVal}')"
             style="padding:8px 16px;background:rgba(56,189,248,0.15);border:1px solid rgba(56,189,248,0.4);
                    color:#38bdf8;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer">
            📋 Copiar datos para IMSS
          </button>
        </div>
      </div>`;
    }

    // Datos del NSS decodificado
    if (ni.subdelegacion) {
      html += `<div style="background:rgba(56,189,248,0.06);border:1px solid rgba(56,189,248,0.25);
                           border-radius:10px;padding:12px;font-size:12px;margin-bottom:12px">
        <div style="font-weight:700;color:#38bdf8;margin-bottom:8px">🔢 NSS Decodificado</div>
        <div style="font-family:monospace;font-size:18px;font-weight:700;color:#38bdf8;letter-spacing:2px;margin-bottom:10px">
          ${ni.estructura || nssVal}
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:10px">
          <span style="font-size:11px;color:var(--muted)">🏛️ Subdelegación IMSS: <strong style="color:#38bdf8">${ni.subdelegacion}</strong></span>
          ${ni.año_alta_imss ? `<span style="font-size:11px;color:var(--muted)">📅 Alta en IMSS: <strong style="color:#38bdf8">~${ni.año_alta_imss}</strong></span>` : ''}
        </div>
      </div>`;
    } else if (ne.subdelegacion_probable) {
      html += `<div style="background:rgba(56,189,248,0.04);border:1px solid rgba(56,189,248,0.15);
                           border-radius:10px;padding:10px 12px;font-size:11px;color:var(--muted);margin-bottom:12px">
        💡 ${ne.nota}
      </div>`;
    }

    return html;
  },

  /* ── COPIAR DATOS PARA IMSS ── */
  _consultarIMSSDirecto(url, curp, nss) {
    const texto = `CURP: ${curp}\nNSS: ${nss}`;
    navigator.clipboard?.writeText(texto).then(() => {
      alert(`✅ Datos copiados al portapapeles:\n\n${texto}\n\nPega estos datos en el portal IMSS.`);
    }).catch(() => {
      prompt('Copia estos datos para el portal IMSS:', texto);
    });
  },

  _tarjetaCURP(d, semanas, nss) {
    const curp   = d.curp  || d.curp_input || '';
    const valida = d.valida !== false;
    const fn     = d.fecha_nacimiento || '';
    const edad   = d.edad  || '';
    const sexo   = d.sexo  || '';
    const estado = d.estado|| '';
    const nssVal = nss || '';

    // ── DESGLOSE VISUAL carácter por carácter ──
    // Estructura CURP: AAAA NNMMAA S EEE CCC VV
    //  0-3  = iniciales nombre+apellidos
    //  4-9  = fecha AAMMDD
    //  10   = sexo H/M
    //  11-12= entidad
    //  13-15= consonantes internas
    //  16   = diferenciador homónimos
    //  17   = dígito verificador
    const segmentos = [
      { chars: curp.slice(0,4),  label: 'Iniciales',  color: '#38bdf8',  tip: 'Apellido paterno, materno y nombre' },
      { chars: curp.slice(4,10), label: 'Nacimiento', color: '#fbbf24',  tip: 'Año/Mes/Día' },
      { chars: curp.slice(10,11),label: 'Sexo',       color: '#f472b6',  tip: 'H=Hombre  M=Mujer' },
      { chars: curp.slice(11,13),label: 'Estado',     color: '#a78bfa',  tip: 'Clave de entidad federativa' },
      { chars: curp.slice(13,16),label: 'Consonantes',color: '#34d399',  tip: 'Consonantes internas del nombre' },
      { chars: curp.slice(16,17),label: 'Homónimo',   color: '#fb923c',  tip: 'Diferenciador de personas iguales' },
      { chars: curp.slice(17,18),label: 'Dígito V.',  color: '#6ee7b7',  tip: 'Dígito verificador' },
    ];

    let desglose = `<div style="margin:0 0 16px;overflow-x:auto">
      <div style="display:flex;gap:3px;align-items:flex-end;min-width:max-content;margin-bottom:4px">`;

    segmentos.forEach(s => {
      const chars = s.chars.split('');
      desglose += `<div style="display:flex;flex-direction:column;align-items:center;gap:2px">
        <div style="display:flex;gap:2px">`;
      chars.forEach(ch => {
        desglose += `<div style="
          width:28px;height:36px;border-radius:5px;
          background:${s.color}22;border:2px solid ${s.color};
          display:flex;align-items:center;justify-content:center;
          font-family:monospace;font-size:15px;font-weight:700;color:${s.color};
          title='${ch}'">${ch}</div>`;
      });
      desglose += `</div>
        <div style="font-size:9px;color:${s.color};white-space:nowrap;text-align:center;max-width:${chars.length*30}px;overflow:hidden;text-overflow:ellipsis">${s.label}</div>
      </div>`;
    });

    desglose += `</div>
      <!-- Leyenda de colores -->
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">`;
    segmentos.forEach(s => {
      desglose += `<div style="display:flex;align-items:center;gap:4px;font-size:10px;color:var(--muted)">
        <span style="width:8px;height:8px;border-radius:2px;background:${s.color};display:inline-block"></span>
        <span style="color:${s.color};font-weight:600">${s.label}:</span> ${s.tip}
      </div>`;
    });
    desglose += `</div></div>`;

    // ── TARJETA CREDENCIAL ──
    const iconoSexo = sexo === 'Hombre' ? '👨' : sexo === 'Mujer' ? '👩' : '👤';
    const acromapa = {
      'Aguascalientes':'AG','Baja California':'BC','Baja California Sur':'BS',
      'Campeche':'CM','Coahuila':'CO','Colima':'CL','Chiapas':'CS','Chihuahua':'CH',
      'Ciudad de México':'DF','Durango':'DG','Guanajuato':'GJ','Guerrero':'GR',
      'Hidalgo':'HG','Jalisco':'JC','Estado de México':'MC','Michoacán':'MN',
      'Morelos':'MS','Nayarit':'NT','Nuevo León':'NL','Oaxaca':'OC',
      'Puebla':'PL','Querétaro':'QO','Quintana Roo':'QR','San Luis Potosí':'SP',
      'Sinaloa':'SL','Sonora':'SO','Tabasco':'TC','Tamaulipas':'TS','Tlaxcala':'TL',
      'Veracruz':'VZ','Yucatán':'YN','Zacatecas':'ZS',
    };

    let tarjeta = `
      <div style="
        background:linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#0f172a 100%);
        border:1px solid rgba(56,189,248,0.4);border-radius:14px;
        padding:20px;margin-bottom:16px;position:relative;overflow:hidden">
        <!-- watermark -->
        <div style="position:absolute;right:16px;top:50%;transform:translateY(-50%);
                    font-size:80px;opacity:0.04;font-weight:900;color:white;
                    pointer-events:none;user-select:none">CURP</div>
        <!-- header -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <div>
            <div style="font-size:10px;color:#64748b;letter-spacing:1px;text-transform:uppercase">
              Registro Nacional de Población — RENAPO
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:2px">
              Clave Única de Registro de Población
            </div>
          </div>
          <div style="
            font-size:11px;font-weight:700;padding:4px 10px;border-radius:20px;
            background:${valida ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)'};
            color:${valida ? '#34d399' : '#f87171'};
            border:1px solid ${valida ? 'rgba(52,211,153,0.4)' : 'rgba(248,113,113,0.4)'}">
            ${valida ? '✓ VÁLIDA' : '✗ VERIFICAR'}
          </div>
        </div>
        <!-- CURP grande -->
        <div style="
          font-family:monospace;font-size:22px;font-weight:900;
          letter-spacing:3px;color:#e2e8f0;margin-bottom:16px;
          text-shadow:0 0 20px rgba(56,189,248,0.3)">
          ${curp.slice(0,4)}<span style="color:#38bdf8">${curp.slice(4,10)}</span>${curp.slice(10,11)}<span style="color:#a78bfa">${curp.slice(11,13)}</span>${curp.slice(13)}
        </div>
        <!-- datos en grid -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px">
          ${fn ? `<div style="border-left:2px solid #fbbf24;padding-left:10px">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px">Fecha de nacimiento</div>
            <div style="font-size:14px;font-weight:700;color:#fbbf24;margin-top:2px">${fn}</div>
          </div>` : ''}
          ${edad ? `<div style="border-left:2px solid #34d399;padding-left:10px">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px">Edad</div>
            <div style="font-size:14px;font-weight:700;color:#34d399;margin-top:2px">${edad} años</div>
          </div>` : ''}
          ${sexo ? `<div style="border-left:2px solid #f472b6;padding-left:10px">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px">Sexo</div>
            <div style="font-size:14px;font-weight:700;color:#f472b6;margin-top:2px">${iconoSexo} ${sexo}</div>
          </div>` : ''}
          ${estado ? `<div style="border-left:2px solid #a78bfa;padding-left:10px">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px">Estado de nacimiento</div>
            <div style="font-size:14px;font-weight:700;color:#a78bfa;margin-top:2px">📍 ${estado}</div>
          </div>` : ''}
          ${nssVal ? `<div style="border-left:2px solid #38bdf8;padding-left:10px">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:.5px">NSS — Seg. Social</div>
            <div style="font-size:14px;font-weight:700;color:#38bdf8;margin-top:2px;font-family:monospace;letter-spacing:1px">${nssVal}</div>
          </div>` : ''}
        </div>
      </div>`;

    // ── VISUALIZACIÓN DE SEMANAS (si se pasan) ──
    if (semanas !== null && semanas !== undefined) {
      const sem  = parseInt(semanas) || 0;
      const META = 1250;
      const pct  = Math.min(100, Math.round((sem / META) * 100));
      const fal  = Math.max(0, META - sem);
      // Estimación de ley: primera afiliación IMSS ≈ año nac + 18 años
      const _a2   = parseInt(curp.slice(4,6));
      const _añoNac = _a2 <= 25 ? 2000 + _a2 : 1900 + _a2;
      const _añoAlta = _añoNac + 18;   // edad promedio de primer empleo
      const ley = _añoAlta < 1997
        ? 'Ley 73'
        : _añoAlta > 2001
          ? 'Ley 97'
          : 'Ley 73 o 97 (verificar)';

      // Calcular barra de bloques (20 bloques)
      const BLOQ = 25;
      const bloqLlenos = Math.round((pct / 100) * BLOQ);
      const barra = '█'.repeat(bloqLlenos) + '░'.repeat(BLOQ - bloqLlenos);

      tarjeta += `
        <div style="
          background:rgba(52,211,153,0.06);border:1px solid rgba(52,211,153,0.25);
          border-radius:12px;padding:16px;margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div style="font-size:12px;font-weight:700;color:#34d399">🏛️ SEMANAS COTIZADAS — IMSS</div>
            <div style="font-size:11px;color:${sem >= META ? '#34d399' : '#fbbf24'}">
              ${sem >= META ? '✅ Meta alcanzada' : `⏳ ${fal} semanas faltantes`}
            </div>
          </div>
          <!-- número grande + barra -->
          <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px">
            <div style="text-align:center;background:rgba(52,211,153,0.1);border-radius:10px;padding:10px 16px;border:1px solid rgba(52,211,153,0.3)">
              <div style="font-size:36px;font-weight:900;color:#34d399;line-height:1">${sem}</div>
              <div style="font-size:10px;color:#64748b;margin-top:2px">de ${META}</div>
            </div>
            <div style="flex:1">
              <!-- barra de bloquecitos -->
              <div style="font-family:monospace;font-size:11px;letter-spacing:1px;
                          color:#34d399;margin-bottom:6px;word-break:break-all">${barra}</div>
              <!-- barra CSS -->
              <div style="background:rgba(255,255,255,0.06);border-radius:6px;height:10px;overflow:hidden;margin-bottom:6px">
                <div style="width:${pct}%;height:100%;
                            background:linear-gradient(90deg,#34d399,#38bdf8);
                            border-radius:6px;transition:width .6s ease"></div>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:10px;color:#64748b">
                <span>0</span><span style="color:#34d399;font-weight:700">${pct}% completado</span><span>${META}</span>
              </div>
            </div>
          </div>
          <!-- cards de datos -->
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px">
            <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;text-align:center">
              <div style="font-size:18px;font-weight:700;color:#34d399">${sem}</div>
              <div style="font-size:9px;color:#64748b;margin-top:2px">Sem. cotizadas</div>
            </div>
            <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;text-align:center">
              <div style="font-size:18px;font-weight:700;color:${fal===0?'#34d399':'#f87171'}">${fal}</div>
              <div style="font-size:9px;color:#64748b;margin-top:2px">Sem. faltantes</div>
            </div>
            <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;text-align:center">
              <div style="font-size:18px;font-weight:700;color:#fbbf24">${pct}%</div>
              <div style="font-size:9px;color:#64748b;margin-top:2px">Progreso</div>
            </div>
            <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;text-align:center">
              <div style="font-size:14px;font-weight:700;color:#a78bfa">${ley}</div>
              <div style="font-size:9px;color:#64748b;margin-top:2px">Ley aplicable</div>
            </div>
          </div>
        </div>`;
    }

    return desglose + tarjeta;
  },

  /* ── DECODIFICADOR LOCAL (sin servidor) ── */
  _decodificarCURPLocal(curp) {
    curp = (curp || '').trim().toUpperCase();
    if (curp.length < 18) return { curp, valida: false };
    const meses = ['','enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
    const estados = {
      AS:'Aguascalientes',BC:'Baja California',BS:'Baja California Sur',
      CM:'Campeche',CO:'Coahuila',CL:'Colima',CS:'Chiapas',CH:'Chihuahua',
      DF:'Ciudad de México',DG:'Durango',GJ:'Guanajuato',GR:'Guerrero',
      HG:'Hidalgo',JC:'Jalisco',MC:'Estado de México',MN:'Michoacán',
      MS:'Morelos',NT:'Nayarit',NL:'Nuevo León',OC:'Oaxaca',
      PL:'Puebla',QO:'Querétaro',QR:'Quintana Roo',SP:'San Luis Potosí',
      SL:'Sinaloa',SO:'Sonora',TC:'Tabasco',TS:'Tamaulipas',TL:'Tlaxcala',
      VZ:'Veracruz',YN:'Yucatán',ZS:'Zacatecas',NE:'Nacido en el Extranjero'
    };
    try {
      const a2 = parseInt(curp.slice(4,6));
      const mm = parseInt(curp.slice(6,8));
      const dd = parseInt(curp.slice(8,10));
      const year = a2 >= 0 && a2 <= 25 ? 2000 + a2 : 1900 + a2;
      const sexCode  = curp[10];
      const entCode  = curp.slice(11,13);
      const fecha    = `${dd} de ${meses[mm] || mm} de ${year}`;
      const ahora    = new Date();
      const edad     = ahora.getFullYear() - year - (ahora.getMonth() + 1 > mm || (ahora.getMonth() + 1 === mm && ahora.getDate() >= dd) ? 0 : 1);
      return {
        curp, valida: /^[A-Z]{4}\d{6}[HM][A-Z]{2}[A-Z]{3}[A-Z0-9]\d$/.test(curp),
        fecha_nacimiento: fecha, edad, año_nacimiento: year,
        sexo: sexCode === 'H' ? 'Hombre' : sexCode === 'M' ? 'Mujer' : sexCode,
        estado: estados[entCode] || entCode,
      };
    } catch(e) {
      return { curp, valida: false };
    }
  },

  /* ══════════════════════════════════════════════
     3. BUSCADOR DE DUPLICADOS
  ══════════════════════════════════════════════ */

  async buscarDuplicados() {
    const carpeta = document.getElementById('dup-carpeta')?.value?.trim();
    const panel = document.getElementById('dup-resultado');
    if (!panel) return;
    if (!carpeta) {
      panel.innerHTML = `<div style="color:var(--muted);font-size:12px">Ingresa la ruta de la carpeta</div>`;
      return;
    }
    panel.innerHTML = `<div class="poder-loading">🔍 Buscando duplicados en:<br><code>${carpeta}</code><br><small>Calculando SHA-256 de cada archivo...</small></div>`;
    try {
      const res = await MAER._call('/api/buscar-duplicados', { carpeta });
      if (!res.ok) {
        panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${res.message}</div>`;
        return;
      }
      const d = res.data;
      let html = `
        <div class="poder-card">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:10px">
            <div class="poder-stat-box"><div style="font-size:22px;font-weight:700;color:var(--accent)">${d.total_archivos}</div><div style="font-size:11px;color:var(--muted)">Archivos analizados</div></div>
            <div class="poder-stat-box"><div style="font-size:22px;font-weight:700;color:#f87171">${d.grupos_duplicados}</div><div style="font-size:11px;color:var(--muted)">Grupos duplicados</div></div>
            <div class="poder-stat-box"><div style="font-size:22px;font-weight:700;color:#fbbf24">${d.archivos_redundantes}</div><div style="font-size:11px;color:var(--muted)">Archivos redundantes</div></div>
            <div class="poder-stat-box"><div style="font-size:22px;font-weight:700;color:#34d399">${d.espacio_recuperable_fmt}</div><div style="font-size:11px;color:var(--muted)">Espacio recuperable</div></div>
          </div>
        </div>`;

      if (d.grupos?.length) {
        html += `<div class="poder-seccion"><div class="poder-seccion-titulo">🗂️ Grupos de Duplicados</div>`;
        d.grupos.slice(0, 20).forEach((g, i) => {
          html += `<div class="poder-item" style="margin-bottom:8px">
            <div style="font-size:12px;font-weight:600;color:var(--accent);margin-bottom:4px">Grupo ${i+1} — ${g.count} copias idénticas</div>
            ${g.archivos.map(a => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid var(--border)">
                <span style="font-size:11px;color:var(--text);font-family:monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:70%">${a.nombre}</span>
                <span style="font-size:10px;color:var(--muted)">${a.tamaño_fmt}</span>
              </div>`).join('')}
          </div>`;
        });
        html += `</div>`;
      } else {
        html += `<div style="text-align:center;padding:20px;color:#34d399;font-size:14px">✅ ¡No se encontraron duplicados! Todos los archivos son únicos.</div>`;
      }

      panel.innerHTML = html;
    } catch(e) {
      panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${e.message}</div>`;
    }
  },

  /* ══════════════════════════════════════════════
     4. IMÁGENES SIMILARES
  ══════════════════════════════════════════════ */

  async buscarImagenesSimilares() {
    const carpeta = document.getElementById('sim-carpeta')?.value?.trim();
    const panel = document.getElementById('sim-resultado');
    if (!panel) return;
    if (!carpeta) {
      panel.innerHTML = `<div style="color:var(--muted);font-size:12px">Ingresa la ruta de la carpeta de imágenes</div>`;
      return;
    }
    panel.innerHTML = `<div class="poder-loading">🖼️ Analizando imágenes similares en:<br><code>${carpeta}</code><br><small>Calculando perceptual hash de cada imagen...</small></div>`;
    try {
      const res = await MAER._call('/api/imagenes-similares', { carpeta, umbral: 8 });
      if (!res.ok) {
        panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${res.message}</div>`;
        return;
      }
      const d = res.data;
      let html = `
        <div class="poder-card">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px">
            <div class="poder-stat-box"><div style="font-size:22px;font-weight:700;color:var(--accent)">${d.total_imagenes}</div><div style="font-size:11px;color:var(--muted)">Imágenes analizadas</div></div>
            <div class="poder-stat-box"><div style="font-size:22px;font-weight:700;color:#f87171">${d.grupos_similares}</div><div style="font-size:11px;color:var(--muted)">Grupos similares</div></div>
          </div>
        </div>`;

      if (d.grupos?.length) {
        html += `<div class="poder-seccion"><div class="poder-seccion-titulo">🖼️ Imágenes Similares</div>`;
        d.grupos.slice(0, 15).forEach((g, i) => {
          html += `<div class="poder-item" style="margin-bottom:8px">
            <div style="font-size:12px;font-weight:600;color:var(--accent);margin-bottom:4px">Grupo ${i+1} — ${g.count} imágenes similares</div>
            ${g.archivos.map(a => `
              <div style="display:flex;justify-content:space-between;padding:2px 0">
                <span style="font-size:11px;color:var(--text);font-family:monospace">${a.nombre}</span>
                <span style="font-size:10px;color:var(--muted)">${a.tamaño_fmt}</span>
              </div>`).join('')}
          </div>`;
        });
        html += `</div>`;
      } else {
        html += `<div style="text-align:center;padding:20px;color:#34d399;font-size:14px">✅ No se encontraron imágenes visualmente similares.</div>`;
      }

      panel.innerHTML = html;
    } catch(e) {
      panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${e.message}</div>`;
    }
  },

  /* ══════════════════════════════════════════════
     5. EXPEDIENTE IMSS
  ══════════════════════════════════════════════ */

  async analizarExpediente() {
    const carpeta = document.getElementById('exp-carpeta')?.value?.trim();
    const panel = document.getElementById('exp-resultado');
    if (!panel) return;
    if (!carpeta) {
      panel.innerHTML = `<div style="color:var(--muted);font-size:12px">Ingresa la ruta de tu carpeta de documentos</div>`;
      return;
    }
    panel.innerHTML = `<div class="poder-loading">📋 Analizando expediente IMSS en:<br><code>${carpeta}</code></div>`;
    try {
      const res = await MAER._call('/api/expediente-imss', { carpeta });
      if (!res.ok) {
        panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${res.message}</div>`;
        return;
      }
      const d = res.data;
      const pct = d.porcentaje;
      const colorPct = pct >= 80 ? '#34d399' : pct >= 50 ? '#fbbf24' : '#f87171';

      let html = `
        <div class="poder-card">
          <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
            <div style="text-align:center">
              <div style="font-size:36px;font-weight:700;color:${colorPct}">${pct}%</div>
              <div style="font-size:11px;color:var(--muted)">Expediente completo</div>
            </div>
            <div style="flex:1">
              <div style="background:var(--border);border-radius:8px;height:12px;overflow:hidden">
                <div style="background:${colorPct};height:100%;width:${pct}%;border-radius:8px;transition:width 0.5s"></div>
              </div>
              <div style="font-size:12px;color:var(--muted);margin-top:4px">${d.documentos_encontrados}/${d.documentos_requeridos} documentos encontrados en ${d.total_archivos_carpeta} archivos</div>
            </div>
          </div>
        </div>`;

      // Faltantes críticos
      if (d.criticos_faltantes?.length) {
        html += `<div class="poder-seccion" style="border-color:rgba(248,113,113,0.4)">
          <div class="poder-seccion-titulo">🔴 Documentos Críticos Faltantes</div>`;
        d.criticos_faltantes.forEach(f => {
          html += `<div class="poder-item">
            <span style="font-size:13px">${f.urgencia}</span>
            <span style="font-size:12px;color:var(--text);margin-left:6px">${f.nombre}</span>
          </div>`;
        });
        html += `</div>`;
      }

      // Encontrados
      if (Object.keys(d.encontrados || {}).length) {
        html += `<div class="poder-seccion">
          <div class="poder-seccion-titulo">✅ Documentos Encontrados</div>`;
        Object.entries(d.encontrados).forEach(([id, archivo]) => {
          html += `<div class="poder-item">
            <span style="font-size:11px;color:#34d399">✅</span>
            <span style="font-size:12px;color:var(--text);margin-left:6px;font-family:monospace">${archivo.nombre}</span>
          </div>`;
        });
        html += `</div>`;
      }

      panel.innerHTML = html;
    } catch(e) {
      panel.innerHTML = `<div style="color:var(--red);padding:12px">❌ ${e.message}</div>`;
    }
  },

  /* ══════════════════════════════════════════════
     6. SELECCIÓN DE CARPETA (Finder nativo)
  ══════════════════════════════════════════════ */

  async seleccionarCarpeta(targetId) {
    try {
      const res = await fetch(`${MAER.API}/api/select-dir`);
      const data = await res.json();
      if (data.ok && data.data) {
        const input = document.getElementById(targetId);
        if (input) input.value = data.data;
      }
    } catch(e) {
      MAER._log(`⚠️ No se pudo abrir Finder: ${e.message}`);
    }
  },

  async seleccionarArchivo(targetId) {
    try {
      const res = await fetch(`${MAER.API}/api/select-file`);
      const data = await res.json();
      if (data.ok && data.data) {
        const input = document.getElementById(targetId);
        if (input) input.value = data.data;
      }
    } catch(e) {
      MAER._log(`⚠️ No se pudo abrir Finder: ${e.message}`);
    }
  },

  /* ══════════════════════════════════════════════
     7. RENDER PANEL PRINCIPAL
  ══════════════════════════════════════════════ */

  _renderPanel() {
    const panel = document.getElementById('poder-panel');
    if (!panel) return;

    panel.innerHTML = `
    <div class="sub-tabs" id="poder-subtabs">
      <button class="sub-tab-btn active" onclick="showSubTab('poder-sub-analizar', this)">🔬 Analizar Doc</button>
      <button class="sub-tab-btn" onclick="showSubTab('poder-sub-curp', this)">🆔 CURP/RFC</button>
      <button class="sub-tab-btn" onclick="showSubTab('poder-sub-duplicados', this)">🗂️ Duplicados</button>
      <button class="sub-tab-btn" onclick="showSubTab('poder-sub-similares', this)">🖼️ Similares</button>
      <button class="sub-tab-btn" onclick="showSubTab('poder-sub-expediente', this)">📋 Expediente</button>
    </div>

    <!-- ANALIZAR DOCUMENTO -->
    <div id="poder-sub-analizar" class="sub-panel active">
      <div class="card">
        <div class="card-title" style="margin-bottom:10px">🔬 Análisis Completo de Documento</div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:12px">
          Sube cualquier PDF, imagen (foto con celular), DOCX o TXT.<br>
          MAER extrae automáticamente: CURP, NSS, RFC, semanas cotizadas, texto completo y clasifica el tipo de documento.
        </div>
        <div id="poder-dropzone" class="poder-dropzone"
          onclick="document.getElementById('poder-file-input').click()"
          ondragover="event.preventDefault();this.classList.add('poder-drop-over')"
          ondragleave="this.classList.remove('poder-drop-over')"
          ondrop="event.preventDefault();this.classList.remove('poder-drop-over');MAER.poder.analizarDocumento(event.dataTransfer.files[0])">
          <div>📂 Arrastra aquí o haz clic para seleccionar</div>
          <div style="font-size:11px;color:var(--muted);margin-top:4px">PDF · JPG · PNG · DOCX · TXT</div>
        </div>
        <input type="file" id="poder-file-input" accept=".pdf,.jpg,.jpeg,.png,.docx,.doc,.txt,.bmp,.tiff"
          style="display:none" onchange="MAER.poder.analizarDocumento(this.files[0])">
      </div>
      <div id="poder-resultado" style="margin-top:12px"></div>
    </div>

    <!-- CURP / RFC -->
    <div id="poder-sub-curp" class="sub-panel">
      <div class="two-col">
        <div class="card">
          <div class="card-title" style="margin-bottom:10px">🆔 Validar y Decodificar CURP</div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:10px">
            Ingresa tu CURP para decodificarla. Agrega tu NSS para consultar semanas cotizadas en IMSS.
          </div>
          <!-- CURP field -->
          <div style="margin-bottom:8px">
            <div style="font-size:11px;color:var(--accent);font-weight:600;margin-bottom:4px">CURP (requerida)</div>
            <input id="curp-input" type="text" class="input-field" placeholder="CURP de 18 caracteres — ej: HEGM560427HVZRRL04"
              maxlength="18" style="width:100%;text-transform:uppercase;font-family:monospace;letter-spacing:1px"
              oninput="this.value=this.value.toUpperCase()"
              onkeydown="if(event.key==='Enter')MAER.poder.validarCURP(this.value)">
          </div>
          <!-- NSS field -->
          <div style="margin-bottom:10px">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">
              <span style="font-size:11px;color:#38bdf8;font-weight:600">NSS — Número de Seguridad Social</span>
              <span style="font-size:10px;color:var(--muted);background:rgba(56,189,248,0.1);
                            border:1px solid rgba(56,189,248,0.3);border-radius:10px;padding:1px 6px">
                opcional — para consultar semanas IMSS
              </span>
            </div>
            <input id="curp-nss-input" type="text" class="input-field"
              placeholder="NSS de 11 dígitos — ej: 12345678901"
              maxlength="11" style="width:100%;font-family:monospace;letter-spacing:2px"
              oninput="
                this.value=this.value.replace(/\D/g,'');
                const b=document.getElementById('curp-decode-btn');
                if(b) b.textContent = this.value.length>=11
                  ? '🏛️ Decodificar CURP + Consultar IMSS'
                  : '🔍 Decodificar CURP';
              "
              onkeydown="if(event.key==='Enter')MAER.poder.validarCURP(document.getElementById('curp-input').value)">
          </div>
          <!-- Botón dinámico -->
          <button id="curp-decode-btn" class="btn btn-primary" style="width:100%;font-size:13px;padding:10px;transition:all .2s"
            onclick="MAER.poder.validarCURP(document.getElementById('curp-input').value)">
            🔍 Decodificar CURP
          </button>
          <div style="font-size:10px;color:var(--muted);margin-top:6px;text-align:center">
            Sin NSS → decodificación visual instantánea &nbsp;·&nbsp; Con NSS → busca semanas en portal IMSS
          </div>
          <div id="curp-resultado" style="margin-top:14px"></div>
        </div>

        <div class="card">
          <div class="card-title" style="margin-bottom:10px">💼 Validar RFC</div>
          <div style="font-size:12px;color:var(--muted);margin-bottom:10px">
            Verifica el dígito verificador del RFC (persona física o moral).
          </div>
          <div style="display:flex;gap:8px">
            <input id="rfc-input" type="text" class="input-field" placeholder="RFC (12 o 13 caracteres)..."
              maxlength="13" style="flex:1;text-transform:uppercase;font-family:monospace"
              oninput="this.value=this.value.toUpperCase()"
              onkeydown="if(event.key==='Enter')MAER.poder.validarRFC(this.value)">
            <button class="btn btn-primary" onclick="MAER.poder.validarRFC(document.getElementById('rfc-input').value)">Validar</button>
          </div>
          <div id="rfc-resultado" style="margin-top:12px"></div>
        </div>
      </div>
    </div>

    <!-- DUPLICADOS -->
    <div id="poder-sub-duplicados" class="sub-panel">
      <div class="card">
        <div class="card-title" style="margin-bottom:10px">🗂️ Buscador de Archivos Duplicados</div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:12px">
          Encuentra archivos idénticos (mismo contenido) en cualquier carpeta. Muestra cuánto espacio puedes recuperar.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <input id="dup-carpeta" type="text" class="input-field" placeholder="Ruta de la carpeta a analizar..."
            style="flex:1;min-width:200px">
          <button class="btn btn-secondary btn-sm" onclick="MAER.poder.seleccionarCarpeta('dup-carpeta')">📂 Finder</button>
          <button class="btn btn-primary" onclick="MAER.poder.buscarDuplicados()">🔍 Buscar Duplicados</button>
        </div>
      </div>
      <div id="dup-resultado" style="margin-top:12px"></div>
    </div>

    <!-- SIMILARES -->
    <div id="poder-sub-similares" class="sub-panel">
      <div class="card">
        <div class="card-title" style="margin-bottom:10px">🖼️ Buscador de Imágenes Similares</div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:12px">
          Agrupa imágenes que se ven parecidas aunque no sean idénticas. Ideal para fotos duplicadas de documentos o selfies similares.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <input id="sim-carpeta" type="text" class="input-field" placeholder="Ruta de la carpeta con imágenes..."
            style="flex:1;min-width:200px">
          <button class="btn btn-secondary btn-sm" onclick="MAER.poder.seleccionarCarpeta('sim-carpeta')">📂 Finder</button>
          <button class="btn btn-primary" onclick="MAER.poder.buscarImagenesSimilares()">🖼️ Buscar Similares</button>
        </div>
      </div>
      <div id="sim-resultado" style="margin-top:12px"></div>
    </div>

    <!-- EXPEDIENTE IMSS -->
    <div id="poder-sub-expediente" class="sub-panel">
      <div class="card">
        <div class="card-title" style="margin-bottom:10px">📋 Análisis de Expediente IMSS</div>
        <div style="font-size:12px;color:var(--muted);margin-bottom:12px">
          Analiza tu carpeta de documentos y te dice qué documentos tienes para tu trámite de pensión y cuáles te faltan.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <input id="exp-carpeta" type="text" class="input-field" placeholder="Ruta de tu carpeta de documentos IMSS..."
            style="flex:1;min-width:200px">
          <button class="btn btn-secondary btn-sm" onclick="MAER.poder.seleccionarCarpeta('exp-carpeta')">📂 Finder</button>
          <button class="btn btn-primary" onclick="MAER.poder.analizarExpediente()">📋 Analizar Expediente</button>
        </div>
      </div>
      <div id="exp-resultado" style="margin-top:12px"></div>
    </div>`;
  },

  /* ── RFC VALIDAR ── */
  async validarRFC(rfc) {
    const panel = document.getElementById('rfc-resultado');
    if (!panel) return;
    if (!rfc || rfc.length < 12) {
      panel.innerHTML = `<div style="color:var(--muted);font-size:12px">Ingresa un RFC de 12 o 13 caracteres</div>`;
      return;
    }
    panel.innerHTML = `<div class="poder-loading">🔍 Validando RFC...</div>`;
    try {
      const res = await MAER._call('/api/rfc-validar', { rfc });
      if (res) {
        const d = res.data;
        const color = d?.valido ? '#34d399' : '#f87171';
        panel.innerHTML = `<div class="poder-item" style="border-left:3px solid ${color}">
          <span style="font-size:20px">${d?.valido ? '✅' : '❌'}</span>
          <span style="font-family:monospace;font-size:14px;font-weight:700;color:${color};margin-left:8px">${rfc.toUpperCase()}</span>
          <span style="font-size:12px;color:var(--muted);margin-left:8px">${res.message}</span>
          ${d?.tipo ? `<div style="font-size:11px;color:var(--muted);margin-top:4px">Tipo: ${d.tipo}</div>` : ''}
        </div>`;
      }
    } catch(e) {
      panel.innerHTML = `<div style="color:var(--muted);font-size:12px">${e.message}</div>`;
    }
  },
};
