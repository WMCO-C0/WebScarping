@echo off
chcp 65001 >nul 2>&1
title File Finder - Web
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)
echo Abriendo File Finder en el navegador...
echo Presiona Ctrl+C para cerrar
streamlit run web.py %*