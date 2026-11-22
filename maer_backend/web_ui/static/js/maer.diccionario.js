// 🦁 MAER — Diccionario de respuestas
const MAER_DICCIONARIO = [
  { triggers: ["hola","buenos dias","buenas","saludos","que tal"], respuesta: "¡Hola, Leonel! ¿En qué puedo ayudarte hoy?" },
  { triggers: ["quien eres","que eres","presentate","tu nombre"], respuesta: "Soy MAER, tu asistente de expedientes IMSS y defensa legal. Versión 4.0 Quantum." },
  { triggers: ["ayuda","que puedes hacer","funciones","como funcionas"], respuesta: "Puedo analizar documentos, extraer CURP/NSS, calcular pensiones Ley 73, generar cartas legales, buscar en archivos y mucho más." },
  { triggers: ["gracias","muchas gracias","te agradezco"], respuesta: "Con gusto, Leonel. Para eso estoy." },
  { triggers: ["adios","hasta luego","chao","nos vemos","bye"], respuesta: "Hasta luego. Recuerda guardar tu trabajo." },
  { triggers: ["semanas","cotizadas","cuantas semanas"], respuesta: "Para verificar tus semanas cotizadas necesito tu NSS y CURP. ¿Los tienes a la mano?" },
  { triggers: ["pension","jubilacion","retiro","ley 73","ley 97"], respuesta: "Para calcular tu pensión Ley 73 necesito: semanas cotizadas, salario promedio y edad. ¿Quieres que lo calcule?" },
  { triggers: ["imss","seguro social"], respuesta: "El IMSS es el Instituto Mexicano del Seguro Social. ¿Necesitas consultar algo específico sobre tu expediente?" },
  { triggers: ["curp"], respuesta: "La CURP es tu Clave Única de Registro de Población. Tiene 18 caracteres. ¿Quieres que la decodifique?" },
  { triggers: ["nss","numero de seguro"], respuesta: "El NSS es tu Número de Seguro Social, tiene 11 dígitos. Es necesario para consultas IMSS." },
  { triggers: ["recurso de inconformidad","inconformidad","recurso legal","impugnacion"], respuesta: "Un recurso de inconformidad se presenta ante el IMSS cuando no estás de acuerdo con el dictamen o con tus semanas reconocidas. Puedo redactarlo contigo." },
  { triggers: ["profedet","telefono profedet","defensoria laboral"], respuesta: "PROFEDET brinda asesoría laboral gratuita. Teléfonos: 800 717 2942 y 55 5998 2000. También puedes acudir a sus oficinas en CDMX." },
  { triggers: ["aguinaldo","prima vacacional","cuando pagan"], respuesta: "El aguinaldo se paga antes del 20 de diciembre y equivale a mínimo 15 días de salario. La prima vacacional es de al menos 25% del salario de los días de vacaciones." },
  { triggers: ["infonavit","credito infonavit","vivienda"], respuesta: "INFONAVIT otorga créditos hipotecarios con tu subcuenta de vivienda. Necesitas tu NSS y tu historial de aportaciones patronales." },
  { triggers: ["exportar chat","exportar conversacion","descargar chat"], respuesta: "En la pestaña de Ajustes o con el módulo de exportación puedes descargar tu chat en TXT o JSON. ¿Quieres que te indique la ruta?" },
  { triggers: ["exportar"], respuesta: "Puedo exportar tu chat, tus eventos y tus notas a TXT o JSON. Dime qué quieres descargar." },
  { triggers: ["curp decodificar","decodificar curp","significado curp"], respuesta: "La CURP se compone de: iniciales y fecha de nacimiento, sexo, entidad, consonantes internas, homoclave y dígito verificador. Pega tu CURP y la decodifico." },
  { triggers: ["rfc","registro federal de contribuyentes"], respuesta: "El RFC es tu Registro Federal de Contribuyentes. Puedo validar su estructura y ayudarte a detectarlo en documentos." },
  { triggers: ["acta de nacimiento","acta"], respuesta: "El acta de nacimiento la emite el Registro Civil. Puedes descargarla en línea con tu CURP en el portal oficial del gobierno." },
  { triggers: ["ine","credencial","identificacion oficial"], respuesta: "La credencial INE es tu identificación oficial vigente. Verifica que tus datos coincidan con tu CURP y NSS." },
  { triggers: ["domicilio","comprobante de domicilio"], respuesta: "Para trámites suelen pedir comprobante de domicilio no mayor a 3 meses: luz, agua, teléfono o estado de cuenta bancario." },
  { triggers: ["constancia de semanas","constancia"], respuesta: "La constancia de semanas cotizadas se descarga en el portal del IMSS con tu NSS y contraseña, o se solicita en la subdelegación." },
  { triggers: ["subdelegacion","oficina imss","cita imss"], respuesta: "Puedes agendar cita en la subdelegación del IMSS por teléfono o en el portal oficial. Lleva identificación, CURP, NSS y documentos del trámite." },
  { triggers: ["afore","cuenta afore","traspaso"], respuesta: "Tu Afore administra tu subcuenta de retiro. Puedes consultar tu saldo en el portal de tu Afore o en e-SAR." },
  { triggers: ["modalidad 40","continuar cotizando"], respuesta: "La Modalidad 40 te permite seguir cotizando de forma voluntaria para alcanzar semanas o mejorar tu salario promedio. Debe tramitarse ante el IMSS." },
  { triggers: ["modalidad 10","trabajador independiente"], respuesta: "La Modalidad 10 es la incorporación voluntaria al régimen obligatorio para trabajadores independientes." },
  { triggers: ["pension alimenticia","alimentos"], respuesta: "La pensión alimenticia se tramita ante el juez familiar. Puedo ayudarte a redactar un escrito o una carta de requerimiento." },
  { triggers: ["amparo"], respuesta: "El amparo protege tus derechos frente a actos de autoridad. Necesitas un abogado o la asesoría de una institución pública gratuita." },
  { triggers: ["demanda","demandar"], respuesta: "Para una demanda laboral puedes acudir a la Junta de Conciliación o al Tribunal Laboral. Cuéntame tu caso y te oriento." },
  { triggers: ["despido","me corrieron","renuncia"], respuesta: "Si te despidieron, revisa tu finiquito: salario devengado, vacaciones, prima vacacional, aguinaldo proporcional y prima de antigüedad." },
  { triggers: ["finiquito","liquidacion"], respuesta: "El finiquito incluye días trabajados, vacaciones y prima vacacional, aguinaldo proporcional y prestaciones. La liquidación aplica en despido injustificado." },
  { triggers: ["salario promedio","salario diario"], respuesta: "El salario promedio se calcula con los últimos 250 salarios semanales o 5 años de cotización, actualizados por INPC." },
  { triggers: ["factor fox","fox"], respuesta: "El Factor Fox es el porcentaje aplicado al salario promedio para estimar el monto de la pensión según la tabla de la Ley 73." },
  { triggers: ["ley 73","ley del 73"], respuesta: "La Ley 73 aplica a quienes cotizaron antes del 1 de julio de 1997. Requiere 500 semanas y permite pensión vitalicia con salario promedio." },
  { triggers: ["ley 97","ley del 97"], respuesta: "La Ley 97 aplica a quienes comenzaron a cotizar después de julio de 1997. La pensión depende de tu cuenta individual y la Afore." },
  { triggers: ["500 semanas","requisitos pension"], respuesta: "Con Ley 73 necesitas al menos 500 semanas cotizadas y tener 60 años cumplidos para pensión por cesantía, o 65 para vejez." },
  { triggers: ["65 anos","vejez"], respuesta: "La pensión por vejez Ley 73 se otorga a los 65 años con 500 semanas cotizadas como mínimo." },
  { triggers: ["60 anos","cesantia"], respuesta: "La pensión por cesantía en edad avanzada aplica desde los 60 años con 500 semanas cotizadas, con un porcentaje menor al de vejez." },
  { triggers: ["clabe","cuenta bancaria"], respuesta: "Para cobrar tu pensión necesitas una CLABE interbancaria de 18 dígitos a tu nombre, registrada ante el IMSS." },
  { triggers: ["pago","deposito","cuando me pagan"], respuesta: "El pago de pensión se deposita mensualmente en la CLABE registrada. Verifica el calendario oficial del IMSS para fechas exactas." },
  { triggers: ["expediente","documentos faltantes"], respuesta: "Puedo revisar tu expediente y decirte qué documentos faltan: identificación, CURP, NSS, acta, constancia de semanas y comprobante de domicilio." },
  { triggers: ["carta poder","poder notarial"], respuesta: "Una carta poder sirve para que alguien te represente en un trámite. Puedo generarte el formato; si es acto jurídico amplio, requiere poder notarial." },
  { triggers: ["carta de solicitud","carta imss"], respuesta: "Puedo redactar tu carta de solicitud al IMSS con tus datos. Ve a la pestaña Pensión → Generador de Cartas." },
  { triggers: ["ocr","escanear","texto de imagen"], respuesta: "Uso OCR para extraer texto de imágenes y PDF escaneados. Sube el archivo y lo proceso." },
  { triggers: ["pdf","documento pdf"], respuesta: "Puedo leer PDFs, extraer texto, tablas y detectar datos como CURP, NSS o RFC. Sube el archivo y lo analizo." },
  { triggers: ["buscar archivos","busqueda"], respuesta: "En la pestaña Búsqueda puedes localizar palabras dentro de todos tus archivos, no solo por nombre." },
  { triggers: ["aprender","aprendizaje","memorizar"], respuesta: "En la pestaña Aprendizaje puedes darme documentos para que los memorice y los use como contexto en el chat." },
  { triggers: ["tarea","investigacion","generar documento"], respuesta: "En la pestaña Tareas puedo investigar o redactar documentos por ti. Describe la tarea y adjunta archivos si aplica." },
  { triggers: ["whatsapp","tasker","mensajes"], respuesta: "La integración con WhatsApp y Tasker permite enviar y recibir mensajes desde la pestaña WhatsApp." },
  { triggers: ["respaldo","backup","copiar archivos"], respuesta: "Puedo crear un respaldo de tus datos desde Sistema → Crear respaldo. Se guarda un respaldo local." },
  { triggers: ["seguridad","contrasena","sesion"], respuesta: "MAER está protegido con contraseña maestra. Puedes cerrar sesión desde Ajustes → Seguridad de Acceso." },
  { triggers: ["version","que version"], respuesta: "MAER 4.0 Quantum — Motor de análisis documental, OCR, validación de identificaciones y defensa legal." },
  { triggers: ["gracias por todo","excelente"], respuesta: "Gracias a ti, Leonel. Aquí sigo para lo que necesites." },
  { triggers: ["no entiendo","explicame"], respuesta: "Claro, dime qué parte quieres que te explique con más detalle y te la desgloso paso a paso." },
  { catch_all: true, respuesta: "No tengo una respuesta exacta para eso, Leonel. Puedo ayudarte con pensión IMSS, semanas cotizadas, documentos, CURP/NSS, cartas y trámites legales. ¿Quieres reformular tu pregunta o adjuntar un documento?" },
];

/* Normaliza texto: minúsculas, sin acentos y sin signos */
function MAER_normalizar(texto) {
  return String(texto == null ? '' : texto)
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9ñ\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// Función de búsqueda en diccionario
function MAER_buscarRespuesta(texto, opts) {
  const t = MAER_normalizar(texto);
  for (const entry of MAER_DICCIONARIO) {
    if (entry.catch_all || !entry.triggers) continue;
    if (entry.triggers.some(trigger => t.includes(MAER_normalizar(trigger)))) {
      return entry.respuesta;
    }
  }
  if (opts && opts.sinFallback) return null;
  const fallback = MAER_DICCIONARIO.find(e => e.catch_all);
  return fallback ? fallback.respuesta : null;
}

window.MAER_DICCIONARIO = MAER_DICCIONARIO;
window.MAER_normalizar = MAER_normalizar;
window.MAER_buscarRespuesta = MAER_buscarRespuesta;
