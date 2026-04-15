/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo Stats Panel
   BLOQUE 16 — Panel de estadísticas y analíticas de uso
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.stats = {

  /* ── INIT ── */
  init() {
    MAER._log('📊 Stats Panel inicializado.');
  },

  /* ── RECOPILAR ESTADÍSTICAS ── */
  recopilar() {
    const s = {};
    const ahora = Date.now();
    const diaMs = 24 * 60 * 60 * 1000;
    const semanaMs = 7 * diaMs;

    // Chat
    try {
      const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
      s.msgTotal = hist.length;
      s.msgHoy = hist.filter(m => (ahora - (m.ts || 0)) < diaMs).length;
      s.msgSemana = hist.filter(m => (ahora - (m.ts || 0)) < semanaMs).length;

      // Mensajes por día (últimos 7 días)
      s.porDia = [];
      for (let i = 6; i >= 0; i--) {
        const inicio = ahora - (i + 1) * diaMs;
        const fin = ahora - i * diaMs;
        const count = hist.filter(m => {
          const ts = m.ts || 0;
          return ts >= inicio && ts < fin;
        }).length;
        const fecha = new Date(fin);
        s.porDia.push({
          dia: fecha.toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' }),
          count
        });
      }

      // Top temas (basado en modos usados)
      const modos = {};
      hist.forEach(m => {
        const modo = m.modo || 'general';
        modos[modo] = (modos[modo] || 0) + 1;
      });
      s.modos = Object.entries(modos).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ modo: k, count: v }));

    } catch(e) {
      s.msgTotal = 0; s.msgHoy = 0; s.msgSemana = 0; s.porDia = []; s.modos = [];
    }

    // Documentos aprendidos
    try {
      s.docsAprendidos = JSON.parse(localStorage.getItem('maer_learned') || '[]').length;
    } catch(e) { s.docsAprendidos = 0; }

    // Cartas generadas
    try {
      const cartas = MAER.cartasHistorial?.listar() || [];
      s.cartasTotal = cartas.length;
    } catch(e) { s.cartasTotal = 0; }

    // Recordatorios
    try {
      const recs = MAER.recordatorios?.listar() || [];
      s.recTotal = recs.length;
      s.recCompletados = recs.filter(r => r.completado).length;
      s.recPendientes = recs.filter(r => !r.completado).length;
    } catch(e) { s.recTotal = 0; s.recCompletados = 0; s.recPendientes = 0; }

    // Etiquetas
    try {
      const st = MAER.etiquetas?.stats() || {};
      s.etiquetasUsadas = st.totalTags || 0;
      s.docsEtiquetados = st.totalDocs || 0;
    } catch(e) { s.etiquetasUsadas = 0; s.docsEtiquetados = 0; }

    // Timeline
    try {
      const etapa = MAER.timeline?.obtenerActual();
      s.etapaActual = etapa?.label || 'Sin iniciar';
    } catch(e) { s.etapaActual = 'N/A'; }

    // Sistema
    s.modulosActivos = MAER.guardian?.MODULOS?.length || 0;
    s.diccionarioPatrones = typeof MAER_DICCIONARIO !== 'undefined' ? MAER_DICCIONARIO.length : 0;
    s.servidorOnline = MAER.config?.backendOK || false;

    return s;
  },

  /* ── RENDER PANEL ── */
  render() {
    const panel = document.getElementById('stats-panel');
    if (!panel) return;

    const s = this.recopilar();

    // Barra simple con caracteres unicode
    const barChar = (val, max) => {
      const total = 12;
      const filled = max > 0 ? Math.round((val / max) * total) : 0;
      return '█'.repeat(filled) + '░'.repeat(total - filled);
    };

    const maxDia = Math.max(...s.porDia.map(d => d.count), 1);

    let html = `
      <div style="margin-bottom:16px">
        <div style="font-size:14px;font-weight:600;color:var(--accent);margin-bottom:12px">📊 Estadísticas de Uso</div>

        <!-- Contadores principales -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:16px">
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border)">
            <div style="font-size:22px;font-weight:700;color:var(--accent)">${s.msgTotal}</div>
            <div style="font-size:11px;color:var(--muted)">Mensajes total</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border)">
            <div style="font-size:22px;font-weight:700;color:#34d399">${s.msgHoy}</div>
            <div style="font-size:11px;color:var(--muted)">Hoy</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border)">
            <div style="font-size:22px;font-weight:700;color:#fbbf24">${s.docsAprendidos}</div>
            <div style="font-size:11px;color:var(--muted)">Docs aprendidos</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border)">
            <div style="font-size:22px;font-weight:700;color:#fb923c">${s.cartasTotal}</div>
            <div style="font-size:11px;color:var(--muted)">Cartas generadas</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border)">
            <div style="font-size:22px;font-weight:700;color:#a78bfa">${s.recPendientes}</div>
            <div style="font-size:11px;color:var(--muted)">Rec. pendientes</div>
          </div>
          <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center;border:1px solid var(--border)">
            <div style="font-size:22px;font-weight:700;color:#38bdf8">${s.etiquetasUsadas}</div>
            <div style="font-size:11px;color:var(--muted)">Etiquetas usadas</div>
          </div>
        </div>

        <!-- Gráfica semanal -->
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:16px">
          <div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:10px">📈 Actividad semanal (mensajes)</div>
          <div style="display:flex;flex-direction:column;gap:4px;font-family:monospace;font-size:11px">
            ${s.porDia.map(d => `
              <div style="display:flex;align-items:center;gap:8px">
                <span style="width:60px;color:var(--muted);text-align:right">${d.dia}</span>
                <span style="color:var(--accent)">${barChar(d.count, maxDia)}</span>
                <span style="color:var(--text);min-width:20px">${d.count}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Modos más usados -->
        ${s.modos.length > 0 ? `
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:16px">
          <div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:10px">🎯 Modos más usados</div>
          <div style="display:flex;flex-direction:column;gap:4px">
            ${s.modos.slice(0, 5).map(m => {
              const pct = s.msgTotal > 0 ? Math.round(m.count / s.msgTotal * 100) : 0;
              const icons = { general: '🤖', pension: '🏛️', legal: '⚖️', doc: '📄' };
              return `<div style="display:flex;align-items:center;gap:8px;padding:4px 0">
                <span style="font-size:14px">${icons[m.modo] || '📋'}</span>
                <span style="font-size:12px;color:var(--text);flex:1;text-transform:capitalize">${m.modo}</span>
                <span style="font-size:11px;color:var(--muted)">${m.count} (${pct}%)</span>
              </div>`;
            }).join('')}
          </div>
        </div>` : ''}

        <!-- Info del sistema -->
        <div style="font-size:12px;color:var(--text);line-height:1.8">
          🏛️ <strong>Etapa pensión:</strong> ${s.etapaActual} ·
          🛡️ <strong>${s.modulosActivos}</strong> módulos activos ·
          📖 <strong>${s.diccionarioPatrones}</strong> patrones diccionario ·
          🔌 ${s.servidorOnline ? '<span style="color:#34d399">Online</span>' : '<span style="color:#f87171">Offline</span>'}
        </div>
      </div>`;

    panel.innerHTML = html;
  },

  /* ── DATOS PARA TESTS ── */
  datos() {
    return this.recopilar();
  }
};
