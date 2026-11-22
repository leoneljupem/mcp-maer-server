// 🦁 MAER — Recordatorios con fecha límite
MAER.recordatorios = {
  _lista: [],

  init() {
    this._lista = JSON.parse(localStorage.getItem('maer_recordatorios') || '[]');
    this._verificarVencidos();
  },

  render() {
    const panel = document.getElementById('recordatorios-lista');
    if (!panel) return;
    if (!this._lista.length) {
      panel.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px">Sin recordatorios.</div>';
      return;
    }
    const hoy = new Date();
    panel.innerHTML = this._lista.map((r, i) => {
      const fecha = new Date(r.fecha);
      const dias = Math.ceil((fecha - hoy) / (1000 * 60 * 60 * 24));
      const color = dias < 0 ? 'var(--red)' : dias <= 3 ? '#f59e0b' : 'var(--green)';
      return `
        <div class="card" style="margin-bottom:8px;padding:10px;border-left:3px solid ${color}">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div style="font-weight:600;font-size:13px">${r.titulo}</div>
              <div style="font-size:11px;color:var(--muted)">${r.fecha} · ${dias < 0 ? '⚠️ Vencido' : dias === 0 ? '🔴 HOY' : `${dias} días`}</div>
              ${r.notas ? `<div style="font-size:11px;color:var(--muted)">${r.notas}</div>` : ''}
            </div>
            <button class="btn btn-danger btn-sm" onclick="MAER.recordatorios._eliminar(${i})">🗑️</button>
          </div>
        </div>`;
    }).join('');
  },

  agregarDesdeUI() {
    const titulo = document.getElementById('rec-titulo')?.value?.trim();
    const fecha  = document.getElementById('rec-fecha')?.value;
    const dias   = document.getElementById('rec-dias')?.value;
    const notas  = document.getElementById('rec-notas')?.value?.trim();
    if (!titulo || !fecha) { alert('Ingresa título y fecha.'); return; }
    this._lista.push({ titulo, fecha, dias_antes: dias, notas, creado: Date.now() });
    localStorage.setItem('maer_recordatorios', JSON.stringify(this._lista));
    document.getElementById('rec-titulo').value = '';
    document.getElementById('rec-fecha').value  = '';
    document.getElementById('rec-notas').value  = '';
    this.render();
    MAER.chat._addMsg('sys', `✅ Recordatorio creado: "${titulo}" para ${fecha}`);
  },

  _eliminar(i) {
    this._lista.splice(i, 1);
    localStorage.setItem('maer_recordatorios', JSON.stringify(this._lista));
    this.render();
  },

  agregar(titulo, fecha, dias_antes, notas) {
    const r = { id: Date.now(), titulo, fecha, dias_antes, notas, creado: Date.now() };
    this._lista.push(r);
    this._guardar();
    this.render();
    return r;
  },

  listar() {
    return this._lista.slice();
  },

  _guardar() {
    localStorage.setItem('maer_recordatorios', JSON.stringify(this._lista));
  },

  get datos() { return this._lista; },
  set datos(v) { this._lista = v || []; },

  _verificarVencidos() {
    const hoy = new Date();
    this._lista.forEach(r => {
      const fecha = new Date(r.fecha);
      const dias = Math.ceil((fecha - hoy) / (1000 * 60 * 60 * 24));
      if (dias <= parseInt(r.dias_antes || 3) && dias >= 0) {
        MAER.notificaciones?.enviar(`Recordatorio: ${r.titulo}`, `Faltan ${dias} día(s) — ${r.fecha}`);
      }
    });
  }
};
