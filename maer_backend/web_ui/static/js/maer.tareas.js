// 🦁 MAER — Módulo de Tareas IA
MAER.tareas = {
  _archivo: null,

  adjuntarArchivo(file) {
    if (!file) return;
    this._archivo = file;
    const el = document.getElementById('tarea-archivo-nombre');
    if (el) el.textContent = file.name;
  },

  quitarAdjunto() {
    this._archivo = null;
    const el = document.getElementById('tarea-archivo-nombre');
    if (el) el.textContent = 'Sin archivo adjunto';
  },

  async ejecutar() {
    const tipo = document.getElementById('tarea-tipo')?.value;
    const desc = document.getElementById('tarea-desc')?.value?.trim();
    if (!desc) { alert('Describe la tarea primero.'); return; }
    const btn = document.getElementById('btn-tarea');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Ejecutando...'; }
    const resultado = document.getElementById('tarea-resultado');
    if (resultado) { resultado.style.display = 'block'; resultado.innerHTML = '<div style="color:var(--muted)">⏳ MAER está trabajando en tu tarea...</div>'; }

    let contexto = '';
    if (this._archivo) {
      const fd = new FormData(); fd.append('file', this._archivo);
      const r = await MAER._upload('/api/learn-file', fd);
      if (r.ok) contexto = r.data.text?.slice(0, 2000) || '';
    }
    const ctx_aprendido = MAER.aprendizaje?.getContexto(desc) || '';
    const prompt = `Tarea: ${tipo}

Descripción: ${desc}${contexto ? '\n\nDocumento adjunto:\n' + contexto : ''}${ctx_aprendido ? '\n\nContexto conocido:\n' + ctx_aprendido : ''}`;
    const r = await MAER._call('/api/llm-chat', { message: prompt, mode: tipo });

    if (btn) { btn.disabled = false; btn.textContent = '⚡ Ejecutar Tarea'; }
    const respuesta = r.ok ? (r.data?.response || r.data?.text || r.msg) : r.msg;
    if (resultado) {
      resultado.innerHTML = `
        <div class="card-title" style="margin-bottom:8px">✅ Resultado</div>
        <div style="white-space:pre-wrap;font-size:13px;line-height:1.7">${respuesta}</div>
        <div style="margin-top:10px;display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText(this.closest('.card') ? this.closest('.card').querySelector('div[style*=pre-wrap]').textContent : '')">📋 Copiar</button>
        </div>`;
      resultado.style.display = 'block';
    }
    MAER._saveToHistory(desc, respuesta);
  }
};
