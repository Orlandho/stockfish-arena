@echo off
setlocal enabledelayedexpansion
title Instalador de Stockfish 19 Arena - Orlando Dorival

:: Cambiar al directorio raiz del proyecto
cd /d "%~dp0\.."

echo ==============================================================================
echo                INSTALADOR OFICIAL: STOCKFISH 19 CHESS ARENA
echo ==============================================================================
echo.
echo  Este instalador configurara la aplicacion de escritorio y creara un
echo  acceso directo en tu Escritorio para que puedas jugar como con cualquier
echo  programa nativo de Windows.
echo.
echo ==============================================================================
echo.

:: 1. Comprobar Python
echo [1/4] Verificando instalacion de Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor instala Python 3.10 o superior desde python.org y vuelve a intentar.
    pause
    exit /b 1
)
python --version
echo [OK] Python detectado correctamente.
echo.

:: 2. Configurar Entorno Virtual (.venv)
echo [2/4] Verificando entorno virtual y dependencias...
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual aislado (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

echo Instalando / actualizando dependencias (FastAPI, WebSockets, pywebview)...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [AVISO] Fallo leve en pip install. Reintentando instalacion de paquetes basicos...
    .\.venv\Scripts\pip install fastapi uvicorn python-chess websockets pywebview Pillow
)
echo [OK] Dependencias listas.
echo.

:: 3. Generar Iconos Oficiales (.ico)
echo [3/4] Comprobando iconos de la aplicacion...
if not exist "assets\icon\app_icon.ico" (
    echo Generando archivo de icono multi-resolucion (.ico)...
    .\.venv\Scripts\python.exe assets\icon\generate_icon.py
)
echo [OK] Iconos listos.
echo.

:: 4. Crear Accesos Directos de Windows
echo [4/4] Creando acceso directo en el Escritorio y Menu Inicio...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "installer\create_shortcut.ps1"
if %errorlevel% neq 0 (
    echo [ERROR] Hubo un problema al crear el acceso directo.
    pause
    exit /b 1
)
echo.

echo ==============================================================================
echo                   INSTALACION COMPLETADA CON EXITO
echo ==============================================================================
echo.
echo  Ya puedes iniciar Stockfish 19 Arena desde el nuevo icono en tu Escritorio:
echo     "Stockfish 19 Arena"
echo.
echo ==============================================================================
echo.

set /p INICIAR="Deseas iniciar Stockfish 19 Arena ahora mismo? (S/N): "
if /i "!INICIAR!"=="S" (
    echo Iniciando aplicacion de escritorio...
    start "" wscript.exe "%~dp0..\launcher_silent.vbs"
)

echo.
echo Gracias por instalar Stockfish 19 Arena. Que disfrutes de tus partidas!
timeout /t 3 >nul
exit /b 0
