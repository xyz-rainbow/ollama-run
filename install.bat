@echo off
setlocal enabledelayedexpansion
title Rainbow Ollama-Run Installer
echo.
echo   [XYZ] OLLAMA-RUN installer (Windows)
echo   ----------------------------------------
echo.

:: ── 1. Comprobar Python ───────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo   [!] Python no encontrado.
    echo   Descargalo en: https://www.python.org/downloads/
    echo   Asegurate de marcar "Add Python to PATH" en la instalacion.
    pause & exit /b 1
)
echo   [ok] Python encontrado.

:: ── 2. Comprobar/instalar Ollama ──────────────────────────────────────────────
ollama --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [!] Ollama no encontrado.
    echo   Abriendo pagina de descarga...
    start https://ollama.com/download/windows
    echo   Instala Ollama y vuelve a ejecutar este script.
    pause & exit /b 1
) else (
    echo   [ok] Ollama encontrado.
)

:: ── 3. Dependencias Python ────────────────────────────────────────────────────
echo.
echo   Instalando dependencias Python...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo   [!] Error instalando dependencias.
    pause & exit /b 1
)

:: ── 4. Instalar ollama-run ────────────────────────────────────────────────────
echo   Instalando ollama-run...
pip install -e "%~dp0" -q
if errorlevel 1 (
    echo   [!] Error instalando ollama-run.
    pause & exit /b 1
)

:: ── 5. Añadir Scripts al PATH si no está ─────────────────────────────────────
for /f "tokens=*" %%i in ('python -c "import sys,os; print(os.path.join(sys.prefix,'Scripts'))"') do set SCRIPTS=%%i
echo %PATH% | find /i "%SCRIPTS%" >nul 2>&1
if errorlevel 1 (
    setx PATH "%PATH%;%SCRIPTS%" >nul 2>&1
    echo   [ok] %SCRIPTS% añadido al PATH.
)

echo.
echo   [OK] Instalacion completada.
echo   Abre una nueva terminal y escribe: ollama-run
echo.
pause
