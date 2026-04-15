/* ══════════════════════════════════════════════════════════
   MAER 4.0 — Suite de Pruebas Automáticas
   Pega esto en la consola del navegador (F12 → Console)
   o abre http://localhost:8765/static/js/maer.test.js
══════════════════════════════════════════════════════════ */

(async function MAER_TEST_SUITE() {
  const resultados = [];
  let pass = 0, fail = 0;

  const ok  = (nombre, detalle='') => { pass++; resultados.push({ok:true,  nombre, detalle}); };
  const err = (nombre, detalle='') => { fail++; resultados.push({ok:false, nombre, detalle}); };

  console.log('%c🦁 MAER 4.0 — SUITE DE PRUEBAS INICIADA', 'color:#38bdf8;font-size:16px;font-weight:bold');
  console.log('%c' + '═'.repeat(55), 'color:#38bdf8');

  // Activar voz para pruebas (simula gesto del usuario)
  if (MAER.voz) MAER.voz.userActivated = true;

  // ══════════════════════════════════
  // BLOQUE 1: MÓDULOS CARGADOS
  // ══════════════════════════════════
  console.log('\n%c📦 BLOQUE 1: Módulos JS', 'color:#fbbf24;font-weight:bold');

  const modulos = [
    ['MAER (core)',        () => typeof MAER === 'object'],
    ['MAER.config',        () => typeof MAER.config === 'object'],
    ['MAER.tabs',          () => typeof MAER.tabs?.show === 'function'],
    ['MAER.voz',           () => typeof MAER.voz?.hablar === 'function'],
    ['MAER.chat',          () => typeof MAER.chat?.send === 'function'],
    ['MAER.aprendizaje',   () => typeof MAER.aprendizaje?.guardar === 'function'],
    ['MAER.archivos',      () => typeof MAER.archivos?.handleInputFiles === 'function'],
    ['MAER.busqueda',      () => typeof MAER.busqueda?.ejecutar === 'function'],
    ['MAER.organizar',     () => typeof MAER.organizar?.analizar === 'function'],
    ['MAER.imagenes',      () => typeof MAER.imagenes?.handleImagen === 'function'],
    ['MAER.pension',       () => typeof MAER.pension?.generarCarta === 'function'],
    ['MAER.tareas',        () => typeof MAER.tareas?.ejecutar === 'function'],
    ['MAER.memoria',       () => typeof MAER.memoria?._render === 'function'],
    ['MAER.sistema',       () => typeof MAER.sistema?.refresh === 'function'],
    ['MAER.guardian',      () => typeof MAER.guardian?.verificar === 'function'],
    ['MAER.whatsapp',      () => typeof MAER.whatsapp?.importar === 'function'],
    ['MAER.notificaciones',() => typeof MAER.notificaciones?.init === 'function'],
    ['MAER.exportar',      () => typeof MAER.exportar?.chatTXT === 'function'],
    ['MAER.ajustes',       () => typeof MAER.ajustes?.init === 'function'],
    ['MAER.timeline',      () => typeof MAER.timeline?.marcar === 'function'],
    ['MAER.recordatorios', () => typeof MAER.recordatorios?.agregar === 'function'],
    ['MAER.cartasHistorial',() => typeof MAER.cartasHistorial?.guardar === 'function'],
    ['MAER.sugerencias',   () => typeof MAER.sugerencias?.buscar === 'function'],
    ['MAER.atajos',        () => typeof MAER.atajos?.registrar === 'function'],
    ['MAER.etiquetas',     () => typeof MAER.etiquetas?.asignar === 'function'],
    ['MAER_DICCIONARIO',   () => Array.isArray(MAER_DICCIONARIO) && MAER_DICCIONARIO.length >= 50],
    ['MAER_buscarRespuesta',() => typeof MAER_buscarRespuesta === 'function'],
    ['MAER_normalizar',    () => typeof MAER_normalizar === 'function'],
  ];

  for (const [nombre, fn] of modulos) {
    try {
      if (fn()) { ok(nombre); console.log(`  ✅ ${nombre}`); }
      else { err(nombre, 'retorna false/undefined'); console.log(`  ❌ ${nombre}`); }
    } catch(e) { err(nombre, e.message); console.log(`  ❌ ${nombre}: ${e.message}`); }
  }

  // ══════════════════════════════════
  // BLOQUE 2: HTML — PESTAÑAS Y ELEMENTOS
  // ══════════════════════════════════
  console.log('\n%c🖥️  BLOQUE 2: Pestañas y Elementos HTML', 'color:#fbbf24;font-weight:bold');

  const tabs = ['chat','archivos','imagenes','busqueda','organizar','aprendizaje','pension','tareas','memoria','sistema','whatsapp','ajustes'];
  for (const tab of tabs) {
    const el = document.getElementById(`panel-${tab}`);
    if (el) { ok(`Panel #panel-${tab}`); console.log(`  ✅ panel-${tab}`); }
    else    { err(`Panel #panel-${tab}`, 'no existe en DOM'); console.log(`  ❌ panel-${tab} — NO ENCONTRADO`); }
  }

  // IDs críticos
  const ids_criticos = [
    'chat-msgs','chat-input','voice-btn','drop-zone',
    'carta-texto','carta-tipo','pension-notas',
    'eventos-lista','tarea-resultado','idb-busq','idb-resultados',
    'sys-console','guardian-reporte','tasker-badge',
    'aprendizaje-lista','learn-count'
  ];
  console.log('\n  IDs críticos:');
  for (const id of ids_criticos) {
    const el = document.getElementById(id);
    if (el) { ok(`ID #${id}`); console.log(`  ✅ #${id}`); }
    else    { err(`ID #${id}`, 'no existe'); console.log(`  ❌ #${id} — NO ENCONTRADO`); }
  }

  // ══════════════════════════════════
  // BLOQUE 3: NAVEGACIÓN DE PESTAÑAS
  // ══════════════════════════════════
  console.log('\n%c🗂️  BLOQUE 3: Navegación de pestañas', 'color:#fbbf24;font-weight:bold');

  for (const tab of tabs) {
    try {
      MAER.tabs.show(tab);
      const panel = document.getElementById(`panel-${tab}`);
      if (panel?.classList.contains('active')) {
        ok(`Tab ${tab} activa`); console.log(`  ✅ Tab "${tab}" abre correctamente`);
      } else {
        err(`Tab ${tab} no activa`); console.log(`  ❌ Tab "${tab}" no se activó`);
      }
    } catch(e) { err(`Tab ${tab}`, e.message); console.log(`  ❌ Tab "${tab}": ${e.message}`); }
    await new Promise(r => setTimeout(r, 80));
  }
  // Volver a chat
  MAER.tabs.show('chat');

  // ══════════════════════════════════
  // BLOQUE 4: DICCIONARIO — RESPUESTAS
  // ══════════════════════════════════
  console.log('\n%c🧠 BLOQUE 4: Diccionario de conocimiento', 'color:#fbbf24;font-weight:bold');

  const preguntas = [
    ['hola',                        true,  'saludo'],
    ['cuantas semanas necesito',     true,  'pensión sin acento'],
    ['cuántas semanas necesito',     true,  'pensión con acento'],
    ['recurso de inconformidad',     true,  'recurso legal'],
    ['jubilacion imss',              true,  'jubilación sin acento'],
    ['profedet telefono',            true,  'PROFEDET'],
    ['aguinaldo cuando pagan',       true,  'aguinaldo'],
    ['infonavit credito',            true,  'INFONAVIT'],
    ['exportar chat',                true,  'comando exportar'],
    ['blablabla xyz 999',            true,  'fallback genérico (/.+/ catch-all)'],
  ];

  for (const [msg, debeResponder, descripcion] of preguntas) {
    try {
      const resp = MAER_buscarRespuesta(msg);
      const respondio = resp !== null && resp !== undefined;
      if (respondio === debeResponder) {
        ok(`Diccionario: "${descripcion}"`);
        console.log(`  ✅ "${msg}" → ${respondio ? resp.substring(0,50).replace(/<[^>]+>/g,'')+'...' : 'null (correcto)'}`);
      } else {
        err(`Diccionario: "${descripcion}"`, respondio ? 'respondió cuando no debía' : 'no respondió');
        console.log(`  ❌ "${msg}" → esperado=${debeResponder}, obtenido=${respondio}`);
      }
    } catch(e) { err(`Diccionario: ${msg}`, e.message); }
  }

  // ══════════════════════════════════
  // BLOQUE 5: INDEXEDDB
  // ══════════════════════════════════
  console.log('\n%c💾 BLOQUE 5: IndexedDB (Memoria Permanente)', 'color:#fbbf24;font-weight:bold');

  try {
    await MAER.aprendizaje.initDB();
    ok('IndexedDB init');
    console.log('  ✅ IndexedDB inicializada correctamente');

    // Guardar algo
    await MAER.aprendizaje.guardar({ nombre: 'test_auditoria', texto: 'Texto de prueba para auditoría MAER 4.0', tipo: 'test' });
    ok('IndexedDB guardar');
    console.log('  ✅ Guardado en IndexedDB');

    // Buscar lo que guardamos
    const r = await MAER.aprendizaje.buscarEnConocimiento('auditoria');
    if (r) { ok('IndexedDB buscar'); console.log(`  ✅ Búsqueda en IDB: "${r.substring(0,60)}..."`); }
    else   { err('IndexedDB buscar', 'no encontró el texto guardado'); console.log('  ❌ Búsqueda en IDB no encontró el texto'); }
  } catch(e) {
    err('IndexedDB', e.message);
    console.log('  ❌ IndexedDB error:', e.message);
  }

  // ══════════════════════════════════
  // BLOQUE 6: VOZ
  // ══════════════════════════════════
  console.log('\n%c🎤 BLOQUE 6: Sistema de Voz', 'color:#fbbf24;font-weight:bold');

  const vozDisp = 'speechSynthesis' in window;
  if (vozDisp) { ok('SpeechSynthesis disponible'); console.log('  ✅ Web Speech API disponible'); }
  else { err('SpeechSynthesis', 'no disponible en este navegador'); console.log('  ❌ SpeechSynthesis no disponible'); }

  const vozInit = MAER.voz?.synth !== undefined || MAER.voz?.hablar !== undefined;
  if (vozInit) { ok('MAER.voz inicializada'); console.log('  ✅ Módulo de voz cargado'); }
  else { err('MAER.voz no inicializada'); }

  const pitch = MAER.config.vozPitch;
  const rate  = MAER.config.vozRate;
  if (pitch === 0.62 && rate === 0.93) {
    ok(`Voz grave correcta (pitch=${pitch}, rate=${rate})`);
    console.log(`  ✅ Configuración de voz grave: pitch=${pitch}, rate=${rate}`);
  } else {
    err(`Voz config`, `pitch=${pitch} (esp. 0.62), rate=${rate} (esp. 0.93)`);
    console.log(`  ⚠️  Voz: pitch=${pitch} rate=${rate} (esperado 0.62/0.93)`);
  }

  // ══════════════════════════════════
  // BLOQUE 7: PENSION — CARTAS
  // ══════════════════════════════════
  console.log('\n%c🏛️  BLOQUE 7: Asistente Pensión IMSS', 'color:#fbbf24;font-weight:bold');

  try {
    MAER.tabs.show('pension');
    await new Promise(r => setTimeout(r, 200));

    // Probar generación de carta
    const nombre = document.getElementById('carta-nombre');
    const nss    = document.getElementById('carta-nss');
    const tipo   = document.getElementById('carta-tipo');
    const texto  = document.getElementById('carta-texto');

    if (nombre && nss && tipo) {
      nombre.value = 'Leonel Houssen Mojica';
      nss.value    = '12345678901';
      tipo.value   = 'semanas';
      MAER.pension.generarCarta();
      await new Promise(r => setTimeout(r, 300));
      if (texto?.textContent?.length > 50) {
        ok('Generar carta IMSS'); console.log(`  ✅ Carta generada: "${texto.textContent.substring(0,80)}..."`);
      } else {
        err('Generar carta IMSS', 'texto vacío');
        console.log('  ❌ Carta no generada o vacía');
      }
    } else {
      err('Campos de carta no encontrados');
      console.log('  ❌ Campos del formulario de carta no encontrados');
    }
  } catch(e) { err('Pensión cartas', e.message); console.log('  ❌ Error en cartas:', e.message); }

  // ══════════════════════════════════
  // BLOQUE 8: CHAT — SIMULACIÓN 5 MINUTOS
  // ══════════════════════════════════
  console.log('\n%c💬 BLOQUE 8: Chat — Simulación de conversación', 'color:#fbbf24;font-weight:bold');

  MAER.tabs.show('chat');
  await new Promise(r => setTimeout(r, 200));

  const conversacion = [
    'hola MAER',
    'cuantas semanas necesito para pensionarme',
    'que es el recurso de inconformidad',
    'dame el telefono de profedet',
    'cuando me pagan el aguinaldo',
    'que documentos necesito para mi pension',
    'que es la modalidad 10',
    'como busco mis semanas cotizadas en imss digital',
    'puedes exportar nuestro chat',
    'como estas MAER',
  ];

  let respuestasOk = 0;
  const msgsEl = document.getElementById('chat-msgs');
  const inputEl = document.getElementById('chat-input');

  for (const pregunta of conversacion) {
    try {
      const prevMsgs = msgsEl?.children.length || 0;
      if (inputEl) {
        inputEl.value = pregunta;
        await MAER.chat.send();
        await new Promise(r => setTimeout(r, 400));
        const newMsgs = msgsEl?.children.length || 0;
        if (newMsgs > prevMsgs) {
          respuestasOk++;
          const lastMsg = msgsEl?.lastElementChild?.textContent?.replace(/<[^>]+>/g,'')?.substring(0,80) || '';
          console.log(`  ✅ P: "${pregunta.substring(0,35)}" → R: "${lastMsg}..."`);
        } else {
          console.log(`  ❌ P: "${pregunta}" → sin respuesta`);
        }
      }
    } catch(e) { console.log(`  ❌ "${pregunta}": ${e.message}`); }
    await new Promise(r => setTimeout(r, 200));
  }

  const chatScore = (respuestasOk / conversacion.length * 100).toFixed(0);
  if (respuestasOk >= 8) { ok(`Chat respondió ${respuestasOk}/${conversacion.length} (${chatScore}%)`); }
  else { err(`Chat solo respondió ${respuestasOk}/${conversacion.length}`); }
  console.log(`\n  📊 Chat respondió ${respuestasOk}/${conversacion.length} preguntas (${chatScore}%)`);

  // ══════════════════════════════════
  // BLOQUE 9: CONSOLA — ERRORES
  // ══════════════════════════════════
  console.log('\n%c🔍 BLOQUE 9: Verificación del Guardián', 'color:#fbbf24;font-weight:bold');

  try {
    MAER.tabs.show('sistema');
    await new Promise(r => setTimeout(r, 300));
    // Activar guardián
    MAER.tabs.show('sistema');
    const btnGuardian = document.querySelector('[onclick*="guardian.verificar"]');
    if (btnGuardian) {
      btnGuardian.click();
      await new Promise(r => setTimeout(r, 800));
    } else {
      // Llamar directamente
      await MAER.guardian.verificar();
      await new Promise(r => setTimeout(r, 800));
    }
    const reporte = document.getElementById('guardian-reporte');
    const tieneContenido = reporte?.innerHTML?.length > 100;
    if (tieneContenido) { ok('Guardian generó reporte'); console.log('  ✅ Guardian: reporte generado'); }
    else { err('Guardian sin reporte'); }
  } catch(e) { err('Guardian', e.message); console.log('  ❌ Guardian:', e.message); }

  MAER.tabs.show('chat');

  // ══════════════════════════════════
  // BLOQUE 10: NUEVOS MÓDULOS (Timeline, Recordatorios, Cartas)
  // ══════════════════════════════════
  console.log('\n%c📊 BLOQUE 10: Módulos Fase 1 (Timeline, Recordatorios, Cartas)', 'color:#fbbf24;font-weight:bold');

  // Timeline
  try {
    MAER.timeline.init();
    const actual = MAER.timeline.obtenerActual();
    if (actual && actual.id) {
      ok('Timeline inicializado'); console.log(`  ✅ Timeline: etapa actual = "${actual.label}"`);
    } else { err('Timeline init', 'no devuelve etapa'); }
  } catch(e) { err('Timeline', e.message); }

  try {
    const etapas = MAER.timeline.etapas;
    if (etapas.length === 8) {
      ok('Timeline 8 etapas'); console.log('  ✅ Timeline: 8 etapas definidas');
    } else { err('Timeline etapas', `esperado 8, obtenido ${etapas.length}`); }
  } catch(e) { err('Timeline etapas', e.message); }

  try {
    const panel = document.getElementById('timeline-panel');
    if (panel && panel.innerHTML.length > 50) {
      ok('Timeline render'); console.log('  ✅ Timeline: panel renderizado');
    } else { err('Timeline render', 'panel vacío'); }
  } catch(e) { err('Timeline render', e.message); }

  // Recordatorios
  try {
    MAER.recordatorios.init();
    const manana = new Date(); manana.setDate(manana.getDate() + 1);
    const rec = MAER.recordatorios.agregar('Test auditoría', manana.toISOString().split('T')[0], 1, 'Nota de prueba');
    if (rec && rec.id) {
      ok('Recordatorios agregar'); console.log(`  ✅ Recordatorio creado: id=${rec.id}`);
    } else { err('Recordatorios agregar', 'no devolvió objeto'); }
  } catch(e) { err('Recordatorios', e.message); }

  try {
    const lista = MAER.recordatorios.listar();
    if (lista.length > 0) {
      ok('Recordatorios listar'); console.log(`  ✅ Recordatorios: ${lista.length} en lista`);
    } else { err('Recordatorios listar', 'lista vacía'); }
    // Limpiar test
    lista.filter(r => r.titulo === 'Test auditoría').forEach(r => {
      MAER.recordatorios.datos = MAER.recordatorios.datos.filter(x => x.id !== r.id);
    });
    MAER.recordatorios._guardar();
  } catch(e) { err('Recordatorios listar', e.message); }

  // Historial de cartas
  try {
    const carta = MAER.cartasHistorial.guardar('semanas', 'Test Auditor', '00000000000', 'Contenido de prueba para auditoría.');
    if (carta && carta.id) {
      ok('Cartas guardar'); console.log(`  ✅ Carta guardada: id=${carta.id}`);
    } else { err('Cartas guardar', 'no devolvió objeto'); }
  } catch(e) { err('Cartas guardar', e.message); }

  try {
    const cartas = MAER.cartasHistorial.listar();
    if (cartas.length > 0) {
      ok('Cartas listar'); console.log(`  ✅ Cartas: ${cartas.length} en historial`);
    } else { err('Cartas listar', 'historial vacío'); }
    // Limpiar test
    cartas.filter(c => c.nombre === 'Test Auditor').forEach(c => {
      MAER.cartasHistorial.datos = MAER.cartasHistorial.datos.filter(x => x.id !== c.id);
    });
    MAER.cartasHistorial._guardar();
  } catch(e) { err('Cartas listar', e.message); }

  // ══════════════════════════════════
  // BLOQUE 11: MÓDULOS FASE 2 (Sugerencias, Atajos, Etiquetas)
  // ══════════════════════════════════
  console.log('\n%c🔧 BLOQUE 11: Módulos Fase 2 (Sugerencias, Atajos, Etiquetas)', 'color:#fbbf24;font-weight:bold');

  // Sugerencias
  try {
    const res = MAER.sugerencias.buscar('pension');
    if (Array.isArray(res) && res.length > 0) {
      ok('Sugerencias buscar'); console.log(`  ✅ Sugerencias: ${res.length} resultados para "pension"`);
    } else { err('Sugerencias buscar', 'sin resultados'); }
  } catch(e) { err('Sugerencias', e.message); }

  try {
    const res2 = MAER.sugerencias.buscar('semanas cotizadas');
    if (res2.some(r => r.texto.includes('semanas'))) {
      ok('Sugerencias multi-palabra'); console.log('  ✅ Sugerencias: búsqueda multi-palabra OK');
    } else { err('Sugerencias multi-palabra', 'no encontró "semanas"'); }
  } catch(e) { err('Sugerencias multi', e.message); }

  try {
    if (MAER.sugerencias.catalogo.length >= 15) {
      ok('Sugerencias catálogo'); console.log(`  ✅ Sugerencias: ${MAER.sugerencias.catalogo.length} en catálogo`);
    } else { err('Sugerencias catálogo', 'menos de 15'); }
  } catch(e) { err('Sugerencias catalogo', e.message); }

  // Atajos
  try {
    const lista = MAER.atajos.listar();
    if (lista.length >= 10) {
      ok('Atajos registrados'); console.log(`  ✅ Atajos: ${lista.length} registrados`);
    } else { err('Atajos registrados', `solo ${lista.length}`); }
  } catch(e) { err('Atajos', e.message); }

  try {
    let ejecutado = false;
    MAER.atajos.registrar('ctrl+shift+t', 'Test atajo', () => { ejecutado = true; });
    // Verificar que se registró
    const tiene = MAER.atajos.listar().some(a => a.combo === 'ctrl+shift+t');
    if (tiene) {
      ok('Atajos registrar'); console.log('  ✅ Atajos: registro personalizado OK');
    } else { err('Atajos registrar', 'no se encontró'); }
    // Limpiar
    delete MAER.atajos.mapa[MAER.atajos._normalizar('ctrl+shift+t')];
  } catch(e) { err('Atajos registrar', e.message); }

  try {
    if (typeof MAER.atajos.mostrarAyuda === 'function' && typeof MAER.atajos.ocultarAyuda === 'function') {
      ok('Atajos panel ayuda'); console.log('  ✅ Atajos: panel de ayuda disponible');
    } else { err('Atajos ayuda', 'funciones faltantes'); }
  } catch(e) { err('Atajos ayuda', e.message); }

  // Etiquetas
  try {
    MAER.etiquetas.asignar('test_doc.pdf', 'IMSS');
    MAER.etiquetas.asignar('test_doc.pdf', 'Urgente');
    const tags = MAER.etiquetas.obtener('test_doc.pdf');
    if (tags.includes('IMSS') && tags.includes('Urgente')) {
      ok('Etiquetas asignar'); console.log(`  ✅ Etiquetas: asignadas ${tags.length} a test_doc.pdf`);
    } else { err('Etiquetas asignar', 'tags faltantes'); }
  } catch(e) { err('Etiquetas', e.message); }

  try {
    const docs = MAER.etiquetas.buscarPorEtiqueta('IMSS');
    if (docs.includes('test_doc.pdf')) {
      ok('Etiquetas buscar'); console.log('  ✅ Etiquetas: búsqueda por etiqueta OK');
    } else { err('Etiquetas buscar', 'no encontró doc'); }
  } catch(e) { err('Etiquetas buscar', e.message); }

  try {
    MAER.etiquetas.quitar('test_doc.pdf', 'Urgente');
    const tags2 = MAER.etiquetas.obtener('test_doc.pdf');
    if (!tags2.includes('Urgente') && tags2.includes('IMSS')) {
      ok('Etiquetas quitar'); console.log('  ✅ Etiquetas: quitar etiqueta OK');
    } else { err('Etiquetas quitar', 'no se eliminó'); }
    // Limpiar
    MAER.etiquetas.quitar('test_doc.pdf', 'IMSS');
    MAER.etiquetas._guardar();
  } catch(e) { err('Etiquetas quitar', e.message); }

  try {
    if (MAER.etiquetas.PREDEFINIDAS.length >= 10) {
      ok('Etiquetas predefinidas'); console.log(`  ✅ Etiquetas: ${MAER.etiquetas.PREDEFINIDAS.length} predefinidas`);
    } else { err('Etiquetas predefinidas', 'menos de 10'); }
  } catch(e) { err('Etiquetas predefinidas', e.message); }

  // ══════════════════════════════════
  // REPORTE FINAL
  // ══════════════════════════════════
  const total = pass + fail;
  const pct   = (pass / total * 100).toFixed(1);

  console.log('\n' + '%c' + '═'.repeat(55), 'color:#38bdf8');
  console.log('%c🦁 REPORTE FINAL DE AUDITORÍA MAER 4.0', 'color:#38bdf8;font-size:15px;font-weight:bold');
  console.log('%c' + '═'.repeat(55), 'color:#38bdf8');

  resultados.forEach(r => {
    const icon  = r.ok ? '✅' : '❌';
    const color = r.ok ? 'color:#34d399' : 'color:#f87171';
    console.log(`%c${icon} ${r.nombre}${r.detalle ? ' — '+r.detalle : ''}`, color);
  });

  const color_total = fail === 0 ? 'color:#34d399;font-size:14px;font-weight:bold' : 'color:#fbbf24;font-size:14px;font-weight:bold';
  console.log('\n%c' + `📊 RESULTADO: ${pass}/${total} pruebas pasadas (${pct}%)`, color_total);

  if (fail === 0) {
    console.log('%c✨ MAER 4.0 está en perfectas condiciones. Todo funciona.', 'color:#34d399;font-size:13px');
    MAER.voz?.hablar(`Auditoría completada. ${pass} pruebas pasadas. MAER en perfectas condiciones.`);
  } else {
    console.log(`%c⚠️  ${fail} prueba(s) fallaron. Revisar arriba para detalles.`, 'color:#fbbf24;font-size:13px');
    MAER.voz?.hablar(`Auditoría completada. ${pass} de ${total} pruebas pasadas. ${fail} requieren atención.`);
  }

  // Mostrar también en el chat
  const resumenChat = `🧪 <strong>Auditoría automática completada</strong><br>
✅ Pasadas: <strong>${pass}</strong> | ❌ Fallidas: <strong>${fail}</strong> | 📊 Score: <strong>${pct}%</strong><br>
<em>Abre la consola (F12 → Console) para ver el reporte detallado.</em>`;
  MAER.chat._addMsg('maer', resumenChat);

  return { pass, fail, total, score: pct, resultados };
})();
