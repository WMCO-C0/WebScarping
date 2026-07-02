"""
Módulo de logging estructurado con métricas.
"""
import os
import sys
import json
import logging
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager


class StructuredFormatter(logging.Formatter):
    """Formatter que produce logs estructurados (JSON)."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Agregar campos extra si existen
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data
        
        # Agregar info de excepción
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class HumanFormatter(logging.Formatter):
    """Formatter legible para humanos en terminal."""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        
        # Timestamp compacto
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Logger name corto
        name = record.name.split(".")[-1] if record.name != "root" else ""
        
        # Formato
        parts = [
            f"{color}{timestamp}{self.RESET}",
            f"{color}{record.levelname:8}{self.RESET}",
        ]
        
        if name:
            parts.append(f"[{name}]")
        
        parts.append(record.getMessage())
        
        return " ".join(parts)


class CrawlMetrics:
    """Métricas del crawler en tiempo real."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Resetea las métricas."""
        self.start_time = datetime.now()
        self.pages_crawled = 0
        self.files_found = 0
        self.errors = 0
        self.retries = 0
        self.rate_limited = 0
        self.skipped_urls = 0
        self.domainsVisited = defaultdict(int)
        self.files_by_extension = defaultdict(int)
        self.response_times = []
    
    def record_page(self, url, status_code, response_time):
        """Registra el rastreo de una página."""
        self.pages_crawled += 1
        
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        self.domainsVisited[domain] += 1
        
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.errors += 1
    
    def record_file(self, url, extension):
        """Registra un archivo encontrado."""
        self.files_found += 1
        self.files_by_extension[extension] += 1
    
    def record_retry(self):
        """Registra un reintento."""
        self.retries += 1
    
    def record_rate_limit(self):
        """Registra un rate limit."""
        self.rate_limited += 1
    
    def record_skip(self):
        """Registra una URL saltada."""
        self.skipped_urls += 1
    
    def get_summary(self):
        """Obtiene un resumen de las métricas."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )
        
        pages_per_second = self.pages_crawled / elapsed if elapsed > 0 else 0
        
        return {
            "duration_seconds": round(elapsed, 2),
            "pages_crawled": self.pages_crawled,
            "files_found": self.files_found,
            "errors": self.errors,
            "retries": self.retries,
            "rate_limited": self.rate_limited,
            "skipped_urls": self.skipped_urls,
            "domains_visited": len(self.domainsVisited),
            "pages_per_second": round(pages_per_second, 2),
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "files_by_extension": dict(self.files_by_extension),
        }
    
    def print_summary(self):
        """Imprime un resumen formateado."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("  RESUMEN DEL RASTREO")
        print("=" * 60)
        print(f"  Duración:           {summary['duration_seconds']}s")
        print(f"  Páginas rastreadas: {summary['pages_crawled']}")
        print(f"  Archivos encontrados: {summary['files_found']}")
        print(f"  Errores:            {summary['errors']}")
        print(f"  Reintentos:         {summary['retries']}")
        print(f"  Rate limited:       {summary['rate_limited']}")
        print(f"  URLs saltadas:      {summary['skipped_urls']}")
        print(f"  Dominios visitados: {summary['domains_visited']}")
        print(f"  Páginas/segundo:    {summary['pages_per_second']}")
        print(f"  Tiempo resp. promedio: {summary['avg_response_time_ms']}ms")
        
        if summary['files_by_extension']:
            print("\n  Archivos por extensión:")
            for ext, count in sorted(summary['files_by_extension'].items(), 
                                     key=lambda x: x[1], reverse=True)[:10]:
                print(f"    {ext}: {count}")
        
        print("=" * 60)


def setup_logging(level="INFO", log_file=None, json_log=False):
    """
    Configura el logging de la aplicación.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Archivo para guardar logs (opcional)
        json_log: Si True, usa formato JSON
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Limpiar handlers existentes
    root_logger.handlers = []
    
    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    if json_log:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(HumanFormatter())
    root_logger.addHandler(console_handler)
    
    # Handler de archivo (opcional)
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    return root_logger


@contextmanager
def log_operation(logger, operation_name, **extra_data):
    """
    Context manager para loggear operaciones con timing.
    
    Usage:
        with log_operation(logger, "fetch", url="http://..."):
            # hacer algo
            pass
    """
    start = datetime.now()
    logger.info(f"Iniciando: {operation_name}", extra={"extra_data": extra_data})
    
    try:
        yield
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(
            f"Completado: {operation_name} ({elapsed:.2f}s)",
            extra={"extra_data": {**extra_data, "elapsed_seconds": elapsed}}
        )
    except Exception as e:
        elapsed = (datetime.now() - start).total_seconds()
        logger.error(
            f"Error en {operation_name}: {e} ({elapsed:.2f}s)",
            extra={"extra_data": {**extra_data, "error": str(e), "elapsed_seconds": elapsed}}
        )
        raise