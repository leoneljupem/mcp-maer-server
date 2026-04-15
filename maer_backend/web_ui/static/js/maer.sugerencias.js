/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo de Sugerencias en Chat
   BLOQUE 8 — Autocompletado en tiempo real desde diccionario
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.sugerencias = {

  contenedor: null,
  input:      null,
  activas:    [],
  indice:     -1,        // índice de navegación con flechas
  MAX:        4,         // máximo sugerencias visibles
  MIN_CHARS:  2,         // mínimo caracteres para buscar

  /* ── Catálogo de sugerencias estáticas (frases comunes) ── */
  catalogo: [
    { texto: 'cuántas semanas necesito para pensionarme',  cat: 'Pensión' },
    { texto: 'qué es el recurso de inconformidad',         cat: 'Legal' },
    { texto: 'dame el teléfono de PROFEDET',               cat: 'Contacto' },
    { texto: 'cuándo me pagan el aguinaldo',               cat: 'Laboral' },
    { texto: 'qué documentos necesito para mi pensión',    cat: 'Pensión' },
    { texto: 'qué es la modalidad 10',                     cat: 'IMSS' },
    { texto: 'cómo busco mis semanas cotizadas en línea',  cat: 'IMSS' },
    { texto: 'qué es una negativa de pensión',             cat: 'Pensión' },
    { texto: 'cómo calcular mi pensión Ley 73',            cat: 'Pensión' },
    { texto: 'requisitos para pensión por cesantía',       cat: 'Pensión' },
    { texto: 'cómo presento un amparo ante el IMSS',       cat: 'Legal' },
    { texto: 'qué es el INFONAVIT y mi pensión',           cat: 'Vivienda' },
    { texto: 'cómo exportar nuestro chat',                 cat: 'Sistema' },
    { texto: 'quién eres MAER',                            cat: 'General' },
    { texto: 'qué puedes hacer',                           cat: 'General' },
    { texto: 'generar carta de inconformidad',             cat: 'Cartas' },
    { texto: 'generar carta de semanas cotizadas',         cat: 'Cartas' },
    { texto: 'mostrar timeline de mi pensión',             cat: 'Pensión' },
    { texto: 'ver mis recordatorios',                      cat: 'Recordatorios' },
    { texto: 'historial de cartas generadas',              cat: 'Cartas' },
  ],

  /* ── INIT ── */
  init() {
    this.input = document.getElementById('chat-input');
    if (!this.input) return;

    // Crear contenedor de sugerencias
    this.contenedor = document.createElement('div');
    this.contenedor.id = 'sugerencias-dropdown';
    this.contenedor.className = 'sugerencias-dropdown';
    this.contenedor.style.display = 'none';

    // Insertar justo después del input-wrap
    const wrap = this.input.closest('.chat-input-wrap');
    if (wrap && wrap.parentNode) {
      wrap.parentNode.insertBefore(this.contenedor, wrap.nextSibling);
    }

    // Listeners
    this.input.addEventListener('input', () => this._onInput());
    this.input.addEventListener('keydown', (e) => this._onKeydown(e));
    // Cerrar al hacer click fuera
    document.addEventListener('click', (e) => {
      if (!this.contenedor.contains(e.target) && e.target !== this.input) {
        this.ocultar();
      }
    });
  },

  /* ── BUSCAR sugerencias ── */
  buscar(texto) {
    if (!texto || texto.length < this.MIN_CHARS) return [];
    const norm = texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const palabras = norm.split(/\s+/).filter(p => p.length > 1);

    const resultados = [];

    // 1. Buscar en catálogo estático
    for (const item of this.catalogo) {
      const itemNorm = item.texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      const match = palabras.every(p => itemNorm.includes(p));
      if (match) {
        // Calcular score — más coincidencias de palabras = mejor
        const score = palabras.reduce((s, p) => s + (itemNorm.includes(p) ? 1 : 0), 0);
        resultados.push({ texto: item.texto, cat: item.cat, score, fuente: 'catalogo' });
      }
    }

    // 2. Buscar en diccionario (extraer label del patrón)
    if (typeof MAER_DICCIONARIO !== 'undefined') {
      for (const entry of MAER_DICCIONARIO) {
        const src = entry.p.source || '';
        // Limpiar regex chars para obtener palabras clave
        const clean = src.replace(/[\^\$\(\)\|\?\*\+\.\[\]\\{}]/g, ' ')
                        .replace(/\s+/g, ' ').trim().toLowerCase()
                        .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        if (!clean || clean.length < 3) continue;
        const match = palabras.some(p => clean.includes(p));
        if (match) {
          // Evitar duplicados del catálogo
          const ya = resultados.find(r =>
            r.texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').includes(clean.substring(0, 15))
          );
          if (!ya) {
            // Usar las primeras palabras del source como sugerencia
            const label = clean.split(' ').slice(0, 6).join(' ');
            if (label.length >= 3) {
              resultados.push({ texto: label, cat: 'Diccionario', score: 0.5, fuente: 'dict' });
            }
          }
        }
      }
    }

    // Ordenar por score descendente, limitar
    resultados.sort((a, b) => b.score - a.score);
    return resultados.slice(0, this.MAX);
  },

  /* ── MOSTRAR sugerencias ── */
  mostrar(resultados) {
    if (!this.contenedor || !resultados.length) {
      this.ocultar();
      return;
    }
    this.activas = resultados;
    this.indice = -1;

    let html = '';
    resultados.forEach((r, i) => {
      html += `<div class="sugerencia-item" data-idx="${i}" onmouseenter="MAER.sugerencias._hover(${i})" onclick="MAER.sugerencias.seleccionar(${i})">
        <span class="sugerencia-texto">${this._highlight(r.texto, this.input.value)}</span>
        <span class="sugerencia-cat">${r.cat}</span>
      </div>`;
    });

    this.contenedor.innerHTML = html;
    this.contenedor.style.display = 'block';
  },

  /* ── OCULTAR ── */
  ocultar() {
    if (this.contenedor) {
      this.contenedor.style.display = 'none';
      this.contenedor.innerHTML = '';
    }
    this.activas = [];
    this.indice = -1;
  },

  /* ── SELECCIONAR ── */
  seleccionar(idx) {
    const item = this.activas[idx];
    if (!item || !this.input) return;
    this.input.value = item.texto;
    this.ocultar();
    this.input.focus();
    // Auto-enviar
    MAER.chat?.send();
  },

  /* ── EVENTOS INTERNOS ── */
  _onInput() {
    const val = this.input.value.trim();
    if (val.length < this.MIN_CHARS) {
      this.ocultar();
      return;
    }
    const res = this.buscar(val);
    this.mostrar(res);
  },

  _onKeydown(e) {
    if (this.contenedor.style.display === 'none' || !this.activas.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.indice = Math.min(this.indice + 1, this.activas.length - 1);
      this._updateHighlight();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.indice = Math.max(this.indice - 1, -1);
      this._updateHighlight();
    } else if (e.key === 'Enter' && this.indice >= 0) {
      e.preventDefault();
      e.stopPropagation();
      this.seleccionar(this.indice);
    } else if (e.key === 'Escape') {
      this.ocultar();
    }
  },

  _hover(idx) {
    this.indice = idx;
    this._updateHighlight();
  },

  _updateHighlight() {
    const items = this.contenedor.querySelectorAll('.sugerencia-item');
    items.forEach((el, i) => {
      el.classList.toggle('sugerencia-activa', i === this.indice);
    });
  },

  /* ── Resaltar texto que coincide ── */
  _highlight(texto, query) {
    if (!query) return texto;
    const norm = query.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const palabras = norm.split(/\s+/).filter(p => p.length > 1);
    let result = texto;
    for (const p of palabras) {
      const regex = new RegExp(`(${p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      result = result.replace(regex, '<mark>$1</mark>');
    }
    return result;
  }
};
