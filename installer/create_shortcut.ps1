# ==============================================================================
# Script de creación de Accesos Directos de Windows (.lnk) para Stockfish 19 Arena
# Utiliza la interfaz COM WScript.Shell para configurar icono, target y argumentos.
# ==============================================================================

$ErrorActionPreference = "Stop"

# Directorio base del proyecto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir

$VbsLauncher = Join-Path $BaseDir "launcher_silent.vbs"
$IconPath = Join-Path $BaseDir "assets\icon\app_icon.ico"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$StartMenuPath = [Environment]::GetFolderPath("Programs")

Write-Host "Configurando accesos directos de Windows..." -ForegroundColor Cyan

$WshShell = New-Object -ComObject WScript.Shell

# 1. Acceso Directo en el Escritorio
$DesktopLnkPath = Join-Path $DesktopPath "Stockfish 19 Arena.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopLnkPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$VbsLauncher`""
$Shortcut.WorkingDirectory = $BaseDir
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath,0"
}
$Shortcut.Description = "Stockfish 19 Arena - Ajedrez con Inteligencia Artificial"
$Shortcut.Save()
Write-Host "Acceso directo en Escritorio creado con exito: $DesktopLnkPath" -ForegroundColor Green

# 2. Acceso Directo en el Menú Inicio de Windows
try {
    $StartMenuLnkPath = Join-Path $StartMenuPath "Stockfish 19 Arena.lnk"
    $StartShortcut = $WshShell.CreateShortcut($StartMenuLnkPath)
    $StartShortcut.TargetPath = "wscript.exe"
    $StartShortcut.Arguments = "`"$VbsLauncher`""
    $StartShortcut.WorkingDirectory = $BaseDir
    if (Test-Path $IconPath) {
        $StartShortcut.IconLocation = "$IconPath,0"
    }
    $StartShortcut.Description = "Stockfish 19 Arena - Ajedrez con Inteligencia Artificial"
    $StartShortcut.Save()
    Write-Host "Acceso directo en Menu Inicio creado con exito: $StartMenuLnkPath" -ForegroundColor Green
} catch {
    Write-Warning "No se pudo crear el acceso directo en el Menu Inicio: $_"
}

Write-Host "`nConfiguracion de accesos directos completada al 100%." -ForegroundColor Green
