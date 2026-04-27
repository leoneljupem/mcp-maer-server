/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Diagnóstico Inteligente
   Verifica conexión, módulos, IndexedDB, dependencias.
   Muestra estado en tiempo real. Auto-diagnóstico al inicio.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.diagnostico = {

  _intervalo: null,
  _ultimoEstado: null,

  /* ── INIT ── */
  init() {
    this._renderPanel();
    // Auto-diagnóstico ligero cada 30 s
    this._intervalo = setInterval(() => this._checkConexion(), 30000);
    // Primer chequeo de conexión en 3 s (no bloquear el init)
    setTimeout(() => this._checkConexion(), 3000);
  },

  /* ── CHEQUEO RÁPIDO DE CONEXIÓN ── */
  async _checkConexion() {
    try {
      const res = await MAER._call('/api/status', null, { timeout: 5000 });
      const ok  = res.ok || res.status === 'ok';
      MAER.config.backendOK = ok;
      this._actualizarIndicador(ok);
      if (ok) MAER._log('🟢 Servidor MAER: conectado.');
    } catch(e) {
      MAER.config.backendOK = false;
      this._actualizarIndicador(false);
    }
  },

  /* ── ACTUALIZAR INDICADOR EN HEADER ── */
  _actualizarIndicador(ok) {
    // Buscar badge de estado en el DOM
    const badges = document.querySelectorAll('.server-badge, #server-status-badge');
    badges.forEach(b => {
      b.textContent = ok ? '🟢 Servidor' : '🔴 Sin conexión';
      b.style.color = ok ? 'var(--green)' : 'var(--red)';
    });
    // Actualizar sidebar si existe
    const sbStatus = document.getElementById('sb-server-status');
    if (sbStatus) sbStatus.textContent = ok ? '🟢 En línea' : '🔴 Sin conexión';
  },

  /* ── DIAGNÓSTICO COMPLETO ── */
  async ejecutar() {
    const area = document.getElementById('diag-resultado');
    if (!area) return;

    area.innerHTML = `<div style="color:var(--accent);font-size:13px;padding:12px">
      <span style="animation:pulse 1s infinite;display:inline-block">🔍</span>
      &nbsp;Ejecutando diagnóstico completo…
    </div>`;

    const checks = [];
    let ok = 0, warn = 0, err = 0;

    // ── 1. Servidor backend ──
    try {
      const r = await MAER._call('/api/status', null, { timeout: 8000 });
      const up = r.ok || r.status === 'ok';
      MAER.config.backendOK = up;
      this._actualizarIndicador(up);
      checks.push({
        icono:  up ? '✅' : '❌',
        nombre: 'Servidor MAER (FastAPI :8765)',
        estado: up ? 'ok' : 'err',
        detalle: up
          ? `Conectado · v${r.data?.version || r.version || '?'}`
          : `Sin conexión — inicia con: python server.py`,
        fix: up ? null : 'servidor'
      });
      up ? ok++ : err++;
    } catch(e) {
      checks.push({ icono:'❌', nombre:'Servidor MAER', estado:'err',
        detalle:'Sin conexión — inicia con: python server.py', fix:'servidor' });
      err++;
    }

    // ── 2. IndexedDB ──
    try {
      await MAER.aprendizaje.initDB();
      checks.push({ icono:'✅', nombre:'IndexedDB (memoria permanente)', estado:'ok', detalle:'Activa y funcionando' });
      ok++;
    } catch(e) {
      checks.push({ icono:'⚠️', nombre:'IndexedDB', estado:'warn',
        detalle:'No disponible — memoria temporal solamente', fix:'idb' });
      warn++;
    }

    // ── 3. Web Speech API ──
    const speechOk = 'speechSynthesis' in window;
    checks.push({
      icono:   speechOk ? '✅' : '⚠️',
      nombre:  'Web Speech API (voz)',
      estado:  speechOk ? 'ok' : 'warn',
      detalle: speechOk ? 'Disponible' : 'No soportado en este navegador'
    });
    speechOk ? ok++ : warn++;

    // ── 4. localStorage ──
    try {
      localStorage.setItem('_maer_diag_test', '1');
      localStorage.removeItem('_maer_diag_test');
      const histLen = JSON.parse(localStorage.getItem('maer_history') || '[]').length;
      checks.push({ icono:'✅', nombre:'localStorage', estado:'ok',
        detalle:`Disponible · ${histLen} mensajes en historial` });
      ok++;
    } catch(e) {
      checks.push({ icono:'❌', nombre:'localStorage', estado:'err',
        detalle:'No disponible — no se guardarán configuraciones', fix:'storage' });
      err++;
    }

    // ── 5. Módulos JS cargados ──
    const modulos = [
      ['MAER.chat',            'Chat IA'],
      ['MAER.archivos',        'Archivos'],
      ['MAER.busqueda',        'Búsqueda'],
      ['MAER.aprendizaje',     'Aprendizaje'],
      ['MAER.organizar',       'Organizar'],
      ['MAER.imagenes',        'Imágenes'],
      ['MAER.poder',           'Analizar (Poder Real)'],
      ['MAER.pension',         'Pensión'],
      ['MAER.tareas',          'Tareas IA'],
      ['MAER.memoria',         'Memoria'],
      ['MAER.sistema',         'Sistema'],
      ['MAER.timeline',        'Timeline'],
      ['MAER.recordatorios',   'Recordatorios'],
      ['MAER.stats',           'Stats'],
      ['MAER.diagnostico',     'Diagnóstico'],
    ];

    let modOk = 0, modErr = 0;
    const modFaltantes = [];
    modulos.forEach(([path, label]) => {
      const parts = path.split('.');
      let obj = window;
      let cargado = true;
      for (const p of parts) {
        obj = obj?.[p];
        if (obj === undefined || obj === null) { cargado = false; break; }
      }
      if (cargado) modOk++;
      else { modErr++; modFaltantes.push(label); }
    });

    checks.push({
      icono:   modErr === 0 ? '✅' : (modErr < 3 ? '⚠️' : '❌'),
      nombre:  `Módulos JS (${modOk}/${modulos.length} cargados)`,
      estado:  modErr === 0 ? 'ok' : (modErr < 3 ? 'warn' : 'err'),
      detalle: modErr === 0
        ? 'Todos los módulos activos'
        : `Faltantes: ${modFaltantes.join(', ')}`
    });
    modErr === 0 ? ok++ : (modErr < 3 ? warn++ : err++);

    // ── 6. Diccionario ──
    const dictOk = Array.isArray(window.MAER_DICCIONARIO) && MAER_DICCIONARIO.length > 50;
    checks.push({
      icono:   dictOk ? '✅' : '⚠️',
      nombre:  'Diccionario de respuestas',
      estado:  dictOk ? 'ok' : 'warn',
      detalle: dictOk ? `${MAER_DICCIONARIO.length} patrones cargados` : 'Diccionario no cargado o vacío'
    });
    dictOk ? ok++ : warn++;

    // ── 7. APIs del backend (si conectado) ──
    if (MAER.config.backendOK) {
      checks.push({
        icono:   '✅',
        nombre:  'APIs REST (endpoints activos)',
        estado:  'ok',
        detalle: 'analizar-doc, CURP, RFC, duplicados, OCR, visión, FTS, watcher y más'
      });
      ok++;
    }

    // ── 7b. Motores OCR (si conectado) ──
    if (MAER.config.backendOK) {
      try {
        const ocr = await MAER._call('/api/ocr-engines-status', null, { timeout: 10000 });
        const engines = ocr?.data?.engines || ocr?.engines || {};
        const names = Object.keys(engines);
        const activos   = names.filter(n => engines[n] && engines[n] !== 'no disponible' && engines[n] !== false && engines[n] !== null);
        const inactivos = names.filter(n => !activos.includes(n));

        const pills = activos.map(n =>
          `<span style="background:rgba(52,211,153,0.15);border:1px solid rgba(52,211,153,0.3);
           border-radius:6px;padding:1px 6px;font-size:10px;margin:1px 2px 1px 0;display:inline-block">
           ${n}</span>`
        ).join('') + inactivos.map(n =>
          `<span style="background:rgba(100,116,139,0.12);border:1px solid var(--border);
           border-radius:6px;padding:1px 6px;font-size:10px;margin:1px 2px 1px 0;display:inline-block;
           color:var(--muted)">${n}</span>`
        ).join('');

        checks.push({
          icono:   activos.length >= 8 ? '✅' : activos.length >= 4 ? '⚠️' : '❌',
          nombre:  `Motores OCR (${activos.length}/${names.length} activos)`,
          estado:  activos.length >= 8 ? 'ok' : activos.length >= 4 ? 'warn' : 'err',
          detalle: `<div style="margin-top:4px">${pills}</div>`,
          _html:   true,
        });
        activos.length >= 8 ? ok++ : activos.length >= 4 ? warn++ : err++;
      } catch(e) {
        checks.push({ icono:'⚠️', nombre:'Motores OCR', estado:'warn',
          detalle:'No se pudo obtener estado de motores' });
        warn++;
      }
    }

    // ── 7c. Índice FTS ──
    if (MAER.config.backendOK) {
      try {
        const fts = await MAER._call('/api/search-index-stats', null, { timeout: 5000 });
        const d = fts?.data || fts || {};
        const n = d.total_files || 0;
        checks.push({
          icono:   n > 0 ? '✅' : '⚠️',
          nombre:  `Índice FTS5 (${n.toLocaleString()} archivos)`,
          estado:  n > 0 ? 'ok' : 'warn',
          detalle: n > 0
            ? `${((d.total_chars||0)/1000).toFixed(0)}k caracteres indexados`
            : 'Vacío — indexa una carpeta desde la pestaña Búsqueda'
        });
        n > 0 ? ok++ : warn++;
      } catch(e) {}
    }

    // ── 8. Memoria usada ──
    let storageKb = 0;
    try {
      for (const key in localStorage) {
        if (key.startsWith('maer_')) storageKb += (localStorage[key]?.length || 0) * 2;
      }
      storageKb = Math.round(storageKb / 1024);
      const storageOk = storageKb < 4000;
      checks.push({
        icono:   storageOk ? '✅' : '⚠️',
        nombre:  'Uso de localStorage',
        estado:  storageOk ? 'ok' : 'warn',
        detalle: `${storageKb} KB usados${storageKb > 3000 ? ' — considera limpiar historial' : ''}`
      });
      storageOk ? ok++ : warn++;
    } catch(e) {}

    // ── GUARDAR ESTADO ──
    this._ultimoEstado = { ts: Date.now(), ok, warn, err, checks };
    localStorage.setItem('maer_diag_last', JSON.stringify({ ts: Date.now(), ok, warn, err }));

    // ── RENDERIZAR RESULTADO ──
    this._renderResultado(checks, ok, warn, err, area);
  },

  /* ── RENDERIZAR RESULTADO ── */
  _renderResultado(checks, ok, warn, err, area) {
    const ahora  = new Date().toLocaleString('es-MX');
    const total  = ok + warn + err;
    const salud  = err > 0 ? 'crítico' : warn > 0 ? 'advertencias' : 'óptimo';
    const salColor = err > 0 ? 'var(--red)' : warn > 0 ? 'var(--yellow)' : 'var(--green)';

    let html = `
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:14px">
        <div>
          <div style="font-size:15px;font-weight:700;color:var(--accent)">🔬 Diagnóstico Completo</div>
          <div style="font-size:11px;color:var(--muted)">${ahora}</div>
        </div>
        <div style="text-align:center;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:10px;padding:8px 16px">
          <div style="font-size:13px;font-weight:700;color:${salColor}">
            Sistema ${salud.toUpperCase()}
          </div>
          <div style="font-size:11px;color:var(--muted)">${ok}/${total} checks OK</div>
        </div>
      </div>

      <div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">
        <div style="background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);
                    border-radius:8px;padding:8px 14px;text-align:center;flex:1">
          <div style="font-size:22px;font-weight:900;color:var(--green)">${ok}</div>
          <div style="font-size:10px;color:var(--muted)">CORRECTOS</div>
        </div>
        <div style="background:rgba(250,204,21,0.1);border:1px solid rgba(250,204,21,0.3);
                    border-radius:8px;padding:8px 14px;text-align:center;flex:1">
          <div style="font-size:22px;font-weight:900;color:var(--yellow)">${warn}</div>
          <div style="font-size:10px;color:var(--muted)">ADVERTENCIAS</div>
        </div>
        <div style="background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);
                    border-radius:8px;padding:8px 14px;text-align:center;flex:1">
          <div style="font-size:22px;font-weight:900;color:var(--red)">${err}</div>
          <div style="font-size:10px;color:var(--muted)">ERRORES</div>
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:14px">`;

    checks.forEach(c => {
      const color = c.estado === 'ok' ? 'var(--green)' : c.estado === 'warn' ? 'var(--yellow)' : 'var(--red)';
      const fixBtn = c.fix ? `<button class="btn btn-secondary btn-sm" style="font-size:10px;padding:2px 8px"
        onclick="MAER.diagnostico._autoFix('${c.fix}')">🔧 Fix</button>` : '';
      const detalleStyle = c._html
        ? `style="font-size:11px;color:${color};flex-shrink:0;max-width:60%"`
        : `style="font-size:11px;color:${color};text-align:right;flex-shrink:0;max-width:55%"`;
      html += `<div style="display:flex;align-items:${c._html?'flex-start':'center'};gap:8px;padding:7px 10px;
                           background:var(--surface);border:1px solid var(--border);border-radius:6px">
        <span style="font-size:14px;flex-shrink:0">${c.icono}</span>
        <span style="font-size:12px;color:var(--text);flex:1">${c.nombre}</span>
        <span ${detalleStyle}>${c.detalle}</span>
        ${fixBtn}
      </div>`;
    });

    html += '</div>';

    // Guía de fix si hay errores
    if (err > 0 || warn > 0) {
      html += `<div style="background:rgba(250,204,21,0.06);border:1px solid rgba(250,204,21,0.25);
                           border-radius:10px;padding:12px;font-size:12px;color:var(--text);margin-bottom:12px">
        <div style="font-weight:700;color:var(--yellow);margin-bottom:8px">🛠️ Guía de corrección</div>
        ${err > 0 && !MAER.config.backendOK ? `
          <div style="margin-bottom:6px">
            <strong style="color:var(--red)">Servidor offline:</strong><br>
            Abre Terminal y ejecuta:<br>
            <code style="background:var(--border);padding:3px 6px;border-radius:4px;font-size:11px">
              cd ~/maer_backend &amp;&amp; python web_ui/server.py
            </code>
          </div>` : ''}
        ${warn > 0 ? `<div><strong style="color:var(--yellow)">Advertencias:</strong> Funcionamiento parcial — las funciones básicas siguen activas.</div>` : ''}
      </div>`;
    } else {
      html += `<div style="background:rgba(52,211,153,0.07);border:1px solid rgba(52,211,153,0.3);
                           border-radius:8px;padding:12px;font-size:13px;color:var(--green);text-align:center">
        🛡️ MAER está en estado óptimo. Todos los sistemas activos.
      </div>`;
      MAER.voz?.hablar('Diagnóstico completo. Sistema en estado óptimo.');
    }

    area.innerHTML = html;
    MAER._log(`🔬 Diagnóstico: ${ok} OK, ${warn} advertencias, ${err} errores.`);
  },

  /* ── AUTO-FIX ── */
  _autoFix(tipo) {
    const area = document.getElementById('diag-resultado');
    const msg  = {
      servidor: `Para iniciar el servidor:<br>
        <code style="font-size:11px;background:var(--border);padding:3px 8px;border-radius:4px">
          cd ~/maer_backend &amp;&amp; python web_ui/server.py
        </code><br><br>
        Después de iniciarlo, espera 5 segundos y vuelve a ejecutar el diagnóstico.`,
      idb: `IndexedDB requiere navegador moderno. Si estás en Firefox con modo privado, activa el almacenamiento.
        En Safari, ve a Configuración → Safari → Privacidad → Sin restricciones.`,
      storage: `El almacenamiento del navegador está bloqueado. Revisa la configuración de cookies/almacenamiento.`,
    }[tipo] || 'Revisa la consola del navegador para más detalles (F12 → Console).';

    // Mostrar en un toast o alert
    const toast = document.createElement('div');
    toast.style.cssText = `
      position:fixed;bottom:80px;right:20px;z-index:9999;
      background:var(--surface);border:1px solid var(--accent);border-radius:12px;
      padding:16px 20px;max-width:360px;font-size:13px;line-height:1.6;color:var(--text);
      box-shadow:0 8px 32px rgba(0,0,0,0.4);animation:slideUp .3s ease`;
    toast.innerHTML = `
      <div style="font-weight:700;color:var(--accent);margin-bottom:8px">🔧 Cómo solucionar</div>
      ${msg}
      <div style="margin-top:10px;text-align:right">
        <button class="btn btn-primary btn-sm" onclick="this.closest('div[style]').remove()">OK</button>
      </div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 15000);
  },

  /* ── RENDER DEL PANEL ── */
  _renderPanel() {
    const panel = document.getElementById('panel-diagnostico');
    if (!panel) return;

    // Solo insertar si está vacío
    if (panel.querySelector('#diag-resultado')) return;

    panel.innerHTML = `
      <div class="panel-header">
        <h2>🔬 Diagnóstico del Sistema</h2>
        <p class="text-muted" style="font-size:13px;margin-top:4px">
          Verifica servidor, módulos, IndexedDB, APIs reales y estado de todos los componentes.
        </p>
      </div>

      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px">
        <button class="btn btn-primary" onclick="MAER.diagnostico.ejecutar()" style="flex:1">
          🔬 Ejecutar Diagnóstico Completo
        </button>
        <button class="btn btn-secondary" onclick="MAER.diagnostico._checkConexion();MAER._log('🔍 Chequeo rápido ejecutado.')" style="flex:1">
          🔄 Chequeo Rápido
        </button>
      </div>

      <div id="diag-resultado" style="min-height:80px">
        <div style="color:var(--muted);font-size:13px;padding:12px;text-align:center">
          Haz clic en <strong>Ejecutar Diagnóstico</strong> para analizar el estado del sistema.
        </div>
      </div>

      <!-- Accesos directos de reparación -->
      <div style="margin-top:20px;border-top:1px solid var(--border);padding-top:16px">
        <div style="font-size:12px;color:var(--accent);font-weight:700;margin-bottom:10px">⚡ Acciones Rápidas</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <button class="btn btn-secondary btn-sm" onclick="MAER.diagnostico._limpiarHistorial()">
            🗑️ Limpiar historial chat
          </button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.diagnostico._exportarLog()">
            📋 Exportar log del sistema
          </button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.diagnostico._recargarModulos()">
            🔄 Recargar página
          </button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.diagnostico._testCURP()">
            🆔 Test CURP rápido
          </button>
          <button class="btn btn-secondary btn-sm" onclick="MAER.diagnostico._testRFC()">
            📋 Test RFC rápido
          </button>
        </div>
      </div>`;
  },

  /* ── ACCIONES RÁPIDAS ── */
  _limpiarHistorial() {
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    if (!hist.length) { alert('El historial ya está vacío.'); return; }
    if (confirm(`¿Limpiar historial de ${hist.length} mensajes? (No afecta el aprendizaje)`) ) {
      localStorage.removeItem('maer_history');
      MAER._log('🗑️ Historial del chat limpiado.');
      MAER._updateStats();
      alert('Historial limpiado correctamente.');
    }
  },

  _exportarLog() {
    const console_el = document.getElementById('sys-console');
    const log = console_el?.innerText || 'Sin log disponible.';
    const blob = new Blob([log], { type: 'text/plain' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `maer_log_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  },

  _recargarModulos() {
    if (confirm('¿Recargar la página? (Los datos guardados en localStorage se conservan.)')) {
      location.reload();
    }
  },

  async _testCURP() {
    const curpTest = 'HEGG560427MVZRRL04';
    if (!MAER.config.backendOK) {
      alert('El servidor no está conectado. Inicia el servidor para probar la API de CURP.');
      return;
    }
    const res = await MAER._call('/api/curp-decodificar', { curp: curpTest });
    if (res.ok && res.data) {
      const d = res.data;
      alert(`✅ Test CURP exitoso!\n\nCURP: ${curpTest}\nFecha: ${d.fecha_nacimiento || '?'}\nEdad: ${d.edad || '?'} años\nSexo: ${d.sexo || '?'}\nEstado: ${d.estado || '?'}`);
    } else {
      alert(`❌ Error en test CURP: ${res.msg || 'Sin respuesta del servidor'}`);
    }
  },

  async _testRFC() {
    const rfcTest = 'HEGM560427XXX';
    if (!MAER.config.backendOK) {
      alert('El servidor no está conectado. Inicia el servidor para probar la API de RFC.');
      return;
    }
    const res = await MAER._call('/api/rfc-validar', { rfc: rfcTest });
    if (res.ok && res.data) {
      const d = res.data;
      alert(`✅ Test RFC exitoso!\n\nRFC: ${rfcTest}\nVálido: ${d.valido ? 'Sí' : 'No'}\n${d.mensaje || ''}`);
    } else {
      alert(`❌ Error en test RFC: ${res.msg || 'Sin respuesta'}`);
    }
  },
};
