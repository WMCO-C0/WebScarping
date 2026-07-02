<div align="center">

#   File Finder

**Buscador de archivos en sitios web**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-orange.svg)]()

Encuentra PDFs, documentos de Word, Excel, ZIPs y más en cualquier página web.

[Instalación](#instalación-rápida) • [Uso](#uso) • [Configuración](#configuración) • [Contribuir](#contribuir)

</div>

---

## ✨ Características

- **Múltiples interfaces**: CLI, TUI (terminal) y Web (navegador)
- **Detección inteligente**: Archivos directos, embebidos y páginas dinámicas
- **Rastreo paralelo**: Procesa múltiples documentos simultáneamente
- **Multiplataforma**: Windows, Linux y Mac
- **Exportación**: Resultados en JSON y CSV
- **Configurable**: Profundidad, páginas, delay y más

##   Instalación rápida

### Requisitos

- **Python 3.8+** ([descargar](https://www.python.org/downloads/))
- En **Windows**: marcar "Add Python to PATH" durante instalación

### Windows

```cmd
install.bat
```

### Linux / Mac

```bash
chmod +x install.sh
./install.sh
```

### Manual (cualquier sistema)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

##  ️ Uso

### Tres formas de usar

| Modo | Comando | Mejor para |
|------|---------|------------|
| **CLI** | `python main.py URL` | Scripts, automatización |
| **TUI** | `python tui.py` | Uso interactivo en terminal |
| **Web** | `streamlit run web.py` | Interfaz gráfica, compartir |

---

### Modo CLI

```bash
# Básico
python main.py https://ejemplo.com/documentos

# Con nombre de salida
python main.py https://ejemplo.com -o mi_busqueda

# Windows
run.bat https://ejemplo.com -o resultado
```

### Modo TUI

```bash
python tui.py
# Interfaz interactiva con tablas y colores
```

### Modo Web

```bash
streamlit run web.py
# Se abre en http://localhost:8501
```

**Características Web:**
- Panel de configuración lateral
- Tabla interactiva con filtros
- Botones de descarga
- Log de rastreo en tiempo real

---

### Atajos por plataforma

| Acción | Windows | Linux/Mac |
|--------|---------|-----------|
| Instalar | `install.bat` | `./install.sh` |
| CLI | `run.bat URL` | `./run.sh URL` |
| TUI | `run-tui.bat` | `./run-tui.sh` |
| Web | `run-web.bat` | `./run-web.sh` |

## ⚙️ Configuración

Edita `config.py` o usa el panel lateral en modo Web:

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `MAX_DEPTH` | 2 | Profundidad de rastreo |
| `MAX_PAGES` | 200 | Máximo de páginas |
| `DELAY_BETWEEN_REQUESTS` | 0.1 | Pausa entre requests (seg) |
| `MAX_CONCURRENT` | 10 | Requests paralelos |
| `TIMEOUT` | 10 | Timeout por request (seg) |
| `TARGET_EXTENSIONS` | `.pdf, .docx, ...` | Extensiones a buscar |

##   Salida

Los resultados se guardan en `output/`:

```
output/
├── mi_busqueda.json    # Todos los detalles
└── mi_busqueda.csv     # Para Excel
```

**Estructura JSON:**
```json
[
  {
    "url": "https://ejemplo.com/doc.pdf",
    "extension": ".pdf",
    "source_page": "https://ejemplo.com/documentos/",
    "size": null,
    "content_type": null
  }
]
```

##   Qué detecta

| Tipo | Ejemplo |
|------|---------|
| **Archivos directos** | `documento.pdf`, `datos.xlsx` |
| **PDFs embebidos** | `<embed src="doc.pdf">` |
| **Páginas dinámicas** | `documento.php?id=123` |
| **Enlaces en JS** | `"file": "reporte.pdf"` |

##  ️ Estructura del proyecto

```
file-finder/
├── src/
│   ├── detector.py     # Detección de archivos
│   ├── crawler.py      # Rastreo de páginas
│   └── storage.py      # Guardar resultados
├── main.py             # CLI
├── tui.py              # Terminal interactiva
├── web.py              # Interfaz web
├── config.py           # Configuración
├── requirements.txt    # Dependencias
├── install.sh/.bat     # Instaladores
├── run*.sh/.bat        # Ejecutadores
└── output/             # Resultados
```

##   Ejemplo rápido

```bash
# Probar con sitio de prueba
python ejemplo.py

# Buscar documentos en un sitio
python main.py https://www.coljuristas.org/observatorio_jep/documentos.php -o coljuristas
```

##   Solución de problemas

| Error | Solución |
|-------|----------|
| "Python no encontrado" | Instalar desde python.org y reiniciar terminal |
| "pip no encontrado" | `python -m ensurepip --upgrade` |
| "No se encontraron archivos" | Verificar URL, ajustar `MAX_DEPTH` |
| Crawler lento | Reducir `MAX_PAGES`, aumentar delay |

##  ️ Consideraciones éticas

- Respeta `robots.txt` y términos de servicio
- No descargues contenido protegido por derechos de autor
- Identifica tu User-Agent para transparencia
- Usa delay entre requests para no sobrecargar servidores

## Contribuir

Las contribuciones son bienvenidas. Abrí un issue o enviá un pull request.

## Licencia

MIT - Ver [LICENSE](LICENSE)

---

<div align="center">

Hecho con ❤️ en Python

</div>