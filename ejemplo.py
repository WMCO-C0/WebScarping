#!/usr/bin/env python3
"""
Script de ejemplo para probar File Finder
"""
import subprocess
import sys
import os


def main():
    print("=== Ejemplo de File Finder ===\n")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("config.py"):
        print("Error: Ejecuta este script desde el directorio file-finder/")
        sys.exit(1)
    
    # Crear sitio de prueba
    print("1. Creando sitio de prueba local...")
    os.makedirs("test_site", exist_ok=True)
    
    with open("test_site/index.html", "w") as f:
        f.write('''<html>
<head><title>Test</title></head>
<body>
<h1>Sitio de Prueba</h1>
<a href="documento.pdf">PDF de ejemplo</a>
<a href="informe.docx">Word de ejemplo</a>
<a href="datos.xlsx">Excel de ejemplo</a>
<a href="page2.html">Mas contenido</a>
</body>
</html>''')
    
    with open("test_site/page2.html", "w") as f:
        f.write('''<html>
<head><title>Pagina 2</title></head>
<body>
<h1>Pagina 2</h1>
<a href="presentacion.pptx">PowerPoint</a>
<a href="archivo.zip">ZIP</a>
</body>
</html>''')
    
    print("   Sitio creado en test_site/")
    
    # Iniciar servidor
    print("\n2. Iniciando servidor local en puerto 8080...")
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080"],
        cwd="test_site",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    import time
    time.sleep(1)
    
    try:
        # Ejecutar file finder
        print("\n3. Ejecutando File Finder...")
        print("-" * 40)
        
        result = subprocess.run(
            [sys.executable, "main.py", "http://localhost:8080"],
            capture_output=False
        )
        
        print("\n" + "=" * 40)
        print("4. ¡Ejemplo completado!")
        print("\nRevisa la carpeta output/ para ver los resultados.")
        
    finally:
        # Detener servidor
        server.terminate()
        server.wait()
        
        # Limpiar
        import shutil
        shutil.rmtree("test_site", ignore_errors=True)
        print("\n5. Sitio de prueba eliminado.")


if __name__ == "__main__":
    main()