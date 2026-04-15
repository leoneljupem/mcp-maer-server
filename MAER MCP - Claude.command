#!/bin/bash
# ═══════════════════════════════════════════════════════
#  🦁 MAER MCP — Conector Claude Code (doble clic)
#  Leonel Houssen Mojica — Ecatepec MX — 2026
# ═══════════════════════════════════════════════════════

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

GRN='\033[0;32m'
RED='\033[0;31m'
CYN='\033[0;36m'
NC='\033[0m'

clear
echo ""
echo -e "${GRN}══════════════════════════════════════════════════${NC}"
echo -e "${GRN}  🦁 MAER MCP Server — Iniciando para Claude     ${NC}"
echo -e "${GRN}══════════════════════════════════════════════════${NC}"
echo ""

# Verificar Node.js
if ! command -v node &>/dev/null; then
    echo -e "${RED}❌ Node.js no encontrado. Instala con: brew install node${NC}"
    read -p "Presiona Enter para cerrar..."
    exit 1
fi

echo -e "${GRN}✅ Node.js $(node --version) encontrado${NC}"

# Verificar dependencias MCP
if [ ! -d "node_modules/@modelcontextprotocol" ]; then
    echo -e "${CYN}📦 Instalando dependencias MCP...${NC}"
    npm install --silent
fi

echo -e "${GRN}✅ MCP SDK listo${NC}"
echo ""
echo -e "${CYN}🚀 Iniciando servidor MCP MAER...${NC}"
echo -e "${CYN}   Conecta este servidor desde Claude Code con /mcp${NC}"
echo ""

node index.mjs

echo ""
echo -e "${GRN}👋 Servidor MCP cerrado.${NC}"
read -p "Presiona Enter para cerrar esta ventana..."
