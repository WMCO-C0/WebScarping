#!/bin/bash
# File Finder - Web (interfaz en navegador)
cd "$(dirname "$0")"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
echo "Abriendo File Finder en el navegador..."
echo "Presiona Ctrl+C para cerrar"
streamlit run web.py "$@"