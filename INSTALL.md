# 🦁 MAER MCP Server — Guía de Instalación

## Instrucciones para Recrear en Otra Computadora

### Prerrequisitos

1. **macOS** (Sonoma, Tahoe o posterior)
2. **Homebrew** — Gestor de paquetes macOS
3. **Python 3.11+** — (3.11 o 3.12 recomendado para mejor compatibilidad con OCR avanzado)
4. **Node.js 18+** — Runtime JavaScript

### Paso 1: Instalar Homebrew (si no está instalado)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Paso 2: Instalar Python y Node.js

```bash
# Python (si no está instalado)
brew install python@3.12

# Node.js (si no está instalado)
brew install node
```

### Paso 3: Clonar el Proyecto

```bash
cd ~/Desktop  # o donde quieras
git clone <url-del-repo> mcp-maer-server
cd mcp-maer-server
```

### Paso 4: Ejecutar Instalador Automático

```bash
chmod +x scripts/setup.sh
bash scripts/setup.sh
```

Esto instalará automáticamente:
- ✅ Tesseract OCR (motor OCR principal)
- ✅ Poppler (conversión PDF→imagen)
- ✅ CMake (compilación nativa)
- ✅ Dependencias Node.js (@modelcontextprotocol/sdk)
- ✅ Dependencias Python (pytesseract, opencv, spacy, fastapi, etc.)
- ✅ Modelo spaCy para español (es_core_news_md)
- ⚠️ EasyOCR, DeepFace, PaddleOCR (opcionales, dependen de PyTorch/TensorFlow)

### Paso 5: Configuración

```bash
# Editar variables de entorno
cp .env.example .env
nano .env  # o usar tu editor favorito
```

Variables importantes:
```
API_CURP_URL=https://tu-api-curp.com/curp
API_CURP_TOKEN=tu_token_secreto
MAER_OCR_ENGINE=auto
MAER_WEB_PORT=8765
```

### Paso 6: Verificar Instalación

```bash
# Verificar backend Python
python3 maer_backend/maer_files.py search_files '{"query":"test","base_dir":"."}'

# Verificar CLI
python3 maer_backend/maer.py --help

# Verificar servidor MCP
node index.mjs  # Ctrl+C para detener

# Iniciar dashboard
python3 maer_backend/web_ui/server.py
# Abrir http://localhost:8765
```

### Paso 7: Configurar en tu Cliente MCP

#### Para Claude Desktop / Cline
Añadir a `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "maer": {
      "command": "node",
      "args": ["/ruta/completa/a/mcp-maer-server/index.mjs"],
      "env": {}
    }
  }
}
```

#### Para Antigravity
Configurar en la sección de servidores MCP con la ruta al proyecto.

---

## Notas sobre Compatibilidad

### Python 3.13
- ⚠️ PyTorch aún no tiene wheels oficiales para Python 3.13
- ⚠️ TensorFlow aún no soporta Python 3.13
- Esto afecta a: EasyOCR, DeepFace, PaddleOCR
- **Recomendación**: Usar Python 3.11 o 3.12 para compatibilidad completa

### Si usas Python 3.11/3.12
```bash
# Todas las dependencias se instalarán correctamente:
pip3 install -r requirements.txt
```

### macOS con Apple Silicon (M1/M2/M3)
- Tesseract y Poppler funcionan nativamente
- OpenCV funciona con `opencv-python-headless`
- Para mejor rendimiento OCR, usar PaddleOCR con Apple Metal

---

## Solución de Problemas

### Error: "Tesseract not found"
```bash
brew install tesseract
# Verificar:
which tesseract
```

### Error: "poppler/pdftoppm not found"
```bash
brew install poppler
```

### Error: "spaCy model not found"
```bash
python3 -m spacy download es_core_news_md
```

### Error: "Address already in use" (port 8765)
```bash
# Encontrar y matar el proceso:
lsof -i :8765
kill -9 <PID>
```

### Dashboard no carga
```bash
# Verificar que el servidor está corriendo:
curl http://localhost:8765/api/status
```
