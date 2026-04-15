# 🦁 MAER MCP Server — Guía para Claude Code

> Proyecto de Leonel Houssen Mojica — Ecatepec, Estado de México — 2026
> Sistema de asistencia para trámites de pensión IMSS con OCR, IA y análisis documental.

---

## Identidad del proyecto

**MAER** (Motor de Asistencia IMSS) es una aplicación web completa que ayuda a ciudadanos mexicanos a navegar el proceso de pensión IMSS. Tiene:

- **Servidor MCP** (Node.js + `@modelcontextprotocol/sdk`) — interfaz Claude ↔ backend
- **Backend Python** (FastAPI en puerto 8765) — OCR, análisis documental, LLM
- **Frontend SPA** (HTML/CSS/JS puro, 32 módulos) — dashboard con 15 pestañas

---

## Entorno obligatorio

| Variable | Valor |
|----------|-------|
| Python | 3.10 (miniforge3_x86 Intel) |
| Entorno | `~/miniforge3_x86/envs/maer_env` |
| Activar | `maer-env` (alias en .zshrc) o `source ~/miniforge3_x86/envs/maer_env/bin/activate` |
| Node.js | v25 (instalado globalmente) — se preferiría v20 LTS para estabilidad MCP |
| macOS | x86_64 Intel — NO Apple Silicon |

### Restricciones críticas de compatibilidad
- **PyTorch MÁXIMO 2.2.2** — Apple eliminó soporte x86_64 en 2.4+. NO actualizar.
- **NumPy fijado en 1.26.4** — requerido por PyTorch 2.2.2. NO actualizar a 2.x.
- **transformers MÁXIMO 4.44.x** — versiones ≥5.0 requieren PyTorch ≥2.4.
- **TensorFlow 2.16.2** — última versión estable para Intel Mac.

---

## Cómo arrancar el sistema

```bash
# Terminal 1 — Backend Python (FastAPI)
maer-env
cd ~/mcp-maer-server
python -m maer_backend.web_ui.server
# → http://localhost:8765  (dashboard web)

# Terminal 2 — Servidor MCP (para Claude Desktop)
cd ~/mcp-maer-server
node index.mjs

# Verificar que todo funciona
npm run env:check
```

### Configuración Claude Desktop (MCP)
En `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "maer": {
      "command": "node",
      "args": ["/Users/houssenm/mcp-maer-server/index.mjs"]
    }
  }
}
```

---

## Estructura del proyecto

```
mcp-maer-server/
├── index.mjs                    ← Servidor MCP (Node.js entry point)
├── package.json                 ← Scripts npm (start, test, dashboard, dev)
├── requirements.txt             ← Dependencias Python con versiones exactas
├── .env                         ← Variables locales (NO en git)
├── .env.example                 ← Plantilla de variables (SÍ en git)
│
├── maer_backend/
│   ├── maer_files.py            ← Validación CURP, NSS, RFC, análisis IMSS
│   ├── ocr_engine.py            ← OCR multi-motor con caché
│   ├── nlp_engine.py            ← Procesamiento de texto / spaCy
│   ├── table_extractor.py       ← Extracción de tablas PDF/Excel
│   ├── image_analyzer.py        ← Análisis de imágenes / DeepFace
│   ├── llm_engine.py            ← Cascada LLM: Ollama → Groq → OpenAI → dict
│   ├── maer_ollama.py           ← Integración Ollama local
│   ├── maer.py                  ← Módulo principal backend
│   ├── maer_core/
│   │   ├── analyzer.py          ← Análisis de documentos
│   │   ├── fixer.py             ← Corrección automática
│   │   └── generator.py         ← Generación de cartas/reportes
│   └── web_ui/
│       ├── server.py            ← FastAPI app (puerto 8765)
│       └── static/
│           ├── index.html       ← SPA principal (15 pestañas)
│           ├── css/
│           │   ├── maer.css     ← Estilos principales (~1050 líneas)
│           │   └── maer-compact.css  ← Modo compacto
│           └── js/              ← 32 módulos JS (ver tabla abajo)
│
├── tests/
│   ├── test_ocr_engine.py       ← OCR, CURP, config (16 tests)
│   ├── test_maer_api.py         ← FastAPI, estructura (8 tests)
│   ├── test_timeline.py         ← Bloque 7 (10 tests)
│   ├── test_bloques_frontend.py ← Bloques 8,9,10,12 + suite JS (66 tests)
│   └── test_modulos_python.py   ← Todos los módulos Python (70 tests)
│
└── data/
    └── expedientes/             ← PDFs IMSS (en .gitignore)
```

