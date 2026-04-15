# PLAN DE TRABAJO — MAER 4.0
## De MAER 3.1 (81/81 estable) a MAER 4.0 (Sistema Completo)
### Leonel Houssen Mojica — Ecatepec MX — Abril 2026

---

## ESTADO ACTUAL (Base de partida)

| Aspecto | Estado |
|---------|--------|
| Pruebas automatizadas | 81/81 (100%) |
| Módulos JS | 19 archivos |
| Servidor Python | FastAPI + 29 endpoints |
| Warnings Chrome | 0 |
| Backups | 3 (Bloque 6, Auditoría, 81/81) |

---

## BLOQUES DE TRABAJO

### BLOQUE 7 — Timeline Visual del Proceso de Pensión
**Carpeta:** `static/js/maer.timeline.js` + componentes en `index.html`
**Prioridad:** ALTA (valor inmediato para el proceso legal)
**Dependencias:** Ninguna

**Qué hace:**
Panel gráfico con las etapas del proceso de pensión IMSS. Leonel marca manualmente en qué etapa está y MAER lo recuerda (localStorage). Cada etapa tiene fecha de inicio, estado, y notas.

**Etapas del timeline:**
1. Reunión de documentos
2. Pre-revisión en IMSS Digital
3. Solicitud presentada en ventanilla
4. En revisión por IMSS
5. Resolución (aprobada / negada)
6. Recurso de inconformidad (si aplica)
7. Amparo / PROFEDET (si aplica)
8. Pensión otorgada

