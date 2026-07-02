"""
TUI con métricas en tiempo real usando Rich.
"""
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from urllib.parse import urlparse
import time

from src.crawler import SmartCrawler
from src.storage import save_results
from src.logger import setup_logging, CrawlMetrics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

console = Console()


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def show_banner():
    banner = Text()
    banner.append("███████╗ ██████╗ ██████╗ ███████╗███████╗", style="bold cyan")
    banner.append("\n██╔════╝██╔════╝██╔═══██╗██╔════╝██╔════╝", style="bold cyan")
    banner.append("\n█████╗  ██║     ██║   ██║█████╗  ███████╗", style="bold cyan")
    banner.append("\n██╔══╝  ██║     ██║   ██║██╔══╝  ╚════██║", style="bold cyan")
    banner.append("\n██║     ╚██████╗╚██████╔╝███████╗███████║", style="bold cyan")
    banner.append("\n╚═╝      ╚═════╝ ╚═════╝ ╚══════╝╚══════╝", style="bold cyan")
    banner.append("\n       Buscador de Archivos en Sitios Web", style="dim")
    banner.append("\n       [bold green]v2.0 - Con Resiliencia Completa[/bold green]", style="dim")
    
    console.print(Panel(banner, border_style="cyan"))


def get_url():
    console.print("\n[bold yellow] CONFIGURACIÓN[/bold yellow]")
    url = Prompt.ask("  [cyan]URL del sitio[/cyan]")
    
    if not url:
        console.print("[red]Error: URL no válida[/red]")
        sys.exit(1)
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    if not validate_url(url):
        console.print("[red]Error: URL no válida. Asegúrate de incluir http:// o https://[/red]")
        sys.exit(1)
    
    return url


def get_config():
    """Obtiene configuración adicional del usuario."""
    console.print("\n[bold yellow] CONFIGURACIÓN AVANZADA[/bold yellow]")
    
    max_depth = Prompt.ask(
        "  [cyan]Profundidad máxima[/cyan]", 
        default="3"
    )
    
    max_pages = Prompt.ask(
        "  [cyan]Máximo de páginas[/cyan]", 
        default="100"
    )
    
    output_name = Prompt.ask(
        "  [cyan]Nombre de salida[/cyan] (Enter para automático)", 
        default=""
    )
    
    return {
        'max_depth': int(max_depth),
        'max_pages': int(max_pages),
        'output_name': output_name if output_name else None,
    }


