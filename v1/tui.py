import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from urllib.parse import urlparse

from src.crawler import crawl_page
from src.storage import save_results

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
    
    console.print(Panel(banner, border_style="cyan"))


def get_url():
    console.print("\n[bold yellow] ingestion[/bold yellow]")
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


def get_output_name():
    console.print("\n[bold yellow] Archivo de salida[/bold yellow]")
    name = Prompt.ask("  [cyan]Nombre[/cyan] (Enter para automático)", default="")
    return name if name else None


def run_crawl(url, output_name):
    visited = set()
    files_found = []
    pages_crawled = [0]
    
    console.print(f"\n[bold green] Iniciando rastreo...[/bold green]")
    console.print(f"  URL: [cyan]{url}[/cyan]")
    if output_name:
        console.print(f"  Salida: [cyan]{output_name}.json / {output_name}.csv[/cyan]")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Rastreando...", total=None)
        
        # Monkey patch para actualizar progreso
        original_print = builtins_print = __builtins__.__dict__.get('print', print)
        
        def custom_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            if "Profundidad" in msg:
                progress.update(task, description=msg.strip())
            elif "Archivo" in msg:
                progress.update(task, description=msg.strip())
        
        import builtins
        builtins.print = custom_print
        
        try:
            crawl_page(url, 0, visited, files_found, pages_crawled)
        finally:
            builtins.print = builtins_print
        
        progress.update(task, description="[green]Completado![/green]")
    
    return files_found, pages_crawled[0]


def show_results(files_found, pages_crawled, output_name):
    # Resumen
    console.print()
    console.print(Panel(
        f"[bold]Páginas rastreadas:[/bold] {pages_crawled}\n"
        f"[bold]Archivos encontrados:[/bold] {len(files_found)}",
        title="[bold green] Resumen[/bold green]",
        border_style="green"
    ))
    
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
    
    for i, file in enumerate(files_found[:20], 1):
        ext = file.get('extension', 'N/A') or 'N/A'
        url = file.get('url', '')
        source = file.get('source_page', '')
        # Acortar URLs para que quepan
        if len(url) > 60:
            url = url[:57] + "..."
        if len(source) > 40:
            source = "..." + source[-37:]
        
        table.add_row(str(i), ext, url, source)
    
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
    output_name = get_output_name()
    
    files_found, pages_crawled = run_crawl(url, output_name)
    show_results(files_found, pages_crawled, output_name)


if __name__ == "__main__":
    main()