// 🦁 MAER — Timeline del proceso de pensión (Bloque 7)
MAER.timeline = {
  STORAGE_KEY: 'maer_timeline',

  _etapas: [
    { id: 1, clave: 'documentos', titulo: '📋 Recopilación de documentos', desc: 'NSS, CURP, Acta, INE, Semanas IMSS' },
    { id: 2, clave: 'pre-revision', titulo: '🔍 Verificación IMSS', desc: 'Semanas cotizadas certificadas en subdelegación' },
    { id: 3, clave: 'solicitud', titulo: '📝 Solicitud formal', desc: 'Presentar formato PM-07 o RMA-07 en IMSS' },
    { id: 4, clave: 'revision', titulo: '📌 Seguimiento del trámite', desc: 'Revisión documental y acuses en subdelegación' },
    { id: 5, clave: 'resolucion', titulo: '⏳ Resolución IMSS', desc: 'Espera resolución (30-60 días hábiles)' },
    { id: 6, clave: 'recurso', titulo: '📑 Dictamen y notificación', desc: 'Notificación oficial del dictamen de pensión' },
    { id: 7, clave: 'amparo', titulo: '🏦 Registro de CLABE', desc: 'Alta de CLABE interbancaria a tu nombre' },
    { id: 8, clave: 'otorgada', titulo: '✅ Pago de pensión', desc: 'Depósito a CLABE interbancaria registrada' },
  ],

  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY)
      ?? localStorage.getItem('maer_timeline_step');
    this._paso = saved ? parseInt(saved, 10) || 0 : 0;
  },

  render() {
    const panel = document.getElementById('timeline-panel');
    if (!panel) return;
    panel.innerHTML = this._etapas.map((e, i) => `
      <div data-etapa="${e.clave}" class="timeline-etapa"
           style="display:flex;gap:12px;align-items:flex-start;margin-bottom:12px;padding:10px;border-radius:8px;background:${i < this._paso ? 'rgba(0,112,60,0.15)' : i === this._paso ? 'rgba(56,189,248,0.1)' : 'var(--surface)'}">
        <div class="timeline-icon" style="width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0;background:${i < this._paso ? '#00703c' : i === this._paso ? 'var(--accent)' : 'var(--border)'}; color:${i <= this._paso ? '#fff' : 'var(--muted)'}">${i < this._paso ? '✓' : i + 1}</div>
        <div style="flex:1">
          <div class="timeline-label" style="font-weight:600;font-size:13px;margin-bottom:2px">${e.titulo}</div>
          <div class="timeline-info" style="font-size:11px;color:var(--muted)">${e.desc}</div>
        </div>
        ${i === this._paso ? `<button class="btn btn-primary btn-sm" onclick="MAER.timeline._avanzar()">Completar →</button>` : ''}
      </div>`).join('');
  },

  get etapas() {
    return this._etapas;
  },

  obtenerActual() {
    return this._etapas[this._paso] || null;
  },

  marcar(paso) {
    const n = Math.max(0, Math.min(parseInt(paso, 10) || 0, this._etapas.length));
    this._paso = n;
    localStorage.setItem(this.STORAGE_KEY, n);
    this.render();
    return this.obtenerActual();
  },

  _avanzar() {
    if (this._paso < this._etapas.length) {
      this._paso++;
      localStorage.setItem(this.STORAGE_KEY, this._paso);
      this.render();
      if (this._paso === this._etapas.length) {
        MAER.chat._addMsg('maer', '🎉 ¡Felicitaciones! Has completado todas las etapas del proceso de pensión.');
      }
    }
  }
};
