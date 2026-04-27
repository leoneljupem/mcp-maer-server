# 🦁 MAER 4.0 — Makefile
# Leonel Houssen Mojica — Ecatepec MX — 2026
#
# Uso rápido:
#   make instalar    ← primera vez (instala todo)
#   make start       ← arrancar dashboard web
#   make todo        ← dashboard + abre navegador
#   make test        ← correr suite de tests
#   make estado      ← verificar estado del sistema

SHELL    := /bin/bash
# Detectar Python del entorno maer_env (prioridad) o fallback a python3
PYTHON   := $(shell \
  if [ -f "$$HOME/miniforge3_x86/envs/maer_env/bin/python" ]; then \
    echo "$$HOME/miniforge3_x86/envs/maer_env/bin/python"; \
  elif [ -f "$$HOME/miniforge3/envs/maer_env/bin/python" ]; then \
    echo "$$HOME/miniforge3/envs/maer_env/bin/python"; \
  elif [ -f "$$HOME/miniconda3/envs/maer_env/bin/python" ]; then \
    echo "$$HOME/miniconda3/envs/maer_env/bin/python"; \
  else \
    echo "python3"; \
  fi)
PORT     := 8765
BASE_URL := http://localhost:$(PORT)

.DEFAULT_GOAL := ayuda

# ─────────────────────────────────────────────────────────────────────
.PHONY: ayuda
ayuda:
	@echo ""
	@echo "  🦁 MAER 4.0 — Comandos disponibles"
	@echo "  ─────────────────────────────────────────────────"
	@echo "  make instalar      Primera instalación completa"
	@echo "  make instalar-rap  Instalación rápida (sin ML)"
	@echo ""
	@echo "  make start         Arrancar dashboard web (puerto $(PORT))"
	@echo "  make todo          Dashboard + abrir navegador"
	@echo "  make mcp           Servidor MCP (para Claude Desktop)"
	@echo "  make ngrok         Dashboard + túnel ngrok (celular)"
	@echo ""
	@echo "  make test          Suite completa de tests"
	@echo "  make test-rapido   Tests sin paquetes ML"
	@echo "  make estado        Ver estado del sistema"
	@echo "  make ollama        Detectar modelos Ollama"
	@echo "  make lint          Verificar sintaxis Python"
	@echo "  ─────────────────────────────────────────────────"
	@echo ""

# ─────────────────────────────────────────────────────────────────────
.PHONY: instalar
instalar:
	bash instalar.sh

.PHONY: instalar-rap
instalar-rap:
	bash instalar.sh --rapido

# ─────────────────────────────────────────────────────────────────────
.PHONY: start
start:
	@echo "🦁 Iniciando MAER en $(BASE_URL) ..."
	$(PYTHON) -m maer_backend.web_ui.server

.PHONY: todo
todo:
	@echo "🦁 Iniciando MAER y abriendo navegador..."
	@{ sleep 2 && open $(BASE_URL); } &
	$(PYTHON) -m maer_backend.web_ui.server

.PHONY: mcp
mcp:
	@echo "🔌 Servidor MCP para Claude Desktop..."
	node index.mjs

.PHONY: ngrok
ngrok:
	$(PYTHON) iniciar_maer_ngrok.py

# ─────────────────────────────────────────────────────────────────────
.PHONY: test
test:
	$(PYTHON) -m pytest tests/ -v --tb=short

.PHONY: test-rapido
test-rapido:
	$(PYTHON) -m pytest tests/ -q --tb=line

.PHONY: lint
lint:
	$(PYTHON) -m py_compile maer_backend/maer_files.py \
	  maer_backend/web_ui/server.py \
	  maer_backend/maer_ocr_advanced.py \
	  maer_backend/maer_search_index.py \
	  && echo "✅ Sintaxis OK"

# ─────────────────────────────────────────────────────────────────────
.PHONY: estado
estado:
	@echo "🦁 Estado del sistema MAER"
	@echo "  Python: $(shell $(PYTHON) --version 2>&1)"
	@echo "  NumPy:  $(shell $(PYTHON) -c 'import numpy; print(numpy.__version__)' 2>/dev/null || echo 'no instalado')"
	@$(PYTHON) -c "from maer_backend.maer_ollama import estado_completo; e=estado_completo(); \
	  print(f'  Ollama: {\"✅ activo\" if e[\"servidor_activo\"] else \"❌ inactivo\"} — modelo: {e[\"modelo_elegido\"] or \"ninguno\"}'); \
	  print(f'  Modelos: {e[\"total_modelos\"]}')" 2>/dev/null || echo "  Ollama: verificar manualmente"
	@echo "  Servidor: $(shell curl -s $(BASE_URL)/api/status 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(\"✅ activo en $(BASE_URL)\")' 2>/dev/null || echo '❌ no activo (usa: make start)')"

.PHONY: ollama
ollama:
	$(PYTHON) detectar_ollama.py

# ─────────────────────────────────────────────────────────────────────
.PHONY: abrir
abrir:
	open $(BASE_URL)
