@echo off
title Desinstalador de Accesos Directos - Stockfish 19 Arena
echo ==============================================================================
echo           DESINSTALADOR DE ACCESOS DIRECTOS - STOCKFISH 19 ARENA
echo ==============================================================================
echo.
echo Este script eliminara los accesos directos de Stockfish 19 Arena del
echo Escritorio y del Menu Inicio de Windows.
echo (Los archivos del proyecto y tus partidas guardadas NO se eliminaran).
echo.
set /p CONFIRMAR="Estas seguro de que deseas desinstalar los accesos directos? (S/N): "
if /i not "%CONFIRMAR%"=="S" (
    echo Operacion cancelada por el usuario.
    pause
    exit /b 0
)

powershell.exe -NoProfile -Command "
$Desktop = [Environment]::GetFolderPath('Desktop');
$StartMenu = [Environment]::GetFolderPath('Programs');
$Lnk1 = Join-Path $Desktop 'Stockfish 19 Arena.lnk';
$Lnk2 = Join-Path $StartMenu 'Stockfish 19 Arena.lnk';

if (Test-Path $Lnk1) { Remove-Item $Lnk1 -Force; Write-Host 'Acceso directo de Escritorio eliminado.' -ForegroundColor Green; }
if (Test-Path $Lnk2) { Remove-Item $Lnk2 -Force; Write-Host 'Acceso directo de Menu Inicio eliminado.' -ForegroundColor Green; }
Write-Host 'Desinstalacion de accesos directos completada.' -ForegroundColor Cyan;
"

echo.
pause
