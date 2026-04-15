/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo Pensión IMSS
   Checklist, notas, eventos, generador de cartas, orientación
   SIN calculadora — Solo información y herramientas prácticas
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.pension = {

  /* ── DOCUMENTOS REQUERIDOS ── */
  DOCS: [
    'Acta de nacimiento (original + copia)',
    'CURP (impresión oficial)',
    'INE / IFE vigente (ambas caras)',
    'Número de Seguro Social (NSS) oficial',
    'Semanas cotizadas certificadas (IMSS)',
    'Historial laboral completo (IMSS Digital)',
    'Últimas 5 nóminas o recibos de salario',
    'Estado de cuenta AFORE (si aplica Ley 97)',
    'Comprobante de domicilio reciente',
    'CLABE interbancaria para depósito',
    'Formato RMA-07 o PM-07 firmado',
  ],

  /* ── CARGAR NOTAS ── */
  _loadNotas() {
    const notas = localStorage.getItem('maer_pension_notas') || '';
    const el = document.getElementById('pension-notas');
    if (el) el.value = notas;
  },

  /* ── GUARDAR NOTAS ── */
  guardarNotas() {
    const el = document.getElementById('pension-notas');
    if (!el) return;
    localStorage.setItem('maer_pension_notas', el.value);
    MAER.chat._addMsg('sys', '💾 Notas de pensión guardadas.');
    MAER.voz?.hablar('Notas guardadas.');
  },

  /* ── ACTUALIZAR CHECKLIST ── */
  updateDocs() {
    const checked = [];
    for (let i = 1; i <= 11; i++) {
      const el = document.getElementById(`doc${i}`);
      if (el) {
        localStorage.setItem(`maer_doc${i}`, el.checked ? '1' : '0');
        if (el.checked) checked.push(i);
      }
    }
    const pct = Math.round((checked.length / 11) * 100);
    const bar = document.getElementById('docs-progress-bar');
    if (bar) {
      bar.style.width = pct + '%';
      bar.style.background = pct < 40 ? 'var(--red)' : pct < 80 ? 'var(--yellow)' : 'var(--green)';
    }
    const label = document.getElementById('docs-progress-label');
    if (label) label.textContent = `${checked.length} / 11 documentos (${pct}%)`;
    MAER._updateStats();
  },

  /* ── CALENDARIOS Y EVENTOS ── */
  _loadEventos() {
    const evs = JSON.parse(localStorage.getItem('maer_eventos') || '[]');
    this._renderEventos(evs);
  },

  agregarEvento() {
    const fecha = document.getElementById('evento-fecha')?.value;
    const desc  = document.getElementById('evento-desc')?.value?.trim();
    if (!fecha || !desc) { alert('Completa fecha y descripción.'); return; }

    const evs = JSON.parse(localStorage.getItem('maer_eventos') || '[]');
    evs.push({ fecha, desc, ts: Date.now() });
    evs.sort((a,b) => a.fecha.localeCompare(b.fecha));
    localStorage.setItem('maer_eventos', JSON.stringify(evs));
    this._renderEventos(evs);

    document.getElementById('evento-desc').value = '';
    MAER.chat._addMsg('sys', `📅 Evento agregado: <strong>${fecha}</strong> — ${desc}`);
    MAER.voz?.hablar(`Evento guardado para el ${fecha}.`);
  },

  _renderEventos(evs) {
    const el = document.getElementById('eventos-lista');
    if (!el) return;
    if (!evs.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">Sin eventos programados.</div>';
      return;
    }
    const hoy = new Date().toISOString().split('T')[0];
    el.innerHTML = evs.map((ev, i) => {
      const pasado = ev.fecha < hoy;
      const hoyMismo = ev.fecha === hoy;
      return `<div style="display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;
        background:${hoyMismo ? 'rgba(56,189,248,0.1)' : 'var(--surface)'};
        border:1px solid ${hoyMismo ? 'var(--accent)' : 'var(--border)'};
        margin-bottom:6px;opacity:${pasado && !hoyMismo ? '0.5' : '1'}">
        <span style="font-size:18px">${hoyMismo ? '🔔' : pasado ? '✅' : '📅'}</span>
        <div style="flex:1">
          <div style="font-size:12px;font-weight:600;color:${hoyMismo ? 'var(--accent)' : 'var(--text)'}">${ev.fecha}${hoyMismo ? ' — HOY' : ''}</div>
          <div style="font-size:12px;color:var(--muted)">${ev.desc}</div>
        </div>
        <button class="btn btn-danger btn-sm" onclick="MAER.pension._borrarEvento(${i})">🗑️</button>
      </div>`;
    }).join('');
  },

  _borrarEvento(idx) {
    const evs = JSON.parse(localStorage.getItem('maer_eventos') || '[]');
    evs.splice(idx, 1);
    localStorage.setItem('maer_eventos', JSON.stringify(evs));
    this._renderEventos(evs);
  },

  /* ── GENERADOR DE CARTAS ── */
  generarCarta() {
    const tipo   = document.getElementById('carta-tipo')?.value;
    const nombre = document.getElementById('carta-nombre')?.value?.trim();
    const nss    = document.getElementById('carta-nss')?.value?.trim();
    const curp   = document.getElementById('carta-curp')?.value?.trim();
    const fecha  = document.getElementById('carta-fecha')?.value?.trim() || new Date().toLocaleDateString('es-MX',{day:'2-digit',month:'long',year:'numeric'});

    if (!nombre || !nss) {
      alert('Por favor completa Nombre completo y NSS.');
      return;
    }

    const cartas = {
      semanas: this._cartaSemanas(nombre, nss, curp, fecha),
      inconformidad: this._cartaInconformidad(nombre, nss, curp, fecha),
      beneficiarios: this._cartaBeneficiarios(nombre, nss, curp, fecha),
      derecho_peticion: this._cartaDerechoPeticion(nombre, nss, curp, fecha),
    };

    const contenido = cartas[tipo] || cartas.semanas;
    const area = document.getElementById('carta-resultado');
    if (area) {
      area.style.display = 'block';
      area.querySelector('#carta-texto').textContent = contenido;
    }
    MAER.voz?.hablar('Carta generada. Revisa y ajusta los datos antes de imprimir.');
  },

  _cartaSemanas(nombre, nss, curp, fecha) {
    return `${fecha}

C. Delegado o Subdelegado del IMSS
Instituto Mexicano del Seguro Social
Presente

ASUNTO: Solicitud de certificación de semanas cotizadas

Yo, ${nombre}, con Número de Seguro Social ${nss}${curp ? ` y CURP ${curp}` : ''}, respetuosamente me dirijo a usted para solicitar la certificación del total de semanas cotizadas en el IMSS durante toda mi vida laboral, conforme a lo establecido en el Artículo 15, fracción I de la Ley del Seguro Social.

Esta información me es necesaria para iniciar el trámite de mi pensión por vejez / cesantía en edad avanzada.

Por lo anterior, solicito se expida en el menor plazo posible la constancia correspondiente.

Agradezco de antemano su atención y quedo a sus órdenes.

Atentamente,

_______________________________
${nombre}
NSS: ${nss}${curp ? `\nCURP: ${curp}` : ''}

Domicilio para oír y recibir notificaciones: ________________________________
Tel/correo: _______________________________________________________________`;
  },

  _cartaInconformidad(nombre, nss, curp, fecha) {
    return `${fecha}

C. Delegado del IMSS
Instituto Mexicano del Seguro Social
Presente

ASUNTO: Recurso de Inconformidad

Yo, ${nombre}, NSS ${nss}${curp ? `, CURP ${curp}` : ''}, con fundamento en los artículos 294 y 295 de la Ley del Seguro Social, interpongo formal RECURSO DE INCONFORMIDAD en contra de la resolución de fecha __________ mediante la cual se niega / resuelve de forma desfavorable mi solicitud de pensión, por las siguientes razones:

PRIMERO. He cumplido con todos los requisitos exigidos por la Ley.

SEGUNDO. La resolución impugnada contiene los siguientes errores de hecho y de derecho: ____________________________________________________________.

TERCERO. Cuento con documentación que acredita mis derechos, misma que se anexa al presente.

Por lo anterior, solicito se revise y revoque la resolución impugnada, emitiendo una nueva que reconozca mis derechos adquiridos.

Atentamente,

_______________________________
${nombre}
NSS: ${nss}${curp ? `\nCURP: ${curp}` : ''}`;
  },

  _cartaBeneficiarios(nombre, nss, curp, fecha) {
    return `${fecha}

C. Delegado del IMSS
Instituto Mexicano del Seguro Social
Presente

ASUNTO: Designación / Actualización de Beneficiarios

Yo, ${nombre}, con Número de Seguro Social ${nss}${curp ? ` y CURP ${curp}` : ''}, por medio del presente escrito solicito se registre / actualice la designación de mis beneficiarios para efectos de pensión de viudez, orfandad y ascendientes, conforme al Artículo 84 y 193 de la Ley del Seguro Social.

Mis beneficiarios son:

1. Nombre: _________________________ Parentesco: _____________ CURP: __________________
2. Nombre: _________________________ Parentesco: _____________ CURP: __________________

Se adjuntan actas de nacimiento / matrimonio y documentos de identificación.

Atentamente,

_______________________________
${nombre}
NSS: ${nss}`;
  },

  _cartaDerechoPeticion(nombre, nss, curp, fecha) {
    return `${fecha}

C. Director General del IMSS
Instituto Mexicano del Seguro Social
Presente

ASUNTO: Derecho de Petición — Artículo 8 Constitucional

Yo, ${nombre}, NSS ${nss}${curp ? `, CURP ${curp}` : ''}, ejerciendo mi derecho constitucional de petición consagrado en el Artículo 8 de la Constitución Política de los Estados Unidos Mexicanos, solicito respetuosamente a esa institución:

1. Me informe sobre el estado actual de mi trámite de pensión, número de expediente y área responsable.
2. Se establezca un plazo definido para resolver mi solicitud.
3. Se me notifique por escrito la resolución correspondiente.

De no recibir respuesta en los plazos que marca la Ley, me reservo el derecho de interponer los recursos legales correspondientes, incluyendo Amparo Indirecto ante Juez de Distrito.

Atentamente,

_______________________________
${nombre}
NSS: ${nss}${curp ? `\nCURP: ${curp}` : ''}`;
  },

  /* ── COPIAR CARTA ── */
  copiarCarta() {
    const el = document.getElementById('carta-texto');
    if (!el) return;
    navigator.clipboard.writeText(el.textContent).then(() => {
      MAER.chat._addMsg('sys', '📋 Carta copiada al portapapeles.');
      MAER.voz?.hablar('Carta copiada.');
    });
  },

  /* ── INFO PLAZOS LEGALES ── */
  plazosInfo() {
    const info = [
      { ley: 'Recurso de Inconformidad',  plazo: '15 días hábiles desde notificación',   ref: 'Art. 294 LSS' },
      { ley: 'Resolución IMSS',           plazo: '30 días hábiles para emitir resolución', ref: 'Art. 296 LSS' },
      { ley: 'Amparo Indirecto',          plazo: '15 días hábiles',                       ref: 'Art. 17 Ley Amparo' },
      { ley: 'Demanda ante TFJFA',        plazo: '30 días hábiles',                       ref: 'Art. 13 LFPCA' },
      { ley: 'Pensión por vejez (L.73)',   plazo: '500 semanas cotizadas mínimo, 60 años', ref: 'Art. 138 LSS 1973' },
      { ley: 'Pensión por vejez (L.97)',   plazo: '1250 semanas, 65 años',                ref: 'Art. 162 LSS 1997' },
      { ley: 'Cesantía (L.73)',            plazo: '500 semanas, 60 años',                 ref: 'Art. 137 LSS 1973' },
      { ley: 'Cesantía (L.97)',            plazo: '1250 semanas, 60 años',                ref: 'Art. 154 LSS 1997' },
    ];

    const ol = document.createElement('div');
    ol.className = 'tooltip-overlay';
    ol.innerHTML = `<div class="tooltip-box" style="max-width:680px;max-height:80vh;overflow-y:auto">
      <h3>⏱️ Plazos y Requisitos Legales IMSS</h3>
      <div style="display:flex;flex-direction:column;gap:8px;margin:14px 0">
        ${info.map(p => `
          <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 14px;display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center">
            <div style="font-size:12px;font-weight:600;color:var(--accent)">${p.ley}</div>
            <div style="font-size:12px;color:var(--text)">${p.plazo}</div>
            <div style="font-size:11px;color:var(--muted);white-space:nowrap">${p.ref}</div>
          </div>`).join('')}
      </div>
      <div style="text-align:right">
        <button class="btn btn-primary btn-sm" onclick="this.closest('.tooltip-overlay').remove()">Cerrar</button>
      </div>
    </div>`;
    ol.addEventListener('click', e => { if(e.target===ol) ol.remove(); });
    document.body.appendChild(ol);
    MAER.voz?.hablar('Mostrando plazos legales del IMSS.');
  },
};
