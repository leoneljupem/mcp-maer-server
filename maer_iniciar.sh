#!/bin/bash
# ═══════════════════════════════════════════════════════
#  🦁 MAER 4.0 — Script de inicio macOS Intel / Linux
#  Uso: bash maer_iniciar.sh [opcion]
#  Opciones: gui | consola | ngrok | server | mcp | test
#            (sin argumento: menú interactivo)
#  Leonel Houssen Mojica — Ecatepec MX — 2026
# ═══════════════════════════════════════════════════════

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

GRN='\033[0;32m'; YLW='\033[1;33m'
RED='\033[0;31m'; CYN='\033[0;36m'
BLU='\033[0;34m'; BLD='\033[1m'; NC='\033[0m'

# ── Rutas de Python a probar (prioridad: maer_env primero) ─────────────
MAER_ENV_PYTHON="$HOME/miniforge3_x86/envs/maer_env/bin/python"
MAER_ENV_PYTHON2="$HOME/miniforge3/envs/maer_env/bin/python"

banner() {
    echo ""
    echo -e "${GRN}══════════════════════════════════════════════════${NC}"
    echo -e "${GRN}  🦁 MAER 4.0 — Sistema de Asistencia IMSS${NC}"
    echo -e "${GRN}  Leonel Houssen Mojica — Ecatepec MX — 2026${NC}"
    echo -e "${GRN}══════════════════════════════════════════════════${NC}"
    echo ""
}

detectar_python() {
    # 1. Entorno maer_env (prioritario — tiene todas las dependencias ML)
    if [ -f "$MAER_ENV_PYTHON" ]; then
        echo "$MAER_ENV_PYTHON"; return 0
    fi
    if [ -f "$MAER_ENV_PYTHON2" ]; then
        echo "$MAER_ENV_PYTHON2"; return 0
    fi
    # 2. Conda base
    if command -v conda &>/dev/null; then
        local py=$(conda run -n maer_env which python 2>/dev/null)
        if [ -n "$py" ]; then echo "$py"; return 0; fi
    fi
    # 3. Python del sistema (fallback)
    for cmd in python3.10 python3.11 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"; return 0
        fi
    done
    echo ""
}

mostrar_llm_estado() {
    local py="$1"
    echo -e "${CYN}── Estado LLM ─────────────────────────────────${NC}"
    # Ollama
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        local modelos=$(curl -s http://localhost:11434/api/tags 2>/dev/null | \
            $py -c "import sys,json; d=json.load(sys.stdin); print(', '.join(m['name'] for m in d.get('models',[])[:4]))" 2>/dev/null)
        echo -e "  ${GRN}✅ Ollama activo${NC} — modelos: ${modelos:-ninguno}"
    else
        echo -e "  ${YLW}⚠  Ollama inactivo (ejecuta: ollama serve)${NC}"
    fi
    # Groq
    if grep -q "^GROQ_API_KEY=gsk_" .env 2>/dev/null; then
        echo -e "  ${GRN}✅ Groq configurado${NC} (clave en .env)"
    else
        echo -e "  ${YLW}⚠  Groq sin clave (console.groq.com — gratis)${NC}"
    fi
    echo ""
}

lanzar() {
    local py="$1"
    local modo="$2"
    case "$modo" in
        instalar|0)
            echo -e "${GRN}🔧 Ejecutando instalador completo...${NC}"
            bash instalar.sh
            ;;
        gui|1|"")
            echo -e "${GRN}🚀 Lanzador gráfico...${NC}"
            if $py -c "import tkinter" 2>/dev/null; then
                $py lanzador_maer.py
            else
                echo -e "${YLW}⚠️  tkinter no disponible.${NC}"
                echo "   macOS: brew install python-tk@3.10"
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
            echo -e "${GRN}🚀 Servidor + túnel ngrok (acceso desde celular)...${NC}"
            $py -c "import pyngrok" 2>/dev/null || \
                $py -m pip install pyngrok -q
            $py iniciar_maer_ngrok.py
            ;;
        server|4)
            echo -e "${GRN}🚀 Servidor backend en http://localhost:8765${NC}"
            $py -m maer_backend.web_ui.server
            ;;
        todo|web)
            echo -e "${GRN}🚀 Dashboard web + abriendo navegador...${NC}"
            echo -e "${CYN}  URL: http://localhost:8765${NC}"
            { sleep 2 && open "http://localhost:8765" 2>/dev/null || \
              xdg-open "http://localhost:8765" 2>/dev/null || true; } &
            $py -m maer_backend.web_ui.server
            ;;
        mcp|5)
            echo -e "${GRN}🚀 Servidor MCP para Claude Desktop...${NC}"
            if command -v node &>/dev/null; then
                node index.mjs
            else
                echo -e "${RED}❌ Node.js no encontrado. Instala desde nodejs.org${NC}"
                exit 1
            fi
            ;;
        test|6)
            echo -e "${GRN}🧪 Ejecutando suite de tests (219+ tests)...${NC}"
            $py -m pytest tests/ -v --tb=short
            ;;
        estado)
            echo -e "${CYN}🦁 Estado del sistema MAER${NC}"
            echo -e "  Python: $($py --version 2>&1)"
            echo -e "  NumPy:  $($py -c 'import numpy; print(numpy.__version__)' 2>/dev/null || echo 'no instalado')"
            $py -c "
