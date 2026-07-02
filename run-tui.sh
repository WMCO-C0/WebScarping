#!/bin/bash
# File Finder - TUI (interfaz en terminal)
cd "$(dirname "$0")"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python tui.py "$@"