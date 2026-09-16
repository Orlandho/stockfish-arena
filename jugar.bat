@echo off
title Stockfish 19 Arena - Orlando Dorival
cd /d "%~dp0"

echo ========================================================
echo       STOCKFISH 19 - GUI INTERACTIVA DE AJEDREZ
echo ========================================================
echo.
echo Iniciando entorno virtual y servidor...

if exist .venv\Scripts\python.exe (
    start "" http://localhost:8000
    .venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
) else (
    echo [ERROR] No se encontro el entorno virtual .venv.
    echo Creando entorno e instalando dependencias...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
    start "" http://localhost:8000
    .venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
)

pause
