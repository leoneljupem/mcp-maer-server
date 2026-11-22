// 🦁 MAER — Sugerencias contextuales
MAER.sugerencias = {
  _sugerencias: [
    "¿Quieres calcular tu pensión con la Ley 73?",
    "¿Tienes tu constancia de semanas cotizadas?",
    "Puedo analizar documentos IMSS que me compartas.",
    "¿Necesitas generar una carta de solicitud al IMSS?",
    "Puedo buscar CURPs y NSS en tus archivos.",
    "¿Ya revisaste tus semanas cotizadas en el IMSS?",
    "Puedo calcular tu pensión con la Ley 97 y tu Afore.",
    "¿Necesitas un recurso de inconformidad por semanas faltantes?",
    "¿Quieres que redacte una carta de inconformidad al IMSS?",
    "Puedo revisar tu resolución de pensión y detectar errores.",
    "¿Te ayudo con el trámite de credito INFONAVIT?",
    "¿Necesitas citar el teléfono de PROFEDET?",
    "Puedo explicarte cuándo pagan el aguinaldo y la prima vacacional.",
    "¿Quieres exportar tu conversación o tus eventos a TXT?",
    "Puedo revisar tu expediente y detectar documentos faltantes.",
    "¿Necesitas una carta poder para tu trámite?",
    "¿Quieres consultar tu vigencia de derechos del IMSS?",
    "Puedo verificar si tu NSS aparece en varios documentos.",
  ],

  init() {
    // Sugerencias se muestran en el chat al inicio
  },

  _normalizar(t) {
    return (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  },

  mostrar(contexto) {
    const sugs = this.buscar(contexto).map(s => s.texto);
    return sugs.length ? sugs : this._sugerencias.slice(0, 2);
  },

  get catalogo() {
    return this._sugerencias.map(texto => ({ texto }));
  },

  buscar(contexto) {
    const palabras = this._normalizar(contexto).split(/\s+/).filter(Boolean);
    if (!palabras.length) return this.catalogo.slice(0, 3);
    return this.catalogo.filter(s => {
      const txt = this._normalizar(s.texto);
      return palabras.every(p => txt.includes(p));
    });
  }
};