**Tareas:**
- Crear `maer.timeline.js` — lógica de etapas, guardado en localStorage, fechas
- Agregar panel visual en pestaña Pensión (barra horizontal con iconos por etapa)
- Botón "Marcar etapa actual" + notas por etapa
- Integrar con eventos de pensión (auto-sugerir eventos según etapa)
- Agregar al guardián (módulo #19)
- Pruebas: 5 tests nuevos

---

### BLOQUE 8 — Autocompletado / Sugerencias en el Chat
**Carpeta:** `static/js/maer.sugerencias.js` + CSS
**Prioridad:** ALTA (mejora la experiencia diaria)
**Dependencias:** maer.diccionario.js

**Qué hace:**
Mientras Leonel escribe en el chat, aparecen 2-3 sugerencias debajo del input basadas en los patrones del diccionario. Click o Enter en una sugerencia la envía directo.

**Tareas:**
- Crear `maer.sugerencias.js` — buscador en tiempo real sobre MAER_DICCIONARIO
- Crear contenedor HTML de sugerencias debajo del chat-input
- CSS para dropdown de sugerencias (posición absoluta, sombra, hover)
- Lógica: filtrar patrones que contengan las palabras que va escribiendo
- Máximo 3 sugerencias visibles
- Navegación con flechas arriba/abajo + Enter para seleccionar
- Agregar al guardián (módulo #20)
- Pruebas: 4 tests nuevos

---

### BLOQUE 9 — Recordatorios con Fecha Límite
**Carpeta:** `static/js/maer.recordatorios.js`
**Prioridad:** ALTA (crítico para el proceso de pensión)
**Dependencias:** maer.notificaciones.js, maer.pension.js

**Qué hace:**
Al agregar un evento de pensión, Leonel puede marcar "avísame X días antes". MAER guarda estos recordatorios en localStorage y los verifica cada vez que se abre la app. Si ya pasó la fecha de aviso, muestra notificación inmediata.

**Tareas:**
- Crear `maer.recordatorios.js` — CRUD de recordatorios con fecha destino y días de anticipación
- Modificar formulario de eventos en Pensión: agregar campo "avisar X días antes"
- Verificación al iniciar MAER: recorrer recordatorios y disparar los vencidos
- Notificación visual (badge en pestaña Pensión) + voz si está activa
- Integrar con Tasker (endpoint `/api/recordatorios-pendientes`) para alertas en celular
- Agregar al guardián (módulo #21)
- Pruebas: 5 tests nuevos

---

### BLOQUE 10 — Historial de Versiones de Cartas
**Carpeta:** `static/js/maer.cartas-historial.js`
**Prioridad:** MEDIA
**Dependencias:** maer.pension.js, IndexedDB

**Qué hace:**
Cada vez que se genera una carta (solicitud de pensión, recurso, amparo), MAER guarda una copia con fecha y tipo en IndexedDB. Leonel puede ver la lista, comparar, re-imprimir o eliminar versiones anteriores.

**Tareas:**
- Crear `maer.cartas-historial.js` — guardar/listar/eliminar cartas en IndexedDB (store separado: `maer_cartas`)
- Hook en `maer.pension.generarCarta()`: auto-guardar carta generada
- Panel visual en Pensión: lista de cartas guardadas con fecha, tipo, preview
- Botón "Comparar" que muestra 2 cartas lado a lado
- Botón "Re-imprimir" y "Eliminar"
- Agregar al guardián (módulo #22)
- Pruebas: 4 tests nuevos

---

### BLOQUE 11 — Modo Compacto (Tablet / Pantalla Pequeña)
**Carpeta:** `static/css/maer-compact.css` + toggle en `maer.ajustes.js`
**Prioridad:** MEDIA
**Dependencias:** maer.ajustes.js

**Qué hace:**
Un botón en Ajustes que activa el modo compacto: pestañas más pequeñas (iconos sin texto), paneles reducidos, fuente menor. Ideal para tablet o ventanas pequeñas. Se guarda en localStorage.

**Tareas:**
- Crear `maer-compact.css` — media queries + clase `.compact` en body
- Agregar toggle en Ajustes: "Modo compacto" on/off
- Reducir tabs a solo iconos cuando está activo
- Ajustar padding, font-size, margins
- Auto-detectar pantalla < 768px y sugerir modo compacto
- Pruebas: 2 tests nuevos

---

### BLOQUE 12 — Atajos de Teclado
**Carpeta:** `static/js/maer.atajos.js`
**Prioridad:** MEDIA
**Dependencias:** Todos los módulos (navega entre ellos)

**Qué hace:**
Combinaciones de teclado para acciones frecuentes sin tocar el mouse.

**Atajos planeados:**
| Atajo | Acción |
|-------|--------|
| `Ctrl+M` | Activar/desactivar micrófono |
| `Ctrl+K` | Ir al chat y enfocar input |
| `Ctrl+B` | Hacer respaldo |
| `Ctrl+E` | Exportar chat como TXT |
| `Ctrl+1..9` | Ir a pestaña 1-9 |
| `Ctrl+G` | Ejecutar guardián |
| `Escape` | Cerrar modales / volver al chat |

**Tareas:**
- Crear `maer.atajos.js` — listener global de keydown
- Registrar cada atajo con su acción
- Indicador visual breve (toast) al usar un atajo
- Panel de ayuda (`Ctrl+?`) que muestra todos los atajos
- No interferir con atajos del navegador
- Agregar al guardián (módulo #23)
- Pruebas: 3 tests nuevos

---

### BLOQUE 13 — Resumen Semanal Automático
**Carpeta:** `static/js/maer.resumen.js`
**Prioridad:** BAJA (nice-to-have)
**Dependencias:** maer.memoria.js, maer.aprendizaje.js, maer.pension.js

**Qué hace:**
Cada lunes (o al abrir MAER si no se ha generado esta semana), genera un resumen en el chat: documentos en memoria, eventos próximos, estadísticas de uso, cosas nuevas aprendidas.

**Tareas:**
- Crear `maer.resumen.js` — recopilar stats de todos los módulos
- Verificar en localStorage si ya se generó esta semana
- Insertar mensaje tipo "sys" en el chat con el resumen
- Formato visual atractivo (card con iconos y números)
- Agregar al guardián (módulo #24)
- Pruebas: 2 tests nuevos

---

### BLOQUE 14 — Etiquetas en Documentos Aprendidos
**Carpeta:** Modificación de `maer.aprendizaje.js` + UI
**Prioridad:** MEDIA
**Dependencias:** maer.aprendizaje.js, IndexedDB

**Qué hace:**
Al subir un archivo a Aprendizaje, Leonel puede agregarle etiquetas (ej: "IMSS", "NSS", "laboral", "personal"). Después puede filtrar por etiqueta en lugar de buscar por texto.

**Tareas:**
- Modificar `guardar()` para incluir campo `etiquetas: []`
- UI: campo de etiquetas al subir archivo (chips con X para borrar)
- Barra de filtrado por etiquetas en panel Aprendizaje
- Sugerir etiquetas automáticamente basado en contenido (si tiene "IMSS" → sugerir etiqueta "IMSS")
- Pruebas: 3 tests nuevos

---

### BLOQUE 15 — Código QR de Configuración
**Carpeta:** `static/js/maer.qr.js`
**Prioridad:** BAJA
**Dependencias:** maer.ajustes.js

**Qué hace:**
Exportar la configuración actual (tema, voz, servidor, atajos) como código QR. Escanear desde otro dispositivo para importar todo automáticamente.

**Tareas:**
- Integrar librería QR (qrcode.js vía CDN)
- Serializar config a JSON compacto → generar QR
- Botón en Ajustes: "Generar QR de configuración"
- En el otro dispositivo: cámara o upload de imagen → decodificar → aplicar config
- Pruebas: 2 tests nuevos

---

### BLOQUE 16 — Panel de Estadísticas de Uso
**Carpeta:** `static/js/maer.stats.js`
**Prioridad:** BAJA
**Dependencias:** maer.memoria.js, maer.chat.js

**Qué hace:**
Panel que muestra: preguntas esta semana, temas más consultados, documentos en memoria, tiempo de uso, gráfica de actividad por día.

**Tareas:**
- Crear `maer.stats.js` — recopilar datos de uso desde localStorage/IDB
- Crear pestaña o sub-panel en Sistema
- Gráfica simple (barras CSS, sin librerías externas)
- Top 5 temas consultados
- Contador de documentos aprendidos vs buscados
- Pruebas: 3 tests nuevos

---

### BLOQUE 17 — Conexión Tasker/AutoRemote ↔ MAER
**Carpeta:** `maer_backend/tasker/` + endpoints en `server.py`
**Prioridad:** ALTA (habilita el celular)
**Dependencias:** Server.py, red WiFi

**Qué hace:**
Endpoints HTTP para que Tasker envíe mensajes de WhatsApp a MAER, reciba respuestas, y ejecute acciones. Perfiles de Tasker pre-configurados.

**Tareas:**
- Crear endpoint `/api/tasker-receive` (recibir mensaje de WhatsApp vía Tasker)
- Crear endpoint `/api/tasker-respond` (MAER devuelve respuesta procesada)
- Crear endpoint `/api/recordatorios-pendientes` (Tasker consulta alertas)
- Crear `tasker/perfiles/` con XMLs de Tasker exportables
- Perfil: "Mensaje WhatsApp → enviar a MAER → recibir respuesta"
- Perfil: "Verificar recordatorios cada hora"
- Documentación paso a paso para instalar en Tasker
- Pruebas: 4 tests nuevos

---

### BLOQUE 18 — WhatsApp Business API (Número Propio de MAER)
**Carpeta:** `maer_backend/whatsapp/` + `maer.whatsapp.js` mejorado
**Prioridad:** MEDIA-ALTA (después de Tasker)
**Dependencias:** Bloque 17, cuenta Twilio

**Qué hace:**
MAER obtiene su propio número de WhatsApp. Leonel le escribe como a una persona y MAER responde con todo su conocimiento.

**Tareas:**
- Documentar registro en Twilio + número virtual
- Crear `maer_backend/whatsapp/webhook.py` — recibir mensajes de Twilio
- Crear `maer_backend/whatsapp/responder.py` — procesar con diccionario + IDB + LLM
- Endpoint webhook `/api/whatsapp-hook` para Twilio
- Configurar ngrok para acceso externo
- Panel de WhatsApp mejorado: ver conversaciones entrantes en tiempo real
- Documentación completa de setup
- Pruebas: 5 tests nuevos

---

## ORDEN DE IMPLEMENTACIÓN RECOMENDADO

| Fase | Bloques | Razón |
|------|---------|-------|
| **Fase 1 — Proceso Legal** | 7, 9, 10 | Timeline + Recordatorios + Historial de cartas. Lo más urgente para tu pensión. |
| **Fase 2 — Experiencia Diaria** | 8, 12, 14 | Sugerencias + Atajos + Etiquetas. Hacen MAER más rápido de usar. |
| **Fase 3 — Conectividad** | 17, 18 | Tasker + WhatsApp. MAER en tu celular. |
| **Fase 4 — Extras** | 11, 13, 15, 16 | Modo compacto + Resumen + QR + Stats. Mejoran pero no son urgentes. |

---

## ESTRUCTURA DE CARPETAS

```
mcp-maer-server/
├── maer_backend/
│   ├── web_ui/
│   │   ├── static/
│   │   │   ├── js/
│   │   │   │   ├── maer.timeline.js        ← BLOQUE 7
│   │   │   │   ├── maer.sugerencias.js     ← BLOQUE 8
│   │   │   │   ├── maer.recordatorios.js   ← BLOQUE 9
│   │   │   │   ├── maer.cartas-historial.js← BLOQUE 10
│   │   │   │   ├── maer.atajos.js          ← BLOQUE 12
│   │   │   │   ├── maer.resumen.js         ← BLOQUE 13
│   │   │   │   ├── maer.qr.js              ← BLOQUE 15
│   │   │   │   └── maer.stats.js           ← BLOQUE 16
│   │   │   ├── css/
│   │   │   │   ├── maer.css                (existente)
│   │   │   │   └── maer-compact.css        ← BLOQUE 11
│   │   │   └── index.html                  (se actualiza en cada bloque)
│   │   └── server.py                       (se actualiza en bloques 17, 18)
│   ├── tasker/                             ← BLOQUE 17
│   │   ├── perfiles/
│   │   │   ├── whatsapp_a_maer.xml
│   │   │   └── recordatorios_hourly.xml
│   │   └── README_TASKER.md
│   └── whatsapp/                           ← BLOQUE 18
│       ├── webhook.py
│       ├── responder.py
│       └── README_WHATSAPP.md
├── respaldo_maer/
│   ├── maer_backup_bloque6_20260401_223743.zip      ← Backup 1
│   ├── maer_backup_20260402_033442.zip              ← Backup 2
│   └── maer_backup_81de81_20260402_151146/          ← Backup 3
├── PLAN_TRABAJO_MAER_4.0.md               ← ESTE ARCHIVO
├── AUDITORIA_MAER_3.1.md
├── BITACORA.md
└── TASKER_GUIA.md
```

---

## MÉTRICAS DE ÉXITO

| Versión | Pruebas | Módulos | Features |
|---------|---------|---------|----------|
| MAER 3.1 (actual) | 81/81 | 19 JS | Base completa |
| MAER 3.5 (Fase 1) | ~96/96 | 22 JS | +Timeline +Recordatorios +Cartas |
| MAER 3.8 (Fase 2) | ~109/109 | 25 JS | +Sugerencias +Atajos +Etiquetas |
| MAER 4.0 (Fase 3+4) | ~130/130 | 28 JS + Python | +Tasker +WhatsApp +Extras |

---

*Plan generado: 2 de abril de 2026*
*Base: MAER 3.1 — 81/81 pruebas — 0 warnings — 0 errores*
