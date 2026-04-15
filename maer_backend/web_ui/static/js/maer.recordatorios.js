/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Recordatorios con Fecha Límite
   BLOQUE 9 — Alertas automáticas para eventos de pensión
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.recordatorios = {

  STORAGE_KEY: 'maer_recordatorios',
  datos: [],

  /* ── INICIALIZAR ── */
  init() {
    this.datos = this._cargar();
    this.verificar();
  },

  /* ── AGREGAR RECORDATORIO ── */
  agregar(titulo, fechaLimite, diasAntes = 3, notas = '') {
    const fechaObj = new Date(fechaLimite);
    if (isNaN(fechaObj.getTime())) return false;

    const fechaAviso = new Date(fechaObj);
    fechaAviso.setDate(fechaAviso.getDate() - diasAntes);

    const recordatorio = {
      id: Date.now(),
      titulo,
      fechaLimite: fechaObj.toISOString(),
      diasAntes,
      fechaAviso: fechaAviso.toISOString(),
      notas,
      notificado: false,
      creadoEn: new Date().toISOString()
    };

    this.datos.push(recordatorio);
    this._guardar();
    this.render();
    MAER.voz?.hablar(`Recordatorio guardado. Te avisaré ${diasAntes} días antes.`);
    return recordatorio;
  },

  /* ── VERIFICAR RECORDATORIOS VENCIDOS ── */
  verificar() {
    const ahora = new Date();
    let alertas = 0;

    this.datos.forEach(r => {
      if (r.notificado) return;
      const fechaAviso = new Date(r.fechaAviso);
      const fechaLimite = new Date(r.fechaLimite);

      if (ahora >= fechaAviso) {
        const diasRestantes = Math.ceil((fechaLimite - ahora) / 86400000);
        let msg;

        if (diasRestantes > 0) {
          msg = `⏰ <strong>Recordatorio:</strong> "${r.titulo}" vence en <strong>${diasRestantes} día${diasRestantes !== 1 ? 's' : ''}</strong>.`;
        } else if (diasRestantes === 0) {
          msg = `🔴 <strong>¡HOY!</strong> "${r.titulo}" vence <strong>hoy</strong>.`;
        } else {
          msg = `🔴 <strong>¡VENCIDO!</strong> "${r.titulo}" venció hace <strong>${Math.abs(diasRestantes)} día${Math.abs(diasRestantes) !== 1 ? 's' : ''}</strong>.`;
        }
        if (r.notas) msg += `<br><em>${r.notas}</em>`;

        MAER.chat?._addMsg('sys', msg, false);

        if (MAER.notificaciones?.enviar) {
          MAER.notificaciones.enviar(r.titulo, diasRestantes > 0 ? `Vence en ${diasRestantes} días` : 'VENCIDO');
        }

        r.notificado = true;
        alertas++;
      }
    });

    if (alertas > 0) {
      this._guardar();
      MAER.voz?.hablar(`Tienes ${alertas} recordatorio${alertas > 1 ? 's' : ''} pendiente${alertas > 1 ? 's' : ''}.`);
      this._actualizarBadge();
    }
    return alertas;
  },

  /* ── LISTAR ── */
  listar() {
    return [...this.datos].sort((a, b) => new Date(a.fechaLimite) - new Date(b.fechaLimite));
  },

  /* ── ELIMINAR ── */
  eliminar(id) {
    this.datos = this.datos.filter(r => r.id !== id);
    this._guardar();
    this.render();
    MAER.voz?.hablar('Recordatorio eliminado.');
  },

  /* ── COMPLETAR ── */
  completar(id) {
    const r = this.datos.find(x => x.id === id);
    if (r) { r.notificado = true; this._guardar(); this.render(); }
  },

  /* ── RENDER ── */
  render() {
    const contenedor = document.getElementById('recordatorios-lista');
    if (!contenedor) return;

    const lista = this.listar();
    if (lista.length === 0) {
      contenedor.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:20px">No hay recordatorios. Agrega uno arriba.</p>';
      return;
    }

    const ahora = new Date();
    let html = '';

    lista.forEach(r => {
      const fechaLimite = new Date(r.fechaLimite);
      const diasRestantes = Math.ceil((fechaLimite - ahora) / 86400000);
      const fechaStr = fechaLimite.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });

      let estadoColor, estadoTexto, estadoIcon;
      if (diasRestantes < 0) {
        estadoColor = '#dc2626'; estadoTexto = `Vencido hace ${Math.abs(diasRestantes)}d`; estadoIcon = '🔴';
      } else if (diasRestantes === 0) {
        estadoColor = '#dc2626'; estadoTexto = '¡HOY!'; estadoIcon = '🔴';
      } else if (diasRestantes <= r.diasAntes) {
        estadoColor = '#f59e0b'; estadoTexto = `${diasRestantes}d restantes`; estadoIcon = '⚠️';
      } else {
        estadoColor = '#22c55e'; estadoTexto = `${diasRestantes}d restantes`; estadoIcon = '🟢';
      }

      html += `
        <div class="card" style="margin-bottom:8px;border-left:3px solid ${estadoColor}">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <div>
              <strong>${estadoIcon} ${r.titulo}</strong>
              <div style="font-size:0.8em;color:var(--text-secondary);margin-top:4px">📅 ${fechaStr} · Aviso: ${r.diasAntes}d antes</div>
              <div style="font-size:0.85em;font-weight:600;color:${estadoColor};margin-top:4px">${estadoTexto}</div>
              ${r.notas ? `<div style="font-size:0.8em;font-style:italic;margin-top:4px">${r.notas}</div>` : ''}
            </div>
            <div style="display:flex;gap:4px">
              ${!r.notificado ? `<button class="btn btn-secondary btn-sm" onclick="MAER.recordatorios.completar(${r.id})" title="Completado">✔️</button>` : ''}
              <button class="btn btn-secondary btn-sm" onclick="MAER.recordatorios.eliminar(${r.id})" title="Eliminar">🗑️</button>
            </div>
          </div>
        </div>`;
    });

    contenedor.innerHTML = html;
    this._actualizarBadge();
  },

  /* ── AGREGAR DESDE UI ── */
  agregarDesdeUI() {
    const titulo = document.getElementById('rec-titulo')?.value?.trim();
    const fecha = document.getElementById('rec-fecha')?.value;
    const dias = parseInt(document.getElementById('rec-dias')?.value || '3');
    const notas = document.getElementById('rec-notas')?.value?.trim() || '';

    if (!titulo || !fecha) {
      MAER.voz?.hablar('Escribe un título y selecciona la fecha.');
      return;
    }

    this.agregar(titulo, fecha, dias, notas);
    document.getElementById('rec-titulo').value = '';
    document.getElementById('rec-notas').value = '';
  },

  /* ── BADGE ── */
  _actualizarBadge() {
    const ahora = new Date();
    const urgentes = this.datos.filter(r => {
      if (r.notificado) return false;
      return Math.ceil((new Date(r.fechaLimite) - ahora) / 86400000) <= (r.diasAntes || 3);
    }).length;

    const tabPension = document.querySelector('[onclick*="pension"]');
    if (tabPension) {
      const badgeExist = tabPension.querySelector('.rec-badge');
      if (badgeExist) badgeExist.remove();
      if (urgentes > 0) {
        const badge = document.createElement('span');
        badge.className = 'rec-badge';
        badge.style.cssText = 'background:#dc2626;color:white;font-size:10px;padding:1px 5px;border-radius:10px;margin-left:4px;';
        badge.textContent = urgentes;
        tabPension.appendChild(badge);
      }
    }
  },

  /* ── PERSISTENCIA ── */
  _cargar() {
    try { return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || []; } catch(e) { return []; }
  },
  _guardar() {
    try { localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.datos)); } catch(e) {}
  }
};
