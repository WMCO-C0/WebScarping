#!/bin/bash
# File Finder - Script de instalación para Linux/Mac

set -e

echo "========================================="
echo "  File Finder - Instalador"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar Python
echo "1. Verificando Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "${RED}Error: Python no encontrado.${NC}"
    echo "Instala Python desde: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo -e "   ${GREEN}✓${NC} $PYTHON_VERSION"

# Verificar pip
echo ""
echo "2. Verificando pip..."
if command -v pip3 &>/dev/null; then
    PIP=pip3
elif command -v pip &>/dev/null; then
    PIP=pip
else
    echo -e "${RED}Error: pip no encontrado.${NC}"
    echo "Ejecuta: $PYTHON -m ensurepip --upgrade"
    exit 1
fi

PIP_VERSION=$($PIP --version 2>&1 | cut -d' ' -f1)
echo -e "   ${GREEN}✓${NC} pip $PIP_VERSION"

# Crear entorno virtual
echo ""
echo "3. Creando entorno virtual..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo -e "   ${GREEN}✓${NC} Entorno virtual creado"
else
    echo -e "   ${YELLOW}⚠${NC} Entorno virtual ya existe"
fi

# Activar entorno virtual
echo ""
echo "4. Activando entorno virtual..."
source venv/bin/activate
echo -e "   ${GREEN}✓${NC} Entorno activado"

# Actualizar pip
echo ""
echo "5. Actualizando pip..."
pip install --upgrade pip --quiet
echo -e "   ${GREEN}✓${NC} pip actualizado"

# Instalar dependencias
echo ""
echo "6. Instalando dependencias..."
pip install -r requirements.txt --quiet
echo -e "   ${GREEN}✓${NC} Dependencias instaladas"

# Hacer scripts ejecutables
echo ""
echo "7. Configurando permisos..."
chmod +x run.sh 2>/dev/null || true
chmod +x ejemplo.py 2>/dev/null || true
echo -e "   ${GREEN}✓${NC} Permisos configurados"

echo ""
echo "========================================="
echo -e "  ${GREEN}¡Instalación completada!${NC}"
echo "========================================="
echo ""
echo "Para ejecutar:"
echo "  ./run.sh"
echo ""
echo "O manualmente:"
echo "  source venv/bin/activate"
echo "  python main.py URL_DEL_SITIO"
echo ""
