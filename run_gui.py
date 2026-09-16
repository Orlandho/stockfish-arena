"""
Script de lanzamiento automático de la GUI de Stockfish 19.
Inicia el servidor local FastAPI en localhost:8000 y abre automáticamente el navegador.
"""

import sys
import os
import webbrowser
import time
import threading
import uvicorn

def open_browser():
    time.sleep(1.2)
    print("\nAbriendo la interfaz en tu navegador: http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("   STOCKFISH 19 - CHESS ARENA (GUI INTERACTIVA)")
    print("=" * 60)
    print("Iniciando servidor local en http://localhost:8000")
    print("Para salir, presiona Ctrl+C en esta terminal.")
    print("=" * 60)

    # Abrir el navegador en un hilo separado
    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar servidor Uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, log_level="info")
