/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo WhatsApp
   Importa exportaciones de chat (.txt de WhatsApp),
   las parsea, indexa y permite buscar en ellas desde el chat.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.whatsapp = {

  conversaciones: [],   // [ { nombre, mensajes:[], fecha_inicio, fecha_fin, total } ]
  busqResultados: [],

  /* ── REGEX PARA PARSEAR EXPORTACIÓN WHATSAPP ── */
  // Formato: "25/03/2026, 14:32 - Nombre: Mensaje"
  // o:       "[25/03/2026, 14:32] Nombre: Mensaje"
  RE_LINEA_WA: /^(?:\[?(\d{1,2}\/\d{1,2}\/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[ap]m)?)\]?\s*[-–]\s*)(.+?):(.+)$/i,

  /* ── IMPORTAR ARCHIVO TXT ── */
  async importar(file) {
    if (!file) return;
    const area = document.getElementById('wa-resultado');
    if (area) area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">📲 Procesando exportación...</div>';

    try {
      const texto = await file.text();
      const conv  = this._parsear(texto, file.name);

      if (!conv || conv.mensajes.length < 5) {
        if (area) area.innerHTML = `<div class="alert alert-warning">
          ⚠️ No se detectó formato de exportación de WhatsApp válido.<br>
          <small>Exporta el chat desde WhatsApp → ··· → Más → Exportar chat → Sin archivos multimedia</small>
        </div>`;
        return;
      }

      // Guardar en memoria (y en IndexedDB como aprendizaje)
      this.conversaciones.push(conv);
      await MAER.aprendizaje.guardar({
        nombre:   `WhatsApp: ${conv.nombre}`,
        etiqueta: 'whatsapp',
        texto:    conv.mensajes.map(m => `[${m.fecha}] ${m.autor}: ${m.texto}`).join('\n').substring(0, 15000),
        chars:    conv.total_chars,
        tipo:     'whatsapp',
      });
      MAER.aprendizaje._renderLista();

      this._renderConversaciones();
      MAER.chat._addMsg('sys', `📲 Chat de WhatsApp importado: <strong>${conv.nombre}</strong> — ${conv.mensajes.length.toLocaleString()} mensajes`);
      MAER.voz?.hablar(`Conversación de WhatsApp importada. ${conv.mensajes.length} mensajes de ${conv.nombre}.`);

    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
    }
  },

  /* ── PARSEAR TEXTO DE EXPORTACIÓN ── */
  _parsear(texto, nombreArchivo) {
    const lineas = texto.split('\n');
    const mensajes = [];
    let msgActual = null;
    let participantes = new Set();

    for (const linea of lineas) {
      const m = this.RE_LINEA_WA.exec(linea.trim());
      if (m) {
        if (msgActual) mensajes.push(msgActual);
        const [, fecha, hora, autor, contenido] = m;
        msgActual = {
          fecha:   `${fecha.trim()} ${hora.trim()}`,
          autor:   autor.trim(),
          texto:   contenido.trim(),
          omitido: false,
        };
        participantes.add(autor.trim());
      } else if (msgActual && linea.trim()) {
        // Continuación de mensaje (multi-línea)
        if (linea.includes('<Multimedia omitido>') || linea.includes('image omitted') || linea.includes('audio omitted')) {
          msgActual.omitido = true;
        } else {
          msgActual.texto += '\n' + linea.trim();
        }
      }
    }
    if (msgActual) mensajes.push(msgActual);

    if (!mensajes.length) return null;

    // Nombre del chat: del nombre del archivo o participantes
    let nombre = nombreArchivo.replace(/\.txt$/i,'').replace(/^WhatsApp Chat con /i,'').replace(/^Chat de WhatsApp con /i,'');
    if (nombre === nombreArchivo.replace(/\.txt$/i,'') && participantes.size > 0) {
      // Tomar todos los participantes excepto "Leonel" si está
      const otros = [...participantes].filter(p => !p.toLowerCase().includes('leonel'));
      if (otros.length) nombre = otros.slice(0,2).join(', ');
    }

    const total_chars = mensajes.reduce((s, m) => s + m.texto.length, 0);
    const fechas = mensajes.map(m => m.fecha).filter(Boolean);

    return {
      nombre,
      archivo:      nombreArchivo,
      mensajes,
      participantes: [...participantes],
      total:        mensajes.length,
      total_chars,
      fecha_inicio: fechas[0]            || '',
      fecha_fin:    fechas[fechas.length-1] || '',
      importado:    new Date().toISOString(),
    };
  },

  /* ── RENDERIZAR LISTA DE CONVERSACIONES ── */
  _renderConversaciones() {
    const el = document.getElementById('wa-lista');
    if (!el) return;

    if (!this.conversaciones.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:10px">Sin conversaciones importadas.</div>';
      return;
    }

    el.innerHTML = this.conversaciones.map((c, i) => `
      <div class="card" style="margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
          <div style="flex:1">
            <div style="font-size:13px;font-weight:600;color:var(--accent)">📱 ${this._esc(c.nombre)}</div>
            <div style="font-size:11px;color:var(--muted);margin-top:3px">
              ${c.mensajes.length.toLocaleString()} mensajes · ${c.participantes.length} participantes
              · ${c.fecha_inicio} — ${c.fecha_fin}
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px">
              ${c.participantes.slice(0,5).map(p => `
                <span style="font-size:11px;background:var(--bg3);border:1px solid var(--border);padding:2px 8px;border-radius:4px">${this._esc(p)}</span>
              `).join('')}
              ${c.participantes.length > 5 ? `<span style="font-size:11px;color:var(--muted)">+${c.participantes.length-5}</span>` : ''}
            </div>
          </div>
          <div style="display:flex;gap:6px;flex-shrink:0">
            <button class="btn btn-secondary btn-sm" onclick="MAER.whatsapp._verEstadisticas(${i})">📊</button>
            <button class="btn btn-primary btn-sm" onclick="MAER.whatsapp._verMensajes(${i})">👁️ Ver</button>
            <button class="btn btn-danger btn-sm" onclick="MAER.whatsapp._borrar(${i})">🗑️</button>
          </div>
        </div>
      </div>`).join('');
  },

  /* ── VER MENSAJES (ÚLTIMOS 50) ── */
  _verMensajes(idx) {
    const c = this.conversaciones[idx];
    if (!c) return;
    const ultimos = c.mensajes.slice(-50);
    const ol = document.createElement('div');
    ol.className = 'tooltip-overlay';
    ol.innerHTML = `<div class="tooltip-box" style="max-width:680px;max-height:85vh;overflow-y:auto">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
        <h3 style="margin:0">📱 ${this._esc(c.nombre)}</h3>
        <button class="btn btn-secondary btn-sm" onclick="this.closest('.tooltip-overlay').remove()">✕ Cerrar</button>
      </div>
      <div style="font-size:11px;color:var(--muted);margin-bottom:12px">
        Mostrando los últimos ${ultimos.length} de ${c.mensajes.length.toLocaleString()} mensajes
      </div>
      <div style="display:flex;flex-direction:column;gap:4px">
        ${ultimos.map(m => `
          <div style="background:${m.autor.toLowerCase().includes('leonel') ? 'rgba(56,189,248,0.06)' : 'var(--surface)'};
            border:1px solid var(--border);border-radius:6px;padding:7px 10px">
            <div style="font-size:10px;color:var(--accent);margin-bottom:2px">${this._esc(m.autor)} · ${this._esc(m.fecha)}</div>
            <div style="font-size:12px;color:var(--text);white-space:pre-wrap">${this._esc(m.texto)}</div>
          </div>`).join('')}
      </div>
    </div>`;
    ol.addEventListener('click', e => { if(e.target===ol) ol.remove(); });
    document.body.appendChild(ol);
  },

  /* ── ESTADÍSTICAS ── */
  _verEstadisticas(idx) {
    const c = this.conversaciones[idx];
    if (!c) return;

    // Contar mensajes por participante
    const conteo = {};
    c.mensajes.forEach(m => { conteo[m.autor] = (conteo[m.autor] || 0) + 1; });
    const ranking = Object.entries(conteo).sort((a,b) => b[1]-a[1]);

    // Palabras más usadas
    const frecuencia = {};
    const stopwords = new Set(['que','de','en','la','el','es','y','a','un','una','no','lo','se','me','te','le','su','si','por','con','del','los','las','al','mas','pero','como','para','todo','este','esta','hay','ya','mi','tu','nos']);
    c.mensajes.forEach(m => {
      m.texto.toLowerCase().split(/\W+/).forEach(w => {
        if (w.length > 3 && !stopwords.has(w)) frecuencia[w] = (frecuencia[w] || 0) + 1;
      });
    });
    const topPalabras = Object.entries(frecuencia).sort((a,b)=>b[1]-a[1]).slice(0,10);

    const ol = document.createElement('div');
    ol.className = 'tooltip-overlay';
    ol.innerHTML = `<div class="tooltip-box" style="max-width:560px">
      <h3>📊 ${this._esc(c.nombre)} — Estadísticas</h3>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0">
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--accent)">${c.mensajes.length.toLocaleString()}</div>
          <div style="font-size:11px;color:var(--muted)">Mensajes totales</div>
        </div>
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--green)">${c.participantes.length}</div>
          <div style="font-size:11px;color:var(--muted)">Participantes</div>
        </div>
      </div>
      <div style="font-size:12px;font-weight:600;color:var(--accent);margin-bottom:8px">Mensajes por participante</div>
      ${ranking.slice(0,8).map(([p,n]) => `
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px">
          <span style="color:var(--text)">${this._esc(p)}</span>
          <span style="color:var(--muted)">${n.toLocaleString()} msgs</span>
        </div>`).join('')}
      <div style="font-size:12px;font-weight:600;color:var(--accent);margin:12px 0 8px">Palabras más frecuentes</div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:14px">
        ${topPalabras.map(([w,n]) => `<span style="background:var(--bg3);border:1px solid var(--border);border-radius:4px;padding:2px 8px;font-size:11px">${w} <span style="color:var(--accent)">${n}</span></span>`).join('')}
      </div>
      <div style="text-align:right">
        <button class="btn btn-primary btn-sm" onclick="this.closest('.tooltip-overlay').remove()">Cerrar</button>
      </div>
    </div>`;
    ol.addEventListener('click', e => { if(e.target===ol) ol.remove(); });
    document.body.appendChild(ol);
  },

  /* ── PALABRAS CLAVE IMSS ── */
  KEYWORDS_IMSS: [
    'imss','nss','curp','rfc','semanas','cotizadas','pensión','pension','jubilación',
    'jubilacion','afore','clinica','clínica','expediente','resolución','resolucion',
    'prestación','prestacion','incapacidad','invalidez','cesantía','cesantia',
    'ndss','modalidad','sdg','dictamen','umf','hgz','derechohabiente','beneficiario',
    'aportaciones','subcuenta','retiro','viudez','orfandad','guarderías','guarderias',
    'subsidio','licencia','maternidad','paternidad','guarderia','derechos','vigencia',
    'número de seguridad','numero de seguridad','semanas de cotización',
  ],

  /* ── FILTRAR MENSAJES RELACIONADOS CON IMSS ── */
  filtrarIMSS() {
    const el = document.getElementById('wa-busq-resultado');
    if (!el) return;

    if (!this.conversaciones.length) {
      el.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">Importa una conversación primero.</div>`;
      return;
    }

    const resultados = [];
    const kws = this.KEYWORDS_IMSS;

    this.conversaciones.forEach(c => {
      c.mensajes.forEach(m => {
        const txt = m.texto.toLowerCase();
        const matches = kws.filter(k => txt.includes(k));
        if (matches.length) resultados.push({ conv: c.nombre, palabras: matches, ...m });
      });
    });

    if (!resultados.length) {
      el.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">No se encontraron mensajes relacionados con IMSS/pensión en los chats importados.</div>`;
      return;
    }

    // Resumen de keywords encontradas
    const resumenKw = {};
    resultados.forEach(r => r.palabras.forEach(k => { resumenKw[k] = (resumenKw[k]||0)+1; }));
    const topKw = Object.entries(resumenKw).sort((a,b)=>b[1]-a[1]).slice(0,8);

    el.innerHTML = `
      <div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.25);border-radius:8px;padding:10px;margin-bottom:10px">
        <div style="font-size:12px;font-weight:600;color:#34d399;margin-bottom:6px">🏛️ ${resultados.length} mensajes con palabras clave IMSS</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
          ${topKw.map(([k,n])=>`<span style="background:var(--bg3);border:1px solid var(--border);padding:2px 8px;border-radius:12px;font-size:11px"><strong style="color:var(--accent)">${k}</strong> <span style="color:var(--muted)">${n}×</span></span>`).join('')}
        </div>
      </div>
      ${resultados.slice(0,40).map(r => {
        const kwRegex = new RegExp('(' + r.palabras.map(k=>k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|') + ')', 'gi');
        const textoHtml = this._esc(r.texto).replace(kwRegex, '<mark style="background:rgba(52,211,153,0.3);color:var(--text);padding:0 2px;border-radius:2px">$1</mark>');
        return `<div style="background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:8px 10px;margin-bottom:5px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:3px">📱 ${this._esc(r.conv)} · ${this._esc(r.autor)} · ${this._esc(r.fecha)}</div>
          <div style="font-size:12px;color:var(--text)">${textoHtml}</div>
        </div>`;
      }).join('')}
      ${resultados.length > 40 ? `<div style="font-size:11px;color:var(--muted);padding:6px">... y ${resultados.length-40} mensajes más</div>` : ''}`;
  },

  /* ── BÚSQUEDA EN MENSAJES ── */
  buscar() {
    const q = document.getElementById('wa-busq')?.value?.trim();
    if (!q) return;
    const el = document.getElementById('wa-busq-resultado');
    if (!el) return;

    const resultados = [];
    this.conversaciones.forEach(c => {
      c.mensajes.forEach(m => {
        if (m.texto.toLowerCase().includes(q.toLowerCase()) || m.autor.toLowerCase().includes(q.toLowerCase())) {
          resultados.push({ conv: c.nombre, ...m });
        }
      });
    });

    if (!resultados.length) {
      el.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">Sin resultados para "${this._esc(q)}".</div>`;
      return;
    }

    el.innerHTML = `<div style="font-size:12px;color:var(--accent);margin-bottom:8px">${resultados.length} resultado${resultados.length>1?'s':''} para "<strong>${this._esc(q)}</strong>"</div>
    ${resultados.slice(0,30).map(r => `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:8px 10px;margin-bottom:5px">
        <div style="font-size:10px;color:var(--muted);margin-bottom:3px">📱 ${this._esc(r.conv)} · ${this._esc(r.autor)} · ${this._esc(r.fecha)}</div>
        <div style="font-size:12px;color:var(--text)">${this._esc(r.texto).replace(new RegExp(q,'gi'), m=>`<mark style="background:rgba(56,189,248,0.3);color:var(--text);padding:0 2px;border-radius:2px">${m}</mark>`)}</div>
      </div>`).join('')}
    ${resultados.length > 30 ? `<div style="font-size:11px;color:var(--muted);padding:6px">... y ${resultados.length-30} más</div>` : ''}`;
  },

  /* ── BORRAR CONVERSACIÓN ── */
  _borrar(idx) {
    const c = this.conversaciones[idx];
    if (!confirm(`¿Eliminar la conversación "${c?.nombre}"? (Solo de esta vista, el aprendizaje en IndexedDB persiste)`)) return;
    this.conversaciones.splice(idx, 1);
    this._renderConversaciones();
  },

  _esc(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
