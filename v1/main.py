import os
import sys
import argparse
from urllib.parse import urlparse
from src.crawler import crawl_page
from src.storage import save_results

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def validate_url(url):
    """Valida que la URL tenga un formato correcto."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="File Finder - Buscador de archivos en sitios web",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py https://ejemplo.com/documentos
  python main.py https://ejemplo.com -o mi_busqueda
  python main.py https://ejemplo.com --output informe_final
        """
    )
    parser.add_argument("url", nargs="?", help="URL del sitio a rastrear")
    parser.add_argument("-o", "--output", help="Nombre del archivo de salida (sin extensión)")
    
    args = parser.parse_args()
    
    print("=== File Finder ===")
    print("Buscador de archivos en sitios web\n")
    
    # Obtener URL
    seed_url = args.url
    if not seed_url:
        seed_url = input("Ingresa la URL del sitio a rastrear: ").strip()
    
    # Validar URL
    if not validate_url(seed_url):
        print("Error: URL no válida. Asegúrate de incluir http:// o https://")
        sys.exit(1)
    
    if not seed_url.startswith(('http://', 'https://')):
        seed_url = 'https://' + seed_url
    
    # Obtener nombre de archivo de salida
    output_name = args.output
    if not output_name:
        output_name = input("Nombre del archivo de salida (Enter para automático): ").strip()
        if not output_name:
            output_name = None
    
    print(f"\nIniciando rastreo de: {seed_url}")
    if output_name:
        print(f"Archivo de salida: {output_name}.json / {output_name}.csv")
    print("-" * 50)
    
    # Estructuras de datos
    visited = set()
    files_found = []
    pages_crawled = [0]
    
    # Iniciar rastreo
    try:
        crawl_page(seed_url, 0, visited, files_found, pages_crawled)
    except KeyboardInterrupt:
        print("\n\nRastreo interrumpido por el usuario")
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN DEL RASTREO")
    print("=" * 50)
    print(f"Páginas rastreadas: {pages_crawled[0]}")
    print(f"Archivos encontrados: {len(files_found)}")
    
    if files_found:
        save_results(files_found, OUTPUT_DIR, output_name)
        
        print(f"\nPrimeros 10 archivos encontrados:")
        for i, file in enumerate(files_found[:10], 1):
            ext = file.get('extension', 'N/A')
            size = file.get('size', 'N/A')
            print(f"  {i}. [{ext}] {file['url']}")
            if size and size != 'N/A':
                print(f"     Tamaño: {size} bytes")
        
        if len(files_found) > 10:
            print(f"  ... y {len(files_found) - 10} archivos más")
    else:
        print("\nNo se encontraron archivos en el sitio especificado.")
        print("Posibles causas:")
        print("  - El sitio no contiene archivos con las extensiones buscadas")
        print("  - Los archivos están protegidos o requieren autenticación")
        print("  - La estructura del sitio impide el rastreo")


if __name__ == "__main__":
    main()