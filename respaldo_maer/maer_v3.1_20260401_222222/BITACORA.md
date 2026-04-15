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

- [ ] **WhatsApp importer**: `maer.whatsapp.js` + pestaña "WhatsApp" para parsear exportaciones .txt
- [ ] **Tasker/AutoRemote**: guía completa de configuración + webhook de prueba
- [ ] **MCP externo**: conexión MAER → servidor MCP para operaciones del sistema
- [ ] **Notificaciones nativas**: cuando hay eventos de pensión próximos (Web Notifications API)
- [ ] **Modo oscuro/claro**: toggle rápido en el header
- [ ] **Búsqueda dentro de IndexedDB**: buscar en los documentos aprendidos desde el chat
- [ ] **Exportar carta a PDF**: desde la pestaña Pensión → Cartas
- [ ] **Sincronización entre dispositivos**: compartir MAER.config entre pc y Android
- [ ] **Plugin de Tasker mejorado**: recibir notificaciones de batería, GPS, apps abiertas

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
