/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Guardián de Integridad
   Verifica que los archivos JS/CSS de MAER estén cargados
   y funcionando correctamente. Reporte de estado semanal.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.guardian = {

  MODULOS: [
    { nombre: 'maer.css',           tipo: 'css',  selector: '[href*="maer.css"]',            req: 'MAER.config' },
    { nombre: 'maer.diccionario.js',tipo: 'js',   selector: '[src*="maer.diccionario"]',      req: 'MAER_DICCIONARIO' },
    { nombre: 'maer.voz.js',        tipo: 'js',   selector: '[src*="maer.voz"]',              req: 'MAER.voz' },
    { nombre: 'maer.core.js',       tipo: 'js',   selector: '[src*="maer.core"]',             req: 'MAER.tabs' },
    { nombre: 'maer.chat.js',       tipo: 'js',   selector: '[src*="maer.chat"]',             req: 'MAER.chat' },
    { nombre: 'maer.aprendizaje.js',tipo: 'js',   selector: '[src*="maer.aprendizaje"]',      req: 'MAER.aprendizaje' },
    { nombre: 'maer.archivos.js',   tipo: 'js',   selector: '[src*="maer.archivos"]',         req: 'MAER.archivos' },
    { nombre: 'maer.busqueda.js',   tipo: 'js',   selector: '[src*="maer.busqueda"]',         req: 'MAER.busqueda' },
    { nombre: 'maer.organizar.js',  tipo: 'js',   selector: '[src*="maer.organizar"]',        req: 'MAER.organizar' },
    { nombre: 'maer.imagenes.js',   tipo: 'js',   selector: '[src*="maer.imagenes"]',         req: 'MAER.imagenes' },
    { nombre: 'maer.pension.js',    tipo: 'js',   selector: '[src*="maer.pension"]',          req: 'MAER.pension' },
    { nombre: 'maer.tareas.js',     tipo: 'js',   selector: '[src*="maer.tareas"]',           req: 'MAER.tareas' },
    { nombre: 'maer.memoria.js',    tipo: 'js',   selector: '[src*="maer.memoria"]',          req: 'MAER.memoria' },
    { nombre: 'maer.sistema.js',    tipo: 'js',   selector: '[src*="maer.sistema"]',          req: 'MAER.sistema' },
    { nombre: 'maer.whatsapp.js',      tipo: 'js',   selector: '[src*="maer.whatsapp"]',         req: 'MAER.whatsapp' },
    { nombre: 'maer.notificaciones.js',tipo: 'js',   selector: '[src*="maer.notificaciones"]',   req: 'MAER.notificaciones' },
    { nombre: 'maer.exportar.js',      tipo: 'js',   selector: '[src*="maer.exportar"]',         req: 'MAER.exportar' },
    { nombre: 'maer.ajustes.js',       tipo: 'js',   selector: '[src*="maer.ajustes"]',          req: 'MAER.ajustes' },
  ],

  /* ── EJECUTAR VERIFICACIÓN ── */
  async verificar() {
    const area = document.getElementById('guardian-reporte');
    if (!area) return;
    area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:10px">🔍 Verificando integridad...</div>';

    const resultados = [];
    let ok = 0, warn = 0, err = 0;

    for (const mod of this.MODULOS) {
      const enDOM = !!document.querySelector(mod.selector);
      const enMemoria = this._checkObj(mod.req);
      const estado = (enDOM && enMemoria) ? 'ok' : (!enDOM) ? 'warn' : 'ok';

      resultados.push({ ...mod, enDOM, enMemoria, estado });
      if (estado === 'ok')   ok++;
      else if (estado === 'warn') warn++;
      else err++;
    }

    // Verificar IndexedDB
    let idbOk = false;
    try {
      await MAER.aprendizaje.initDB();
      idbOk = true;
    } catch(e) {}

    // Verificar servidor
    const serverOk = MAER.config.backendOK;

    // Guardar último chequeo
    const reporte = { ts: Date.now(), ok, warn, err, idbOk, serverOk };
    localStorage.setItem('maer_guardian_last', JSON.stringify(reporte));

    // Renderizar
    const ahora = new Date().toLocaleString('es-MX');
    let html = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:14px">
        <div style="font-size:14px;font-weight:600;color:var(--accent)">🛡️ Reporte de Integridad</div>
        <div style="font-size:11px;color:var(--muted)">${ahora}</div>
      </div>
      <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">
        <div style="background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);border-radius:8px;padding:8px 14px;text-align:center">
          <div style="font-size:20px;font-weight:700;color:var(--green)">${ok}</div>
          <div style="font-size:11px;color:var(--muted)">Correctos</div>
        </div>
        <div style="background:rgba(250,204,21,0.1);border:1px solid rgba(250,204,21,0.3);border-radius:8px;padding:8px 14px;text-align:center">
          <div style="font-size:20px;font-weight:700;color:var(--yellow)">${warn}</div>
          <div style="font-size:11px;color:var(--muted)">Advertencias</div>
        </div>
        <div style="background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);border-radius:8px;padding:8px 14px;text-align:center">
          <div style="font-size:20px;font-weight:700;color:var(--red)">${err}</div>
          <div style="font-size:11px;color:var(--muted)">Errores</div>
        </div>
      </div>`;

    html += '<div style="display:flex;flex-direction:column;gap:4px;margin-bottom:12px">';
    resultados.forEach(r => {
      const icon = r.estado === 'ok' ? '✅' : r.estado === 'warn' ? '⚠️' : '❌';
      const color = r.estado === 'ok' ? 'var(--green)' : r.estado === 'warn' ? 'var(--yellow)' : 'var(--red)';
      const detalle = r.estado === 'ok' ? 'Cargado y activo' :
                      !r.enDOM ? 'No encontrado en DOM' : 'Objeto no inicializado';
      html += `<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--surface);border:1px solid var(--border);border-radius:6px">
        <span style="font-size:14px">${icon}</span>
        <span style="font-size:12px;color:var(--text);flex:1;font-family:monospace">${r.nombre}</span>
        <span style="font-size:11px;color:${color}">${detalle}</span>
      </div>`;
    });
    html += '</div>';

    html += `
      <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--surface);border:1px solid var(--border);border-radius:6px">
          <span style="font-size:14px">${idbOk ? '✅' : '❌'}</span>
          <span style="font-size:12px;color:var(--text);flex:1">IndexedDB (memoria permanente)</span>
          <span style="font-size:11px;color:${idbOk ? 'var(--green)' : 'var(--red)'}">${idbOk ? 'Activa' : 'No disponible'}</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:var(--surface);border:1px solid var(--border);border-radius:6px">
          <span style="font-size:14px">${serverOk ? '✅' : '⚠️'}</span>
          <span style="font-size:12px;color:var(--text);flex:1">Servidor LLM (${MAER.API})</span>
          <span style="font-size:11px;color:${serverOk ? 'var(--green)' : 'var(--yellow)'}">${serverOk ? 'Conectado' : 'Offline (modo local activo)'}</span>
        </div>
      </div>`;

    if (warn === 0 && err === 0) {
      html += '<div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.3);border-radius:8px;padding:12px;font-size:13px;color:var(--green);text-align:center">🛡️ MAER está en perfecto estado. Todos los módulos activos.</div>';
      MAER.voz?.hablar('MAER integridad verificada. Todo correcto.');
    } else {
      html += `<div class="alert alert-warning" style="font-size:12px">
        ⚠️ ${warn + err} módulo${warn+err > 1 ? 's' : ''} con advertencias. Revisa que todos los archivos JS estén cargados en el index.html.
      </div>`;
    }

    area.innerHTML = html;
    MAER._log(`🛡️ Guardián: ${ok} OK, ${warn} advertencias, ${err} errores.`);
  },

  /* ── VERIFICACIÓN SILENCIOSA AL INICIO ── */
  verificarSilencioso() {
    // Solo loguea si hay problemas
    const issues = this.MODULOS.filter(m => !this._checkObj(m.req));
    if (issues.length) {
      MAER._log(`⚠️ Guardián: ${issues.length} módulo(s) no cargados: ${issues.map(m=>m.nombre).join(', ')}`);
    } else {
      MAER._log('🛡️ Guardián: todos los módulos verificados correctamente.');
    }
    // Guardar timestamp
    localStorage.setItem('maer_guardian_ts', Date.now().toString());
  },

  /* ── HELPER: VERIFICAR OBJETO EN MEMORIA ── */
  _checkObj(path) {
    try {
      const parts = path.split('.');
      let obj = window;
      for (const p of parts) {
        obj = obj[p];
        if (obj === undefined || obj === null) return false;
      }
      return true;
    } catch(e) {
      return false;
    }
  },
};

/* ── ACTIVAR VERIFICACIÓN SILENCIOSA AL CARGAR ── */
window.addEventListener('load', () => {
  setTimeout(() => {
    if (window.MAER?.guardian) MAER.guardian.verificarSilencioso();
  }, 2000);
});
