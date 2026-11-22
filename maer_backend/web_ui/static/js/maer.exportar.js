// 🦁 MAER — Módulo de Exportación
MAER.exportar = {
  chatTXT() {
    const msgs = document.querySelectorAll('#chat-msgs .msg');
    const texto = Array.from(msgs).map(m => m.textContent).join('\n');
    this._descargar(texto, 'maer_chat.txt', 'text/plain');
  },

  chatJSON() {
    const hist = JSON.parse(localStorage.getItem('maer_history') || '[]');
    this._descargar(JSON.stringify(hist, null, 2), 'maer_chat_backup.json', 'application/json');
  },

  eventosTXT() {
    const eventos = JSON.parse(localStorage.getItem('maer_eventos') || '[]');
    const texto = eventos.map(e => `${e.fecha} — ${e.desc}`).join('\n');
    this._descargar(texto, 'maer_eventos.txt', 'text/plain');
  },

  notasTXT() {
    const notas = document.getElementById('pension-notas')?.value || '';
    this._descargar(notas, 'maer_notas.txt', 'text/plain');
  },

  cartaPDF() {
    window.print();
  },

  mostrarBusquedaIDB() {
    const query = document.getElementById('idb-busq')?.value?.trim();
    if (!query) return;
    const docs = JSON.parse(localStorage.getItem('maer_learned_docs') || '[]');
    const q = query.toLowerCase();
    const resultados = docs.filter(d => d.texto?.toLowerCase().includes(q));
    const panel = document.getElementById('idb-resultados');
    if (!panel) return;
    if (!resultados.length) { panel.innerHTML = '<div style="color:var(--muted);font-size:13px">Sin resultados en documentos aprendidos.</div>'; return; }
    panel.innerHTML = resultados.map(d => {
      const idx = d.texto?.toLowerCase().indexOf(q) || 0;
      const fragmento = d.texto?.slice(Math.max(0, idx-50), idx+100) || '';
      return `<div class="card" style="margin-bottom:8px;padding:10px"><strong>${d.label}</strong><br><span style="font-size:12px;color:var(--muted)">...${fragmento}...</span></div>`;
    }).join('');
  },

  _descargar(contenido, nombre, tipo) {
    const blob = new Blob([contenido], { type: tipo });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = nombre; a.click();
  }
};