from maer_backend.maer_ollama import estado_completo
e = estado_completo()
estado = '✅ activo' if e['servidor_activo'] else '❌ inactivo'
print(f'  Ollama: {estado} — modelo: {e[\"modelo_elegido\"] or \"ninguno\"}')
print(f'  Modelos disponibles: {e[\"total_modelos\"]}')
" 2>/dev/null || echo "  Ollama: verificar manualmente"
            if curl -s http://localhost:8765/api/status >/dev/null 2>&1; then
                echo -e "  Servidor: ${GRN}✅ activo en http://localhost:8765${NC}"
            else
                echo -e "  Servidor: ${YLW}⚠  no activo (opción 4 = servidor, opción 5 = todo)${NC}"
            fi
            ;;
        *)
            echo -e "${RED}❌ Opción desconocida: $modo${NC}"
            echo -e "   Opciones: instalar | 1-6 | todo | estado"
            exit 1
            ;;
    esac
}

# ── Main ──────────────────────────────────────────────────────────────
banner

PYTHON=$(detectar_python)
if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ Python no encontrado.${NC}"
    echo "   Activa el entorno: source ~/miniforge3_x86/envs/maer_env/bin/activate"
    exit 1
fi
echo -e "${GRN}✅ Python: $($PYTHON --version 2>&1) — $PYTHON${NC}"

# Cargar .env si existe
if [ -f ".env" ]; then
    set -a; source .env 2>/dev/null; set +a
fi

mostrar_llm_estado "$PYTHON"

# Si se pasa argumento por línea de comandos, lanzar directamente
if [ -n "$1" ]; then
    lanzar "$PYTHON" "$1"
    exit 0
fi

# Menú interactivo
echo -e "${CYN}¿Qué deseas hacer?${NC}"
echo ""
echo -e "  ${BLU}[0]${NC} 🔧  Instalar / actualizar dependencias"
echo ""
echo -e "  ${GRN}[1]${NC} 🖥  Lanzador gráfico       (recomendado)"
echo -e "  ${GRN}[2]${NC} 💬  Consola IA avanzada"
echo -e "  ${GRN}[3]${NC} 🌐  Servidor + ngrok        (acceso desde celular)"
echo -e "  ${GRN}[4]${NC} ⚙️   Solo servidor backend   (http://localhost:8765)"
echo -e "  ${GRN}[5]${NC} 🔮  Dashboard + navegador   (RECOMENDADO para web)"
echo -e "  ${GRN}[6]${NC} 🔌  Servidor MCP            (para Claude Desktop)"
echo -e "  ${GRN}[7]${NC} 🧪  Ejecutar todos los tests"
echo -e "  ${CYN}[8]${NC} 📊  Ver estado del sistema"
echo ""
read -p "Opción [0-8, Enter=5]: " OPCION
echo ""
# Mapear numeración nueva
case "${OPCION:-5}" in
    0) lanzar "$PYTHON" "instalar" ;;
    1) lanzar "$PYTHON" "gui" ;;
    2) lanzar "$PYTHON" "consola" ;;
    3) lanzar "$PYTHON" "ngrok" ;;
    4) lanzar "$PYTHON" "server" ;;
    5) lanzar "$PYTHON" "todo" ;;
    6) lanzar "$PYTHON" "mcp" ;;
    7) lanzar "$PYTHON" "test" ;;
    8) lanzar "$PYTHON" "estado" ;;
    *) lanzar "$PYTHON" "${OPCION}" ;;
esac
echo ""
echo -e "${GRN}👋 MAER cerrado.${NC}"