def create_live_display():
    """Crea un layout para métricas en tiempo real."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    return layout


def get_status_panel(metrics):
    """Genera panel de estado actualizado."""
    summary = metrics.get_summary()
    
    status_text = Text()
    status_text.append("Páginas: ", style="bold")
    status_text.append(f"{summary['pages_crawled']}", style="cyan")
    status_text.append(" | ")
    status_text.append("Archivos: ", style="bold")
    status_text.append(f"{summary['files_found']}", style="green")
    status_text.append(" | ")
    status_text.append("Errores: ", style="bold")
    status_text.append(f"{summary['errors']}", style="red" if summary['errors'] > 0 else "dim")
    status_text.append(" | ")
    status_text.append("P/s: ", style="bold")
    status_text.append(f"{summary['pages_per_second']}", style="yellow")
    status_text.append(" | ")
    status_text.append("Dominios: ", style="bold")
    status_text.append(f"{summary['domains_visited']}", style="magenta")
    
    return Panel(status_text, title="[bold]Estado[/bold]", border_style="blue")


def run_crawl(url, config):
    """Ejecuta el rastreo con métricas en tiempo real."""
    setup_logging(level="WARNING")  # Silenciar logs en TUI
    
    console.print(f"\n[bold green] INICIANDO RASTREO[/bold green]")
    console.print(f"  URL: [cyan]{url}[/cyan]")
    console.print(f"  Profundidad: [cyan]{config['max_depth']}[/cyan]")
    console.print(f"  Máx. páginas: [cyan]{config['max_pages']}[/cyan]")
    console.print()
    
    # Crear crawler
    crawler_config = {
        'max_depth': config['max_depth'],
        'max_pages': config['max_pages'],
        'max_concurrent': 10,
        'timeout': 30,
    }
    crawler = SmartCrawler(crawler_config)
    
    # Ejecutar con Live display
    start_time = time.time()
    
    with Live(create_live_display(), refresh_per_second=2, console=console) as live:
        # Simular actualizaciones de progreso
        # En producción, esto se integraría con callbacks del crawler
        try:
            files_found = crawler.crawl(url, config['output_name'])
        except KeyboardInterrupt:
            console.print("\n[yellow]Rastreo interrumpido[/yellow]")
            files_found = crawler._files_found
        
        # Actualización final
        layout = create_live_display()
        layout["header"].update(get_status_panel(crawler._metrics))
        layout["body"].update(Panel(
            f"[green]Rastreo completado en {time.time() - start_time:.1f}s[/green]",
            title="Resultado"
        ))
        live.update(layout)
    
    return files_found, crawler._metrics


def show_results(files_found, metrics, output_name):
    """Muestra los resultados del rastreo."""
    summary = metrics.get_summary()
    
    # Panel de resumen
    console.print()
    console.print(Panel(
        f"[bold]Duración:[/bold] {summary['duration_seconds']}s\n"
        f"[bold]Páginas rastreadas:[/bold] {summary['pages_crawled']}\n"
        f"[bold]Archivos encontrados:[/bold] {summary['files_found']}\n"
        f"[bold]Errores:[/bold] {summary['errors']}\n"
        f"[bold]Reintentos:[/bold] {summary['retries']}\n"
        f"[bold]Páginas/segundo:[/bold] {summary['pages_per_second']}\n"
        f"[bold]Tiempo resp. promedio:[/bold] {summary['avg_response_time_ms']}ms",
        title="[bold green] RESUMEN[/bold green]",
        border_style="green"
    ))
    
    # Archivos por extensión
    if summary['files_by_extension']:
        ext_table = Table(title="Archivos por extensión", show_lines=True)
        ext_table.add_column("Extensión", style="cyan")
        ext_table.add_column("Cantidad", style="green", justify="right")
        
        for ext, count in sorted(summary['files_by_extension'].items(), 
                                 key=lambda x: x[1], reverse=True)[:10]:
            ext_table.add_row(ext, str(count))
        
        console.print(ext_table)
    
    if not files_found:
        console.print("\n[yellow]No se encontraron archivos.[/yellow]")
        console.print("Posibles causas:")
        console.print("  - El sitio no contiene archivos con las extensiones buscadas")
        console.print("  - Los archivos están protegidos o requieren autenticación")
        return
    
    # Tabla de resultados
    table = Table(title="Archivos encontrados", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Ext", style="cyan", width=6)
    table.add_column("URL", style="white")
    table.add_column("Origen", style="dim")
    table.add_column("Fuente", style="magenta")
    
    for i, file in enumerate(files_found[:20], 1):
        ext = file.get('extension', 'N/A') or 'N/A'
        url = file.get('url', '')
        source = file.get('source_page', '')
        source_type = file.get('source', 'crawl')
        
        # Acortar URLs
        if len(url) > 50:
            url = url[:47] + "..."
        if len(source) > 30:
            source = "..." + source[-27:]
        
        table.add_row(str(i), ext, url, source, source_type)
    
    console.print(table)
    
    if len(files_found) > 20:
        console.print(f"\n  [dim]... y {len(files_found) - 20} archivos más[/dim]")
    
    # Guardar
    json_path, csv_path = save_results(files_found, OUTPUT_DIR, output_name)
    
    console.print(Panel(
        f"[bold green] Archivos guardados[/bold green]\n\n"
        f"  [cyan]JSON:[/cyan] {json_path}\n"
        f"  [cyan]CSV:[/cyan]  {csv_path}",
        border_style="green"
    ))


def main():
    show_banner()
    
    url = get_url()
    config = get_config()
    
    files_found, metrics = run_crawl(url, config)
    show_results(files_found, metrics, config['output_name'])


if __name__ == "__main__":
    main()