/* ══════════════════════════════════════════════════════════
   MAER 4.0 — SINAVID + PDF Export + Selenium IMSS
   Módulo para consultas SINAVID, exportar expediente PDF,
   y automatización de consulta de semanas IMSS.
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.sinavid = {

  /* ── CONSULTAR SINAVID ── */
  async consultarSinavid() {
    const curp = document.getElementById('sinavid-curp')?.value?.trim().toUpperCase() || '';
    const nss  = document.getElementById('sinavid-nss')?.value?.trim()  || '';

    if (!curp && !nss) {
      MAER.voz?.hablar('Ingresa tu CURP o NSS para consultar SINAVID.');
      return;
    }

    const area = document.getElementById('sinavid-resultado');
    if (area) area.innerHTML = '<div class="loading-pulse">🔍 Consultando SINAVID...</div>';

    const btn = document.getElementById('btn-sinavid');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Consultando...'; }

    try {
      const res = await MAER._call('/api/sinavid-consulta', { curp, nss }, { timeout: 15000 });
      if (res.ok && res.data) {
        this._renderSinavid(res.data);
      } else {
        if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ ${res.msg || 'Error en consulta SINAVID'}</div>`;
      }
    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ Servidor no disponible: ${e.message}</div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🔍 Consultar SINAVID'; }
    }
  },

  /* ── RENDERIZAR RESULTADO SINAVID ── */
  _renderSinavid(d) {
    const area = document.getElementById('sinavid-resultado');
    if (!area) return;

    const portalUrl  = d.portal_url || 'https://serviciosdigitales.imss.gob.mx/gob.mx/IMSS/vigencia_derechos';
    const pasosHTML  = (d.pasos_manuales || []).map(p =>
      `<li style="margin-bottom:6px;font-size:12.5px">${this._escHTML(p)}</li>`).join('');

    const statusColor = {
      encontrado:       'var(--success,#22c55e)',
      requiere_portal:  'var(--warning,#f59e0b)',
      pendiente:        'var(--muted)',
    }[d.status] || 'var(--muted)';

    let vigenciaHTML = '';
    if (d.vigencia !== null && d.vigencia !== undefined) {
      const vigente = Boolean(d.vigencia);
      vigenciaHTML = `
        <div style="margin:12px 0;padding:12px;border-radius:10px;background:${vigente ? 'var(--success-bg,#e8f5ee)' : 'var(--error-bg,#fff0f0)'}">
          <strong>${vigente ? '✅ Derechos VIGENTES' : '❌ Derechos NO vigentes'}</strong>
          <div style="font-size:12px;margin-top:4px;color:var(--muted)">
            ${vigente ? 'Tienes vigencia de derechos IMSS activa.' : 'No se encontró vigencia activa. Verifica en el portal.'}
          </div>
        </div>`;
    }

    area.innerHTML = `
      <div style="border:1px solid var(--border);border-radius:12px;padding:18px;background:var(--bg-card)">

        <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">
          <div style="font-size:28px">🏥</div>
          <div>
            <div style="font-weight:700;font-size:15px">SINAVID — Vigencia de Derechos IMSS</div>
            <div style="font-size:12px;color:${statusColor}">
              ${d.status === 'encontrado' ? '✅ Datos obtenidos' :
                d.status === 'requiere_portal' ? '⚠️ Requiere portal (CAPTCHA)' : '⏳ Pendiente'}
            </div>
          </div>
        </div>

        ${vigenciaHTML}

        ${d.error ? `<div style="font-size:12px;color:var(--muted);margin-bottom:10px;padding:8px;background:var(--bg-hover);border-radius:6px">
          ℹ️ ${this._escHTML(d.error)}
        </div>` : ''}

        <div style="background:var(--bg-hover);border-radius:8px;padding:14px;margin-top:10px">
          <div style="font-weight:600;font-size:13px;margin-bottom:8px">📋 Cómo consultar manualmente:</div>
          <ol style="margin:0;padding-left:18px;color:var(--text)">${pasosHTML}</ol>
        </div>

        <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
          <a href="${portalUrl}" target="_blank" rel="noopener"
             style="display:inline-block;padding:8px 16px;background:var(--accent);color:#fff;
                    border-radius:8px;text-decoration:none;font-size:13px;font-weight:600">
            🌐 Abrir Portal SINAVID
          </a>
          <button class="btn btn-secondary btn-sm"
                  onclick="MAER.sinavid._copiarDatos()"
                  style="font-size:13px">
            📋 Copiar CURP+NSS
          </button>
        </div>

        <div style="margin-top:12px;font-size:11px;color:var(--muted)">
          Consultado: ${new Date(d.timestamp || Date.now()).toLocaleString('es-MX')}
        </div>
      </div>`;

    MAER.voz?.hablar('Consulta SINAVID completada. Sigue los pasos para verificar en el portal.');
  },

  /* ── COPIAR DATOS PARA PORTAL ── */
  _copiarDatos() {
    const curp = document.getElementById('sinavid-curp')?.value?.trim() || '';
    const nss  = document.getElementById('sinavid-nss')?.value?.trim()  || '';
    const txt  = `CURP: ${curp}\nNSS: ${nss}`;
    navigator.clipboard?.writeText(txt).then(() => {
      MAER.voz?.hablar('Datos copiados al portapapeles.');
    });
  },

  /* ── EXPORTAR EXPEDIENTE PDF ── */
  async exportarPDF() {
    const area = document.getElementById('pdf-resultado');
    if (area) area.innerHTML = '<div class="loading-pulse">📄 Generando PDF...</div>';

    const btn = document.getElementById('btn-exportar-pdf');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Generando...'; }

    // Recopilar datos del expediente desde otros módulos
    const curp    = document.getElementById('sinavid-curp')?.value?.trim() ||
                    document.getElementById('curp-input')?.value?.trim() || '';
    const nss     = document.getElementById('sinavid-nss')?.value?.trim()  ||
                    document.getElementById('curp-nss-input')?.value?.trim() || '';
    const semanas = parseInt(document.getElementById('pdf-semanas')?.value || '') || null;
    const nombre  = document.getElementById('pdf-nombre')?.value?.trim() || 'Asegurado MAER';
    const ley     = document.getElementById('pdf-ley')?.value || 'Verificar';
    const notas   = document.getElementById('pdf-notas')?.value?.trim() || '';

    try {
      const res = await MAER._call('/api/exportar-pdf', {
        curp, nss, nombre, semanas, ley, notas
      }, { timeout: 30000 });

      if (res.ok && res.data) {
        const d = res.data;
        if (area) area.innerHTML = `
          <div style="padding:16px;background:var(--success-bg,#e8f5ee);border-radius:10px;border:1px solid #22c55e">
            <div style="font-weight:700;font-size:14px;margin-bottom:8px">✅ PDF generado correctamente</div>
            <div style="font-size:12.5px;margin-bottom:10px">
              📄 <strong>${this._escHTML(d.pdf_nombre)}</strong> — ${d.pdf_size_kb} KB
            </div>
            <div style="font-size:11.5px;color:var(--muted);margin-bottom:10px">
              Guardado en tu carpeta MAER. Ábrelo desde el explorador de archivos.
            </div>
            <div style="font-size:11px;word-break:break-all;color:var(--muted)">${this._escHTML(d.pdf_path)}</div>
          </div>`;
        MAER.voz?.hablar('PDF del expediente generado correctamente.');
      } else {
        if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ ${this._escHTML(res.msg || 'Error al generar PDF')}</div>`;
      }
    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ Error: ${e.message}</div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '📄 Exportar PDF'; }
    }
  },

  /* ── CONSULTA IMSS AUTOMÁTICA (SELENIUM) ── */
  async consultaSelenium() {
    const curp = document.getElementById('sinavid-curp')?.value?.trim().toUpperCase() || '';
    const nss  = document.getElementById('sinavid-nss')?.value?.trim()  || '';

    if (!curp || !nss) {
      MAER.voz?.hablar('Necesitas ingresar CURP y NSS para la consulta automática.');
      const area = document.getElementById('selenium-resultado');
      if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ Ingresa CURP y NSS completos para usar la consulta automática.</div>`;
      return;
    }

    const area = document.getElementById('selenium-resultado');
    if (area) area.innerHTML = `<div class="loading-pulse">🤖 Consultando IMSS automáticamente... (puede tardar 20-40 segundos)</div>`;

    const btn = document.getElementById('btn-selenium');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Consultando...'; }

    try {
      const res = await MAER._call('/api/imss-selenium', { curp, nss }, { timeout: 60000 });

      if (res.ok && res.data) {
        this._renderSelenium(res.data);
      } else {
        if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ ${this._escHTML(res.msg || 'Error en consulta automática')}</div>`;
      }
    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ ${e.message}</div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🤖 Consulta Automática IMSS'; }
    }
  },

  _renderSelenium(d) {
    const area = document.getElementById('selenium-resultado');
    if (!area) return;

    let html = '';

    if (d.semanas_encontradas !== null && d.semanas_encontradas !== undefined) {
      html += `
        <div style="padding:16px;background:var(--success-bg,#e8f5ee);border-radius:10px;margin-bottom:12px">
          <div style="font-size:28px;font-weight:900;color:var(--success,#16a34a)">
            ${d.semanas_encontradas} semanas
          </div>
          <div style="font-size:13px;margin-top:4px">✅ Semanas cotizadas obtenidas automáticamente del portal IMSS</div>
        </div>`;
    } else if (d.captcha_detectado) {
      html += `
        <div style="padding:14px;background:var(--warning-bg,#fff7ed);border-radius:10px;margin-bottom:12px;border:1px solid #f59e0b">
          <div style="font-weight:700;font-size:13px;margin-bottom:6px">🤖 CAPTCHA detectado</div>
          <div style="font-size:12.5px">El portal IMSS requiere que resuelvas un CAPTCHA manualmente.
          Haz clic en "Abrir Portal" e ingresa tus datos.</div>
        </div>`;
    } else {
      html += `<div class="alert alert-info">ℹ️ ${this._escHTML(d.error || 'Consulta procesada — verifica en portal')}</div>`;
    }

    if (d.screenshot_b64) {
      html += `
        <div style="margin-top:10px">
          <div style="font-size:12px;color:var(--muted);margin-bottom:6px">📸 Captura del portal:</div>
          <img src="data:image/png;base64,${d.screenshot_b64}"
               style="width:100%;border-radius:8px;border:1px solid var(--border)" />
        </div>`;
    }

    html += `
      <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
        <a href="${d.portal_url}" target="_blank" rel="noopener"
           style="display:inline-block;padding:8px 14px;background:var(--accent);color:#fff;
                  border-radius:8px;text-decoration:none;font-size:12.5px;font-weight:600">
          🌐 Abrir Portal IMSS
        </a>
      </div>`;

    area.innerHTML = html;
  },

  /* ── VERIFICAR DEPENDENCIAS ── */
  async verificarDeps() {
    const area = document.getElementById('deps-resultado');
    if (area) area.innerHTML = '<div class="loading-pulse">🔍 Verificando dependencias...</div>';

    try {
      const res = await MAER._call('/api/verificar-dependencias', null, {
        method: 'GET', timeout: 15000
      });
      if (res.ok && res.data) {
        this._renderDeps(res.data);
      }
    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-warning">⚠️ ${e.message}</div>`;
    }
  },

  _renderDeps(d) {
    const area = document.getElementById('deps-resultado');
    if (!area) return;

    const pkg = d.python_packages || {};
    const pkgRows = Object.entries(pkg).map(([k, v]) =>
      `<tr>
        <td style="padding:4px 8px;font-size:12px">${k}</td>
        <td style="padding:4px 8px;font-size:12px;color:${v ? 'var(--success,#22c55e)' : 'var(--danger,#ef4444)'}">
          ${v ? '✅' : '❌'}
        </td>
      </tr>`).join('');

    const sistemas = [
      { n: 'Tesseract OCR', ok: d.tesseract_bin,      info: d.tesseract_path },
      { n: 'Java',          ok: d.java,                info: d.java_version },
      { n: 'Conda',         ok: d.conda,               info: d.conda_path },
      { n: 'Ollama (LLM)',  ok: d.ollama,              info: d.ollama ? 'Activo en localhost:11434' : 'No activo — instala desde ollama.ai' },
      { n: 'Google Chrome', ok: d.chrome,              info: '' },
      { n: 'Poppler',       ok: d.poppler_pdftoppm,    info: d.poppler_path },
    ];

    const sysRows = sistemas.map(s => `
      <tr>
        <td style="padding:4px 8px;font-size:12px">${s.n}</td>
        <td style="padding:4px 8px;font-size:12px;color:${s.ok ? 'var(--success,#22c55e)' : 'var(--danger,#ef4444)'}">
          ${s.ok ? '✅ Instalado' : '❌ No encontrado'}
        </td>
        <td style="padding:4px 8px;font-size:11px;color:var(--muted)">${this._escHTML(s.info || '')}</td>
      </tr>`).join('');

    area.innerHTML = `
      <div style="border:1px solid var(--border);border-radius:12px;padding:16px">
        <div style="font-weight:700;font-size:14px;margin-bottom:12px">🔧 Estado del Sistema MAER</div>

        <div style="font-size:13px;font-weight:600;margin-bottom:6px">Herramientas del Sistema</div>
        <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
          <thead><tr style="background:var(--bg-hover)">
            <th style="padding:5px 8px;text-align:left;font-size:11px">Herramienta</th>
            <th style="padding:5px 8px;text-align:left;font-size:11px">Estado</th>
            <th style="padding:5px 8px;text-align:left;font-size:11px">Info</th>
          </tr></thead>
          <tbody>${sysRows}</tbody>
        </table>

        <div style="font-size:13px;font-weight:600;margin-bottom:6px">Paquetes Python</div>
        <table style="width:100%;border-collapse:collapse">
          <thead><tr style="background:var(--bg-hover)">
            <th style="padding:4px 8px;text-align:left;font-size:11px">Paquete</th>
            <th style="padding:4px 8px;text-align:left;font-size:11px">Estado</th>
          </tr></thead>
          <tbody>${pkgRows}</tbody>
        </table>

        <div style="margin-top:12px;font-size:11px;color:var(--muted)">
          Verificado: ${new Date(d.timestamp || Date.now()).toLocaleString('es-MX')}
        </div>
      </div>`;
  },

  /* ── RENDER PANEL ── */
  _renderPanel() {
    const panel = document.getElementById('panel-sinavid');
    if (!panel || panel.dataset.rendered) return;
    panel.dataset.rendered = '1';

    panel.innerHTML = `
      <div style="max-width:860px;margin:0 auto;padding:20px 16px">

        <!-- TÍTULO -->
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
          <div style="font-size:36px">🏥</div>
          <div>
            <div style="font-weight:800;font-size:20px">SINAVID & Expediente</div>
            <div style="font-size:13px;color:var(--muted)">Vigencia de derechos · Exportar PDF · Consulta automática IMSS</div>
          </div>
        </div>

        <!-- INPUTS CURP + NSS -->
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-weight:600;font-size:13px;margin-bottom:10px">📋 Tus datos de identificación</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div>
              <label style="font-size:12px;color:var(--muted)">CURP (18 caracteres)</label>
              <input id="sinavid-curp" type="text" maxlength="18" placeholder="LOOA531113HTCPBN09"
                     class="input-maer" style="text-transform:uppercase"
                     oninput="this.value=this.value.toUpperCase()" />
            </div>
            <div>
              <label style="font-size:12px;color:var(--muted)">NSS (11 dígitos)</label>
              <input id="sinavid-nss" type="text" maxlength="11" placeholder="12345678901"
                     class="input-maer" oninput="this.value=this.value.replace(/\D/g,'')" />
            </div>
          </div>
        </div>

        <!-- TABS DE FUNCIONES -->
        <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap">
          <button class="btn btn-primary" id="btn-sinavid"
                  onclick="MAER.sinavid.consultarSinavid()">🔍 Consultar SINAVID</button>
          <button class="btn btn-secondary" id="btn-selenium"
                  onclick="MAER.sinavid.consultaSelenium()">🤖 Consulta Automática IMSS</button>
          <button class="btn btn-secondary" id="btn-verificar-deps"
                  onclick="MAER.sinavid.verificarDeps()">🔧 Verificar Dependencias</button>
        </div>

        <!-- RESULTADO SINAVID -->
        <div id="sinavid-resultado" style="margin-bottom:16px"></div>

        <!-- RESULTADO SELENIUM -->
        <div id="selenium-resultado" style="margin-bottom:16px"></div>

        <!-- EXPORTAR PDF -->
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px">
          <div style="font-weight:600;font-size:14px;margin-bottom:12px">📄 Exportar Expediente a PDF</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
            <div>
              <label style="font-size:12px;color:var(--muted)">Nombre / Referencia</label>
              <input id="pdf-nombre" type="text" placeholder="Tu nombre o referencia" class="input-maer" />
            </div>
            <div>
              <label style="font-size:12px;color:var(--muted)">Semanas cotizadas</label>
              <input id="pdf-semanas" type="number" min="0" max="5000" placeholder="Ej: 1250" class="input-maer" />
            </div>
            <div>
              <label style="font-size:12px;color:var(--muted)">Ley aplicable</label>
              <select id="pdf-ley" class="input-maer">
                <option value="Verificar">Verificar con IMSS</option>
                <option value="Ley 73">Ley 73 (antes de 1997)</option>
                <option value="Ley 97">Ley 97 (después de 1997)</option>
                <option value="Ley 73 o 97 (verificar)">Transición 1997-2001</option>
              </select>
            </div>
            <div>
              <label style="font-size:12px;color:var(--muted)">Notas adicionales</label>
              <input id="pdf-notas" type="text" placeholder="Notas opcionales..." class="input-maer" />
            </div>
          </div>
          <button class="btn btn-primary" id="btn-exportar-pdf"
                  onclick="MAER.sinavid.exportarPDF()">📄 Exportar Expediente PDF</button>
          <div id="pdf-resultado" style="margin-top:12px"></div>
        </div>

        <!-- RESULTADO DEPENDENCIAS -->
        <div id="deps-resultado"></div>

        <!-- ACCESO MÓVIL / NGROK -->
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-top:16px">
          <div style="font-weight:600;font-size:14px;margin-bottom:10px">📱 Acceso desde celular (PWA)</div>
          <div style="font-size:12.5px;color:var(--muted);margin-bottom:12px">
            Para instalar MAER en tu celular o acceder desde Chrome, necesitas un túnel público.
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
            <button class="btn btn-secondary btn-sm" onclick="MAER.sinavid._verificarNgrok()">
              🌐 Verificar URL pública
            </button>
            <button id="btn-instalar-pwa" class="btn btn-primary btn-sm"
                    onclick="instalarPWA()" style="display:none">
              📲 Instalar MAER en este dispositivo
            </button>
          </div>
          <div id="ngrok-resultado" style="font-size:12px"></div>
          <div style="margin-top:10px;padding:10px;background:var(--bg-hover);border-radius:8px;font-size:12px">
            <strong>Para activar acceso móvil:</strong><br>
            Ejecuta en terminal: <code style="background:var(--bg-card);padding:2px 6px;border-radius:4px">python iniciar_maer_ngrok.py</code><br>
            Luego abre la URL que aparece en tu celular.
          </div>
        </div>

      </div>`;
  },

  /* ── VERIFICAR NGROK ── */
  async _verificarNgrok() {
    const area = document.getElementById('ngrok-resultado');
    if (area) area.innerHTML = '<div class="loading-pulse">🔍 Verificando túnel...</div>';

    try {
      const res = await MAER._call('/api/ngrok-url', null, { method: 'GET', timeout: 5000 });
      if (res.ok && res.data?.url) {
        const url = res.data.url;
        if (area) area.innerHTML = `
          <div style="padding:10px;background:var(--success-bg,#e8f5ee);border-radius:8px">
            <div style="font-weight:600;margin-bottom:6px">✅ Túnel ngrok activo</div>
            <div style="font-size:13px;margin-bottom:8px">
              <a href="${url}" target="_blank" rel="noopener" style="color:var(--accent)">${url}</a>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard?.writeText('${url}')">
              📋 Copiar URL
            </button>
          </div>`;
        // Generar QR si QR module existe
        if (MAER.qr?._generarQR) {
          MAER.qr._generarQR(url, 'ngrok-qr');
        }
      } else {
        if (area) area.innerHTML = `
          <div style="padding:10px;background:var(--bg-hover);border-radius:8px;color:var(--muted);font-size:12px">
            ⚠️ ${res.msg || 'ngrok no activo'}<br>
            Ejecuta: <code>python iniciar_maer_ngrok.py</code>
          </div>`;
      }
    } catch(e) {
      if (area) area.innerHTML = `<div style="font-size:12px;color:var(--muted)">⚠️ ${e.message}</div>`;
    }
  },

  _escHTML(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
