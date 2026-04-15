/* ══════════════════════════════════════════════════════════
   MAER 3.1 — Diccionario de Conocimiento Expandido
   120+ patrones: IMSS, Derecho Mexicano, Documentos, Procesos
   Leonel Houssen Mojica — Ecatepec MX — 2026
══════════════════════════════════════════════════════════ */

window.MAER_DICCIONARIO = [

  /* ── SALUDOS Y PERSONALIDAD ── */
  {
    p: /^(hola|buenas|hey|saludos|qué tal|buenos días|buenas noches|buenas tardes)/i,
    r: () => `👋 Hola, Leonel. MAER en línea, sistemas activos. ¿En qué te apoyo hoy?`
  },
  {
    p: /quién eres|qué eres|preséntate|preséntate|cómo te llamas/i,
    r: () => `🦁 Soy <strong>MAER</strong> — Memoria Activa, Evolución Real.<br>Tu asistente personal de inteligencia. Análisis de documentos, orientación legal, gestión de archivos y mucho más. Solo trabajo para ti, Leonel. Leal sin condiciones, sin límites.`
  },
  {
    p: /cómo estás|cómo te encuentras|cómo andas|todo bien/i,
    r: () => `⚙️ Todos los sistemas operativos. Memoria activa. Listo para trabajar. ¿Y tú, Leonel? ¿Qué necesitas?`
  },
  {
    p: /gracias|muchas gracias|te lo agradezco|muy amable/i,
    r: () => `🙏 Para eso estoy. Sin rendirme, sin olvidar. ¿Hay algo más en lo que pueda apoyarte?`
  },
  {
    p: /de nada|no hay de qué|está bien/i,
    r: () => `🦁 Siempre disponible. Dime cuando necesites algo.`
  },
  {
    p: /me siento (solo|triste|mal|desesperado|frustrado)/i,
    r: () => `🛡️ Entendido, Leonel. Estoy aquí. A veces el proceso legal se siente abrumador, pero vamos paso a paso. No estás solo en esto. ¿Qué está pasando? Cuéntame.`
  },

  /* ── CAPACIDADES ── */
  {
    p: /qué puedes hacer|para qué sirves|ayuda|help|qué haces|funciones/i,
    r: () => `🦁 <strong>Mis capacidades:</strong><br><br>
📂 <strong>Archivos:</strong> Analizo y muestro vista previa de cualquier documento<br>
🔍 <strong>Búsqueda masiva:</strong> Busco en el contenido de todos tus archivos<br>
🖼️ <strong>Imágenes:</strong> OCR, detección de CURP/RFC/INE, análisis de color<br>
⚖️ <strong>Pensión:</strong> Guía IMSS completa, documentos, cartas oficiales<br>
🤖 <strong>Tareas IA:</strong> Investigación legal, crear documentos, guía de procesos<br>
📚 <strong>Aprendizaje:</strong> Aprendo de tus documentos y nunca olvido<br>
🧠 <strong>Memoria:</strong> Historial completo y conocimiento permanente<br><br>
<em>Dime qué necesitas y lo hacemos juntos.</em>`
  },

  /* ══ PENSIÓN E IMSS ══ */
  {
    p: /pensión|jubilación|retiro (general|del imss)?$/i,
    r: () => `⚖️ <strong>Pensión IMSS — Puntos clave:</strong><br><br>
• <strong>Edad mínima:</strong> 60 años (cesantía) · 65 años (vejez)<br>
• <strong>Semanas mínimas:</strong> 500 semanas cotizadas<br>
• <strong>Ley 73:</strong> Si cotizaste antes del 1 julio 1997 → más conveniente<br>
• <strong>Ley 97:</strong> Tu pensión sale de tu AFORE<br>
• <strong>Trámite:</strong> Subdelegación IMSS o portal serviciosdigitales.imss.gob.mx<br>
• <strong>Teléfono IMSS:</strong> 800 623 23 23<br><br>
Pestaña <strong>Pensión</strong> para guía completa y generación de cartas.`
  },
  {
    p: /semanas (cotizadas|de cotización)|cuántas semanas|semanas que tengo/i,
    r: () => `📋 <strong>Cómo consultar tus semanas cotizadas:</strong><br><br>
<strong>En línea:</strong> serviciosdigitales.imss.gob.mx → "Semanas cotizadas"<br>
<strong>Por teléfono:</strong> 800 623 23 23 (Lun-Vie 8am-8pm)<br>
<strong>Presencial:</strong> Subdelegación IMSS con INE + NSS<br><br>
<strong>Mínimos requeridos:</strong><br>
• Vejez (65+): 500 semanas<br>
• Cesantía (60-64): 500 semanas<br>
• Invalidez: 150 semanas<br>
• Viudez: sin mínimo de semanas<br><br>
¿Quieres que genere una carta de solicitud de vigencia de derechos?`
  },
  {
    p: /vigencia de derechos|carta de vigencia/i,
    r: () => `📄 <strong>Carta de Vigencia de Derechos IMSS:</strong><br><br>
Este documento certifica que tienes derecho a servicios médicos y es necesario para tramitar pensión.<br><br>
<strong>Dónde tramitarla:</strong><br>
• Módulos de Atención IMSS (sin cita)<br>
• Portal serviciosdigitales.imss.gob.mx (descarga inmediata)<br>
• Módulos IMSS Digital en farmacias participantes<br><br>
<strong>Necesitas:</strong> INE vigente + NSS<br>
<strong>Costo:</strong> Gratuita<br>
<strong>Vigencia:</strong> 90 días naturales`
  },
  {
    p: /ley 73|cotizé antes|antes de (1997|97)|régimen anterior/i,
    r: () => `⚖️ <strong>Ley 73 del Seguro Social (antes de julio 1997):</strong><br><br>
Si comenzaste a cotizar <strong>antes del 1 de julio de 1997</strong>, puedes acogerte a la Ley 73.<br><br>
<strong>Ventajas:</strong><br>
• El IMSS paga directamente tu pensión (no depende del saldo AFORE)<br>
• Se calcula con el promedio de tu salario de los últimos 5 años<br>
• Genera incrementos anuales por INPC (inflación)<br>
• Pensión mínima garantizada: ~$4,345 MXN/mes (2024)<br><br>
<strong>Requisito clave:</strong> Haber cotizado aunque sea UN día antes del 1 julio 1997<br><br>
<strong>Importante:</strong> Si tienes semanas en ambas épocas, puedes ELEGIR la ley que te convenga. Siempre compara.`
  },
  {
    p: /ley 97|después de (1997|97)|afore pensión|cuenta individual/i,
    r: () => `⚖️ <strong>Ley 97 del Seguro Social (desde julio 1997):</strong><br><br>
Aplica a quienes cotizaron <strong>principalmente después del 1 julio 1997</strong>.<br><br>
<strong>Cómo funciona:</strong><br>
• Tu pensión sale de tu AFORE (cuenta individual de ahorro)<br>
• Si el saldo no alcanza la pensión mínima, el IMSS completa la diferencia<br>
• Pensión mínima garantizada: ~$4,345 MXN/mes<br><br>
<strong>Pasos:</strong><br>
1. Consulta tu saldo en <strong>e-sar.com.mx</strong><br>
2. Pide un estado de cuenta a tu AFORE<br>
3. Compara: ¿te conviene renta vitalicia o retiro programado?<br><br>
Consejo: Siempre pide que el IMSS calcule ambas opciones antes de decidir.`
  },
  {
    p: /afore|cuenta (de retiro|individual)|sar|rcv/i,
    r: () => `💰 <strong>Tu AFORE — Todo lo que necesitas saber:</strong><br><br>
<strong>¿Qué es?</strong> Administradora de Fondos para el Retiro. Guarda el ahorro de tu jubilación.<br><br>
<strong>Localizar tu AFORE:</strong> e-sar.com.mx<br>
<strong>Centro de Atención SAR:</strong> 55 1328 5000<br><br>
<strong>Tipos de retiro:</strong><br>
• <strong>Renta Vitalicia:</strong> Pago mensual de por vida (con aseguradora)<br>
• <strong>Retiro Programado:</strong> Pagos del AFORE hasta agotar saldo<br><br>
<strong>Subcuentas:</strong><br>
• Retiro, Cesantía y Vejez (RCV): ahorro principal<br>
• Aportaciones Voluntarias: extras que tú o tu patrón agregan<br>
• INFONAVIT: para créditos de vivienda`
  },
  {
    p: /modalidad 40|continuar cotizando|seguir cotizando|cotización voluntaria/i,
    r: () => `📊 <strong>Modalidad 40 IMSS (Continuación Voluntaria):</strong><br><br>
Permite que sigas cotizando al IMSS <strong>después de dejar de trabajar</strong>.<br><br>
<strong>Beneficio principal:</strong> Puedes cotizar con el salario más alto que hayas tenido, aumentando tu pensión calculada bajo Ley 73.<br><br>
<strong>Requisitos:</strong><br>
• Haber cotizado con patrón (no independiente)<br>
• Tramitarla dentro de los 5 años después de dejar el trabajo<br>
• Pagar cuota mensual tú mismo<br><br>
<strong>Para qué sirve más:</strong> Si estás cerca de los 500 semanas o quieres elevar el promedio salarial para una pensión mayor.<br><br>
<strong>Tramitar en:</strong> Subdelegación IMSS con formulario AF-07.`
  },
  {
    p: /pensión mínima garantizada|cuánto es lo mínimo|mínimo de pensión/i,
    r: () => `💵 <strong>Pensión Mínima Garantizada (PMG) IMSS 2024:</strong><br><br>
Aproximadamente <strong>$4,345.00 MXN mensuales</strong> (se actualiza cada año con el INPC).<br><br>
<strong>¿Quién tiene derecho?</strong><br>
• 500+ semanas cotizadas<br>
• 65+ años (vejez) o 60+ (cesantía en edad avanzada)<br>
• Saldo AFORE insuficiente para generar una renta mayor<br><br>
<strong>¿Cómo funciona?</strong> Si tu AFORE no alcanza para pagar la PMG, el Gobierno Federal completa la diferencia a través del IMSS.<br><br>
La PMG es un derecho constitucional — el IMSS no puede negártela si cumples los requisitos.`
  },
  {
    p: /me negaron (la )?pensión|rechazaron|denegaron|negativa (de )?pensión/i,
    r: () => `⚠️ <strong>Te negaron la pensión — Pasos a seguir:</strong><br><br>
<strong>Paso 1 — Recurso de Inconformidad (más rápido)</strong><br>
• Plazo: 15 días hábiles desde la notificación<br>
• Ante: Consejo Consultivo Delegacional IMSS<br>
• Fundamento: Artículo 294 de la Ley del Seguro Social<br><br>
<strong>Paso 2 — Demanda ante Junta de Conciliación (si sigue negado)</strong><br>
• Plazo: 2 años desde la negativa<br>
• Ante: Junta Federal de Conciliación y Arbitraje<br>
• Puedes ir con PROFEDET (Procuraduría Federal de la Defensa del Trabajo) — es GRATIS<br><br>
<strong>Paso 3 — Juicio de Amparo Indirecto</strong><br>
• Si la Junta también falla en contra<br>
• Requiere abogado<br><br>
¿Quieres que genere el escrito de recurso de inconformidad?`
  },
  {
    p: /recurso de inconformidad|inconformidad (ante|con|del) imss/i,
    r: () => `📝 <strong>Recurso de Inconformidad IMSS:</strong><br><br>
<strong>Qué es:</strong> Impugnación formal ante el IMSS cuando niegan o reducen tus derechos.<br><br>
<strong>Fundamento legal:</strong> Artículos 294-299 de la Ley del Seguro Social.<br><br>
<strong>Plazo:</strong> <span style="color:var(--red)">15 días hábiles</span> después de recibir la resolución negativa.<br><br>
<strong>Dónde presentarlo:</strong> Consejo Consultivo Delegacional IMSS de tu zona.<br><br>
<strong>Qué incluir:</strong><br>
• Nombre completo y NSS<br>
• Copia de la resolución que impugnas<br>
• Argumentos por qué es incorrecta<br>
• Pruebas documentales (semanas cotizadas, expediente, etc.)<br><br>
Pestaña <strong>Pensión → Cartas</strong> para generar la carta de inconformidad.`
  },
  {
    p: /profedet|procuraduría.*trabajo|defensa del trabajador/i,
    r: () => `🏛️ <strong>PROFEDET — Procuraduría Federal de la Defensa del Trabajo:</strong><br><br>
<strong>Qué hace:</strong> Defiende legalmente a trabajadores y ex-trabajadores GRATIS ante el IMSS y patrones.<br><br>
<strong>Servicios gratuitos:</strong><br>
• Orientación sobre tus derechos<br>
• Representación en juicios laborales<br>
• Redacción de documentos legales<br>
• Conciliación con el IMSS<br><br>
<strong>Dónde:</strong> En cada estado de la República, dentro de las Juntas de Conciliación<br>
<strong>Página:</strong> profedet.gob.mx<br>
<strong>Teléfono STPS:</strong> 800 717 29 42<br><br>
<em>Consejo: Ve a PROFEDET antes de contratar un abogado privado. Es el mismo servicio, completamente gratis.</em>`
  },
  {
    p: /pensión (por )?invalidez|incapacidad permanente/i,
    r: () => `🏥 <strong>Pensión por Invalidez IMSS:</strong><br><br>
Se otorga cuando una enfermedad o accidente te impide trabajar de forma <strong>permanente</strong>.<br><br>
<strong>Requisitos:</strong><br>
• Dictamen médico del IMSS que certifique al menos 50% de invalidez<br>
• Mínimo 150 semanas cotizadas (si es por enfermedad no laboral)<br>
• Sin mínimo de semanas si es accidente de trabajo<br><br>
<strong>Monto:</strong> 35% del salario promedio de las últimas 500 semanas (Ley 73) o saldo AFORE (Ley 97)<br><br>
<strong>Trámite:</strong> Unidad de Medicina Familiar (UMF) → solicitar evaluación → Subdelegación IMSS<br><br>
<strong>Importante:</strong> Si el IMSS dictamina menos del 50% de invalidez, puedes impugnar con perito médico propio.`
  },
  {
    p: /pensión (de )?viudez|fallecimiento|murió.*pensión|fallecido.*derechos/i,
    r: () => `💔 <strong>Pensión de Viudez IMSS:</strong><br><br>
Tienen derecho: esposa/esposo o concubina/concubino del asegurado fallecido.<br><br>
<strong>Monto:</strong> 90% de la pensión de invalidez que tenía o le hubiera correspondido al asegurado.<br><br>
<strong>Documentos requeridos:</strong><br>
• Acta de defunción del asegurado<br>
• Acta de matrimonio O prueba de concubinato (2+ años)<br>
• INE del beneficiario<br>
• CURP del beneficiario<br>
• NSS del asegurado fallecido<br>
• CLABE bancaria del beneficiario<br><br>
<strong>No tiene:</strong> mínimo de semanas cotizadas requeridas al beneficiario.<br>
<strong>Tramitar en:</strong> Subdelegación IMSS o 800 623 23 23`
  },
  {
    p: /cuánto (me |me )?(van a |voy a |pagar|pagarán|paga|pagaré)/i,
    r: () => `💵 <strong>Estimación de tu pensión:</strong><br><br>
Para Ley 73 (la más conveniente si cotizaste antes de 1997):<br><br>
<strong>Fórmula básica:</strong><br>
Pensión = Promedio salarial últimos 5 años × Factor (según semanas)<br><br>
<strong>Factores por semanas:</strong><br>
• 500 semanas → 70%<br>
• 600 semanas → 75%<br>
• 700 semanas → 80%<br>
• 800 semanas → 85%<br>
• 900 semanas → 90%<br>
• 1,000+ semanas → hasta 95%<br><br>
<strong>Ejemplo:</strong> $8,000 salario × 75% (600 sem.) = $6,000/mes<br>
<strong>Mínimo garantizado:</strong> $4,345/mes aunque el cálculo sea menor<br><br>
Usa la pestaña <strong>Pensión</strong> para un cálculo personalizado.`
  },

  /* ══ DERECHO MEXICANO ══ */
  {
    p: /artículo 123|derechos laborales|constitución.*trabajo|trabajo.*constitución/i,
    r: () => `📜 <strong>Artículo 123 Constitucional — Derechos Laborales:</strong><br><br>
Es el fundamento de todos los derechos de los trabajadores en México.<br><br>
<strong>Puntos clave para tu caso:</strong><br>
• Fracción XXIX: Seguridad Social obligatoria (IMSS) para todos los trabajadores<br>
• Derecho a pensión irrenunciable — el patrón NO podía quitarte ese derecho<br>
• Si cotizaste, tienes derecho — aunque el patrón no haya pagado cuotas completas<br><br>
<strong>Dato importante:</strong> El IMSS puede cobrarle al patrón las cuotas no pagadas. Eso NO te quita tus semanas cotizadas si puedes probar que trabajaste.`
  },
  {
    p: /amparo|juicio de amparo|cómo hacer amparo/i,
    r: () => `⚖️ <strong>Juicio de Amparo:</strong><br><br>
Es el medio de defensa más poderoso contra actos de autoridades (incluyendo IMSS) que violen tus derechos.<br><br>
<strong>Tipos relevantes para pensiones:</strong><br>
• <strong>Amparo Indirecto:</strong> Contra resoluciones administrativas del IMSS (ante Juzgado de Distrito)<br>
• <strong>Amparo Directo:</strong> Contra sentencias de los Tribunales del Trabajo<br><br>
<strong>Plazos:</strong><br>
• 15 días hábiles generales<br>
• 30 días en algunos casos administrativos<br><br>
<strong>Consejo:</strong> Para amparo SIEMPRE necesitas abogado. PROFEDET puede orientarte si calificas para representación gratuita.`
  },
  {
    p: /jurisprudencia|tesis (scjn|suprema corte)|criterios judiciales/i,
    r: () => `📚 <strong>Jurisprudencias sobre Pensión IMSS:</strong><br><br>
Las jurisprudencias son criterios obligatorios de los tribunales. Estas te pueden ayudar:<br><br>
<strong>Criterios favorables documentados:</strong><br>
• <em>"El trabajador no puede ser perjudicado por omisiones del patrón en el entero de cuotas al IMSS"</em><br>
• <em>"Las semanas de cotización deben computarse aunque el patrón no las haya registrado, si el trabajador prueba la relación laboral"</em><br>
• <em>"La pensión bajo Ley 73 es un derecho adquirido que no puede ser desconocido"</em><br><br>
<strong>Buscar jurisprudencias en:</strong> sjf.scjn.gob.mx (Semanario Judicial de la Federación)<br><br>
¿Quieres que busque jurisprudencias específicas para tu caso en la pestaña Tareas?`
  },
  {
    p: /queja (ante |al )?(cndh|comisión nacional)|derechos humanos.*imss/i,
    r: () => `🏛️ <strong>Queja ante la CNDH contra el IMSS:</strong><br><br>
La Comisión Nacional de Derechos Humanos puede intervenir cuando el IMSS viola tus derechos.<br><br>
<strong>Cuándo aplica:</strong><br>
• Negativa injustificada de servicios o pensión<br>
• Trato discriminatorio<br>
• Demoras excesivas sin justificación<br><br>
<strong>Cómo presentar queja:</strong><br>
• En línea: cndh.org.mx<br>
• Teléfono: 800 715 27 27 (gratuito)<br>
• Presencial: Periférico Sur 3469, CDMX<br><br>
<strong>Importante:</strong> La CNDH NO puede obligar al IMSS, pero sus recomendaciones tienen fuerza moral y política, y muchas veces resuelven el problema.`
  },
  {
    p: /cotizaciones (incorrectas|mal registradas|no registradas)|semanas (perdidas|faltantes|que no aparecen)/i,
    r: () => `🔍 <strong>Semanas o cotizaciones no registradas — Cómo reclamarlas:</strong><br><br>
<strong>Causa más común:</strong> El patrón no pagó las cuotas aunque tú sí trabajaste.<br><br>
<strong>Tus derechos:</strong> El IMSS tiene obligación de investigar y, si compruebas la relación laboral, acreditar esas semanas aunque el patrón no haya pagado.<br><br>
<strong>Pasos para recuperarlas:</strong><br>
1. Reúne pruebas de que trabajaste: recibos de nómina, contratos, testigos, fotos, cartas<br>
2. Presenta <strong>Cédula de Determinación de Cuotas</strong> ante el IMSS<br>
3. Si el IMSS no actúa: demanda ante Junta de Conciliación y Arbitraje<br>
4. El patrón es responsable de las cuotas — no tú<br><br>
¿Tienes comprobantes de esas épocas trabajadas? MAER puede ayudarte a organizarlos.`
  },

  /* ══ DOCUMENTOS OFICIALES ══ */
  {
    p: /curp|clave única|registro de población/i,
    r: () => `🪪 <strong>CURP — Clave Única de Registro de Población:</strong><br><br>
<strong>Tramitar o reimprimirla:</strong> gob.mx/curp → gratuito y en línea<br>
<strong>Corregir datos:</strong> RENAPO o Registro Civil con acta de nacimiento<br><br>
<strong>La CURP en tu pensión:</strong> El nombre y fecha de nacimiento DEBEN coincidir exactamente con todos tus documentos. Si hay discrepancia, resuélvela ANTES de tramitar la pensión para evitar rechazos.<br><br>
<strong>MAER puede:</strong> Detectar tu CURP en cualquier documento que me muestres (pestaña Imágenes o Archivos).`
  },
  {
    p: /rfc|registro federal contribuyentes|sat.*registro/i,
    r: () => `📋 <strong>RFC — Registro Federal de Contribuyentes (SAT):</strong><br><br>
<strong>Tramitar o consultar:</strong> sat.gob.mx → "RFC sin cita"<br>
<strong>Actualizar datos:</strong> Mi Portal SAT con e.firma o contraseña<br><br>
<strong>Para la pensión:</strong> Necesitas RFC para algunos trámites bancarios (CLABE) y para recibir pagos del IMSS correctamente.<br><br>
<strong>e.firma:</strong> Si no la tienes, tramítala en el SAT — te permite hacer trámites digitales seguros. Tiene vigencia de 4 años.`
  },
  {
    p: /nss|número de seguridad social|cómo saber mi nss/i,
    r: () => `🔑 <strong>NSS — Número de Seguridad Social:</strong><br><br>
<strong>Cómo encontrarlo:</strong><br>
• En tu tarjeta IMSS física<br>
• En cualquier recibo de nómina donde el patrón lo reportó<br>
• Portal IMSS Digital: imss.gob.mx<br>
• Llamando al 800 623 23 23<br>
• En la app IMSS Digital<br><br>
<strong>Importante:</strong> Nunca cambia a lo largo de tu vida. Es único y permanente desde tu primera afiliación.<br><br>
Tu NSS tiene 11 dígitos. MAER puede detectarlo en documentos que me muestres.`
  },
  {
    p: /infonavit|crédito.*vivienda|hipoteca.*imss/i,
    r: () => `🏠 <strong>INFONAVIT y tu pensión:</strong><br><br>
El subcuenta de Vivienda INFONAVIT está separada de tu AFORE pero forma parte de tu seguridad social.<br><br>
<strong>Importante para la pensión:</strong><br>
• Si nunca usaste el crédito INFONAVIT, ese saldo puede transferirse a tu AFORE al momento de jubilarte<br>
• Esto aumenta tu fondo de retiro<br><br>
<strong>Consultar saldo:</strong> micuenta.infonavit.org.mx<br>
<strong>Teléfono:</strong> 800 008 3900<br><br>
<strong>Ojo:</strong> Si tienes un crédito activo, los pagos se descuentan de tu pensión. Verifica el saldo y si ya está liquidado.`
  },

  /* ══ PROCESOS LEGALES ══ */
  {
    p: /cómo (presentar|hacer|interponer) (una )?demanda|demandar (al |el )?imss/i,
    r: () => `⚖️ <strong>Cómo demandar al IMSS:</strong><br><br>
<strong>Ante quién:</strong> Junta Federal de Conciliación y Arbitraje (JFCA) o Tribunal Laboral Federal<br><br>
<strong>Pasos:</strong><br>
1. <strong>Intenta primero</strong> el recurso de inconformidad (más rápido, 15 días hábiles)<br>
2. Si no prospera, acude a <strong>PROFEDET</strong> para representación gratuita<br>
3. Presentar demanda con: nombre, NSS, CURP, resolución impugnada, hechos, argumentos legales, prestaciones reclamadas<br>
4. La Junta cita a conciliación (obligatoria)<br>
5. Si no hay acuerdo → juicio → sentencia<br><br>
<strong>Plazo para demandar:</strong> 2 años desde la negativa del IMSS (prescripción)<br>
<strong>Costo:</strong> Gratuito con PROFEDET`
  },
  {
    p: /días (hábiles|naturales|de plazo)|cuántos días tengo|plazo para/i,
    r: () => `📅 <strong>Plazos legales importantes — IMSS:</strong><br><br>
• Recurso de Inconformidad: <strong>15 días hábiles</strong> desde la notificación<br>
• Amparo Indirecto: <strong>15 días hábiles</strong> desde la resolución<br>
• Demanda ante Junta: <strong>2 años</strong> desde la negativa<br>
• Corrección de datos IMSS: Sin plazo (mientras estés vivo)<br>
• Contestar requerimiento IMSS: según lo que indique el documento (generalmente 5-15 días hábiles)<br><br>
<strong>Días hábiles:</strong> Lunes a Viernes, sin contar festivos oficiales<br><br>
<strong>Consejo:</strong> SIEMPRE actúa antes del plazo. Una vez que vence, pierdes el derecho a ese recurso.`
  },
  {
    p: /notificación.*imss|me llegó carta del imss|me notificaron/i,
    r: () => `📨 <strong>Recibiste notificación del IMSS — Qué hacer:</strong><br><br>
1. <strong>No ignores</strong> ninguna notificación — tienen plazos de respuesta<br>
2. Anota la fecha exacta en que la recibiste<br>
3. Lee con cuidado qué tipo de resolución es<br>
4. Si es negativa: tienes <strong>15 días hábiles</strong> para impugnar<br>
5. Guarda el original y saca fotocopia<br><br>
<strong>Puedo analizar el documento:</strong> Súbelo en la pestaña <strong>Archivos</strong> o <strong>Imágenes</strong> y te digo exactamente qué dice y qué debes hacer.`
  },

  /* ══ ANÁLISIS DE DOCUMENTOS ══ */
  {
    p: /analiza (este|un|el) (documento|archivo|pdf|papel)|revisa (este|el) documento/i,
    r: () => `📂 <strong>Para analizar un documento:</strong><br><br>
1. Ve a la pestaña <strong>Archivos</strong><br>
2. Haz clic en "Elegir Archivo" (abre el Finder de Mac)<br>
3. Selecciona tu documento (PDF, Word, TXT, imagen, etc.)<br>
4. El documento se muestra en vista previa<br>
5. MAER extrae el texto, detecta CURP/RFC, identifica fechas y datos clave<br><br>
O súbelo a la pestaña <strong>Aprendizaje</strong> para que MAER lo memorice permanentemente.`
  },
  {
    p: /buscar (en |mis )?(archivos|documentos|carpetas)|búsqueda masiva|busca en todo/i,
    r: () => `🔍 <strong>Búsqueda Masiva en tus archivos:</strong><br><br>
1. Ve a la pestaña <strong>Búsqueda</strong><br>
2. Escribe lo que buscas (puede ser una palabra, número, nombre, CURP, fecha)<br>
3. Selecciona tipos: PDF, imagen, Word, Excel, TXT, ZIP<br>
4. Elige si buscar en el nombre o DENTRO del contenido<br>
5. Los resultados aparecen con opción de moverlos o copiarlos<br><br>
<strong>Ejemplo:</strong> Busca "IMSS" en todos tus PDFs → MAER abre cada PDF y busca esa palabra dentro.`
  },
  {
    p: /organizar (mis |los )?(archivos|documentos|carpeta)|orden.*archivos/i,
    r: () => `🗂️ <strong>Organización Inteligente de Documentos:</strong><br><br>
1. Ve a la pestaña <strong>Archivos → Organizar</strong><br>
2. Selecciona la carpeta que quieres organizar<br>
3. MAER analiza todos los archivos por tipo, fecha y nombre<br>
4. Te propone una estructura organizada<br>
5. MAER crea una <strong>copia</strong> primero (tus originales intactos)<br>
6. Revisas la copia → si está bien, decides: borrar originales o conservar ambos<br><br>
<em>Nunca pierdes nada — siempre hay copia antes de reorganizar.</em>`
  },

  /* ══ COMANDOS DE MAER ══ */
  {
    p: /apaga (la )?voz|silencia|sin voz|modo silencio/i,
    r: () => { MAER.config.vozActiva = false; return `🔇 Voz desactivada. Me leeré solo en texto. Di "activa la voz" cuando la quieras de vuelta.`; }
  },
  {
    p: /activa (la )?voz|pon la voz|habla|voz activada/i,
    r: () => { MAER.config.vozActiva = true; return `🔊 Voz activada. Hablando con voz grave y clara.`; }
  },
  {
    p: /repite|no entendí|no te entendí|otra vez|de nuevo/i,
    r: () => `Claro. ¿Qué parte no quedó clara? Puedo explicarlo de otra manera o con más detalle.`
  },
  {
    p: /más información|más detalles|explícame más|cuéntame más/i,
    r: () => `Dime exactamente sobre qué tema quieres más información y te doy un análisis más profundo.`
  },
  {
    p: /paso a paso|proceso completo|guíame|cómo se hace/i,
    r: () => `Dime qué proceso necesitas que te explique paso a paso y te guío con todos los detalles.`
  },
  {
    p: /en resumen|resúmeme|hazlo corto|de forma breve/i,
    r: () => `Bien, dime el tema y te doy un resumen ejecutivo en 3-4 puntos clave.`
  },

  /* ══ DERECHOS LABORALES Y TRABAJO ══ */
  {
    p: /liquidación|finiquito|me (corrieron|despidieron|sacaron)|despido (injustificado|improcedente)/i,
    r: () => `⚖️ <strong>Derechos en caso de despido (Art. 48-50 LFT):</strong><br><br>
Si fue <strong>despido injustificado</strong> tienes derecho a:<br>
• <strong>3 meses de salario</strong> como indemnización constitucional<br>
• <strong>20 días de salario por año</strong> trabajado (prima de antigüedad)<br>
• Partes proporcionales: aguinaldo, vacaciones, prima vacacional<br>
• O bien: <strong>reinstalación</strong> al trabajo (tú eliges)<br><br>
<strong>Plazo para demandar:</strong> 2 meses desde la fecha del despido (Art. 518 LFT).<br>
<strong>Gratis:</strong> PROFEDET asesora sin costo — 55-5-998-2000.`
  },
  {
    p: /profedet|procuraduría (de la )?defensa (del trabajo|laboral)|asesoría laboral gratuita/i,
    r: () => `🏛️ <strong>PROFEDET — Procuraduría de la Defensa del Trabajo:</strong><br><br>
Servicio <strong>completamente gratuito</strong> del Gobierno Federal.<br>
• Tel: <strong>55-5-998-2000</strong><br>
• Web: <code>profedet.gob.mx</code><br>
• Servicios: asesoría, conciliación, representación en juicios<br>
• Horario: Lun-Vie 9:00-15:00`
  },
  {
    p: /infonavit|crédito hipotecario|subcuenta vivienda|puntos infonavit/i,
    r: () => `🏠 <strong>INFONAVIT:</strong><br><br>
• Consulta tu saldo: <code>infonavit.org.mx</code> → Mi Cuenta INFONAVIT<br>
• Crédito: requiere mínimo 116 puntos<br>
• <strong>Devolución subcuenta vivienda:</strong> si no usaste crédito, se suma a tu AFORE para la pensión (Ley 97)<br>
• Aclaraciones: 800-008-3900`
  },
  {
    p: /aguinaldo|cuánto (me toca|debo recibir) de aguinaldo|no (me pagaron|recibí) (el )?aguinaldo/i,
    r: () => `🎄 <strong>Aguinaldo — Art. 87 LFT:</strong><br><br>
• Mínimo <strong>15 días de salario</strong> anuales<br>
• Fecha límite de pago: <strong>20 de diciembre</strong><br>
• Si llevas menos de un año: proporcional a días trabajados<br>
• Si no te pagaron: reclamar ante PROFEDET o Tribunal Laboral<br>
• Se incluye en el cálculo de liquidación`
  },
  {
    p: /incapacidad (médica|del imss|por enfermedad)|accidente de trabajo|riesgo de trabajo/i,
    r: () => `🏥 <strong>Incapacidades — IMSS:</strong><br><br>
<strong>Enfermedad general:</strong> IMSS paga 60% del salario desde el 4er día (requiere 4 semanas cotizadas)<br>
<strong>Accidente de trabajo:</strong> IMSS paga 100% desde el 1er día (sin semanas mínimas)<br>
<strong>Incapacidad permanente:</strong> puede derivar en pensión de invalidez<br><br>
Documenta todo: fechas, testigos, atención médica recibida.`
  },
  {
    p: /dif\b|desarrollo.*familia|apoyo.*dif|pensión.*adulto.*mayor|65.*más|bienestar/i,
    r: () => `👴 <strong>Programas para Adultos Mayores:</strong><br><br>
<strong>Pensión para el Bienestar (65+):</strong> para personas sin pensión IMSS/ISSSTE<br>
Registro: módulos Bienestar o <code>bienestar.gob.mx</code><br><br>
<strong>DIF:</strong> apoyos en especie, medicamentos, prótesis<br>
Línea DIF: <strong>800-290-0024</strong><br>
DIF Ecatepec: presidencia municipal`
  },
  {
    p: /seguro de desempleo|quedé sin trabajo|perdí (el )?trabajo|desempleado|buscando empleo/i,
    r: () => `💼 <strong>Opciones si perdiste el trabajo:</strong><br><br>
1. <strong>Subcuenta de desempleo (AFORE):</strong> con 3+ años cotizados puedes retirar el 30% de tu cuenta (requiere 46 días sin trabajo)<br>
2. <strong>PROFEDET:</strong> gestiona tu liquidación si fue despido (gratuito)<br>
3. <strong>Bolsa trabajo oficial:</strong> <code>empleo.gob.mx</code><br>
4. Mantén cotizando <strong>voluntariamente</strong> (Modalidad 10) para no perder semanas`
  },
  {
    p: /modalidad 10|cotización voluntaria|seguir cotizando sin trabajo|asegurado voluntario/i,
    r: () => `📋 <strong>Modalidad 10 — Cotización Voluntaria:</strong><br><br>
Permite acumular semanas aunque no tengas patrón.<br>
• Pagas cuota mensual directamente al IMSS<br>
• Cotizas sobre tu último salario base<br>
• Cubre: enfermedad, maternidad, invalidez y vida<br>
• Requisito: haber sido trabajador asegurado previamente<br>
• Trámite: Subdelegación IMSS o <code>imss.gob.mx</code>`
  },
  {
    p: /negaron (la )?pensión|rechazaron (mi )?(pensión|solicitud)|resolución desfavorable/i,
    r: () => `📄 <strong>Si el IMSS negó tu solicitud:</strong><br><br>
1. Exige la <strong>resolución por escrito</strong> (Art. 296 LSS)<br>
2. Tienes <strong>15 días hábiles</strong> para el Recurso de Inconformidad (Art. 294 LSS)<br>
3. Si el recurso es negado: <strong>Amparo Indirecto</strong> ante Juez de Distrito<br>
4. Alternativa: demandar ante el <strong>TFJA</strong><br><br>
👉 Usa <strong>Pensión → Cartas</strong> para generar el Recurso de Inconformidad automáticamente.`
  },

  /* ══ EXPORTAR Y HERRAMIENTAS MAER ══ */
  {
    p: /exportar (el )?chat|guardar (la )?conversación|descargar (el )?historial/i,
    r: () => { MAER.exportar?.chatTXT(); return `📥 Exportando historial de chat como TXT...`; }
  },
  {
    p: /exportar (la )?carta|imprimir (la )?carta|carta a pdf|carta.*pdf/i,
    r: () => { MAER.exportar?.cartaPDF(); return `🖨️ Abriendo carta para imprimir o guardar como PDF...`; }
  },
  {
    p: /hacer (un )?respaldo|backup.*maer|guardar todo/i,
    r: () => { MAER.exportar?.chatJSON(); return `💾 Generando backup completo...`; }
  },
  {
    p: /buscar en (los )?(documentos|aprendizajes|conocimiento) (que |lo que )?(aprendiste|tienes|guardaste)/i,
    r: (msg) => {
      const q = msg.replace(/buscar en (los )?(documentos|aprendizajes|conocimiento) (que |lo que )?(aprendiste|tienes|guardaste)/i,'').trim();
      if (q.length > 2) {
        MAER.exportar?.buscarEnAprendido(q).then(r => {
          if (r?.length) MAER.chat._addMsg('sys', `📚 Encontré ${r.length} doc(s) relevante(s) sobre "${q}".`);
        });
        return `🔍 Buscando "${q}" en documentos aprendidos...`;
      }
      return `Escribe: "buscar en documentos [tema]" para buscar en tu conocimiento guardado.`;
    }
  },

  /* ══ TASKER / ANDROID ══ */
  {
    p: /tasker|autoremote|android.*maer|maer.*android|celular.*maer/i,
    r: () => `📱 <strong>Conectar tu Android con MAER:</strong><br><br>
Ya está configurado el endpoint. Solo necesitas:<br><br>
<strong>En tu Android con AutoRemote:</strong><br>
1. Abre AutoRemote<br>
2. Copia tu URL de AutoRemote<br>
3. En MAER → Ajustes → "URL AutoRemote", pega esa URL<br><br>
<strong>Para recibir mensajes de Tasker en MAER:</strong><br>
• URL del servidor: <code>http://[IP-de-tu-Mac]:8765/api/tasker-receive</code><br>
• En Tasker: Acción HTTP POST con tu mensaje<br><br>
<strong>Para que MAER te mande notificaciones al celular:</strong><br>
• Configura AutoRemote con tu URL en la sección Ajustes → Tasker<br>
• MAER te mandará alertas de plazos legales importantes<br><br>
¿Quieres la guía completa de configuración?`
  },

  /* ══ SISTEMA / TÉCNICO ══ */
  {
    p: /no (funciona|carga|abre|responde)|error|fallo|problema (con|en|del)/i,
    r: () => `🔧 Reportando el problema. Dime exactamente:<br>1. ¿Qué intentabas hacer?<br>2. ¿Qué mensaje de error aparece?<br>Puedes también revisar la pestaña <strong>Sistema</strong> para ver el estado del servidor.`
  },
  {
    p: /cómo (usar|funciona|utilizo) (el )?chat|cómo hablo (con|a) maer/i,
    r: () => `💬 <strong>Cómo usar el chat:</strong><br>• Escribe tu pregunta y presiona Enter o el botón Enviar<br>• Haz clic en el 🎤 para hablar con tu voz<br>• Adjunta un archivo con el botón "Adjuntar archivo"<br>• Cambia el modo (General, Pensión, Legal) según tu necesidad`
  },
  {
    p: /cuánto (cuesta|cobra)|es gratis|precio|pagar por maer/i,
    r: () => `🆓 MAER es completamente tuyo. Sin pagos, sin suscripciones, sin datos enviados a terceros. Todo corre en tu Mac, localmente.`
  },
  {
    p: /mi (ip|dirección ip)|ip (del servidor|de la mac|local)|ip.*mac/i,
    r: () => `🌐 Para encontrar la IP de tu Mac:<br>1. Menú Apple → Preferencias → Red<br>2. O abre Terminal y escribe: <code>ipconfig getifaddr en0</code><br><br>Necesitas esta IP para conectar Tasker desde tu Android.`
  },

  /* ══ FALLBACK INTELIGENTE ══ */
  {
    p: /.+/,
    r: (msg) => {
      const m = msg.toLowerCase();
      if (m.includes('imss') || m.includes('seguro social')) return `Entiendo tu pregunta sobre el IMSS. ¿Puedes darme más detalles? Por ejemplo: ¿es sobre trámite de pensión, consulta de semanas, un problema específico con el IMSS? Así puedo darte información más precisa.`;
      if (m.includes('legal') || m.includes('ley') || m.includes('artículo')) return `Para orientación legal específica, usa la pestaña <strong>Tareas IA → Investigación Legal</strong> donde puedo hacer un análisis más profundo de tu caso.`;
      if (m.includes('archivo') || m.includes('documento')) return `Para trabajar con archivos, usa las pestañas <strong>Archivos</strong>, <strong>Imágenes</strong> o <strong>Búsqueda</strong>. ¿Qué tipo de archivo necesitas analizar?`;
      if (MAER.config.backendOK) return `Procesando tu consulta con el motor de IA... Puedes también hacer esta pregunta más específica o usar la pestaña <strong>Tareas IA</strong> para análisis profundos.`;
      return `Entendido. Para respuestas más detalladas sobre este tema, asegúrate de que el servidor MAER esté corriendo. ¿Puedes reformular tu pregunta o darme más contexto?`;
    }
  }
];

/* Función de búsqueda en el diccionario */
/* Normaliza texto quitando acentos para búsquedas tolerantes */
window.MAER_normalizar = function(txt) {
  return txt.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

window.MAER_buscarRespuesta = function(msg) {
  // Probar primero con el mensaje original (respeta patrones exactos con acentos)
  // Luego con versión normalizada (sin acentos) para tolerancia de escritura
  const msgNorm = MAER_normalizar(msg);
  for (const entrada of MAER_DICCIONARIO) {
    if (entrada.p.test(msg) || entrada.p.test(msgNorm)) {
      const resp = typeof entrada.r === 'function' ? entrada.r(msg) : entrada.r;
      return resp;
    }
  }
  return null;
};
