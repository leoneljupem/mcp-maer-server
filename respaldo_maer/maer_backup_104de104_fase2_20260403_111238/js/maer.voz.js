/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Módulo de Voz Grave y Segura
   Voz masculina, grave, que transmite autoridad
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

// Guard: si MAER no existe aún, crearlo vacío (core.js lo completará después)
if (typeof MAER === 'undefined') { window.MAER = { config: {} }; }

MAER.voz = {

  recognition: null,
  listening:   false,
  synth:       window.speechSynthesis || null,
  vocesListas: false,
  vocesCargadas: [],

  /* ── INICIALIZAR ── */
  init() {
    if (!this.synth) return;
    // Cargar voces (pueden tardar en cargarse)
    const cargar = () => {
      this.vocesCargadas = this.synth.getVoices();
      this.vocesListas = this.vocesCargadas.length > 0;
    };
    cargar();
    this.synth.onvoiceschanged = cargar;
    // Chrome 71+: marcar activación tras primer gesto del usuario
    const _activar = () => {
      this.userActivated = true;
      document.removeEventListener('click', _activar);
      document.removeEventListener('keydown', _activar);
    };
    document.addEventListener('click', _activar, { once: true });
    document.addEventListener('keydown', _activar, { once: true });
    // Log voces disponibles en System
    setTimeout(() => {
      const esp = this.vocesCargadas.filter(v => v.lang.startsWith('es'));
      MAER._log(`🔊 Voces en español disponibles: ${esp.map(v=>v.name).join(', ') || 'Ninguna detectada'}`);
    }, 1500);
  },

  /* ── SELECCIONAR LA MEJOR VOZ GRAVE MASCULINA ── */
  _elegirVoz() {
    if (!this.vocesListas) {
      this.vocesCargadas = this.synth.getVoices();
    }
    const voces = this.vocesCargadas;

    // 1. Voces masculinas mexicanas conocidas (macOS / Chrome)
    const preferidas = ['Eddy', 'Diego', 'Jorge', 'Reed', 'Rocko', 'Sandy', 'Grandpa'];
    for (const nombre of preferidas) {
      const v = voces.find(v => v.name.includes(nombre) && v.lang.startsWith('es'));
      if (v) return v;
    }
    // 2. Cualquier voz masculina en español
    const masculinas = voces.filter(v =>
      v.lang.startsWith('es') &&
      (v.name.toLowerCase().includes('male') ||
       v.name.toLowerCase().includes('hombre') ||
       v.name.includes('Jorge') ||
       v.name.includes('Eddy') ||
       v.name.includes('Diego'))
    );
    if (masculinas.length) return masculinas[0];
    // 3. Cualquier voz en español
    const espanola = voces.find(v => v.lang === 'es-MX') ||
                     voces.find(v => v.lang.startsWith('es'));
    if (espanola) return espanola;
    // 4. Fallback
    return null;
  },

  userActivated: false,

  /* ── HABLAR ── */
  hablar(texto, opciones = {}) {
    if (!MAER.config.vozActiva || !this.synth) return;
    // Chrome 71+: no hablar si el usuario no ha interactuado aún
    // Doble verificación: flag interno + API nativa del navegador
    const nativeActive = navigator.userActivation?.hasBeenActive;
    if (!this.userActivated && !nativeActive) return;
    // Limpiar HTML tags
    const textoLimpio = texto.replace(/<[^>]+>/g, '').replace(/&[a-z]+;/g, ' ').trim();
    if (!textoLimpio) return;
    // Máximo 400 caracteres para no cortar el flujo
    const textoFinal = textoLimpio.substring(0, 400) + (textoLimpio.length > 400 ? '...' : '');

    this.synth.cancel();

    const utt = new SpeechSynthesisUtterance(textoFinal);
    utt.lang   = 'es-MX';
    utt.pitch  = parseFloat(opciones.pitch  || MAER.config.vozPitch  || 0.62);  // Grave
    utt.rate   = parseFloat(opciones.rate   || MAER.config.vozRate   || 0.93);  // Pausado, con peso
    utt.volume = parseFloat(opciones.volume || MAER.config.vozVol    || 1.0);

    const vozElegida = this._elegirVoz();
    if (vozElegida) utt.voice = vozElegida;

    // Indicador visual de que MAER está hablando
    const ind = document.getElementById('voice-indicator');
    if (ind) {
      ind.classList.add('active');
      utt.onend   = () => ind.classList.remove('active');
      utt.onerror = () => ind.classList.remove('active');
    }

    try {
      this.synth.speak(utt);
    } catch(e) {
      // Chrome puede bloquear speak() si no detecta gesto real — silenciar
      console.warn('[MAER] speechSynthesis bloqueado:', e.message);
    }
  },

  /* ── PROBAR VOZ ── */
  probar() {
    this.hablar('MAER activo. Voz grave y segura. Leonel, estoy contigo. Listo para trabajar.', { pitch: 0.62, rate: 0.9 });
  },

  /* ── ANUNCIO DE ALERTA ── */
  alerta(texto) {
    this.hablar(texto, { pitch: 0.55, rate: 0.88, volume: 1.0 });
  },

  /* ── RECONOCIMIENTO DE VOZ ── */
  toggle() {
    if (this.listening) this.detener();
    else this.escuchar();
  },

  escuchar() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert('Reconocimiento de voz no disponible. Usa Chrome o Edge para esta función.');
      return;
    }
    this.recognition = new SR();
    this.recognition.lang = 'es-MX';
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.maxAlternatives = 1;

    this.recognition.onresult = (e) => {
      const texto = e.results[0][0].transcript;
      const input = document.getElementById('chat-input');
      if (input) {
        input.value = texto;
        // Auto-enviar si el texto es completo (tiene punto final o es largo)
        if (texto.length > 3) MAER.chat.send();
      }
    };

    this.recognition.onerror = (e) => {
      console.warn('Error de voz:', e.error);
      this.detener();
      if (e.error === 'not-allowed') {
        alert('Permiso de micrófono denegado. Habilita el micrófono en la configuración del navegador.');
      }
    };

    this.recognition.onend = () => this.detener();

    try {
      this.recognition.start();
      this.listening = true;
      const btn = document.getElementById('voice-btn');
      if (btn) { btn.classList.add('listening'); btn.textContent = '🔴'; }
    } catch(e) {
      console.error('Error al iniciar reconocimiento:', e);
    }
  },

  detener() {
    this.recognition?.stop();
    this.listening = false;
    const btn = document.getElementById('voice-btn');
    if (btn) { btn.classList.remove('listening'); btn.textContent = '🎤'; }
  },

  /* ── LEER SELECCIÓN ── */
  leerSeleccion() {
    const sel = window.getSelection()?.toString()?.trim();
    if (sel) this.hablar(sel);
    else this.hablar('No hay texto seleccionado.');
  },
};
