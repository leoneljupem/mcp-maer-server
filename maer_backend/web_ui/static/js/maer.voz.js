// 🦁 MAER — Módulo de Voz
MAER.voz = {
  _synth: window.speechSynthesis,
  _recognition: null,
  _hablando: false,
  _escuchando: false,

  init() {
    if (!('speechSynthesis' in window)) {
      MAER._log('⚠️ Voz: speechSynthesis no disponible en este navegador.');
      return;
    }
    this._cargarVoces();
    window.speechSynthesis.onvoiceschanged = () => this._cargarVoces();
    MAER._log('🔊 Módulo de voz inicializado.');
  },

  _cargarVoces() {
    const voces = this._synth.getVoices();
    const lista = document.getElementById('voces-lista');
    if (!lista) return;
    const esp = voces.filter(v => v.lang.startsWith('es'));
    lista.innerHTML = esp.length
      ? esp.map(v => `<div style="font-size:11px;padding:3px 0;color:var(--text)">${v.name} <span style="color:var(--muted)">(${v.lang})</span></div>`).join('')
      : '<div style="color:var(--muted);font-size:12px">No hay voces en español instaladas.</div>';
  },

  hablar(texto) {
    if (!MAER.config.vozActiva || !texto) return;
    this._synth.cancel();
    const utt = new SpeechSynthesisUtterance(texto);
    utt.lang  = 'es-MX';
    utt.pitch = MAER.config.vozPitch || 0.62;
    utt.rate  = MAER.config.vozRate  || 0.93;
    utt.volume= MAER.config.vozVol   || 1.0;
    const voces = this._synth.getVoices();
    const voz = voces.find(v => v.lang === 'es-MX') || voces.find(v => v.lang.startsWith('es'));
    if (voz) utt.voice = voz;
    const ind = document.getElementById('voice-indicator');
    if (ind) { ind.style.display = 'block'; this._hablando = true; }
    utt.onend = () => { if (ind) ind.style.display = 'none'; this._hablando = false; };
    this._synth.speak(utt);
  },

  toggle() {
    if (this._escuchando) this.detener();
    else this.escucharComando();
  },

  escucharComando() {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      MAER.chat._addMsg('sys', '⚠️ Reconocimiento de voz no disponible en este navegador.');
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    this._recognition = new SR();
    this._recognition.lang = 'es-MX';
    this._recognition.continuous = false;
    this._recognition.interimResults = false;
    this._recognition.onstart = () => {
      this._escuchando = true;
      const ind = document.getElementById('voice-indicator');
      if (ind) ind.style.display = 'block';
      const hdr = document.getElementById('voice-indicator-hdr');
      if (hdr) hdr.style.display = 'block';
      const btn = document.getElementById('voice-btn');
      if (btn) btn.textContent = '🔴 Escuchando...';
    };
    this._recognition.onresult = (e) => {
      const texto = e.results[0][0].transcript;
      const input = document.getElementById('chat-input');
      if (input) { input.value = texto; MAER.chat.send(); }
    };
    this._recognition.onerror = (e) => {
      MAER._log('⚠️ Error de voz: ' + e.error);
      this._escuchando = false;
    };
    this._recognition.onend = () => {
      this._escuchando = false;
      const ind = document.getElementById('voice-indicator');
      if (ind) ind.style.display = 'none';
      const hdr = document.getElementById('voice-indicator-hdr');
      if (hdr) hdr.style.display = 'none';
      const btn = document.getElementById('voice-btn');
      if (btn) btn.textContent = '🎤';
    };
    this._recognition.start();
  },

  leerSeleccion() {
    const sel = window.getSelection()?.toString().trim();
    if (sel) this.hablar(sel);
    else MAER.chat._addMsg('sys', 'Selecciona texto primero para que MAER lo lea.');
  },

  probar() {
    this.hablar('Prueba de voz MAER. Sistema funcionando correctamente.');
  },

  detener() {
    this._synth.cancel();
    if (this._recognition) this._recognition.stop();
    this._escuchando = false;
    this._hablando = false;
  }
};
