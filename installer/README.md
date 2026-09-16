# 📦 Instalador de Stockfish 19 Arena para Windows

Esta carpeta contiene la suite de automatización e instalación de **Stockfish 19 Arena** como aplicación de escritorio nativa de Windows.

---

## 📂 Contenido de la Carpeta

| Archivo | Descripción |
| :--- | :--- |
| [`instalar.bat`](file:///C:/Users/Orlando/Desktop/stockfish/installer/instalar.bat) | **Instalador principal de un solo clic**. Verifica Python, configura `.venv`, instala dependencias y genera el acceso directo en el Escritorio. |
| [`create_shortcut.ps1`](file:///C:/Users/Orlando/Desktop/stockfish/installer/create_shortcut.ps1) | Script PowerShell que crea los accesos directos `.lnk` con icono oficial en el **Escritorio** y en el **Menú Inicio**. |
| [`desinstalar.bat`](file:///C:/Users/Orlando/Desktop/stockfish/installer/desinstalar.bat) | Script para eliminar los accesos directos creados si en el futuro se desea remover la aplicación. |

---

## 🚀 Instrucciones de Instalación

1. Haz doble clic sobre [`instalar.bat`](file:///C:/Users/Orlando/Desktop/stockfish/installer/instalar.bat).
2. El instalador configurará el entorno y creará el acceso directo:
   - **Nombre:** `Stockfish 19 Arena`
   - **Ubicación:** En tu Escritorio de Windows y en el Menú Inicio.
   - **Icono:** Icono oficial en alta resolución (`assets/icon/app_icon.ico`).
3. Al finalizar, podrás iniciar la aplicación inmediatamente desde la consola o haciendo doble clic sobre el icono en tu Escritorio.

---

## 🖥️ Características de la Versión de Escritorio

- **Ventana Nativa Independiente:** Sin barra de URLs, sin pestañas de navegador ni menús innecesarios.
- **Motor Dual Resiliente:** Ejecución primaria mediante **Microsoft Edge WebView2 (`pywebview`)**, con conmutación automática (*fallback*) a modo ventana de aplicación.
- **Lanzamiento 100% Silencioso:** Mediante [`launcher_silent.vbs`](file:///C:/Users/Orlando/Desktop/stockfish/launcher_silent.vbs), **sin consolas negras CMD de fondo**.
- **Apagado Limpio:** Al cerrar la ventana, se detiene el subproceso de Stockfish y el servidor local de manera ordenada sin dejar procesos colgados.
