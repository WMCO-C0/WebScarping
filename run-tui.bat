@echo off
chcp 65001 >nul 2>&1
title File Finder - TUI
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)
python tui.py %*