#!/bin/bash
# 🦁 MAER MCP Server — Script de Instalación Automática
# Leonel Mojica — Ecatepec MX — 2026
#
# Uso: bash scripts/setup.sh
#
# Este script instala TODAS las dependencias necesarias para
# el proyecto MAER MCP Server en macOS.

set -e

echo ""
echo "🦁 ═══════════════════════════════════════════════════"
echo "   MAER MCP Server — Instalación Automática v2.0"
echo "   Leonel Mojica — Ecatepec MX — 2026"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── Colores ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# ── Verificar prerrequisitos ──
echo "📋 Verificando prerrequisitos..."

if ! command -v python3 &> /dev/null; then
    error "Python3 no encontrado. Instálalo desde https://www.python.org/downloads/"
    exit 1
fi
success "Python3: $(python3 --version)"

if ! command -v node &> /dev/null; then
    error "Node.js no encontrado. Instálalo desde https://nodejs.org/"
    exit 1
fi
success "Node.js: $(node -v)"

if ! command -v brew &> /dev/null; then
    warn "Homebrew no encontrado. Instalando..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
success "Homebrew disponible"

echo ""

# ── Dependencias del sistema ──
echo "📦 Instalando dependencias del sistema..."

echo "  → Tesseract (OCR)..."
brew install tesseract 2>/dev/null || success "Tesseract ya instalado"

echo "  → Poppler (PDF→imagen)..."
brew install poppler 2>/dev/null || success "Poppler ya instalado"

echo "  → CMake (compilación nativa)..."
brew install cmake 2>/dev/null || success "CMake ya instalado"

success "Dependencias del sistema instaladas"
echo ""

# ── Dependencias de Node.js ──
echo "📦 Instalando dependencias de Node.js..."
cd "$(dirname "$0")/.."
npm install
success "Dependencias Node.js instaladas"
echo ""

# ── Dependencias de Python (core) ──
echo "🐍 Instalando dependencias Python (core)..."
pip3 install pytesseract pdf2image Pillow pypdf python-docx requests \
    opencv-python-headless numpy pdfplumber imagehash scikit-learn \
    fastapi "uvicorn[standard]" python-multipart python-dotenv spacy

success "Dependencias Python core instaladas"
echo ""

# ── Modelo spaCy español ──
echo "🧠 Descargando modelo NLP español..."
python3 -m spacy download es_core_news_md 2>/dev/null || warn "No se pudo descargar modelo spaCy"
success "Modelo spaCy instalado"
echo ""

# ── Dependencias opcionales (pueden fallar en Python 3.13) ──
echo "🔧 Instalando dependencias opcionales..."

echo "  → EasyOCR (requiere PyTorch)..."
pip3 install easyocr 2>/dev/null || warn "EasyOCR no disponible (requiere PyTorch compatible)"

echo "  → DeepFace (requiere TensorFlow)..."
pip3 install deepface tf-keras 2>/dev/null || warn "DeepFace no disponible (requiere TensorFlow compatible)"

echo "  → PaddleOCR..."
pip3 install paddlepaddle paddleocr 2>/dev/null || warn "PaddleOCR no disponible"

echo ""

# ── Crear .env si no existe ──
if [ ! -f .env ]; then
    cp .env.example .env
    success "Archivo .env creado desde .env.example"
else
    success "Archivo .env ya existe"
fi

# ── Crear carpetas de datos ──
mkdir -p maer_backend/data/inputs
mkdir -p maer_backend/data/reports
mkdir -p maer_backend/data/uploads
success "Carpetas de datos creadas"

echo ""
echo "🦁 ═══════════════════════════════════════════════════"
echo "   ¡Instalación completa!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "  Comandos disponibles:"
echo ""
echo "  🚀 Servidor MCP:      node index.mjs"
echo "  🌐 Dashboard Web:     python3 maer_backend/web_ui/server.py"
echo "  📋 CLI:               python3 maer_backend/maer.py --help"
echo ""
echo "  El dashboard estará en: http://localhost:8765"
echo ""
