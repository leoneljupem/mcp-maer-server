/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Organizador de Documentos
   SIEMPRE copia primero — nunca mueve los originales
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.organizar = {

  propuesta: null,

  /* ── ANALIZAR CARPETA ── */
  async analizar() {
    const carpeta = document.getElementById('org-carpeta')?.value?.trim();
    if (!carpeta) {
      alert('Escribe la ruta de la carpeta que quieres organizar.');
      return;
    }

    const btn = document.getElementById('btn-org-analizar');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Analizando...'; }

    const area = document.getElementById('org-propuesta');
    if (area) area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:12px">🔍 Analizando archivos...</div>';

    try {
      const res = await MAER._call('/api/organizar-sugerir', { carpeta }, { timeout: 30000 });
      if (res.ok && res.data?.grupos) {
        this.propuesta = { carpeta, grupos: res.data.grupos, destino: res.data.destino_sugerido };
        this._renderPropuesta();
        MAER.voz.hablar(`Análisis listo. ${res.data.total || ''} archivos en ${res.data.grupos.length} categorías.`);
      } else {
        if (area) area.innerHTML = `<div class="alert alert-warning">
          ⚠️ ${res.msg || 'No se pudo analizar la carpeta. Verifica que el servidor esté activo y la ruta sea correcta.'}
        </div>`;
      }
    } catch(e) {
      if (area) area.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '🔍 Analizar Carpeta'; }
    }
  },

  /* ── RENDERIZAR PROPUESTA ── */
  _renderPropuesta() {
    const area = document.getElementById('org-propuesta');
    if (!area || !this.propuesta) return;

    const { carpeta, grupos, destino } = this.propuesta;
    const destinoSugerido = destino || (carpeta.replace(/\/?$/, '') + '_ORGANIZADO_MAER');

    let html = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <div>
            <div style="font-size:14px;font-weight:600;color:var(--accent);margin-bottom:6px">📊 Propuesta de Organización</div>
            <div style="font-size:12px;color:var(--muted)">Origen: <code>${this._escHTML(carpeta)}</code></div>
          </div>
          <div style="display:flex;flex-direction:column;gap:6px">
            <div style="font-size:11px;color:var(--muted)">Carpeta destino:</div>
            <input type="text" id="org-destino" value="${this._escHTML(destinoSugerido)}"
              style="font-size:12px;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:6px 10px;border-radius:6px;width:300px">
          </div>
        </div>

        <div style="background:rgba(250,204,21,0.08);border:1px solid rgba(250,204,21,0.3);border-radius:8px;padding:12px;margin:14px 0">
          🛡️ <strong>MAER SIEMPRE COPIA — nunca mueve los originales.</strong>
          Tu carpeta original queda intacta. La organización se crea en la carpeta destino.
        </div>
      </div>`;

    html += '<div style="display:flex;flex-direction:column;gap:10px">';
    grupos.forEach((g, gi) => {
      const icons = {
        PDFs:'📄', Imágenes:'🖼️', Documentos:'📝', Hojas:'📊',
        Código:'💻', Audio:'🎵', Video:'🎬', Comprimidos:'📦',
        JSON:'📋', Otros:'📁'
      };
      const icon = icons[g.nombre] || '📁';
      html += `
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-size:13px;font-weight:600">${icon} ${g.nombre}
              <span style="font-size:11px;color:var(--muted);font-weight:400;margin-left:6px">(${g.archivos.length} archivos)</span>
            </div>
            <div style="font-size:11px;color:var(--muted)">${g.tamaño_total || ''}</div>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:4px">
            ${g.archivos.slice(0, 8).map(f => `<span style="font-size:11px;background:var(--bg);border:1px solid var(--border);padding:2px 8px;border-radius:4px;color:var(--text)">${this._escHTML(f)}</span>`).join('')}
            ${g.archivos.length > 8 ? `<span style="font-size:11px;color:var(--muted);padding:2px 8px">+${g.archivos.length - 8} más</span>` : ''}
          </div>
        </div>`;
    });
    html += '</div>';

    html += `
      <div style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap">
        <button class="btn btn-primary" onclick="MAER.organizar.ejecutar()">
          📋 Copiar y Organizar
        </button>
        <button class="btn btn-secondary" onclick="MAER.organizar._cancelar()">
          ✕ Cancelar
        </button>
      </div>`;

    area.innerHTML = html;
  },

  /* ── EJECUTAR COPIA Y ORGANIZACIÓN ── */
  async ejecutar() {
    if (!this.propuesta) return;
    const destino = document.getElementById('org-destino')?.value?.trim();
    if (!destino) { alert('Ingresa la carpeta destino.'); return; }

    if (!confirm(`MAER copiará los archivos a:\n${destino}\n\nLos ORIGINALES quedan intactos. ¿Continuar?`)) return;

    const btn = document.querySelector('[onclick="MAER.organizar.ejecutar()"]');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Copiando...'; }

    try {
      const res = await MAER._call('/api/copy-files', {
        origen:  this.propuesta.carpeta,
        destino: destino,
        grupos:  this.propuesta.grupos,
      }, { timeout: 60000 });

      if (res.ok) {
        const area = document.getElementById('org-propuesta');
        if (area) area.innerHTML = `
          <div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.3);border-radius:10px;padding:20px;text-align:center">
            <div style="font-size:32px;margin-bottom:12px">✅</div>
            <div style="font-size:15px;font-weight:600;color:var(--green);margin-bottom:8px">Organización completada</div>
            <div style="font-size:13px;color:var(--muted)">
              ${res.data?.copiados || ''} archivos copiados en ${res.data?.carpetas || ''} carpetas.<br>
              Carpeta destino: <code>${this._escHTML(destino)}</code><br><br>
              Tus archivos originales están intactos.
            </div>
          </div>`;
        MAER.voz.hablar('Organización completada. Los archivos fueron copiados. Los originales están intactos.');
        this.propuesta = null;
      } else {
        alert(`Error al organizar: ${res.msg || 'Error desconocido'}`);
        if (btn) { btn.disabled = false; btn.textContent = '📋 Copiar y Organizar'; }
      }
    } catch(e) {
      alert(`Error: ${e.message}`);
      if (btn) { btn.disabled = false; btn.textContent = '📋 Copiar y Organizar'; }
    }
  },

  _cancelar() {
    this.propuesta = null;
    const area = document.getElementById('org-propuesta');
    if (area) area.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:12px">Ingresa una carpeta y presiona Analizar.</div>';
  },

  /* ── SELECCIONAR CARPETA ── */
  async seleccionarCarpeta() {
    try {
      const res = await MAER._call('/api/select-file', null);
      if (res.ok && res.data) {
        const ruta = typeof res.data === 'string' ? res.data.trim() : String(res.data).trim();
        // Obtener directorio del archivo
        const dir = ruta.includes('/') ? ruta.substring(0, ruta.lastIndexOf('/')) : ruta;
        const el = document.getElementById('org-carpeta');
        if (el) el.value = dir;
      }
    } catch(e) {}
  },

  _escHTML(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
