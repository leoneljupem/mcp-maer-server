/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Timeline del Proceso de Pensión IMSS
   BLOQUE 7 — Panel visual de seguimiento por etapas
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.timeline = {

  STORAGE_KEY: 'maer_timeline',

  etapas: [
    { id: 'documentos',   icon: '📄', label: 'Documentos reunidos',      desc: 'Reunir acta de nacimiento, CURP, INE, NSS, semanas cotizadas, historial laboral, nóminas, AFORE, comprobante domicilio, CLABE, formato RMA-07.' },
    { id: 'pre-revision', icon: '🔍', label: 'Pre-revisión IMSS Digital', desc: 'Verificar semanas cotizadas en portal IMSS Digital. Confirmar que el expediente esté completo antes de ir a ventanilla.' },
    { id: 'solicitud',    icon: '📋', label: 'Solicitud presentada',      desc: 'Presentar solicitud formal en la Subdelegación del IMSS. Recibir acuse con folio y fecha.' },
    { id: 'revision',     icon: '⏳', label: 'En revisión por IMSS',      desc: 'El IMSS tiene máximo 45 días hábiles para resolver. Estar atento a cualquier requerimiento adicional.' },
    { id: 'resolucion',   icon: '📜', label: 'Resolución emitida',        desc: 'El IMSS emite resolución: aprobada o negada. Si es aprobada, revisar monto y condiciones. Si es negada, preparar recurso.' },
    { id: 'recurso',      icon: '⚖️', label: 'Recurso de inconformidad',  desc: 'Si la resolución fue negativa o el monto es incorrecto. Plazo: 15 días hábiles después de la notificación. Presentar ante el Consejo Consultivo Delegacional.' },
    { id: 'amparo',       icon: '🏛️', label: 'Amparo / PROFEDET',        desc: 'Si el recurso no prospera: juicio de amparo ante Juzgado de Distrito, o acudir a PROFEDET para representación gratuita.' },
    { id: 'otorgada',     icon: '✅', label: 'Pensión otorgada',          desc: 'Pensión confirmada y primer depósito recibido. Verificar monto mensual y vigencia del pago.' }
  ],

  datos: null, // { etapaActual: 'documentos', historial: [{id, fecha, notas}], notas: {} }

  /* ── INICIALIZAR ── */
  init() {
    this.datos = this._cargar();
    if (!this.datos) {
      this.datos = {
        etapaActual: 'documentos',
        historial: [{ id: 'documentos', fecha: new Date().toISOString(), notas: 'Inicio del proceso' }],
        notas: {}
      };
      this._guardar();
    }
  },

  /* ── MARCAR ETAPA ── */
  marcar(etapaId, notas = '') {
    const idx = this.etapas.findIndex(e => e.id === etapaId);
    if (idx < 0) return false;

    this.datos.etapaActual = etapaId;
    this.datos.historial.push({
      id: etapaId,
      fecha: new Date().toISOString(),
      notas: notas || ''
    });
    if (notas) this.datos.notas[etapaId] = notas;
    this._guardar();
    this.render();

    const etapa = this.etapas[idx];
    MAER.voz?.hablar(`Etapa actualizada: ${etapa.label}.`);
    return true;
  },

  /* ── OBTENER ETAPA ACTUAL ── */
  obtenerActual() {
    if (!this.datos) this.init();
    const idx = this.etapas.findIndex(e => e.id === this.datos.etapaActual);
    const etapa = this.etapas[idx] || this.etapas[0];
    // Calcular días en esta etapa
    const ultimoRegistro = [...this.datos.historial].reverse().find(h => h.id === etapa.id);
    let diasEnEtapa = 0;
    if (ultimoRegistro) {
      diasEnEtapa = Math.floor((Date.now() - new Date(ultimoRegistro.fecha).getTime()) / 86400000);
    }
    return { ...etapa, indice: idx, diasEnEtapa, notas: this.datos.notas[etapa.id] || '' };
  },

  /* ── RENDER COMPLETO ── */
  render() {
    const contenedor = document.getElementById('timeline-panel');
    if (!contenedor) return;
    if (!this.datos) this.init();

    const actual = this.obtenerActual();
    const idxActual = actual.indice;

    let html = '<div class="timeline-track">';

    this.etapas.forEach((etapa, i) => {
      const estado = i < idxActual ? 'completada' : (i === idxActual ? 'actual' : 'pendiente');
      const notas = this.datos.notas[etapa.id] || '';
      const histEntry = this.datos.historial.find(h => h.id === etapa.id);
      const fecha = histEntry ? new Date(histEntry.fecha).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : '';

      html += `
        <div class="timeline-etapa timeline-${estado}" data-etapa="${etapa.id}" onclick="MAER.timeline._clickEtapa('${etapa.id}')">
          <div class="timeline-icon">${estado === 'completada' ? '✔️' : etapa.icon}</div>
          <div class="timeline-info">
            <div class="timeline-label">${etapa.label}</div>
            ${fecha ? `<div class="timeline-fecha">${fecha}</div>` : ''}
            ${estado === 'actual' ? `<div class="timeline-dias">${actual.diasEnEtapa} día${actual.diasEnEtapa !== 1 ? 's' : ''} en esta etapa</div>` : ''}
          </div>
          ${i < this.etapas.length - 1 ? '<div class="timeline-line"></div>' : ''}
        </div>`;
    });

    html += '</div>';

    // Info de la etapa actual
    html += `
      <div class="card" style="margin-top:16px;border-left:4px solid var(--primary)">
        <div class="card-title">${actual.icon} ${actual.label}</div>
        <p style="margin:8px 0;color:var(--text-secondary);font-size:0.9em">${actual.desc}</p>
        ${actual.notas ? `<p style="margin:4px 0;font-style:italic">"${actual.notas}"</p>` : ''}
      </div>`;

    // Botones de acción
    const siguienteIdx = idxActual + 1;
    const anteriorIdx = idxActual - 1;

    html += '<div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">';

    if (anteriorIdx >= 0) {
      html += `<button class="btn btn-secondary btn-sm" onclick="MAER.timeline._retroceder()">← Etapa anterior</button>`;
    }

    if (siguienteIdx < this.etapas.length) {
      html += `<button class="btn btn-primary btn-sm" onclick="MAER.timeline._avanzar()">Avanzar a: ${this.etapas[siguienteIdx].label} →</button>`;
    }

    html += `<button class="btn btn-secondary btn-sm" onclick="MAER.timeline._editarNotas()">📝 Notas</button>`;
    html += '</div>';

    // Historial
    if (this.datos.historial.length > 1) {
      html += `<div style="margin-top:16px"><strong>📅 Historial de cambios:</strong><ul style="margin:8px 0;padding-left:20px">`;
      [...this.datos.historial].reverse().forEach(h => {
        const etapa = this.etapas.find(e => e.id === h.id);
        const f = new Date(h.fecha).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        html += `<li style="margin:4px 0"><strong>${etapa?.icon || ''} ${etapa?.label || h.id}</strong> — ${f}${h.notas ? ` — <em>${h.notas}</em>` : ''}</li>`;
      });
      html += '</ul></div>';
    }

    contenedor.innerHTML = html;
  },

  /* ── ACCIONES PRIVADAS ── */
  _avanzar() {
    const actual = this.obtenerActual();
    const siguiente = this.etapas[actual.indice + 1];
    if (!siguiente) return;
    const notas = prompt(`Notas para "${siguiente.label}" (opcional):`) || '';
    this.marcar(siguiente.id, notas);
  },

  _retroceder() {
    const actual = this.obtenerActual();
    const anterior = this.etapas[actual.indice - 1];
    if (!anterior) return;
    if (confirm(`¿Regresar a "${anterior.label}"?`)) {
      this.marcar(anterior.id, 'Retroceso manual');
    }
  },

  _clickEtapa(etapaId) {
    const etapa = this.etapas.find(e => e.id === etapaId);
    if (!etapa) return;
    const notas = this.datos.notas[etapaId] || 'Sin notas';
    const hist = this.datos.historial.filter(h => h.id === etapaId);
    let msg = `${etapa.icon} <strong>${etapa.label}</strong><br>${etapa.desc}`;
    if (hist.length > 0) {
      msg += `<br><br><strong>Registros:</strong>`;
      hist.forEach(h => {
        const f = new Date(h.fecha).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
        msg += `<br>• ${f}${h.notas ? ` — ${h.notas}` : ''}`;
      });
    }
    MAER.chat._addMsg('sys', msg, false);
    MAER.tabs.show('chat');
  },

  _editarNotas() {
    const actual = this.obtenerActual();
    const nuevas = prompt(`Notas para "${actual.label}":`, actual.notas || '');
    if (nuevas !== null) {
      this.datos.notas[actual.id] = nuevas;
      this._guardar();
      this.render();
    }
  },

  /* ── PERSISTENCIA ── */
  _cargar() {
    try { return JSON.parse(localStorage.getItem(this.STORAGE_KEY)); } catch(e) { return null; }
  },

  _guardar() {
    try { localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.datos)); } catch(e) {}
  }
};
