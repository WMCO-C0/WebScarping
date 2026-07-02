@echo off
chcp 65001 >nul 2>&1
title File Finder

cd /d "%~dp0"

:: Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Ejecutar con argumentos o pedir URL
if "%~1"=="" (
    python main.py
) else (
    python main.py %*
)
