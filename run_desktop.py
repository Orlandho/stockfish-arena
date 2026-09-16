"""
Lanzador de Escritorio Nativo para Stockfish 19 Arena.
Inicia el servidor ASGI local en segundo plano y despliega una ventana
de escritorio nativa de Windows (mediante Edge WebView2 / pywebview)
con fallback transparente a modo aplicación standalone.
"""

import sys
import os
import time
import threading
import subprocess
import urllib.request
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon", "app_icon.ico")
SERVER_URL = "http://127.0.0.1:8000"

# Servidor en hilo demonio
server_instance = None
is_running = True

def start_server():
    global server_instance
    config = uvicorn.Config(
        "server:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
        access_log=False
    )
    server_instance = uvicorn.Server(config)
    server_instance.run()

def wait_for_server(timeout=10.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(SERVER_URL, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False

def launch_fallback_app():
    """Lanza la ventana en modo aplicación mediante Edge o Chrome instalado."""
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    browser_bin = None
    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            browser_bin = p
            break

    if browser_bin:
        args = [
            browser_bin,
            f"--app={SERVER_URL}",
            "--window-size=1280,860",
            f"--app-id=Stockfish19Arena"
        ]
        proc = subprocess.Popen(args)
        proc.wait()
    else:
        import webbrowser
        webbrowser.open(SERVER_URL)
        # Mantener proceso vivo hasta que el usuario cierre la consola
        try:
            while is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def main():
    global is_running
    # 1. Iniciar servidor en segundo plano
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Esperar a que el servidor responda
    if not wait_for_server():
        print("Error: No se pudo iniciar el servidor local en el tiempo esperado.")
        sys.exit(1)

    # 3. Intentar desplegar con pywebview (Edge WebView2 nativo)
    webview_launched = False
    try:
        import webview
        
        window = webview.create_window(
            title="Stockfish 19 Arena",
            url=SERVER_URL,
            width=1280,
            height=860,
            min_size=(960, 640),
            resizable=True
        )

        def on_closed():
            global is_running
            is_running = False
            if server_instance:
                server_instance.should_exit = True

        window.events.closed += on_closed
        
        # Desplegar ventana con motor WebView2 nativo
        webview.start(icon=ICON_PATH if os.path.exists(ICON_PATH) else None)
        webview_launched = True
    except Exception as e:
        print(f"Aviso: pywebview no pudo iniciarse ({e}). Conmutando a modo aplicación...")

    # 4. Si pywebview no se ejecutó, usar el fallback nativo
    if not webview_launched:
        launch_fallback_app()

    # Finalizar servidor limpiamente
    if server_instance:
        server_instance.should_exit = True

if __name__ == "__main__":
    main()
