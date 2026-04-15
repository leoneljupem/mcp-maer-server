# 🦁 MAER — Bitácora de Cambios y Eventos

> **Proyecto:** MAER — Memoria Activa, Evolución Real
> **Autor:** Leonel Houssen Mojica — Ecatepec, Estado de México
> **Inicio del proyecto:** 2026
> **Formato:** Más reciente primero

---

## v3.1 — Arquitectura Multi-Módulo (2026-04-01)

### Nuevos archivos creados

| Archivo | Descripción |
|---|---|
| `static/css/maer.css` | Hoja de estilos completa con variables CSS personalizables |
| `static/js/maer.diccionario.js` | 120+ patrones de respuesta: IMSS, derecho mexicano, sistema, Tasker |
| `static/js/maer.voz.js` | Síntesis de voz grave masculina (pitch 0.62, rate 0.93) |
| `static/js/maer.core.js` | Núcleo: config, tabs, API, tooltips, temas de color |
| `static/js/maer.chat.js` | Chat con resolución en 4 pasos (aprendido → LLM → diccionario → IndexedDB) |
| `static/js/maer.aprendizaje.js` | Memoria permanente en IndexedDB (nunca se borra) |
| `static/js/maer.archivos.js` | Análisis de archivos con vista previa, detección CURP/RFC/NSS |
| `static/js/maer.busqueda.js` | Búsqueda masiva por tipo/contenido + mover archivos a carpeta |
| `static/js/maer.organizar.js` | Organizador de documentos — COPIA primero, originals intactos |
| `static/js/maer.imagenes.js` | Análisis de imágenes con Canvas + OCR (backend/Tesseract.js) |
| `static/js/maer.pension.js` | Asistente IMSS: checklist, eventos, 4 tipos de cartas oficiales |
| `static/js/maer.tareas.js` | Tareas IA: investigación legal, redacción, estrategia, orientación IMSS |
| `static/js/maer.memoria.js` | Historial paginado + aprendizajes manuales (trigger/respuesta) |
| `static/js/maer.sistema.js` | Estado servidor, rendimiento, ping, consola de log, respaldo |
| `static/js/maer.guardian.js` | Guardián HTML: verifica integridad de los 15 módulos en tiempo real |
| `static/js/maer.ajustes.js` | Ajustes: 8 temas de color, sliders de voz, importar/exportar backup |
| `static/index.html` | UI nueva — 11 pestañas, carga todos los módulos en orden correcto |
| `maer_guardian.py` | Guardián Python: manifiestos SHA-256, modo watch, reporte de integridad |
| `respaldo_maer/.guardian.json` | Manifiesto raíz del proyecto |
| `BITACORA.md` | Este archivo — registro permanente de cambios |

### Cambios en archivos existentes

| Archivo | Cambio |
|---|---|
| `maer_backend/web_ui/server.py` | +7 endpoints: `/api/move-files`, `/api/copy-files`, `/api/learn-file`, `/api/busqueda-masiva`, `/api/organizar-sugerir`, `/api/tasker-receive`, `/api/tasker-messages`, `/favicon.ico` |
| `static/index.html` | Reemplazado MAER 3.0 (1 archivo monolítico) → MAER 3.1 (multi-módulo) |

### Decisiones técnicas

- **IndexedDB** sobre localStorage para memoria permanente de documentos (mayor capacidad, no se borra accidentalmente)
- **Voz grave**: pitch 0.62 / rate 0.93 — prioridad de voces: Eddy → Diego → Jorge → Reed → español masculino
- **Organización SIEMPRE copia**: nunca mueve archivos originales, elimina riesgo de pérdida de datos
- **Resolución de chat en 4 pasos**: aprendidos manuales → LLM backend → diccionario → IndexedDB (funciona offline)
- **Guardián doble**: Python (maer_guardian.py) para servidor + JS (maer.guardian.js) para navegador

---

## v3.1 — Bloque 6: Exportar, Notificaciones, Diccionario (2026-04-01)

### Nuevos archivos

| Archivo | Descripción |
|---|---|
| `static/js/maer.whatsapp.js` | Importador de exportaciones WhatsApp (.txt), parseo dual de formato |
| `static/js/maer.notificaciones.js` | Web Notifications API — alertas OS de eventos pensión (día y día previo), badge Tasker |
| `static/js/maer.exportar.js` | Exportar: chat TXT/JSON, cartas PDF, tareas HTML/TXT, eventos, notas, búsqueda IDB |
| `TASKER_GUIA.md` | 7 perfiles Tasker documentados + endpoints + troubleshooting |

### Cambios en archivos existentes

