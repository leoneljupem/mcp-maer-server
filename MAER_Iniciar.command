#!/bin/bash
# ═══════════════════════════════════════════════════════
#  🦁 MAER 4.0 — Iniciador macOS (doble clic en Finder)
#  Leonel Houssen Mojica — Ecatepec MX — 2026
# ═══════════════════════════════════════════════════════
# Para usar: doble clic en este archivo desde el Finder.
# Si pide permiso: Sistema → Privacidad → Acceso total al disco
# ═══════════════════════════════════════════════════════

# Ir a la carpeta donde está este script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ── Colores ANSI ──
GRN='\033[0;32m'
YLW='\033[1;33m'
RED='\033[0;31m'
CYN='\033[0;36m'
NC='\033[0m'

clear
echo ""
echo -e "${GRN}══════════════════════════════════════════════════${NC}"
echo -e "${GRN}  🦁 MAER 4.0 — Sistema de Asistencia IMSS${NC}"
echo -e "${GRN}══════════════════════════════════════════════════${NC}"
echo ""

# ── Detectar Python ──
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}❌ Python no encontrado.${NC}"
    echo "   Descarga Python desde: https://www.python.org/downloads/"
    echo ""
    read -p "Presiona Enter para cerrar..."
    exit 1
fi

PYVER=$($PYTHON --version 2>&1)
echo -e "${GRN}✅ $PYVER encontrado${NC}"

# ── Verificar dependencias básicas ──
echo -e "${CYN}🔍 Verificando dependencias...${NC}"

MISSING=""
for pkg in requests fastapi uvicorn; do
    if ! $PYTHON -c "import $pkg" 2>/dev/null; then
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    echo -e "${YLW}⚠️  Instalando paquetes faltantes:$MISSING${NC}"
    $PYTHON -m pip install $MISSING --break-system-packages --quiet
    if [ $? -eq 0 ]; then
        echo -e "${GRN}✅ Paquetes instalados${NC}"
    else
        echo -e "${YLW}⚠️  Algunos paquetes no se instalaron. MAER puede funcionar de forma limitada.${NC}"
    fi
else
    echo -e "${GRN}✅ Dependencias básicas OK${NC}"
fi

echo ""
echo -e "${CYN}¿Qué deseas iniciar?${NC}"
echo ""
echo "  [1] 🖥  Lanzador gráfico (recomendado)"
echo "  [2] 💬  Consola IA avanzada"
echo "  [3] 🌐  Servidor + túnel ngrok (acceso celular)"
echo "  [4] ⚙️  Solo el servidor backend"
echo ""
read -p "Opción [1-4]: " OPCION

echo ""

case "$OPCION" in
    1|"")
        echo -e "${GRN}🚀 Iniciando Lanzador gráfico...${NC}"
        if ! $PYTHON -c "import tkinter" 2>/dev/null; then
            echo -e "${YLW}⚠️  tkinter no disponible. Instala con: brew install python-tk${NC}"
            echo -e "${CYN}   Iniciando Consola IA en su lugar...${NC}"
            $PYTHON maer_consola.py
        else
            $PYTHON lanzador_maer.py
        fi
        ;;
    2)
        echo -e "${GRN}🚀 Iniciando Consola IA...${NC}"
        $PYTHON maer_consola.py
        ;;
    3)
        echo -e "${GRN}🚀 Iniciando servidor + ngrok...${NC}"
        if ! $PYTHON -c "import pyngrok" 2>/dev/null; then
            echo -e "${YLW}⚠️  Instalando pyngrok...${NC}"
            $PYTHON -m pip install pyngrok --break-system-packages --quiet
        fi
        $PYTHON iniciar_maer_ngrok.py
        ;;
    4)
        echo -e "${GRN}🚀 Iniciando servidor backend en http://localhost:8765...${NC}"
        $PYTHON maer_backend/web_ui/server.py
        ;;
    *)
        echo -e "${RED}❌ Opción no válida. Iniciando lanzador por defecto...${NC}"
        $PYTHON lanzador_maer.py
        ;;
esac

echo ""
echo -e "${GRN}👋 MAER cerrado.${NC}"
read -p "Presiona Enter para cerrar esta ventana..."
