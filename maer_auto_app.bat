@echo off
TITLE MAER Unified Launcher Windows
echo ========================================
echo    MAER: Iniciando Secuencia en Windows
echo ========================================

IF EXIST ".git" (
    echo Buscando actualizaciones en Git...
    git pull origin main
)

IF NOT EXIST ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Instalando dependencias de Inteligencia Artificial...
pip install -q -r requirements.txt
pip install -q thefuzz python-Levenshtein pdfplumber pytesseract easyocr

echo Verificando dependencias de Node.js...
IF NOT EXIST "node_modules" (
    npm install --silent
)

echo Iniciando Dashboard Web en http://localhost:8765 ...
start /B python maer_backend\web_ui\server.py

echo MAER MCP Server ejecutandose y listo!
node index.mjs
pause
