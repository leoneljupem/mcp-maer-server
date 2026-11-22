// 🦁 MAER — Sugerencias contextuales en el chat (Bloque 8)
MAER.sugerencias = {
  MIN_CHARS: 2,
  MAX: 6,

  _sugerencias: [
    { texto: '¿Quieres calcular tu pensión con la Ley 73?', cat: 'Pensión' },
    { texto: '¿Tienes tu constancia de semanas cotizadas?', cat: 'Semanas' },
    { texto: 'Puedo analizar documentos IMSS que me compartas.', cat: 'IMSS' },
    { texto: '¿Necesitas generar una carta de solicitud al IMSS?', cat: 'Cartas' },
    { texto: 'Puedo buscar CURPs y NSS en tus archivos.', cat: 'Búsqueda' },
    { texto: '¿Ya revisaste tus semanas cotizadas en el IMSS?', cat: 'Semanas' },
    { texto: 'Puedo calcular tu pensión con la Ley 97 y tu Afore.', cat: 'Pensión' },
    { texto: '¿Necesitas un recurso de inconformidad por semanas faltantes?', cat: 'Recurso' },
    { texto: '¿Quieres que redacte una carta de inconformidad al IMSS?', cat: 'Cartas' },
    { texto: 'Puedo revisar tu resolución de pensión y detectar errores.', cat: 'Revisión' },
    { texto: '¿Te ayudo con el trámite de crédito INFONAVIT?', cat: 'Derechos' },
    { texto: '¿Necesitas citar el teléfono de PROFEDET?', cat: 'Derechos' },
    { texto: 'Puedo explicarte cuándo pagan el aguinaldo y la prima vacacional.', cat: 'Derechos' },
    { texto: '¿Quieres exportar tu conversación o tus eventos a TXT?', cat: 'Exportar' },
    { texto: 'Puedo revisar tu expediente y detectar documentos faltantes.', cat: 'Documentos' },
    { texto: '¿Necesitas una carta poder para tu trámite?', cat: 'Cartas' },
    { texto: '¿Quieres consultar tu vigencia de derechos del IMSS?', cat: 'IMSS' },
    { texto: 'Puedo verificar si tu NSS aparece en varios documentos.', cat: 'Semanas' },
  ],

  _indice: -1,
  _activas: [],
  _dropdown: null,
  _inicializado: false,

  init() {
    const input = document.getElementById('chat-input');
    if (!input || this._inicializado) return;
    this._inicializado = true;

    this._dropdown = document.createElement('div');
    this._dropdown.id = 'sugerencias-dropdown';
    this._dropdown.className = 'sugerencias-dropdown';
    this._dropdown.setAttribute('role', 'listbox');
    this._dropdown.style.display = 'none';
    const wrap = input.closest('.chat-input-wrap');
    (wrap?.parentElement || document.body).appendChild(this._dropdown);

    input.addEventListener('input', () => this.mostrar(input.value));
    input.addEventListener('focus', () => {
      if ((input.value || '').trim().length >= this.MIN_CHARS) this.mostrar(input.value);
    });
    input.addEventListener('blur', () => window.setTimeout(() => this.ocultar(), 180));

    // Captura: se ejecuta antes del onkeydown inline del input (Enter → MAER.chat.send()).
    input.addEventListener('keydown', (e) => this._onTecla(e), true);
  },

  _normalizar(t) {
    return String(t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  },

  _escapar(t) {
    return String(t).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  },

  get catalogo() {
    return this._sugerencias.map(s => ({ texto: s.texto, cat: s.cat }));
  },

  buscar(contexto) {
    const consulta = this._normalizar(contexto).trim();
    if (consulta.length < this.MIN_CHARS) return [];
    const tokens = consulta.split(/\s+/).filter(Boolean);
    const exactas = this.catalogo.filter(s =>
      tokens.every(t => this._normalizar(s.texto).includes(t)));
    if (exactas.length) return exactas.slice(0, this.MAX);
    return this.catalogo.filter(s =>
      tokens.some(t => this._normalizar(s.texto).includes(t))).slice(0, this.MAX);
  },

  mostrar(contexto) {
    this._activas = this.buscar(contexto);
    this._indice = this._activas.length ? 0 : -1;
    if (!this._activas.length) {
      this.ocultar();
      return [];
    }

    const seguro = this._escapar(String(contexto || '').trim());
    const resaltar = (texto) => {
      const esc = this._escapar(texto);
      const partes = seguro.split(/\s+/).filter(p => p.length >= 2);
      if (!partes.length) return esc;
      const patron = partes
        .map(p => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        .join('|');
      return esc.replace(new RegExp(`(${patron})`, 'ig'), '<mark>$1</mark>');
    };

    this._dropdown.innerHTML = this._activas.map((s, i) => `
      <div class="sugerencia-item${i === this._indice ? ' sugerencia-activa' : ''}"
           role="option" data-i="${i}" onmousedown="MAER.sugerencias.seleccionar(${i})">
        <span class="sugerencia-texto">${resaltar(s.texto)}</span>
        <span class="sugerencia-cat">${this._escapar(s.cat)}</span>
      </div>`).join('');
    this._dropdown.style.display = 'block';
    return this._activas.map(s => s.texto);
  },

  ocultar() {
    if (this._dropdown) {
      this._dropdown.style.display = 'none';
      this._dropdown.innerHTML = '';
    }
    this._indice = -1;
  },

  seleccionar(i) {
    const pos = typeof i === 'number' ? i : this._indice;
    const item = this._activas[pos];
    if (!item) return false;
    const input = document.getElementById('chat-input');
    if (input) input.value = item.texto;
    this.ocultar();
    MAER.chat.send();
    return true;
  },

  _onTecla(e) {
    if (!this._activas.length || this._dropdown?.style.display === 'none') return;
    const manejar = () => { e.preventDefault(); e.stopImmediatePropagation(); };
    switch (e.key) {
      case 'ArrowDown':
        manejar();
        this._indice = (this._indice + 1) % this._activas.length;
        this._marcar();
        break;
      case 'ArrowUp':
        manejar();
        this._indice = (this._indice - 1 + this._activas.length) % this._activas.length;
        this._marcar();
        break;
      case 'Enter':
        manejar();
        this.seleccionar(this._indice);
        break;
      case 'Escape':
        manejar();
        this.ocultar();
        break;
      default:
        break;
    }
  },

  _marcar() {
    if (!this._dropdown) return;
    [...this._dropdown.querySelectorAll('.sugerencia-item')].forEach((el, i) => {
      el.classList.toggle('sugerencia-activa', i === this._indice);
    });
    this._dropdown.querySelector('.sugerencia-activa')?.scrollIntoView({ block: 'nearest' });
  }
};
