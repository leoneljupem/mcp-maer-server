# 🦁 MAER MCP Server v2.0

**Motor Multimodal de Análisis Documental, OCR, Validación de IDs Mexicanos y Reconocimiento Facial**

Autor: Leonel Mojica — Ecatepec MX, México
Fecha: 2026

---

## 🏗️ Arquitectura

```
┌─────────────────────┐     ┌──────────────────────────────┐
│   Cliente MCP       │     │   Dashboard Web (FastAPI)     │
│   (Antigravity,     │     │   http://localhost:8765       │
│    Claude, etc.)    │     └─────────────┬────────────────┘
└─────────┬───────────┘                   │
          │ stdio                         │ HTTP/JSON
          ▼                               ▼
┌─────────────────────────────────────────────────┐
│           index.mjs (Node.js MCP Server)        │
│   17 herramientas • Resources • Prompts         │
└─────────────────────┬───────────────────────────┘
                      │ spawn python3
                      ▼
┌─────────────────────────────────────────────────┐
│               maer_files.py (Backend)           │
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐ │
│  │OCR      │  │NLP       │  │Image Analyzer  │ │
│  │Engine   │  │Engine    │  │(pHash, Faces)  │ │
│  └─────────┘  └──────────┘  └────────────────┘ │
│  ┌─────────┐  ┌──────────┐                     │
│  │Table    │  │ID        │                     │
│  │Extractor│  │Validator │                     │
│  └─────────┘  └──────────┘                     │
└─────────────────────────────────────────────────┘
```

## 🚀 Instalación Rápida

```bash
# Clonar repositorio
git clone <repo-url> mcp-maer-server
cd mcp-maer-server

# Ejecutar instalador automático
bash scripts/setup.sh
```

O manualmente:

```bash
# Sistema (macOS)
brew install tesseract poppler cmake

# Node.js
npm install

# Python
pip3 install -r requirements.txt
python3 -m spacy download es_core_news_md

# Configuración
cp .env.example .env
# Editar .env con tus tokens
```

## 📋 Herramientas MCP Disponibles

### Análisis Básico
| Herramienta | Descripción |
|-------------|-------------|
| `ping_maer` | Verifica que el servidor está activo |
| `suma_simple` | Suma dos números (demo) |
| `maer_search_files` | Busca archivos por nombre/contenido |
| `maer_analyze_file` | Analiza un archivo (metadatos, preview) |
| `maer_fix_code_file` | Corrige trailing spaces (con backup) |
| `maer_extract_text` | Extrae texto de PDF/DOCX/imágenes |

### Indexación
| Herramienta | Descripción |
|-------------|-------------|
| `maer_index_full` | Indexa carpeta completa → JSON |
| `maer_search_index` | Busca en índice JSON |

### IDs Mexicanos
| Herramienta | Descripción |
|-------------|-------------|
| `maer_detect_ids` | Detecta CURP/RFC/INE + homonimias |
| `maer_detect_related` | Busca archivos con un ID específico |
| `maer_curp_renapo_check` | Valida CURP contra API RENAPO |

### Multimodal v2.0
| Herramienta | Descripción |
|-------------|-------------|
| `maer_ocr_multimodal` | OCR con Tesseract/EasyOCR/PaddleOCR + cache |
| `maer_extract_tables` | Extrae tablas de PDFs (pdfplumber) |
| `maer_nlp_entities` | Entidades NLP: personas, fechas, orgs (spaCy) |
| `maer_image_duplicates` | Imágenes duplicadas (pHash/dHash) |
| `maer_face_detect` | Reconocimiento facial (DeepFace) |
| `maer_cluster_files` | Clustering por similitud visual (DBSCAN) |

## 💬 Ejemplos de Payloads JSON

### Buscar archivos
```json
{
  "query": "jose luis mora",
  "base_dir": "/Users/houssenm/Documentos",
  "mode": "both",
  "max_results": 50
}
```

### OCR multimodal
```json
{
  "path": "/ruta/al/documento.pdf",
  "engine": "auto",
  "use_cache": true
}
```

### Detectar IDs
```json
{
  "mode": "file",
  "path": "/ruta/al/documento.pdf",
  "ocr_for_pdf": true
}
```

### Extraer tablas
```json
{
  "path": "/ruta/al/documento.pdf",
  "max_pages": 50
}
```

### NLP entidades
```json
{
  "path": "/ruta/al/documento.txt"
}
```

### Imágenes duplicadas
```json
{
  "base_dir": "/ruta/a/fotos",
  "threshold": 10,
  "max_files": 1000
}
```

## 🖥️ Esquema de Respuesta Uniforme

Todas las herramientas devuelven:

```json
{
  "ok": true,
  "code": "SEARCH_OK",
  "message": "Búsqueda completada",
  "timestamp": "2026-03-31T16:00:00+00:00",
  "data": { ... }
}
```

## 🌐 Dashboard Web

```bash
python3 maer_backend/web_ui/server.py
# Abre http://localhost:8765
```

Funcionalidades:
- Upload de archivos con drag & drop
- OCR en tiempo real con selección de motor
- Detección de CURP/RFC/INE con validación visual
- Extracción de tablas de PDFs
- Clasificación NLP de entidades
- Búsqueda de imágenes duplicadas
- Clustering visual

## 📁 Estructura del Proyecto

```
mcp-maer-server/
├── index.mjs                    # Servidor MCP (Node.js)
├── package.json                 # Dependencias Node
├── requirements.txt             # Dependencias Python
├── .env.example                 # Template de configuración
├── .gitignore
├── README.md
├── INSTALL.md
├── scripts/
│   └── setup.sh                 # Instalador automático
└── maer_backend/
    ├── maer_files.py            # Backend principal
    ├── ocr_engine.py            # Motor OCR multimodal
    ├── table_extractor.py       # Extractor de tablas
    ├── nlp_engine.py            # Motor NLP (spaCy)
    ├── image_analyzer.py        # Análisis de imágenes
    ├── maer.py                  # CLI con argparse
    ├── maer_core/               # Módulos del CLI
    │   ├── analyzer.py
    │   ├── fixer.py
    │   └── generator.py
    └── web_ui/
        ├── server.py            # FastAPI server
        └── static/
            ├── index.html
            ├── styles.css
            └── app.js
```

## 📄 Licencia

ISC — Leonel Mojica 2026
