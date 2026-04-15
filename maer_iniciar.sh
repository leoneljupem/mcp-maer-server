#!/bin/bash
# ═══════════════════════════════════════════════════════
#  🦁 MAER 4.0 — Script de inicio Linux / Mac
#  Uso: bash maer_iniciar.sh [opcion]
#  Opciones: gui | consola | ngrok | server
#            (sin argumento: menú interactivo)
# ═══════════════════════════════════════════════════════

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

GRN='\033[0;32m'; YLW='\033[1;33m'
RED='\033[0;31m'; CYN='\033[0;36m'; NC='\033[0m'

banner() {
    echo ""
    echo -e "${GRN}══════════════════════════════════════════════════${NC}"
    echo -e "${GRN}  🦁 MAER 4.0 — Sistema de Asistencia IMSS v4.0${NC}"
    echo -e "${GRN}══════════════════════════════════════════════════${NC}"
    echo ""
}

detectar_python() {
    for cmd in python3 python python3.11 python3.10 python3.9; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"; return 0
        fi
    done
    echo ""
}

instalar_deps_basicas() {
    local py="$1"
    local missing=""
    for pkg in requests fastapi uvicorn; do
        $py -c "import $pkg" 2>/dev/null || missing="$missing $pkg"
    done
    if [ -n "$missing" ]; then
        echo -e "${YLW}⚠️  Instalando:$missing${NC}"
        $py -m pip install $missing --break-system-packages -q 2>/dev/null || \
        $py -m pip install $missing -q
    fi
}

lanzar() {
    local py="$1"
    local modo="$2"
    case "$modo" in
        gui|1|"")
            echo -e "${GRN}🚀 Lanzador gráfico...${NC}"
            if $py -c "import tkinter" 2>/dev/null; then
                $py lanzador_maer.py
            else
                echo -e "${YLW}⚠️  tkinter no disponible.${NC}"
                echo "   macOS: brew install python-tk"
                echo "   Linux: sudo apt install python3-tk"
                echo ""
                echo -e "${CYN}Iniciando Consola IA como alternativa...${NC}"
                $py maer_consola.py
            fi
            ;;
        consola|2)
            echo -e "${GRN}🚀 Consola IA avanzada...${NC}"
            $py maer_consola.py
            ;;
        ngrok|3)
            echo -e "${GRN}🚀 Servidor + túnel ngrok...${NC}"
            $py -c "import pyngrok" 2>/dev/null || \
                $py -m pip install pyngrok --break-system-packages -q
            $py iniciar_maer_ngrok.py
            ;;
        server|4)
            echo -e "${GRN}🚀 Servidor backend en http://localhost:8765${NC}"
            $py maer_backend/web_ui/server.py
            ;;
        *)
            echo -e "${RED}❌ Opción desconocida: $modo${NC}"
            exit 1
            ;;
    esac
}

# ── Main ──
banner

PYTHON=$(detectar_python)
if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ Python no encontrado.${NC}"
    echo "   Ubuntu/Debian: sudo apt install python3"
    echo "   macOS: brew install python3"
    exit 1
fi
echo -e "${GRN}✅ $($PYTHON --version 2>&1)${NC}"

instalar_deps_basicas "$PYTHON"

# Si se pasa argumento por línea de comandos, lanzar directamente
if [ -n "$1" ]; then
    lanzar "$PYTHON" "$1"
    exit 0
fi

# Menú interactivo
echo ""
echo -e "${CYN}¿Qué deseas iniciar?${NC}"
echo "  [1] 🖥  Lanzador gráfico     (python lanzador_maer.py)"
echo "  [2] 💬  Consola IA avanzada  (python maer_consola.py)"
echo "  [3] 🌐  Servidor + ngrok     (python iniciar_maer_ngrok.py)"
echo "  [4] ⚙️  Solo servidor        (python maer_backend/web_ui/server.py)"
echo ""
read -p "Opción [1-4, Enter=1]: " OPCION
echo ""
lanzar "$PYTHON" "${OPCION:-1}"
echo ""
echo -e "${GRN}👋 MAER cerrado.${NC}"
