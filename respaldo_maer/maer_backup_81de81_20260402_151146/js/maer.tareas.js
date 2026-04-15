/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Tareas IA
   Investigación legal, redacción de documentos,
   análisis de procesos, orientación jurídica
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.tareas = {

  archivoAdjunto: null,
  resultadoActual: null,

  /* ── TIPOS DE TAREA ── */
  TIPOS: {
    investigacion_legal: {
      label: '⚖️ Investigación Legal',
      prompt: (desc, ctx) => `Eres MAER, experto en derecho mexicano. Realiza una investigación legal completa sobre el siguiente tema:\n\n${desc}\n\n${ctx ? 'Contexto adicional:\n' + ctx : ''}\n\nIncluye: artículos de ley relevantes, criterios jurisprudenciales, plazos, instancias competentes, y recomendaciones prácticas para Leonel. Cita artículos específicos.`,
    },
    redactar_carta: {
      label: '✉️ Redactar Documento',
      prompt: (desc, ctx) => `Eres MAER, redactor de documentos legales y oficiales mexicanos. Redacta el siguiente documento:\n\n${desc}\n\n${ctx ? 'Datos o contexto:\n' + ctx : ''}\n\nRedacta de forma formal, clara y profesional. Si es una carta al IMSS o autoridad, incluye fundamento legal.`,
    },
    analisis_proceso: {
      label: '🗺️ Análisis de Proceso',
      prompt: (desc, ctx) => `Eres MAER, analista de procesos administrativos y legales mexicanos. Analiza el siguiente proceso paso a paso:\n\n${desc}\n\n${ctx ? 'Información relevante:\n' + ctx : ''}\n\nDetalla: pasos a seguir, documentos requeridos, instancias, plazos, posibles obstáculos y alternativas. Hazlo práctico y accionable para Leonel.`,
    },
    orientacion_imss: {
      label: '🏛️ Orientación IMSS',
      prompt: (desc, ctx) => `Eres MAER, especialista en trámites y derechos del IMSS. Orienta sobre:\n\n${desc}\n\n${ctx ? 'Situación actual:\n' + ctx : ''}\n\nProporciona orientación práctica: ventanillas, documentos, fundamento en la Ley del Seguro Social, y los mejores argumentos para defender los derechos del trabajador.`,
    },
    resumen_documento: {
      label: '📋 Resumir Documento',
      prompt: (desc, ctx) => `Eres MAER, analista de documentos. Resume y extrae los puntos más importantes del siguiente documento:\n\n${desc}\n\n${ctx ? 'Texto del documento:\n' + ctx : ''}\n\nIdentifica: fechas clave, personas mencionadas, NSS/CURP/RFC si los hay, compromisos o resoluciones, y cualquier dato relevante para un caso de pensión.`,
    },
    estrategia_legal: {
      label: '🎯 Estrategia Legal',
      prompt: (desc, ctx) => `Eres MAER, estratega legal. Diseña una estrategia legal para el siguiente caso:\n\n${desc}\n\n${ctx ? 'Antecedentes:\n' + ctx : ''}\n\nDefine: objetivo principal, pasos en orden de prioridad, recursos legales disponibles, fortalezas y debilidades del caso, y un plan de acción concreto.`,
    },
  },

  /* ── EJECUTAR TAREA ── */
  async ejecutar() {
    const tipo = document.getElementById('tarea-tipo')?.value;
    const desc = document.getElementById('tarea-desc')?.value?.trim();
    if (!desc) {
      alert('Describe la tarea que necesitas.');
      return;
    }

    const tipoDef = this.TIPOS[tipo];
    if (!tipoDef) { alert('Tipo de tarea no reconocido.'); return; }

    const btn = document.getElementById('btn-tarea');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loader"></span> Procesando...'; }

    const area = document.getElementById('tarea-resultado');
    if (area) {
      area.style.display = 'block';
      area.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:12px">
        <div class="typing-dots"><span></span><span></span><span></span></div>
        MAER está trabajando en tu solicitud...
      </div>`;
    }

    // Contexto: texto de documento adjunto
    let contexto = '';
    if (this.archivoAdjunto) {
      try {
        const ext = this.archivoAdjunto.name.split('.').pop().toLowerCase();
        const textExts = ['txt','md','csv','json','js','py','html','xml'];
        if (textExts.includes(ext)) {
          contexto = (await this.archivoAdjunto.text()).substring(0, 3000);
        }
      } catch(e) {}
    }

    const prompt = tipoDef.prompt(desc, contexto);

    try {
      if (MAER.config.backendOK) {
        const res = await MAER._call('/api/llm-chat', { prompt }, { timeout: 60000 });
        if (res.ok && res.data?.response) {
          this._mostrarResultado(tipoDef.label, res.data.response, area);
          MAER.voz?.hablar(`Tarea completada: ${tipoDef.label}`);
          return;
        }
      }
      // Fallback: respuesta del diccionario / básica
      this._fallbackTarea(tipoDef.label, desc, tipo, area);
    } catch(e) {
      this._fallbackTarea(tipoDef.label, desc, tipo, area);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '⚡ Ejecutar Tarea'; }
    }
  },

  /* ── MOSTRAR RESULTADO ── */
  _mostrarResultado(label, texto, area) {
    this.resultadoActual = texto;
    if (!area) return;
    // Convertir saltos de línea a párrafos HTML
    const html = texto
      .split('\n\n').map(p => `<p style="margin:0 0 10px 0;line-height:1.7">${
        p.replace(/\n/g,'<br>')
         .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
         .replace(/\*(.*?)\*/g, '<em>$1</em>')
      }</p>`).join('');

    area.innerHTML = `
      <div style="border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div style="font-size:14px;font-weight:600;color:var(--accent)">${label}</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-secondary btn-sm" onclick="MAER.tareas._copiar()">📋 Copiar</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.tareas._guardarComoNota()">📝 Nota</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.exportar?.tareaHTML()" title="Imprimir o guardar como PDF">🖨️ PDF</button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.exportar?.tareasTXT()" title="Descargar como TXT">⬇️ TXT</button>
          <button class="btn btn-primary btn-sm" onclick="MAER.tareas._aprenderResultado()">📚 Memorizar</button>
        </div>
      </div>
      <div style="font-size:13px;color:var(--text);line-height:1.7">${html}</div>`;
  },

  /* ── FALLBACK SIN SERVIDOR ── */
  _fallbackTarea(label, desc, tipo, area) {
    const msgs = {
      investigacion_legal: `Para investigación legal completa, el servidor LLM necesita estar activo.\n\nMientras tanto, puedes consultar:\n• ley.imss.gob.mx — Ley del Seguro Social\n• scjn.gob.mx — Jurisprudencia\n• sat.gob.mx — Normativa fiscal\n• profedet.gob.mx — Defensa del trabajo\n\nIniciar servidor: python server.py`,
      redactar_carta: `Para redacción automática de documentos el servidor LLM es necesario.\n\nUsa la pestaña Pensión → Cartas para generar cartas prediseñadas al IMSS, incluyendo: solicitud de semanas, recurso de inconformidad, derecho de petición y más.`,
      orientacion_imss: `Para orientación IMSS completa el servidor LLM es necesario.\n\nDatos clave para pensiones:\n• Ley 73 requiere 500 semanas + 60 años\n• Ley 97 requiere 1,250 semanas + 65 años\n• Recurso de inconformidad: Art. 294 LSS (15 días hábiles)\n• PROFEDET: 55-5-998-2000\n• IMSS Digital: imss.gob.mx`,
      analisis_proceso: `Análisis de proceso detallado requiere servidor LLM.\n\nPara trámites IMSS los pasos generales son:\n1. Solicitar Constancia de Semanas (Módulo o IMSS Digital)\n2. Reunir documentos (ver Pensión → Checklist)\n3. Presentar solicitud en Subdelegación\n4. Esperar resolución (30 días hábiles)\n5. Si hay negativa: Recurso de Inconformidad Art. 294 LSS`,
      resumen_documento: `Para resumir documentos automáticamente el servidor LLM es necesario.\n\nMientras tanto:\n• Sube el documento a la pestaña Archivos para ver su contenido\n• Usa Aprendizaje para que MAER lo memorice\n• Pregunta sobre su contenido en el Chat una vez memorizado`,
      estrategia_legal: `Para diseño de estrategia legal el servidor LLM es necesario.\n\nOrientación básica:\n1. Recopila toda la documentación (ver checklist)\n2. Certifica semanas en el IMSS\n3. Presenta solicitud formal por escrito\n4. En caso de negativa: Recurso de Inconformidad (15 días)\n5. Si persiste: Amparo Indirecto ante Juez de Distrito\n6. Considera PROFEDET o asesor jurídico laboral`,
    };

    const msg = msgs[tipo] || 'Para esta tarea necesitas el servidor LLM activo. Inicia el servidor y vuelve a intentarlo.';
    this.resultadoActual = msg;
    if (area) {
      area.innerHTML = `
        <div style="border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:14px">
          <div style="font-size:14px;font-weight:600;color:var(--yellow)">${label} — Modo Offline</div>
        </div>
        <div style="font-size:13px;color:var(--text);line-height:1.8;white-space:pre-wrap">${msg}</div>
        <div style="margin-top:12px">
          <button class="btn btn-secondary btn-sm" onclick="MAER.tareas._copiar()">📋 Copiar</button>
        </div>`;
    }
    MAER.voz?.hablar('El servidor LLM no está activo. Te muestro orientación básica.');
  },

  /* ── ADJUNTAR ARCHIVO A TAREA ── */
  adjuntarArchivo(file) {
    if (!file) return;
    this.archivoAdjunto = file;
    const el = document.getElementById('tarea-archivo-nombre');
    if (el) el.textContent = `📎 ${file.name}`;
    MAER.chat._addMsg('sys', `📎 Documento adjuntado para tarea: <strong>${file.name}</strong>`);
  },

  quitarAdjunto() {
    this.archivoAdjunto = null;
    const el = document.getElementById('tarea-archivo-nombre');
    if (el) el.textContent = 'Sin archivo adjunto';
  },

  /* ── ACCIONES SOBRE RESULTADO ── */
  _copiar() {
    if (!this.resultadoActual) return;
    navigator.clipboard.writeText(this.resultadoActual).then(() => {
      MAER.chat._addMsg('sys', '📋 Resultado copiado al portapapeles.');
      MAER.voz?.hablar('Copiado.');
    });
  },

  _guardarComoNota() {
    if (!this.resultadoActual) return;
    const existing = localStorage.getItem('maer_pension_notas') || '';
    const nueva = existing + '\n\n---\n' + new Date().toLocaleString('es-MX') + '\n' + this.resultadoActual;
    localStorage.setItem('maer_pension_notas', nueva);
    const el = document.getElementById('pension-notas');
    if (el) el.value = nueva;
    MAER.chat._addMsg('sys', '📝 Resultado guardado en notas de pensión.');
    MAER.voz?.hablar('Guardado en notas.');
  },

  async _aprenderResultado() {
    if (!this.resultadoActual) return;
    const tipo = document.getElementById('tarea-tipo')?.value || 'tarea';
    const desc = document.getElementById('tarea-desc')?.value?.trim().substring(0, 50) || 'Tarea IA';
    await MAER.aprendizaje.guardar({
      nombre:   `${tipo}: ${desc}`,
      etiqueta: tipo,
      texto:    this.resultadoActual,
      chars:    this.resultadoActual.length,
      tipo:     'tarea_ia',
    });
    MAER.aprendizaje._renderLista();
    MAER.chat._addMsg('sys', '📚 Resultado memorizado en conocimiento permanente.');
    MAER.voz?.hablar('Resultado memorizado.');
  },
};
