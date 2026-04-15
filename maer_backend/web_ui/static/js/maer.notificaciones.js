/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo de Notificaciones
   Web Notifications API: alertas de eventos de pensión,
   mensajes Tasker, recordatorios programados.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.notificaciones = {

  permiso:     'default',   // 'default' | 'granted' | 'denied'
  _checkTimer: null,
  _taskerTimer: null,
  INTERVALO_EVENTOS_MS:  60  * 1000,   // revisar eventos cada 1 min
  INTERVALO_TASKER_MS:   30  * 1000,   // revisar Tasker cada 30 s

  /* ── INICIALIZAR ── */
  async init() {
    if (!('Notification' in window)) {
      MAER._log('⚠️ Notificaciones no disponibles en este navegador.');
      return;
    }
    this.permiso = Notification.permission;

    // Si ya hay permiso, arrancar los watchers
    if (this.permiso === 'granted') {
      this._iniciarWatchers();
    }
    MAER._log(`🔔 Notificaciones: permiso = ${this.permiso}`);
  },

  /* ── SOLICITAR PERMISO ── */
  async solicitarPermiso() {
    if (!('Notification' in window)) {
      alert('Tu navegador no soporta notificaciones nativas.');
      return false;
    }
    try {
      const resultado = await Notification.requestPermission();
      this.permiso = resultado;
      this._actualizarUI();

      if (resultado === 'granted') {
        this._iniciarWatchers();
        this.enviar('🦁 MAER', 'Notificaciones activadas. Leonel, te mantendré al tanto.', '🔔');
        MAER.voz?.hablar('Notificaciones activadas.');
        MAER._log('✅ Permiso de notificaciones concedido.');
        return true;
      } else {
        MAER._log('❌ Permiso de notificaciones denegado.');
        return false;
      }
    } catch(e) {
      MAER._log(`Error solicitando permiso: ${e.message}`);
      return false;
    }
  },

  /* ── ENVIAR NOTIFICACIÓN ── */
  enviar(titulo, cuerpo, icono = '🦁', tag = '') {
    if (this.permiso !== 'granted') return;
    try {
      const n = new Notification(titulo, {
        body: cuerpo,
        icon: icono,
        tag:  tag || `maer-${Date.now()}`,
        badge: '🦁',
        lang: 'es-MX',
      });
      n.onclick = () => { window.focus(); n.close(); };
      setTimeout(() => n.close(), 8000);
    } catch(e) {
      MAER._log(`Error enviando notificación: ${e.message}`);
    }
  },

  /* ── INICIAR WATCHERS ── */
  _iniciarWatchers() {
    // Watcher de eventos de pensión
    if (this._checkTimer) clearInterval(this._checkTimer);
    this._checkTimer = setInterval(() => this._checkEventosPension(), this.INTERVALO_EVENTOS_MS);
    this._checkEventosPension(); // check inmediato

    // Watcher de mensajes Tasker (solo si backend activo)
    if (MAER.config.backendOK) {
      if (this._taskerTimer) clearInterval(this._taskerTimer);
      this._taskerTimer = setInterval(() => this._checkTaskerMensajes(), this.INTERVALO_TASKER_MS);
    }
  },

  /* ── DETENER WATCHERS ── */
  detener() {
    if (this._checkTimer)  { clearInterval(this._checkTimer);  this._checkTimer  = null; }
    if (this._taskerTimer) { clearInterval(this._taskerTimer); this._taskerTimer = null; }
  },

  /* ── REVISAR EVENTOS DE PENSIÓN ── */
  _checkEventosPension() {
    const eventos = JSON.parse(localStorage.getItem('maer_eventos') || '[]');
    if (!eventos.length) return;

    const hoy      = new Date();
    const hoyStr   = hoy.toISOString().split('T')[0];
    const mananaStr = new Date(hoy.getTime() + 86400000).toISOString().split('T')[0];

    eventos.forEach(ev => {
      const tag = `pension-${ev.fecha}-${ev.ts || 0}`;
      const yaNotificado = localStorage.getItem(`maer_notif_${tag}`);
      if (yaNotificado) return;

      if (ev.fecha === hoyStr) {
        this.enviar(
          '🏛️ Evento IMSS — HOY',
          ev.desc,
          '🔔',
          tag
        );
        MAER.voz?.hablar(`Recordatorio: hoy tienes un evento importante. ${ev.desc}`);
        localStorage.setItem(`maer_notif_${tag}`, '1');
        MAER._log(`🔔 Notificación evento HOY: ${ev.desc}`);
      } else if (ev.fecha === mananaStr) {
        this.enviar(
          '🏛️ Evento IMSS — Mañana',
          `⏰ ${ev.desc}`,
          '📅',
          tag + '-manana'
        );
        localStorage.setItem(`maer_notif_${tag}-manana`, '1');
        MAER._log(`🔔 Notificación evento MAÑANA: ${ev.desc}`);
      }
    });
  },

  /* ── REVISAR MENSAJES TASKER ── */
  async _checkTaskerMensajes() {
    if (!MAER.config.backendOK) return;
    try {
      const res = await MAER._call('/api/tasker-messages', null, { timeout: 5000 });
      if (!res.ok || !res.data?.mensajes?.length) return;

      const noLeidos = res.data.mensajes.filter(m => !m.leido);
      noLeidos.slice(-3).forEach(m => {
        this.enviar(
          `📱 Tasker — ${m.fuente || 'Android'}`,
          m.mensaje?.substring(0, 100) || '',
          '📱',
          `tasker-${m.id || Date.now()}`
        );
        MAER._log(`📱 Tasker recibido: ${m.mensaje?.substring(0,50)}`);
      });

      // Actualizar el indicador visual del header
      const badge = document.getElementById('tasker-badge');
      if (badge) {
        badge.textContent = noLeidos.length || '';
        badge.style.display = noLeidos.length ? 'inline-block' : 'none';
      }
    } catch(e) {}
  },

  /* ── ACTUALIZAR UI ── */
  _actualizarUI() {
    const btn  = document.getElementById('btn-notif-permiso');
    const stat = document.getElementById('notif-estado');
    if (btn) {
      btn.textContent = this.permiso === 'granted' ? '🔔 Notificaciones activas'
                      : this.permiso === 'denied'  ? '🔕 Permiso denegado (ver ajustes del navegador)'
                                                   : '🔔 Activar notificaciones';
      btn.disabled = this.permiso === 'denied';
      btn.className = this.permiso === 'granted'
        ? 'btn btn-secondary btn-sm'
        : 'btn btn-primary btn-sm';
    }
    if (stat) {
      stat.textContent = this.permiso === 'granted' ? '✅ Activas'
                       : this.permiso === 'denied'  ? '❌ Denegadas'
                                                    : '⚠️ Sin configurar';
      stat.style.color = this.permiso === 'granted' ? 'var(--green)'
                       : this.permiso === 'denied'  ? 'var(--red)'
                                                    : 'var(--yellow)';
    }
  },

  /* ── PRUEBA MANUAL ── */
  probar() {
    if (this.permiso !== 'granted') {
      this.solicitarPermiso();
      return;
    }
    this.enviar(
      '🦁 MAER — Prueba',
      'Las notificaciones funcionan correctamente. Leonel, estoy vigilando.',
      '🦁'
    );
    MAER.voz?.hablar('Notificación de prueba enviada.');
  },
};

/* ── Inicializar al cargar ── */
window.addEventListener('load', () => {
  setTimeout(() => {
    if (window.MAER?.notificaciones) MAER.notificaciones.init();
  }, 1500);
});
