"""
Módulo de robots.txt: Parseo y cumplimiento.
"""
import re
import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class RobotsParser:
    """Parser de robots.txt con caché y funcionalidades avanzadas."""
    
    def __init__(self, user_agent="*"):
        self._parsers = {}
        self._sitemaps = {}
        self._crawldelays = {}
        self._user_agent = user_agent
    
    def fetch(self, base_url):
        """Obtiene y parsea robots.txt de un sitio."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        if robots_url in self._parsers:
            return self._parsers[robots_url]
        
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        try:
            parser.read()
            self._parsers[robots_url] = parser
            
            # Extraer sitemaps declarados
            self._extract_sitemaps(parser, robots_url)
            
            # Extraer crawl-delay
            self._extract_crawldelay(parser)
            
            logger.info(f"Robots.txt cargado: {robots_url}")
            return parser
            
        except Exception as e:
            logger.warning(f"Error cargando robots.txt {robots_url}: {e}")
            # Si no hay robots.txt, permitir todo
            return None
    
    def _extract_sitemaps(self, parser, robots_url):
        """Extrae URLs de sitemaps del robots.txt."""
        sitemaps = []
        
        try:
            # Acceder al contenido raw del robots.txt
            # RobotFileParser no expone sitemaps directamente
            # Pero podemos parsear el archivo manualmente
            from urllib.request import urlopen
            response = urlopen(robots_url, timeout=10)
            content = response.read().decode('utf-8', errors='ignore')
            
            for line in content.split('\n'):
                line = line.strip()
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemaps.append(sitemap_url)
            
            self._sitemaps[robots_url] = sitemaps
            
        except Exception as e:
            logger.debug(f"Error extrayendo sitemaps de {robots_url}: {e}")
            self._sitemaps[robots_url] = []
    
    def _extract_crawldelay(self, parser):
        """Extrae crawl-delay del robots.txt."""
        try:
            # RobotFileParser no expone crawl-delay directamente
            # Pero podemos intentar obtenerlo
            crawl_delay = parser.crawl_delay(self._user_agent)
            if crawl_delay:
                self._crawldelays[parser.url] = float(crawl_delay)
        except:
            pass
    
    def can_fetch(self, url, user_agent=None):
        """Verifica si se puede rastrear una URL."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        parser = self._parsers.get(robots_url)
        if not parser:
            # Si no hay robots.txt, permitir
            return True
        
        ua = user_agent or self._user_agent
        
        try:
            return parser.can_fetch(ua, url)
        except Exception as e:
            logger.debug(f"Error verificando robots.txt para {url}: {e}")
            return True  # En caso de error, permitir
    
    def get_sitemaps(self, url):
        """Obtiene los sitemaps declarados para un sitio."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        return self._sitemaps.get(robots_url, [])
    
    def get_crawldelay(self, url):
        """Obtiene el crawl-delay para un sitio."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        return self._crawldelays.get(robots_url, None)
    
    def get_allowed_paths(self, url):
        """Obtiene las rutas permitidas para nuestro user-agent."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        parser = self._parsers.get(robots_url)
        if not parser:
            return ["/"]
        
        # Esto es una simplificación - RobotFileParser no expone esto directamente
        return ["/"]


def normalize_robots_url(url):
    """Normaliza una URL para robots.txt."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"