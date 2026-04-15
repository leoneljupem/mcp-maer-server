@echo off
REM ═══════════════════════════════════════════════════════
REM  🦁 MAER 4.0 — Script de inicio Windows
REM  Doble clic en este archivo para iniciar MAER
REM ═══════════════════════════════════════════════════════
chcp 65001 >nul
title MAER 4.0 — Sistema de Asistencia IMSS

cd /d "%~dp0"

echo.
echo ══════════════════════════════════════════════════
echo   MAER 4.0 — Sistema de Asistencia IMSS v4.0
echo ══════════════════════════════════════════════════
echo.

REM ── Detectar Python ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python no encontrado.
        echo   Descarga desde: https://www.python.org/downloads/
        echo   IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
        echo.
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

for /f "tokens=*" %%i in ('%PYTHON% --version 2^>^&1') do set PYVER=%%i
echo [OK] %PYVER% encontrado

REM ── Verificar/instalar dependencias básicas ──
echo [..] Verificando dependencias...

%PYTHON% -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Instalando requests...
    %PYTHON% -m pip install requests --quiet
)

%PYTHON% -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Instalando fastapi + uvicorn...
    %PYTHON% -m pip install fastapi uvicorn --quiet
)

echo [OK] Dependencias basicas listas
echo.

REM ── Menú de inicio ──
echo Que deseas iniciar?
echo.
echo   [1] Lanzador grafico     (recomendado)
echo   [2] Consola IA avanzada
echo   [3] Servidor + ngrok     (acceso desde celular)
echo   [4] Solo el servidor     (http://localhost:8765)
echo.
set /p OPCION="Opcion [1-4, Enter=1]: "

if "%OPCION%"=="" set OPCION=1
echo.

if "%OPCION%"=="1" goto GUI
if "%OPCION%"=="2" goto CONSOLA
if "%OPCION%"=="3" goto NGROK
if "%OPCION%"=="4" goto SERVER

echo [ERROR] Opcion no valida. Iniciando lanzador...
goto GUI

:GUI
echo [>>] Iniciando Lanzador grafico...
%PYTHON% -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] tkinter no disponible. Usando Consola IA como alternativa.
    echo   Para instalar tkinter: descarga Python con "tcl/tk and IDLE" marcado.
    goto CONSOLA
)
%PYTHON% lanzador_maer.py
goto FIN

:CONSOLA
echo [>>] Iniciando Consola IA avanzada...
%PYTHON% maer_consola.py
goto FIN

:NGROK
echo [>>] Iniciando servidor + ngrok...
%PYTHON% -c "import pyngrok" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Instalando pyngrok...
    %PYTHON% -m pip install pyngrok --quiet
)
%PYTHON% iniciar_maer_ngrok.py
goto FIN

:SERVER
echo [>>] Iniciando servidor backend en http://localhost:8765...
%PYTHON% maer_backend\web_ui\server.py
goto FIN

:FIN
echo.
echo [OK] MAER cerrado.
echo.
pause
