/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo Exportar
   Exporta chat, cartas y resultados de tareas a PDF/TXT/JSON.
   Búsqueda dentro de IndexedDB (documentos aprendidos).
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

MAER.exportar = {

  /* ══════════════════════════════════════════════
     EXPORTAR CHAT A TXT / JSON
  ══════════════════════════════════════════════ */

  chatTXT() {
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    if (!hist.length) { MAER.voz?.hablar('No hay historial para exportar.'); return; }
    const lines = hist.map(h => {
      const fecha = h.ts ? new Date(h.ts).toLocaleString('es-MX') : '';
      const resp  = (h.a || '').replace(/<[^>]+>/g, '').trim();
      return `[${fecha}]\nLeonel: ${h.q}\nMAER: ${resp}\n`;
    });
    const texto = `MAER 3.1 — Historial de Chat\nExportado: ${new Date().toLocaleString('es-MX')}\n${'─'.repeat(60)}\n\n` + lines.join('\n');
    this._descargar(texto, `maer_chat_${this._ts()}.txt`, 'text/plain');
    MAER._log(`📥 Chat exportado: ${hist.length} mensajes.`);
    MAER.voz?.hablar(`Historial exportado. ${hist.length} mensajes.`);
  },

  chatJSON() {
    const hist    = JSON.parse(localStorage.getItem('maer_history') || '[]');
    const learned = JSON.parse(localStorage.getItem('maer_learned') || '[]');
    const data = { exportado: new Date().toISOString(), version: '3.1', historial: hist, aprendizajes: learned };
    this._descargar(JSON.stringify(data, null, 2), `maer_backup_${this._ts()}.json`, 'application/json');
    MAER.voz?.hablar('Backup JSON exportado.');
  },

  /* ══════════════════════════════════════════════
     EXPORTAR CARTA A PDF (via ventana de impresión)
  ══════════════════════════════════════════════ */

  cartaPDF() {
    const texto = document.getElementById('carta-texto')?.textContent?.trim();
    if (!texto) { alert('Genera una carta primero.'); return; }

    const win = window.open('', '_blank', 'width=800,height=900');
    if (!win) { alert('Permite ventanas emergentes para exportar PDF.'); return; }

    win.document.write(`<!DOCTYPE html>
<html lang="es-MX"><head>
<meta charset="UTF-8">
<title>Carta IMSS — MAER</title>
<style>
  body { font-family: 'Times New Roman', serif; font-size: 12pt; line-height: 1.9;
         margin: 2.5cm 3cm; color: #000; }
  pre  { white-space: pre-wrap; font-family: inherit; font-size: 12pt; }
  h1   { font-size: 13pt; text-align: center; margin-bottom: 24pt; }
  footer { position: fixed; bottom: 1cm; left: 3cm; right: 3cm;
           font-size: 9pt; color: #666; text-align: center; border-top: 1px solid #ccc; padding-top: 4pt; }
  @media print {
    body { margin: 2cm 2.5cm; }
    footer { position: fixed; bottom: 0.5cm; }
  }
</style>
</head><body>
<pre>${texto.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</pre>
<footer>Generado por MAER 3.1 — ${new Date().toLocaleString('es-MX')}</footer>
<script>window.onload=()=>{window.print()}<\/script>
</body></html>`);
    win.document.close();
    MAER._log('🖨️ Carta enviada a impresión/PDF.');
    MAER.voz?.hablar('Abriendo vista de impresión. Elige "Guardar como PDF" en tu impresora.');
  },

  /* ══════════════════════════════════════════════
     EXPORTAR RESULTADO DE TAREA
  ══════════════════════════════════════════════ */

  tareaHTML() {
    const texto = MAER.tareas.resultadoActual;
    if (!texto) { alert('Ejecuta una tarea primero.'); return; }
    const tipo = document.getElementById('tarea-tipo')?.value || 'tarea';
    const desc = document.getElementById('tarea-desc')?.value?.trim()?.substring(0, 60) || 'Resultado';

    const win = window.open('', '_blank', 'width=900,height=800');
    if (!win) { alert('Permite ventanas emergentes para exportar.'); return; }

    const htmlContent = texto
      .split('\n\n').map(p => `<p>${p.replace(/\n/g,'<br>').replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/\*(.*?)\*/g,'<em>$1</em>')}</p>`).join('');

    win.document.write(`<!DOCTYPE html>
<html lang="es-MX"><head>
<meta charset="UTF-8"><title>${desc}</title>
<style>
  body{font-family:Georgia,serif;font-size:12pt;line-height:1.8;margin:2.5cm 3cm;color:#111}
  h1{font-size:14pt;color:#1a2d45;border-bottom:2px solid #38bdf8;padding-bottom:8px}
  p{margin:0 0 12pt}strong{color:#1a2d45}
  footer{position:fixed;bottom:1cm;left:3cm;right:3cm;font-size:9pt;color:#888;
    text-align:center;border-top:1px solid #ddd;padding-top:4pt}
  @media print{body{margin:2cm 2.5cm}}
</style></head><body>
<h1>${desc}</h1>
<p style="font-size:10pt;color:#666;margin-bottom:18pt">MAER 3.1 · ${new Date().toLocaleString('es-MX')} · ${tipo}</p>
${htmlContent}
<footer>Generado por MAER 3.1 — Leonel Houssen Mojica</footer>
<script>window.onload=()=>{window.print()}<\/script>
</body></html>`);
    win.document.close();
    MAER.voz?.hablar('Documento abierto para imprimir o guardar como PDF.');
  },

  tareasTXT() {
    const texto = MAER.tareas.resultadoActual;
    if (!texto) { alert('Ejecuta una tarea primero.'); return; }
    const desc = document.getElementById('tarea-desc')?.value?.trim()?.substring(0,50) || 'tarea';
    this._descargar(texto, `maer_tarea_${this._ts()}.txt`, 'text/plain');
    MAER.voz?.hablar('Resultado exportado como TXT.');
  },

  /* ══════════════════════════════════════════════
     BÚSQUEDA DENTRO DE INDEXEDDB
     (documentos aprendidos permanentes)
  ══════════════════════════════════════════════ */

  async buscarEnAprendido(consulta) {
    if (!consulta?.trim()) return [];

    // Usar el método de MAER.aprendizaje que ya tiene relevancia ponderada
    const resultados = await MAER.aprendizaje.buscarEnConocimiento(consulta);
    return resultados;
  },

  async mostrarBusquedaIDB() {
    const q = document.getElementById('idb-busq')?.value?.trim();
    if (!q) return;

    const el = document.getElementById('idb-resultados');
    if (el) el.innerHTML = '<div style="color:var(--muted);font-size:13px;padding:8px">🔍 Buscando en documentos aprendidos...</div>';

    const resultados = await this.buscarEnAprendido(q);

    if (!resultados?.length) {
      if (el) el.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:8px">Sin resultados para "<strong>${this._esc(q)}</strong>" en los documentos aprendidos.</div>`;
      return;
    }

    if (el) el.innerHTML = `
      <div style="font-size:12px;color:var(--accent);margin-bottom:10px">
        <strong>${resultados.length}</strong> documento${resultados.length>1?'s':''} relevantes para "<em>${this._esc(q)}</em>"
      </div>
      ${resultados.map(r => `
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <div style="font-size:13px;font-weight:600;color:var(--accent)">📚 ${this._esc(r.nombre || r.etiqueta || 'Documento')}</div>
            <div style="font-size:11px;color:var(--muted)">${r.relevancia || ''} coincidencias</div>
          </div>
          <div style="font-size:12px;color:var(--text);line-height:1.6">${this._esc((r.fragmento || r.texto || '').substring(0, 200))}...</div>
          <div style="margin-top:8px">
            <button class="btn btn-secondary btn-sm" onclick="MAER.exportar._usarEnChat(${JSON.stringify((r.texto||'').substring(0,2000)).replace(/'/g,"\\'")})">
              💬 Usar en chat
            </button>
          </div>
        </div>`).join('')}`;
  },

  _usarEnChat(fragmento) {
    const input = document.getElementById('chat-input');
    if (input) {
      input.value = fragmento.substring(0, 200);
      input.focus();
    }
    MAER.tabs.show('chat');
    MAER.voz?.hablar('Fragmento cargado en el chat.');
  },

  /* ══════════════════════════════════════════════
     EXPORTAR EVENTOS PENSIÓN
  ══════════════════════════════════════════════ */

  eventosTXT() {
    const eventos = JSON.parse(localStorage.getItem('maer_eventos') || '[]');
    if (!eventos.length) { alert('No hay eventos guardados.'); return; }
    const texto = `MAER 3.1 — Eventos de Pensión IMSS\nExportado: ${new Date().toLocaleString('es-MX')}\n${'─'.repeat(50)}\n\n` +
      eventos.map(e => `${e.fecha}  —  ${e.desc}`).join('\n');
    this._descargar(texto, `maer_eventos_${this._ts()}.txt`, 'text/plain');
    MAER.voz?.hablar('Eventos exportados.');
  },

  notasTXT() {
    const notas = localStorage.getItem('maer_pension_notas') || '';
    if (!notas.trim()) { alert('No hay notas guardadas.'); return; }
    this._descargar(notas, `maer_notas_pension_${this._ts()}.txt`, 'text/plain');
    MAER.voz?.hablar('Notas exportadas.');
  },

  /* ══════════════════════════════════════════════
     UTILIDADES
  ══════════════════════════════════════════════ */

  _descargar(contenido, nombre, tipo) {
    const blob = new Blob([contenido], { type: tipo });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = nombre;
    a.click();
    URL.revokeObjectURL(a.href);
  },

  _ts() {
    return new Date().toISOString().replace(/[:.]/g,'-').substring(0, 19);
  },

  _esc(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  },
};
