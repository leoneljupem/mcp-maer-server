// 🦁 MAER — Recordatorios con fecha límite (Bloque 9)
MAER.recordatorios = {
  _lista: [],

  init() {
    this._lista = JSON.parse(localStorage.getItem('maer_recordatorios') || '[]');
    this.verificar();
  },

  diasRestantes(r) {
    if (!r || !r.fecha) return 0;
    const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
    const fecha = new Date(r.fecha); fecha.setHours(0, 0, 0, 0);
    return Math.round((fecha - hoy) / 86400000);
  },

  _colorUrgencia(dias) {
    if (dias <= 0) return '#dc2626';
    if (dias <= 3) return '#f59e0b';
    return '#22c55e';
  },

  verificar() {
    let urgentes = 0;
    this._lista.forEach(r => {
      const dias = this.diasRestantes(r);
      const umbral = parseInt(r.dias_antes || 3, 10);
      if (!r.completado && dias >= 0 && dias <= umbral) {
        urgentes++;
        MAER.notificaciones?.enviar?.(`Recordatorio: ${r.titulo}`, `Faltan ${dias} día(s) — ${r.fecha}`);
      }
    });
    this._actualizarBadge(urgentes);
    return urgentes;
  },

  _actualizarBadge(n) {
    let badge = document.getElementById('rec-badge');
    if (!badge && n > 0) {
      const tab = document.querySelector('[data-tab="pension"]') || document.getElementById('tab-pension');
      if (!tab) return;
      badge = document.createElement('span');
      badge.id = 'rec-badge';
      badge.className = 'rec-badge';
      tab.appendChild(badge);
    }
    if (badge) {
      badge.textContent = n > 0 ? String(n) : '';
      badge.style.display = n > 0 ? 'inline-flex' : 'none';
    }
  },

  render() {
    const panel = document.getElementById('recordatorios-lista');
    if (!panel) return;
    if (!this._lista.length) {
      panel.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px">Sin recordatorios.</div>';
      this._actualizarBadge(0);
      return;
    }
    panel.innerHTML = this._lista.map((r, i) => {
      const dias = this.diasRestantes(r);
      const color = r.completado ? '#22c55e' : this._colorUrgencia(dias);
      const estado = r.completado ? '✅ Completado'
        : dias < 0 ? '⚠️ Vencido' : dias === 0 ? '🔴 HOY' : `${dias} día(s)`;
      return `
        <div class="card" style="margin-bottom:8px;padding:10px;border-left:3px solid ${color}">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
            <div>
              <div style="font-weight:600;font-size:13px">${this._escapar(r.titulo)}</div>
              <div style="font-size:11px;color:var(--muted)">${this._escapar(r.fecha)} · ${estado}</div>
              ${r.notas ? `<div style="font-size:11px;color:var(--muted)">${this._escapar(r.notas)}</div>` : ''}
            </div>
            <div style="display:flex;gap:6px">
              ${r.completado ? '' : `<button class="btn btn-secondary btn-sm" title="Completar" onclick="MAER.recordatorios.completar(${i})">✔️</button>`}
              <button class="btn btn-danger btn-sm" title="Eliminar" onclick="MAER.recordatorios.eliminar(${i})">🗑️</button>
            </div>
          </div>
        </div>`;
    }).join('');
    this.verificar();
  },

  _escapar(t) {
    return String(t ?? '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  },

  agregarDesdeUI() {
    const titulo = document.getElementById('rec-titulo')?.value?.trim();
    const fecha = document.getElementById('rec-fecha')?.value;
    const dias = document.getElementById('rec-dias')?.value;
    const notas = document.getElementById('rec-notas')?.value?.trim();
    if (!titulo || !fecha) { alert('Ingresa título y fecha.'); return; }
    const r = this.agregar(titulo, fecha, dias, notas);
    ['rec-titulo', 'rec-fecha', 'rec-notas'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    MAER.chat._addMsg('sys', `✅ Recordatorio creado: "${this._escapar(r.titulo)}" para ${this._escapar(r.fecha)}`);
  },

  agregar(titulo, fecha, dias_antes, notas) {
    const r = {
      id: Date.now(), titulo, fecha,
      dias_antes: dias_antes ?? 3, notas: notas || '',
      creado: Date.now(), completado: false
    };
    this._lista.push(r);
    this._guardar();
    this.render();
    return r;
  },

  listar() {
    return this._lista.slice();
  },

  eliminar(i) {
    const indice = typeof i === 'number' ? i : this._lista.findIndex(r => r.id === i);
    if (indice < 0 || indice >= this._lista.length) return false;
    this._lista.splice(indice, 1);
    this._guardar();
    this.render();
    return true;
  },

  completar(i) {
    const indice = typeof i === 'number' ? i : this._lista.findIndex(r => r.id === i);
    const r = this._lista[indice];
    if (!r) return false;
    r.completado = true;
    this._guardar();
    this.render();
    MAER.voz?.hablar(`Recordatorio completado: ${r.titulo}.`);
    return true;
  },

  _guardar() {
    localStorage.setItem('maer_recordatorios', JSON.stringify(this._lista));
  },

  get datos() { return this._lista; },
  set datos(v) { this._lista = v || []; },

  _eliminar(i) { return this.eliminar(i); },
  _verificarVencidos() { return this.verificar(); }
};
