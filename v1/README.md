# File Finder v1

Versión original del File Finder sin módulos de resiliencia.

## Archivos

- `main.py` - CLI interface
- `tui.py` - TUI interface (Rich)
- `web.py` - Web interface (Streamlit)
- `config.py` - Configuración
- `src/` - Módulos core (crawler, detector, wordpress, storage)

## Uso

```bash
# CLI
python main.py https://ejemplo.com -o test

# TUI
python tui.py

# Web
python web.py
```

## Nota

Esta es la versión original. Para la versión completa con resiliencia, usa los archivos en el directorio raíz.