---

## Módulos JS — 32 archivos

| # | Módulo | Función |
|---|--------|---------|
| 1 | `maer.diccionario.js` | Base de conocimiento IMSS (patrones regex → respuestas) |
| 2 | `maer.core.js` | Núcleo: init, tabs, API call, reloj, tooltips |
| 3 | `maer.voz.js` | Síntesis de voz (Web Speech API) — tono grave pitch=0.62 |
| 4 | `maer.chat.js` | Chat principal con diccionario + backend LLM |
| 5 | `maer.aprendizaje.js` | IndexedDB — memoriza documentos permanentemente |
| 6 | `maer.archivos.js` | Subida/análisis de archivos (PDF, Word, Excel, etc.) |
| 7 | `maer.busqueda.js` | Búsqueda masiva en archivos por nombre o contenido |
| 8 | `maer.organizar.js` | Organizador de carpetas por tipo de documento |
| 9 | `maer.imagenes.js` | OCR de imágenes vía backend |
| 10 | `maer.pension.js` | Checklist docs, eventos, generador cartas IMSS |
| 11 | `maer.timeline.js` | **Bloque 7** — Timeline visual 8 etapas proceso pensión |
| 12 | `maer.recordatorios.js` | **Bloque 9** — Alertas con fecha límite + badge urgencia |
| 13 | `maer.cartas-historial.js` | **Bloque 10** — Historial/comparar/reimprimir cartas |
| 14 | `maer.sugerencias.js` | **Bloque 8** — Autocompletado tiempo real en chat |
| 15 | `maer.atajos.js` | **Bloque 12** — Hotkeys globales (Alt+1..9, Ctrl+K, etc.) |
| 16 | `maer.etiquetas.js` | Etiquetas por documento (IMSS, Urgente, etc.) |
| 17 | `maer.compacto.js` | Modo compacto — UI reducida para pantallas pequeñas |
| 18 | `maer.resumen.js` | Resumen automático del estado del expediente |
| 19 | `maer.qr.js` | Exportar/importar configuración vía QR |
| 20 | `maer.stats.js` | Estadísticas de uso (mensajes, docs, etapas) |
| 21 | `maer.poder.js` | Análisis avanzado: CURP, RFC, duplicados, expediente |
| 22 | `maer.diagnostico.js` | Panel diagnóstico del sistema + suite de pruebas |
| 23 | `maer.sinavid.js` | Integración portal SINAVID del IMSS |
| 24 | `maer.tareas.js` | Tareas IA: investigación legal, redactar docs, análisis |
| 25 | `maer.memoria.js` | Historial de conversaciones + aprendizajes |
| 26 | `maer.sistema.js` | Info navegador, rendimiento, red, log, Tasker |
| 27 | `maer.guardian.js` | Verificación de integridad de todos los módulos |
| 28 | `maer.whatsapp.js` | Importar/buscar en chats exportados de WhatsApp |
| 29 | `maer.notificaciones.js` | Notificaciones del navegador (Web Notifications API) |
| 30 | `maer.exportar.js` | Exportar chat TXT/JSON, cartas PDF, eventos TXT |
| 31 | `maer.ajustes.js` | Configuración: voz, tema, servidor, datos |
| 32 | `maer.test.js` | Suite de 80+ pruebas — llamar con `MAER_runTests()` |

---

## Comandos frecuentes

