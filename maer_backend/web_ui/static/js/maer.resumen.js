/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Módulo Resumen Semanal
   BLOQUE 13 — Resumen automático al inicio de semana
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.resumen = {

  STORAGE_KEY: 'maer_resumen_semana',

  /* ── INIT ── */
  init() {
    if (this._debeGenerar()) {
      setTimeout(() => this.generar(), 3000);
    }
  },

  /* ── GENERAR RESUMEN ── */
  generar() {
    const datos = this._recopilar();
    const html = this._formatear(datos);
    MAER.chat?._addMsg('sys', html);
    this._marcarGenerado();
    MAER._log('📊 Resumen semanal generado.');
    return datos;
  },

  /* ── RECOPILAR DATOS ── */
  _recopilar() {
    const d = {};
    const semanaMs = 7 * 24 * 60 * 60 * 1000;

    // Chat
    try {
      const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
      d.mensajesTotal = hist.length;
      d.mensajesSemana = hist.filter(m => {
        const ts = m.ts || m.timestamp;
        return ts && (Date.now() - new Date(ts).getTime()) < semanaMs;
      }).length;
    } catch(e) { d.mensajesTotal = 0; d.mensajesSemana = 0; }

    // Documentos aprendidos
    try {
      d.docsAprendidos = JSON.parse(localStorage.getItem('maer_learned') || '[]').length;
    } catch(e) { d.docsAprendidos = 0; }

    // Timeline
    try {
      const etapa = MAER.timeline?.obtenerActual();
      d.etapaActual = etapa?.label || 'Sin iniciar';
    } catch(e) { d.etapaActual = 'N/A'; }

    // Recordatorios
    try {
      const recs = MAER.recordatorios?.listar() || [];
      d.recPendientes = recs.filter(r => !r.completado).length;
      d.recVencidos = recs.filter(r => !r.completado && new Date(r.fechaLimite) <= new Date()).length;
    } catch(e) { d.recPendientes = 0; d.recVencidos = 0; }

    // Cartas
    try {
      const cartas = MAER.cartasHistorial?.listar() || [];
      d.cartasTotal = cartas.length;
      d.cartasSemana = cartas.filter(c => c.fecha && (Date.now() - new Date(c.fecha).getTime()) < semanaMs).length;
    } catch(e) { d.cartasTotal = 0; d.cartasSemana = 0; }

    // Etiquetas
    try {
      const st = MAER.etiquetas?.stats() || {};
      d.docsEtiquetados = st.totalDocs || 0;
    } catch(e) { d.docsEtiquetados = 0; }

    // Sistema
    d.patronesDiccionario = typeof MAER_DICCIONARIO !== 'undefined' ? MAER_DICCIONARIO.length : 0;
    d.modulosActivos = MAER.guardian?.MODULOS?.length || 0;
    d.servidorOnline = MAER.config.backendOK;
    d.fecha = new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

    return d;
  },

  /* ── FORMATEAR HTML ── */
  _formatear(d) {
    return `<div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin:8px 0">
      <div style="font-size:15px;font-weight:600;color:var(--accent);margin-bottom:12px">📊 Resumen Semanal — ${d.fecha}</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:12px">
        <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--accent)">${d.mensajesSemana}</div>
          <div style="font-size:11px;color:var(--muted)">Mensajes semana</div>
        </div>
        <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:#34d399">${d.docsAprendidos}</div>
          <div style="font-size:11px;color:var(--muted)">Docs aprendidos</div>
        </div>
        <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:#fbbf24">${d.recPendientes}</div>
          <div style="font-size:11px;color:var(--muted)">Recordatorios</div>
        </div>
        <div style="background:var(--bg);border-radius:8px;padding:10px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:#fb923c">${d.cartasSemana}</div>
          <div style="font-size:11px;color:var(--muted)">Cartas semana</div>
        </div>
      </div>
      <div style="font-size:12px;color:var(--text);line-height:1.8">
        🏛️ <strong>Etapa pensión:</strong> ${d.etapaActual} · 📝 Cartas totales: ${d.cartasTotal} · 🏷️ Etiquetados: ${d.docsEtiquetados}<br>
        📖 Diccionario: ${d.patronesDiccionario} patrones · 🛡️ ${d.modulosActivos} módulos · 🔌 ${d.servidorOnline ? '🟢 En línea' : '🔴 Sin conexión'}
      </div>
      ${d.recVencidos > 0 ? `<div style="margin-top:10px;padding:8px;background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);border-radius:8px;font-size:12px;color:#f87171">⚠️ <strong>${d.recVencidos}</strong> recordatorio(s) vencido(s)</div>` : ''}
    </div>`;
  },

  /* ── ¿DEBE GENERAR? ── */
  _debeGenerar() {
    try {
      const ultimo = localStorage.getItem(this.STORAGE_KEY);
      if (!ultimo) return true;
      const fecha = new Date(parseInt(ultimo));
      const ahora = new Date();
      const getWeek = (d) => {
        const s = new Date(d.getFullYear(), 0, 1);
        return Math.ceil(((d - s) / 86400000 + s.getDay() + 1) / 7);
      };
      return getWeek(ahora) !== getWeek(fecha) || ahora.getFullYear() !== fecha.getFullYear();
    } catch(e) { return true; }
  },

  _marcarGenerado() {
    localStorage.setItem(this.STORAGE_KEY, Date.now().toString());
  },

  /* ── FORZAR (testing/manual) ── */
  forzar() { return this.generar(); }
};