| Archivo | Cambio |
|---|---|
| `static/js/maer.core.js` | Hooks en `tabs.show()` para whatsapp, ajustes, pensión + `MAER._updateStats()` |
| `static/js/maer.guardian.js` | MODULOS array: 16 → 18 (agregados `maer.notificaciones.js` y `maer.exportar.js`) |
| `static/js/maer.tareas.js` | Botones 🖨️ PDF y ⬇️ TXT en cabecera del resultado de tarea |
| `static/js/maer.diccionario.js` | +90 líneas: liquidación/despido, PROFEDET, INFONAVIT, aguinaldo, incapacidades, DIF/bienestar, desempleo, Modalidad 10, pensión negada, comandos exportar |
| `static/index.html` | +1 script tag (`maer.exportar.js`); botones ⬇️ TXT / 💾 JSON en Chat; 🖨️ PDF en Cartas; ⬇️ Exportar en Notas/Eventos; buscador IDB en Aprendizaje |
| `maer_backend/web_ui/server.py` | Parámetros alineados (termino/carpeta/rutas); nuevo `/api/backup`; Tasker endpoints mejorados |

### Funcionalidades completadas en Bloque 6

- ✅ **Exportar chat** — TXT con timestamps o JSON backup completo (historial + aprendizajes)
- ✅ **Carta a PDF** — ventana de impresión con tipografía Times New Roman 12pt, márgenes correctos
- ✅ **Resultado de tarea → PDF o TXT** — desde el header del resultado en la pestaña Tareas
- ✅ **Exportar eventos de pensión** — TXT con fecha y descripción de cada evento
- ✅ **Exportar notas** — descarga directa del área de notas libre de pensión
- ✅ **Búsqueda en IndexedDB** — campo `idb-busq` en pestaña Aprendizaje, muestra fragmentos relevantes con botón "Usar en chat"
- ✅ **Notificaciones OS nativas** — solicitud de permiso, alertas día-de y día-previo de eventos pensión
- ✅ **Badge Tasker en header** — contador de mensajes no leídos actualizado cada 30 s
- ✅ **WhatsApp importer** — soporta ambos formatos (corchetes y guion)
- ✅ **Comandos en diccionario** — "exportar chat", "carta a pdf", "hacer respaldo", "buscar en documentos"
- ✅ **Guardián actualizado** — 18 módulos registrados en MODULOS array

### Backup Bloque 6

`respaldo_maer/maer_backup_bloque6_20260401_223743.zip` — 25 archivos, 98.8 KB

---

## v3.0 — MAER Inicial (2026-03-xx)

### Descripción
Primera versión funcional de MAER. Archivo HTML monolítico de ~1,627 líneas.

### Características
- 8 pestañas: Chat, Archivos, Imágenes, Búsqueda, Aprendizaje, Pensión, Sistema, Ajustes
- Conexión a servidor FastAPI en puerto 8765
- Voz con Web Speech API
- Memoria en localStorage
- Análisis de archivos con FileReader API
- Asistente IMSS con calculadora (posteriormente removida)
- Sistema de monitoreo básico

### Archivos
- `static/index.html` — archivo único con HTML + CSS + JS embebidos
- `maer_backend/web_ui/server.py` — servidor FastAPI original

---

## Pendientes / Próximas versiones

- [x] ~~**WhatsApp importer**: `maer.whatsapp.js` + pestaña "WhatsApp"~~ — ✅ Completado Bloque 4
- [x] ~~**Tasker/AutoRemote**: guía completa de configuración~~ — ✅ Completado: `TASKER_GUIA.md`
- [x] ~~**Notificaciones nativas**~~ — ✅ Completado: `maer.notificaciones.js`
- [x] ~~**Búsqueda dentro de IndexedDB**~~ — ✅ Completado: `MAER.exportar.buscarEnAprendido()` + UI en Aprendizaje
- [x] ~~**Exportar carta a PDF**~~ — ✅ Completado: `MAER.exportar.cartaPDF()`
- [ ] **MCP externo**: conexión MAER → servidor MCP para operaciones del sistema (abrir apps, mover archivos del OS)
- [ ] **Modo oscuro/claro**: toggle rápido en el header (actualmente solo desde Ajustes)
- [ ] **Sincronización entre dispositivos**: compartir MAER.config entre PC y Android vía JSON/QR
- [ ] **Plugin de Tasker mejorado**: push de notificaciones de batería/GPS en tiempo real
- [ ] **`/api/status` enriquecido**: versión, uptime, lista de módulos cargados, memoria usada
- [ ] **`/api/pdf-export`**: endpoint server-side para PDF sin ventana emergente (usando WeasyPrint/pdfkit)

---

## Registro de incidencias

| Fecha | Problema | Resolución |
|---|---|---|
| 2026-03-xx | JSZip CDN: ITP tracking warning en Edge | Harmless — solo bloquea acceso a storage del CDN, no la carga del script |
| 2026-03-xx | favicon.ico 404 en cada carga | Resuelto agregando `@app.get("/favicon.ico")` en server.py |
| 2026-04-01 | Monolítico difícil de mantener | Migrado a arquitectura 15-módulos con maer.core.js como base |

---

*Última actualización: 2026-04-01*
*Guardian hash: ver `.guardian.json` en cada carpeta*
