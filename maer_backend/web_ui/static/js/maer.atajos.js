/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo de Atajos de Teclado
   BLOQUE 12 — Hotkeys globales para navegación rápida
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.atajos = {

  mapa: {},
  activo: true,
  panelVisible: false,

  /* ── INIT ── */
  init() {
    // Registrar atajos por defecto
    this._registrarDefaults();

    // Listener global
    document.addEventListener('keydown', (e) => this._handler(e));
  },

  /* ── REGISTRAR ATAJO ── */
  registrar(combo, descripcion, accion) {
    const key = this._normalizar(combo);
    this.mapa[key] = { combo, descripcion, accion };
    return true;
  },

  /* ── LISTAR ATAJOS ── */
  listar() {
    return Object.values(this.mapa).map(a => ({
      combo: a.combo,
      descripcion: a.descripcion
    }));
  },

  /* ── HANDLER GLOBAL ── */
  _handler(e) {
    if (!this.activo) return;

    // No interceptar si estamos escribiendo en un input/textarea
    const tag = e.target.tagName.toLowerCase();
    const enInput = (tag === 'input' || tag === 'textarea' || tag === 'select');

    // Construir combo actual
    const partes = [];
    if (e.ctrlKey || e.metaKey) partes.push('ctrl');
    if (e.altKey)   partes.push('alt');
    if (e.shiftKey) partes.push('shift');
    const tecla = (e.key || '').toLowerCase();
    if (!['control','alt','shift','meta'].includes(tecla)) {
      partes.push(tecla);
    }
    const combo = partes.join('+');

    // Buscar en mapa
    const atajo = this.mapa[combo];
    if (atajo) {
      // Permitir Escape siempre, otros solo si no estamos en input
      if (combo !== 'escape' && enInput && !combo.includes('ctrl') && !combo.includes('alt')) return;
      e.preventDefault();
      e.stopPropagation();
      try {
        atajo.accion();
      } catch(err) {
        console.warn('[MAER] Error en atajo', combo, err.message);
      }
    }
  },

  /* ── NORMALIZAR COMBO ── */
  _normalizar(combo) {
    return combo.toLowerCase()
      .replace(/\s/g, '')
      .split('+')
      .sort((a, b) => {
        const orden = { ctrl: 0, alt: 1, shift: 2 };
        return (orden[a] ?? 3) - (orden[b] ?? 3);
      })
      .join('+');
  },

  /* ── DEFAULTS ── */
  _registrarDefaults() {
    // Navegación entre pestañas: Alt + número
    const tabs = ['chat','archivos','imagenes','busqueda','organizar','aprendizaje',
                  'pension','tareas','memoria','sistema','whatsapp','ajustes'];
    tabs.forEach((tab, i) => {
      if (i < 9) {
        this.registrar(`alt+${i+1}`, `Ir a pestaña ${tab}`, () => MAER.tabs?.show(tab));
      }
    });
    this.registrar('alt+0', 'Ir a pestaña ajustes', () => MAER.tabs?.show('ajustes'));

    // Atajos funcionales
    this.registrar('ctrl+enter', 'Enviar mensaje', () => MAER.chat?.send());
    this.registrar('escape', 'Cerrar panel / sugerencias', () => {
      MAER.sugerencias?.ocultar();
      if (this.panelVisible) this.ocultarAyuda();
    });
    this.registrar('ctrl+k', 'Enfocar chat', () => {
      const input = document.getElementById('chat-input');
      if (input) { input.focus(); input.select(); }
    });
    this.registrar('ctrl+shift+g', 'Ejecutar Guardián', () => MAER.guardian?.verificar());
    this.registrar('ctrl+shift+e', 'Exportar chat', () => MAER.exportar?.chatTXT());
    this.registrar('ctrl+shift+v', 'Probar voz', () => MAER.voz?.probar());
    this.registrar('shift+?', 'Mostrar atajos de teclado', () => this.toggleAyuda());
  },

  /* ── PANEL DE AYUDA ── */
  toggleAyuda() {
    if (this.panelVisible) this.ocultarAyuda();
    else this.mostrarAyuda();
  },

  mostrarAyuda() {
    let panel = document.getElementById('atajos-panel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'atajos-panel';
      panel.className = 'atajos-overlay';
      document.body.appendChild(panel);
    }

    const grupos = {};
    for (const a of Object.values(this.mapa)) {
      // Agrupar por tipo
      let grupo = 'General';
      if (a.combo.startsWith('alt+')) grupo = 'Navegación';
      else if (a.combo.includes('ctrl+shift')) grupo = 'Acciones';
      else if (a.combo.includes('ctrl+')) grupo = 'Edición';
      if (!grupos[grupo]) grupos[grupo] = [];
      grupos[grupo].push(a);
    }

    let html = `
      <div class="atajos-modal">
        <div class="atajos-header">
          <span>⌨️ Atajos de Teclado</span>
          <button class="btn btn-secondary btn-sm" onclick="MAER.atajos.ocultarAyuda()">✕</button>
        </div>
        <div class="atajos-body">`;

    for (const [grupo, atajos] of Object.entries(grupos)) {
      html += `<div class="atajos-grupo-titulo">${grupo}</div>`;
      for (const a of atajos) {
        const teclas = a.combo.split('+').map(t =>
          `<kbd>${t.charAt(0).toUpperCase() + t.slice(1)}</kbd>`
        ).join(' + ');
        html += `<div class="atajos-fila">
          <span class="atajos-desc">${a.descripcion}</span>
          <span class="atajos-combo">${teclas}</span>
        </div>`;
      }
    }

    html += '</div></div>';
    panel.innerHTML = html;
    panel.style.display = 'flex';
    this.panelVisible = true;
  },

  ocultarAyuda() {
    const panel = document.getElementById('atajos-panel');
    if (panel) panel.style.display = 'none';
    this.panelVisible = false;
  }
};
