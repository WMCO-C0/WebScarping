@echo off
chcp 65001 >nul 2>&1
title File Finder - Instalador

echo =========================================
echo   File Finder - Instalador
echo =========================================
echo.

:: Verificar Python
echo 1. Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: Python no encontrado.
    echo    Instala Python desde: https://www.python.org/downloads/
    echo    IMPORTANTE: Marca "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo    OK: %PYVER%

:: Verificar pip
echo.
echo 2. Verificando pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: pip no encontrado.
    echo    Ejecuta: python -m ensurepip --upgrade
    pause
    exit /b 1
)
echo    OK: pip encontrado

:: Crear entorno virtual
echo.
echo 3. Creando entorno virtual...
if not exist "venv" (
    python -m venv venv
    echo    OK: Entorno virtual creado
) else (
    echo    AVISO: Entorno virtual ya existe
)

:: Activar entorno virtual
echo.
echo 4. Activando entorno virtual...
call venv\Scripts\activate.bat
echo    OK: Entorno activado

:: Actualizar pip
echo.
echo 5. Actualizando pip...
python -m pip install --upgrade pip --quiet
echo    OK: pip actualizado

:: Instalar dependencias
echo.
echo 6. Instalando dependencias...
pip install -r requirements.txt --quiet
echo    OK: Dependencias instaladas

echo.
echo =========================================
echo   ¡Instalacion completada!
echo =========================================
echo.
echo Para ejecutar:
echo   run.bat
echo.
echo O manualmente:
echo   venv\Scripts\activate
echo   python main.py URL_DEL_SITIO
echo.
pause
