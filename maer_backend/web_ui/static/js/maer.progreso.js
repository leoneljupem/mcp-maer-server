/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Indicador de Progreso Discreto
   Pill pequeño en esquina inferior-izquierda
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.progreso = {

  _el: null,
  _timer: null,
  _countdownTimer: null,
  _remaining: 0,

  /* Tiempos estimados por acción (segundos) */
  _tiempos: {
    'upload':           2,
    'ocr-tesseract':    4,
    'ocr-easyocr':      8,
    'ocr-surya':       22,
    'ocr-doctr':       16,
    'ocr-trocr':       18,
    'ocr-kraken':      12,
    'ocr-ocrmypdf':    20,
    'ocr-rapidocr':     3,
    'ocr-manga':       18,
    'ocr-paddle':      10,
    'ocr-auto':        20,
    'ocr-avanzado':    25,
    'vision-ocr':      10,
    'vision-analizar': 12,
    'vision-classify':  8,
    'semantic-index':  60,
    'semantic-search':  5,
    'pdf-analizar':    10,
    'llm-chat':        12,
    'llm-groq':         6,
    'tablas':          15,
    'generico':         8,
  },

  /* Etiquetas cortas por acción */
  _labels: {
    'upload':           'Subiendo…',
    'ocr-tesseract':    'OCR clásico',
    'ocr-easyocr':      'OCR EasyOCR',
    'ocr-surya':        'OCR surya',
    'ocr-doctr':        'OCR docTR',
    'ocr-trocr':        'OCR TrOCR',
    'ocr-kraken':       'OCR Kraken',
    'ocr-ocrmypdf':     'OCR+PDF',
    'ocr-rapidocr':     'OCR rápido',
    'ocr-manga':        'OCR MangaOCR',
    'ocr-paddle':       'OCR PaddleOCR',
    'ocr-auto':         'OCR auto',
    'ocr-avanzado':     'OCR avanzado',
    'vision-ocr':       'Visión OCR',
    'vision-analizar':  'Visión IA',
    'vision-classify':  'Clasificando',
    'semantic-index':   'Índice semántico',
    'semantic-search':  'Búsqueda IA',
    'pdf-analizar':     'Analizando PDF',
    'llm-chat':         'MAER pensando',
    'llm-groq':         'MAER (Groq)',
    'tablas':           'Extrayendo tablas',
    'generico':         'Procesando',
  },

  _ensureEl() {
    if (this._el) return;
    this._el = document.createElement('div');
    this._el.id = 'maer-prog';
    this._el.innerHTML = `
      <span class="mp-spinner"></span>
      <span class="mp-label"></span>
      <span class="mp-time"></span>
    `;
    document.body.appendChild(this._el);
  },

  /* Mostrar indicador */
  show(accion = 'generico') {
    this._ensureEl();
    clearInterval(this._countdownTimer);
    clearTimeout(this._timer);

    const label = this._labels[accion] || accion;
    const secs  = this._tiempos[accion] || 8;
    this._remaining = secs;

    this._el.querySelector('.mp-label').textContent = label;
    this._updateTime();
    this._el.classList.add('visible');

    this._countdownTimer = setInterval(() => {
      this._remaining = Math.max(0, this._remaining - 1);
      this._updateTime();
    }, 1000);
  },

  _updateTime() {
    const t = this._el?.querySelector('.mp-time');
    if (!t) return;
    t.textContent = this._remaining > 0 ? `~${this._remaining}s` : '…';
  },

  /* Ocultar indicador */
  hide() {
    if (!this._el) return;
    clearInterval(this._countdownTimer);
    this._el.classList.remove('visible');
  },

  /* Mostrar brevemente un mensaje de éxito y ocultar */
  done(msg = '') {
    if (!this._el) return;
    clearInterval(this._countdownTimer);
    if (msg) this._el.querySelector('.mp-label').textContent = msg;
    this._el.querySelector('.mp-time').textContent = '✓';
    this._timer = setTimeout(() => this.hide(), 1200);
  },
};
