/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo de Memoria
   Historial de conversaciones, aprendizajes del usuario,
   exportación y limpieza controlada
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.memoria = {

  filtro: '',
  pagina: 0,
  POR_PAGINA: 20,

  /* ── RENDERIZAR HISTORIAL ── */
  _render() {
    const el = document.getElementById('memoria-lista');
    if (!el) return;

    const hist    = JSON.parse(localStorage.getItem('maer_history') || '[]').reverse();
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');

    // Stats rápidas
    const statEl = document.getElementById('mem-stats');
    if (statEl) {
      const hoy = new Date().toDateString();
      const hoy_count = hist.filter(h => new Date(h.ts).toDateString() === hoy).length;
      statEl.innerHTML = `
        <div class="mem-stat-card">
          <div style="font-size:22px;font-weight:700;color:var(--accent)">${hist.length}</div>
          <div style="font-size:11px;color:var(--muted)">Mensajes totales</div>
        </div>
        <div class="mem-stat-card">
          <div style="font-size:22px;font-weight:700;color:var(--green)">${hoy_count}</div>
          <div style="font-size:11px;color:var(--muted)">Mensajes hoy</div>
        </div>
        <div class="mem-stat-card">
          <div style="font-size:22px;font-weight:700;color:var(--yellow)">${learned.length}</div>
          <div style="font-size:11px;color:var(--muted)">Respuestas aprendidas</div>
        </div>`;
    }

    // Filtrar historial
    const filtrado = this.filtro
      ? hist.filter(h => (h.q + ' ' + h.a).toLowerCase().includes(this.filtro.toLowerCase()))
      : hist;

    if (!filtrado.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:14px">Sin historial todavía.</div>';
      return;
    }

    const inicio = this.pagina * this.POR_PAGINA;
    const pagina = filtrado.slice(inicio, inicio + this.POR_PAGINA);

    el.innerHTML = pagina.map((h, i) => {
      const fecha = h.ts ? new Date(h.ts).toLocaleString('es-MX') : '';
      const pregunta = (h.q || '').substring(0, 120);
      const resp = (h.a || '').replace(/<[^>]+>/g,'').substring(0, 120);
      return `<div class="mem-item">
        <div style="font-size:11px;color:var(--muted);margin-bottom:4px">${fecha}</div>
        <div class="mem-q">👤 ${this._esc(pregunta)}${h.q?.length > 120 ? '...' : ''}</div>
        <div class="mem-a">🦁 ${this._esc(resp)}${resp.length >= 120 ? '...' : ''}</div>
      </div>`;
    }).join('');

    // Paginación
    const total = Math.ceil(filtrado.length / this.POR_PAGINA);
    const pagEl = document.getElementById('mem-paginacion');
    if (pagEl && total > 1) {
      pagEl.innerHTML = `
        <button class="btn btn-secondary btn-sm" onclick="MAER.memoria.irPagina(${this.pagina - 1})" ${this.pagina === 0 ? 'disabled' : ''}>← Anterior</button>
        <span style="font-size:12px;color:var(--muted);padding:0 10px">${this.pagina + 1} / ${total}</span>
        <button class="btn btn-secondary btn-sm" onclick="MAER.memoria.irPagina(${this.pagina + 1})" ${this.pagina >= total - 1 ? 'disabled' : ''}>Siguiente →</button>`;
    } else if (pagEl) {
      pagEl.innerHTML = '';
    }
  },

  irPagina(n) {
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    const total = Math.ceil(hist.length / this.POR_PAGINA);
    this.pagina = Math.max(0, Math.min(n, total - 1));
    this._render();
  },

  /* ── FILTRAR ── */
  buscar(q) {
    this.filtro = q;
    this.pagina = 0;
    this._render();
  },

  /* ── EXPORTAR HISTORIAL ── */
  exportar() {
    const hist    = JSON.parse(localStorage.getItem('maer_history') || '[]');
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    const data = { historial: hist, aprendizajes: learned, exportado: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `maer_memoria_${Date.now()}.json`;
    a.click();
    MAER.chat._addMsg('sys', `📥 Memoria exportada: ${hist.length} mensajes, ${learned.length} aprendizajes.`);
    MAER.voz?.hablar('Memoria exportada correctamente.');
  },

  /* ── LIMPIAR HISTORIAL ── */
  limpiarHistorial() {
    if (!confirm('⚠️ ¿Borrar el historial de conversaciones? (Los aprendizajes permanentes NO se borran)')) return;
    localStorage.removeItem('maer_history');
    this.pagina = 0;
    this._render();
    MAER._updateStats();
    MAER.chat._addMsg('sys', '🗑️ Historial de conversaciones limpiado.');
    MAER.voz?.hablar('Historial limpiado.');
  },

  /* ── PANEL DE APRENDIZAJES MANUALES ── */
  _renderAprendizajes() {
    const el = document.getElementById('learned-lista');
    if (!el) return;
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    if (!learned.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:10px">Sin respuestas aprendidas manualmente.</div>';
      return;
    }
    el.innerHTML = learned.map((l, i) => `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
          <div style="flex:1">
            <div style="font-size:12px;font-weight:600;color:var(--accent)">Trigger: <code>${this._esc(l.trigger)}</code></div>
            <div style="font-size:12px;color:var(--muted);margin-top:4px">${this._esc((l.response||'').substring(0,100))}...</div>
          </div>
          <button class="btn btn-danger btn-sm" onclick="MAER.memoria._borrarAprendizaje(${i})">🗑️</button>
        </div>
      </div>`).join('');
  },

  /* ── AGREGAR APRENDIZAJE MANUAL ── */
  agregarAprendizaje() {
    const trigger  = document.getElementById('learn-trigger')?.value?.trim();
    const response = document.getElementById('learn-response')?.value?.trim();
    if (!trigger || !response) {
      alert('Completa el trigger y la respuesta.');
      return;
    }
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    learned.push({ trigger, response });
    localStorage.setItem('maer_learned', JSON.stringify(learned));
    document.getElementById('learn-trigger').value  = '';
    document.getElementById('learn-response').value = '';
    this._renderAprendizajes();
    MAER._updateStats();
    MAER.chat._addMsg('sys', `🧠 Aprendizaje guardado: cuando me preguntes "<strong>${trigger}</strong>", responderé con lo que indicaste.`);
    MAER.voz?.hablar('Aprendizaje guardado.');
  },

  _borrarAprendizaje(idx) {
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    learned.splice(idx, 1);
    localStorage.setItem('maer_learned', JSON.stringify(learned));
    this._renderAprendizajes();
    MAER._updateStats();
  },

  _esc(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
