/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo de Chat IA
   Contexto enriquecido: analiza archivos adjuntos con el
   backend real, incluye CURP, RFC, semanas, tipo doc.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.chat = {

  ctxPath:    null,   // Ruta del archivo adjunto
  ctxTexto:   null,   // Texto libre o JSON del análisis
  ctxAnalisis: null,  // Objeto completo del último análisis backend

  /* ── ENVIAR MENSAJE ── */
  send() {
    const input = document.getElementById('chat-input');
    const texto = (input?.value || '').trim();
    if (!texto) return;
    input.value = '';
    this._addMsg('user', texto);
    this._responder(texto);
  },

  /* ── LIMPIAR CHAT ── */
  clear() {
    if (!confirm('¿Limpiar la conversación?')) return;
    document.getElementById('chat-msgs').innerHTML =
      '<div class="msg sys">🦁 MAER activo · Chat limpiado · Listo para continuar.</div>';
    this.ctxPath    = null;
    this.ctxTexto   = null;
    this.ctxAnalisis= null;
    const el = document.getElementById('chat-ctx-file');
    if (el) el.innerHTML = '<span style="color:var(--muted);font-size:11px">Sin archivo adjunto</span>';
  },

  /* ── AGREGAR MENSAJE AL DOM ── */
  _addMsg(quien, html, hablar = true) {
    const msgs = document.getElementById('chat-msgs');
    if (!msgs) return;
    const div = document.createElement('div');
    div.className = `msg ${quien}`;

    if (quien === 'maer') {
      div.innerHTML = `<div class="sender">🦁 MAER</div>${html}`;
      if (hablar && MAER.config.vozActiva) {
        MAER.voz?.hablar(html);
      }
    } else if (quien === 'sys') {
      div.className = 'msg sys';
      div.innerHTML = html;
    } else {
      div.innerHTML = html;
    }

    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  },

  /* ── TYPING INDICATOR ── */
  _showTyping() {
    const msgs = document.getElementById('chat-msgs');
    const div  = document.createElement('div');
    div.className = 'msg maer';
    div.id = 'typing-indicator';
    div.innerHTML = '<div class="sender">🦁 MAER</div><div class="typing-dots"><span></span><span></span><span></span></div>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  },
  _hideTyping() {
    document.getElementById('typing-indicator')?.remove();
  },

  /* ── RESPONDER ── */
  async _responder(userMsg) {
    const modo = document.getElementById('chat-mode')?.value || 'general';

    // 1. Respuestas aprendidas por el usuario
    const learnedResp = this._buscarAprendido(userMsg);
    if (learnedResp) {
      this._addMsg('maer', learnedResp);
      MAER._saveToHistory(userMsg, learnedResp);
      MAER._updateStats();
      return;
    }

    // 2. Backend LLM con contexto enriquecido + historial de conversación
    if (MAER.config.backendOK) {
      this._showTyping();
      const payload = { prompt: this._construirPrompt(userMsg, modo) };
      if (this.ctxPath)  payload.path  = this.ctxPath;
      if (this.ctxTexto) payload.texto = this.ctxTexto.substring(0, 8000);

      // Pasar últimas 6 rondas del historial para contexto de conversación
      payload.history = this._getHistorial(6);

      const res = await MAER._call('/api/llm-chat', payload, { timeout: 45000 });
      this._hideTyping();

      if (res.ok && res.data?.response) {
        const reply = res.data.response;
        this._addMsg('maer', reply);
        MAER._saveToHistory(userMsg, reply);
        MAER._updateStats();
        return;
      }
    }

    // 3. Respuesta inteligente usando datos del análisis adjunto
    const docResp = this._responderConContextoDoc(userMsg);
    if (docResp) {
      this._addMsg('maer', docResp);
      MAER._saveToHistory(userMsg, docResp);
      MAER._updateStats();
      return;
    }

    // 4. Diccionario de 120+ patrones
    const dictResp = MAER_buscarRespuesta(userMsg);
    if (dictResp) {
      this._addMsg('maer', dictResp);
      MAER._saveToHistory(userMsg, dictResp);
      MAER._updateStats();
      return;
    }

    // 5. Conocimiento aprendido (IndexedDB)
    const conocimientoResp = await MAER.aprendizaje.buscarEnConocimiento(userMsg);
    if (conocimientoResp) {
      this._addMsg('maer', `📚 <em>Basado en lo que me enseñaste:</em><br><br>${conocimientoResp}`);
      MAER._saveToHistory(userMsg, conocimientoResp);
      MAER._updateStats();
      return;
    }

    // 6. Fallback
    this._addMsg('maer', this._fallback(userMsg, modo));
    MAER._updateStats();
  },

  /* ── RESPONDER CON DATOS DEL DOCUMENTO ADJUNTO ── */
  _responderConContextoDoc(userMsg) {
    const d = this.ctxAnalisis;
    if (!d) return null;

    const m = userMsg.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

    // Pregunta sobre CURP
    if (m.includes('curp') && d.curps?.length) {
      const c    = d.curps[0];
      const info = c.info || {};
      return `Según el documento adjunto:<br>
        <strong>CURP:</strong> <code>${c.curp}</code><br>
        ${info.fecha_nacimiento ? `<strong>Fecha de nacimiento:</strong> ${info.fecha_nacimiento}<br>` : ''}
        ${info.edad             ? `<strong>Edad:</strong> ${info.edad} años<br>` : ''}
        ${info.sexo             ? `<strong>Sexo:</strong> ${info.sexo}<br>` : ''}
        ${info.estado           ? `<strong>Estado:</strong> ${info.estado}<br>` : ''}
        <em>Estado de validación: ${c.valida ? 'Formato correcto ✓' : 'Verificar formato ⚠️'}</em>`;
    }

    // Pregunta sobre RFC
    if (m.includes('rfc') && d.rfcs?.length) {
      const r = d.rfcs[0];
      return `Según el documento adjunto:<br>
        <strong>RFC:</strong> <code>${r.rfc}</code><br>
        <em>${r.valido ? '✓ RFC con dígito verificador correcto.' : '⚠️ Verificar RFC en el SAT.'}</em>`;
    }

    // Pregunta sobre NSS
    if ((m.includes('nss') || m.includes('numero de seguridad') || m.includes('seguro social')) && d.nss?.length) {
      return `El NSS encontrado en el documento es: <strong><code>${d.nss[0]}</code></strong><br>
        ${d.nss.length > 1 ? `(También se encontraron: ${d.nss.slice(1).join(', ')})` : ''}`;
    }

    // Pregunta sobre semanas / pensión
    if (m.includes('semana') || m.includes('pension') || m.includes('cotiz') || m.includes('imss')) {
      if (d.semanas_cotizadas || d.pension_info) {
        const sem    = d.semanas_cotizadas || 0;
        const p      = d.pension_info || {};
        const faltan = Math.max(0, 1250 - sem);
        const ley    = p.ley || '';
        return `Análisis de pensión del documento adjunto:<br><br>
          📊 <strong>Semanas cotizadas detectadas:</strong> ${sem}<br>
          ${faltan > 0 ? `⏳ <strong>Faltan:</strong> ${faltan} semanas para la pensión base (1,250 requeridas)<br>` : '✅ <strong>Semanas suficientes</strong> para pensión base<br>'}
          ${ley ? `⚖️ <strong>Ley aplicable:</strong> ${ley}<br>` : ''}
          ${p.porcentaje_pension ? `💰 <strong>Cuantía estimada:</strong> ${p.porcentaje_pension}% del salario base<br>` : ''}
          <br><em>Para un análisis más completo, consulta directamente en el IMSS o usa Tareas IA → Investigación Pensión.</em>`;
      }
    }

    // Pregunta sobre el tipo de documento
    if (m.includes('que documento') || m.includes('tipo') || m.includes('que es') || m.includes('de que se trata')) {
      return `El documento adjunto fue clasificado como: <strong>${d.tipo_documento || 'Documento general'}</strong><br>
        Contiene ${(d.texto||'').length.toLocaleString()} caracteres de texto extraído.<br>
        ${d.curps?.length  ? `✅ ${d.curps.length} CURP detectada(s)<br>` : ''}
        ${d.rfcs?.length   ? `✅ ${d.rfcs.length} RFC detectado(s)<br>` : ''}
        ${d.nss?.length    ? `✅ ${d.nss.length} NSS detectado(s)<br>` : ''}
        ${d.semanas_cotizadas ? `✅ ${d.semanas_cotizadas} semanas cotizadas<br>` : ''}`;
    }

    return null;
  },

  /* ── OBTENER HISTORIAL DE CONVERSACIÓN ── */
  _getHistorial(maxRondas = 6) {
    const msgs = document.querySelectorAll('#chat-msgs .msg');
    const history = [];
    for (const el of msgs) {
      if (el.classList.contains('user')) {
        history.push({ role: 'user', content: el.textContent.trim() });
      } else if (el.classList.contains('maer')) {
        // Obtener solo el texto, sin el "🦁 MAER" del sender
        const sender = el.querySelector('.sender');
        const text = sender
          ? el.textContent.replace(sender.textContent, '').trim()
          : el.textContent.trim();
        if (text) history.push({ role: 'assistant', content: text });
      }
    }
    // Devolver las últimas maxRondas rondas (cada ronda = user + assistant)
    const limit = maxRondas * 2;
    return history.slice(-limit);
  },

  /* ── CONSTRUIR PROMPT CON CONTEXTO ── */
  _construirPrompt(msg, modo) {
    const prompts = {
      general: 'Eres MAER, asistente personal leal de Leonel Houssen Mojica en Ecatepec MX. Eres analítico, directo y protector. Responde siempre en español de México, de forma clara y sin rodeos.',
      pension: 'Eres MAER, experto en pensiones IMSS mexicanas. Conoces la Ley 73, Ley 97, AFORE, trámites del IMSS, recursos de inconformidad y derechos del trabajador. Ayuda a Leonel con su caso de pensión de forma práctica.',
      doc:     'Eres MAER, analizas documentos con precisión quirúrgica. Extrae información clave, detecta fechas, nombres, NSS, CURP, montos y cualquier dato relevante. Sé específico.',
      legal:   'Eres MAER, con profundo conocimiento del derecho mexicano: Ley del Seguro Social, Ley Federal del Trabajo, Código Civil, Ley de Amparo. Orienta a Leonel sobre sus derechos y procesos. Sé específico sobre artículos y plazos.'
    };

    let ctx = '';
    if (this.ctxAnalisis) {
      const d = this.ctxAnalisis;
      ctx = `\n\n[CONTEXTO DEL DOCUMENTO ANALIZADO]\n`;
      ctx += `Tipo: ${d.tipo_documento || 'Desconocido'}\n`;
      if (d.curps?.length)         ctx += `CURPs: ${d.curps.map(c=>c.curp).join(', ')}\n`;
      if (d.rfcs?.length)          ctx += `RFCs: ${d.rfcs.map(r=>r.rfc).join(', ')}\n`;
      if (d.nss?.length)           ctx += `NSS: ${d.nss.join(', ')}\n`;
      if (d.semanas_cotizadas)     ctx += `Semanas cotizadas: ${d.semanas_cotizadas}\n`;
      if (d.pension_info?.ley)     ctx += `Ley aplicable: ${d.pension_info.ley}\n`;
      if (d.texto)                 ctx += `Extracto de texto: ${d.texto.substring(0, 1000)}\n`;
      ctx += '[FIN CONTEXTO]\n';
    } else if (this.ctxTexto) {
      ctx = `\n\n[CONTEXTO ADICIONAL]\n${this.ctxTexto.substring(0, 1500)}\n[FIN CONTEXTO]\n`;
    }

    return `${prompts[modo] || prompts.general}${ctx}\n\nConsulta de Leonel: ${msg}`;
  },

  /* ── BUSCAR EN APRENDIZAJES ── */
  _buscarAprendido(msg) {
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    for (const l of learned) {
      try {
        if (new RegExp(l.trigger, 'i').test(msg)) return l.response;
      } catch(e) {
        if (msg.toLowerCase().includes(l.trigger.toLowerCase())) return l.response;
      }
    }
    return null;
  },

  /* ── FALLBACK ── */
  _fallback(msg, modo) {
    const m = msg.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    if (m.includes('imss') || m.includes('seguro'))
      return `Entiendo tu pregunta sobre el IMSS. ¿Puedes darme más detalles? Por ejemplo: semanas cotizadas, trámite específico, negativa de pensión o consulta sobre tu expediente.`;
    if (m.includes('ley') || m.includes('legal') || m.includes('articulo'))
      return `Para investigación legal profunda, usa la pestaña <strong>Tareas IA → Investigación Legal</strong>.`;
    if (m.includes('archivo') || m.includes('documento') || m.includes('pdf'))
      return `Para analizar documentos usa la pestaña <strong>Archivos</strong> — extrae CURP, RFC, NSS y calcula semanas de pensión automáticamente.`;
    if (this.ctxAnalisis)
      return `Tengo el documento <em>${this.ctxAnalisis.tipo_documento}</em> adjunto. ¿Sobre qué parte quieres que te informe? (CURP, RFC, semanas, tipo de documento, fechas…)`;
    const server = MAER.config.backendOK
      ? 'El motor LLM está activo.'
      : 'El servidor LLM no está conectado — actívalo para respuestas más completas.';
    return `${server} Puedo ayudarte mejor si reformulas la pregunta. Temas donde soy más fuerte: pensión IMSS, documentos legales, búsqueda de archivos.`;
  },

  /* ── ADJUNTAR ARCHIVO AL CHAT ── */
  async adjuntarArchivo() {
    const res = await MAER._call('/api/select-file', null);
    if (!res.ok || !res.data) return;

    const path = typeof res.data === 'string' ? res.data.trim() : String(res.data).trim();
    const name = path.split('/').pop();
    this.ctxPath = path;

    const el = document.getElementById('chat-ctx-file');
    if (el) el.innerHTML = `📎 <strong>${name}</strong>
      <span style="font-size:10px;color:var(--muted);margin-left:6px" id="chat-ctx-status">⏳ Analizando…</span>
      <button class="btn btn-secondary btn-sm" style="margin-left:6px" onclick="MAER.chat.quitarAdjunto()">✕</button>`;

    this._addMsg('sys', `📎 Archivo adjuntado: <strong>${name}</strong>. Analizando con el servidor…`);

    // Auto-análisis si el servidor está disponible
    if (MAER.config.backendOK) {
      try {
        // Necesitamos el File object para el análisis. Intentar /api/extract-text con path
        const ext = name.split('.').pop().toLowerCase();
        const r2  = await MAER._call('/api/extract-text', { path });
        if (r2.ok && r2.data) {
          // Simular el objeto de análisis con la data disponible
          const texto = r2.data.text || r2.data.texto || '';
          const datos = MAER.archivos._extraerDatos(texto);
          this.ctxAnalisis = {
            tipo_documento: this._clasificarPorNombre(name),
            texto,
            curps: datos.curp.map(c => ({ curp: c, valida: true, info: {} })),
            rfcs:  datos.rfc.map(r => ({ rfc: r, valido: true })),
            nss:   datos.nss,
            fechas: datos.fechas,
            montos: datos.montos,
          };
          this.ctxTexto = texto.substring(0, 4000);

          const statusEl = document.getElementById('chat-ctx-status');
          if (statusEl) statusEl.textContent = '✓ Listo';
          this._addMsg('sys', `✅ <strong>${name}</strong> analizado. Puedes preguntar sobre CURP, RFC, NSS, semanas de pensión, o el contenido del documento.`);
          MAER._log(`💬 Archivo adjunto analizado: ${name}`);
        } else {
          const statusEl = document.getElementById('chat-ctx-status');
          if (statusEl) statusEl.textContent = '(como referencia)';
          this._addMsg('sys', `📎 Archivo adjuntado como referencia: <strong>${name}</strong>.`);
        }
      } catch(e) {
        MAER._log(`⚠️ Auto-análisis adjunto: ${e.message}`);
      }
    } else {
      this._addMsg('sys', `📎 <strong>${name}</strong> adjuntado (servidor offline — análisis limitado).`);
    }
  },

  /* ── CLASIFICAR POR NOMBRE DE ARCHIVO ── */
  _clasificarPorNombre(nombre) {
    const n = nombre.toLowerCase();
    if (n.includes('resolucion') || n.includes('resolución')) return 'Resolución IMSS';
    if (n.includes('semana') || n.includes('cotiz'))          return 'Constancia de Semanas';
    if (n.includes('carta'))                                  return 'Carta';
    if (n.includes('acta'))                                   return 'Acta';
    if (n.includes('curp'))                                   return 'Documento CURP';
    if (n.includes('nss') || n.includes('seguro'))            return 'Documento IMSS';
    return 'Documento General';
  },

  quitarAdjunto() {
    this.ctxPath     = null;
    this.ctxTexto    = null;
    this.ctxAnalisis = null;
    const el = document.getElementById('chat-ctx-file');
    if (el) el.innerHTML = '<span style="color:var(--muted);font-size:11px">Sin archivo adjunto</span>';
  },
};