```bash
# Correr todos los tests
npm test
# → equivale a: python -m pytest tests/ -v --tb=short

# Tests rápidos (sin verbosidad)
npm run test:rapido

# Tests por módulo
npm run test:ocr
npm run test:api

# Lint Python
npm run lint

# Verificar entorno ML completo
npm run env:check

# Servidor en modo desarrollo (auto-reload)
npm run dev
```

### Tests del navegador
Abrir MAER → pestaña **Diagnóstico** → "🧪 Ejecutar suite completa"
O desde consola F12: `MAER_runTests()`

---

## Variables de entorno críticas

| Variable | Dónde obtener | Obligatoria |
|----------|--------------|-------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com/settings/keys | **SÍ** — sin esto el chat no funciona |
| `OLLAMA_MODEL` | `ollama list` | No — se auto-detecta |
| `GROQ_API_KEY` | console.groq.com (gratuito) | No — fallback LLM |
| `OPENAI_API_KEY` | platform.openai.com | No — fallback LLM |
| `NGROK_AUTHTOKEN` | dashboard.ngrok.com | No — solo para acceso remoto |

---

## Estado de los bloques implementados

| Bloque | Módulo | Estado |
|--------|--------|--------|
| 7 | `maer.timeline.js` | ✅ Completo — 8 etapas, localStorage, render |
| 8 | `maer.sugerencias.js` | ✅ Completo — autocomplete, catálogo 20 frases, teclado |
| 9 | `maer.recordatorios.js` | ✅ Completo — alertas, badge, integración notificaciones |
| 10 | `maer.cartas-historial.js` | ✅ Completo — guardar, comparar, reimprimir (max 50) |
| 12 | `maer.atajos.js` | ✅ Completo — 19 hotkeys, panel ayuda (Shift+?) |
| 17 | `maer.sistema.js` | 🔶 Parcial — UI Tasker lista, sin integración AutoRemote real |
| 18 | WhatsApp API | ❌ Pendiente — solo importa TXT exportado, no API Business |
| 20 | `maer.poder.js` | 🔶 Parcial — base implementada, análisis profundo en desarrollo |

---

## Problemas conocidos y sus workarounds

| Problema | Workaround |
|----------|------------|
| `CryptographyDeprecationWarning` (ARC4 en pypdf) | Se resuelve cuando pypdf libere versión sin ARC4 legacy. No bloquea nada. |
| `PaddleOCR` hace petición de red al importar | `npm run env:check` necesita internet. En offline, importar falla gracefully. |
| Node.js v25 (inestable) | Funciona pero se recomienda `nvm use 20`. Instalar: `nvm install 20 && nvm alias default 20` |
| `spaCy` sin modelo español | Ejecutar: `python -m spacy download es_core_news_sm` |
| `transformers` desactiva PyTorch | Es aviso informativo — PyTorch 2.2.2 funciona para EasyOCR y DeepFace |

---

## Convenciones de código

- **Python**: sin type hints en funciones existentes, docstrings solo donde la lógica no sea obvia
- **JavaScript**: sin clases ES6 en módulos MAER, usar objetos literales con métodos
- **CSS**: variables CSS `var(--accent)`, `var(--bg)`, etc. — no hardcodear colores
- **Tests**: pytest, sin mocks de base de datos, fixture `tmp_path` para archivos temporales
- **Commits**: `feat:`, `fix:`, `test:`, `docs:` + descripción en español

---

## Historial de commits

```
58ddd50  feat: implementación armónica completa — 170 tests
120cdfc  feat: Bloque 7 — Timeline Visual del Proceso de Pensión IMSS
a989e5e  feat: unificar entornos y actualizar package.json v2.1.0
99cafef  fix: corregir todos los problemas detectados en auditoria
4667a19  fix: mover expedientes IMSS a data/expedientes y proteger PDFs
8f2e1ab  fix: excluir instaladores y reportes grandes del repositorio
07430b6  feat: commit inicial MAER MCP Server v2.0
```
