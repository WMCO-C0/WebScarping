#!/bin/bash
# File Finder - Script de ejecución para Linux/Mac

cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar con argumentos o pedir URL
if [ $# -gt 0 ]; then
    python main.py "$@"
else
    python main.py
fi
