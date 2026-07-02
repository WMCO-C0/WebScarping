"""
File Finder - Buscador de archivos en sitios web
Versión 2.0 con resiliencia completa
"""
import os
import sys
import argparse
from urllib.parse import urlparse

from src.crawler import SmartCrawler
from src.storage import save_results
from src.logger import setup_logging

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
  python main.py https://ejemplo.com --max-depth 5 --max-pages 200
        """
    )
    parser.add_argument("url", nargs="?", help="URL del sitio a rastrear")
    parser.add_argument("-o", "--output", help="Nombre del archivo de salida (sin extensión)")
    parser.add_argument("--max-depth", type=int, default=3, help="Profundidad máxima de rastreo (default: 3)")
    parser.add_argument("--max-pages", type=int, default=100, help="Número máximo de páginas a rastrear (default: 100)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Nivel de logging (default: INFO)")
    parser.add_argument("--log-file", help="Archivo para guardar logs (opcional)")
    parser.add_argument("--json-log", action="store_true", help="Usar formato JSON en logs")
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(level=args.log_level, log_file=args.log_file, json_log=args.json_log)
    
    print("=== File Finder v2.0 ===")
    print("Buscador de archivos con resiliencia completa\n")
    
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
    
    # Configuración del crawler
    config = {
        'max_depth': args.max_depth,
        'max_pages': args.max_pages,
        'max_concurrent': 10,
        'timeout': 30,
    }
    
    # Crear y ejecutar crawler
    crawler = SmartCrawler(config)
    
    try:
        files_found = crawler.crawl(seed_url, output_name)
    except KeyboardInterrupt:
        print("\n\nRastreo interrumpido por el usuario")
        files_found = crawler._files_found
    
    # Guardar resultados
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