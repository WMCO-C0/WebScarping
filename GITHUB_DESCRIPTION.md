# Descripción para GitHub

## Opción 1 (Corta - para el campo About)
Buscador de archivos en sitios web. Encuentra PDFs, Word, Excel, ZIPs y más. CLI + TUI + Web.

## Opción 2 (Media - para la sección del repositorio)
Herramienta multiplataforma para rastrear sitios web y encontrar archivos (PDFs, documentos de Word, Excel, presentaciones, ZIPs). Incluye interfaz de línea de comandos, terminal interactiva (TUI) y aplicación web con Streamlit.

## Opción 3 (Larga - para descripción completa)
File Finder es una herramienta de Python para rastrear sitios web y encontrar archivos como PDFs, documentos de Word, Excel, presentaciones PowerPoint, archivos ZIP y más.

### Características principales:
- **Múltiples interfaces**: CLI, TUI (terminal interactiva con Rich) y Web (Streamlit)
- **Detección inteligente**: Encuentra archivos directos, PDFs embebidos en HTML, y páginas dinámicas como `documento.php?id=XXX`
- **Rastreo paralelo**: Procesa múltiples documentos simultáneamente para mayor velocidad
- **Multiplataforma**: Funciona en Windows, Linux y Mac
- **Exportación**: Resultados en JSON y CSV
- **Configurable**: Profundidad de rastreo, límite de páginas, delay entre requests, y más

### Uso rápido:
```bash
# Instalar
./install.sh  # Linux/Mac
install.bat   # Windows

# Ejecutar
python main.py https://ejemplo.com -o resultados
python tui.py  # Terminal interactiva
streamlit run web.py  # Interfaz web
```

### Tecnologías:
- Python 3.8+
- Requests + BeautifulSoup (web scraping)
- Rich (TUI)
- Streamlit (Web UI)
- Pandas (procesamiento de datos)

## Tags sugeridos para GitHub
`python` `web-scraping` `crawler` `pdf` `file-finder` `streamlit` `rich` `tui` `cli` `multiplatform`