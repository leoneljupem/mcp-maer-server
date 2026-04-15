#!/bin/bash
# 🦁 MAER Web Server Launcher

echo "Iniciando Dashboard MAER v2.2 (Entorno Conda Nativo)..."
eval "$(~/miniforge3_x86/bin/conda shell.bash hook)"
conda activate maer_env

python3 maer_backend/web_ui/server.py
