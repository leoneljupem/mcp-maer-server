/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo de Chat IA
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.chat = {

  ctxPath:  null,   // Archivo adjunto al chat
  ctxTexto: null,   // Texto del archivo adjunto (de aprendizaje)

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
        MAER.voz.hablar(html);
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

  /* ── INDICADOR DE TYPING ── */
  _showTyping() {
    const msgs = document.getElementById('chat-msgs');
    const div = document.createElement('div');
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

    // 1. Buscar en respuestas aprendidas por el usuario
    const learnedResp = this._buscarAprendido(userMsg);
    if (learnedResp) {
      this._addMsg('maer', learnedResp);
      MAER._saveToHistory(userMsg, learnedResp);
      MAER._updateStats();
      return;
    }

    // 2. Intentar backend LLM si está disponible
    if (MAER.config.backendOK) {
      this._showTyping();
      const payload = { prompt: this._construirPrompt(userMsg, modo) };
      if (this.ctxPath) payload.path = this.ctxPath;
      const res = await MAER._call('/api/llm-chat', payload, { timeout: 30000 });
      this._hideTyping();

      if (res.ok && res.data?.response) {
        const reply = res.data.response;
        this._addMsg('maer', reply);
        MAER._saveToHistory(userMsg, reply);
        MAER._updateStats();
        return;
      }
    }

    // 3. Buscar en diccionario de 120+ patrones
    const dictResp = MAER_buscarRespuesta(userMsg);
    if (dictResp) {
      this._addMsg('maer', dictResp);
      MAER._saveToHistory(userMsg, dictResp);
      MAER._updateStats();
      return;
    }

    // 4. Buscar en conocimiento aprendido (IndexedDB)
    const conocimientoResp = await MAER.aprendizaje.buscarEnConocimiento(userMsg);
    if (conocimientoResp) {
      this._addMsg('maer', `📚 <em>Basado en lo que me enseñaste:</em><br><br>${conocimientoResp}`);
      MAER._saveToHistory(userMsg, conocimientoResp);
      MAER._updateStats();
      return;
    }

    // 5. Respuesta genérica de fallback
    this._addMsg('maer', this._fallback(userMsg, modo));
    MAER._updateStats();
  },

  /* ── CONSTRUIR PROMPT CON CONTEXTO ── */
  _construirPrompt(msg, modo) {
    const prompts = {
      general: 'Eres MAER, asistente personal leal de Leonel Houssen Mojica en Ecatepec MX. Eres analítico, directo y protector. Responde siempre en español de México, de forma clara y sin rodeos.',
      pension: 'Eres MAER, experto en pensiones IMSS mexicanas. Conoces la Ley 73, Ley 97, AFORE, trámites del IMSS, recursos de inconformidad y derechos del trabajador. Ayuda a Leonel con su caso de pensión de forma práctica.',
      doc: 'Eres MAER, analizas documentos con precisión quirúrgica. Extrae información clave, detecta fechas, nombres, NSS, CURP, montos y cualquier dato relevante. Sé específico.',
      legal: 'Eres MAER, con profundo conocimiento del derecho mexicano: Ley del Seguro Social, Ley Federal del Trabajo, Código Civil, Ley de Amparo. Orienta a Leonel sobre sus derechos y procesos. Sé específico sobre artículos y plazos.'
    };
    return `${prompts[modo] || prompts.general}\n\nConsulta de Leonel: ${msg}`;
  },

  /* ── BUSCAR EN APRENDIZAJES DEL USUARIO ── */
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
    if (m.includes('imss') || m.includes('seguro')) return `Entiendo tu pregunta sobre el IMSS. Para una respuesta más completa, ¿puedes darme más detalles? Por ejemplo: ¿es sobre semanas cotizadas, un trámite específico, o una negativa?`;
    if (m.includes('ley') || m.includes('legal') || m.includes('articulo')) return `Para investigación legal profunda, usa la pestaña <strong>Tareas IA → Investigación Legal</strong> donde puedo analizar leyes, artículos y jurisprudencias específicas para tu caso.`;
    if (m.includes('archivo') || m.includes('documento') || m.includes('pdf')) return `Para analizar documentos, usa las pestañas <strong>Archivos</strong> o <strong>Imágenes</strong>. También puedes enseñarme el contenido en <strong>Aprendizaje</strong> para que lo memorice.`;
    const server = MAER.config.backendOK ? 'El motor LLM está activo pero no generó respuesta para esta consulta.' : 'El servidor LLM no está conectado en este momento.';
    return `${server} Puedo ayudarte mejor si reformulas la pregunta. Temas donde soy más fuerte: pensión IMSS, documentos legales, búsqueda de archivos, orientación de procesos.`;
  },

  /* ── ADJUNTAR ARCHIVO AL CHAT ── */
  async adjuntarArchivo() {
    const res = await MAER._call('/api/select-file', null);
    if (res.ok && res.data) {
      const path = typeof res.data === 'string' ? res.data.trim() : String(res.data).trim();
      const name = path.split('/').pop();
      this.ctxPath = path;
      const el = document.getElementById('chat-ctx-file');
      if (el) el.innerHTML = `📎 <strong>${name}</strong> <button class="btn btn-secondary btn-sm" onclick="MAER.chat.quitarAdjunto()">✕</button>`;
      this._addMsg('sys', `📎 Archivo adjuntado: <strong>${name}</strong>. Lo usaré como contexto en las respuestas.`);
    }
  },

  quitarAdjunto() {
    this.ctxPath = null;
    const el = document.getElementById('chat-ctx-file');
    if (el) el.innerHTML = '<span style="color:var(--muted);font-size:11px">Sin archivo adjunto</span>';
  },
};
