"""
Módulo de parseo de sitemaps XML.
"""
import logging
import requests
from urllib.parse import urlparse
from xml.etree import ElementTree

logger = logging.getLogger(__name__)

# Namespaces comunes de sitemaps
SITEMAP_NAMESPACES = {
    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1',
    'video': 'http://www.google.com/schemas/sitemap-video/1.1',
    'news': 'http://www.google.com/schemas/sitemap-news/0.9',
}


class SitemapParser:
    """Parser de sitemaps con soporte para sitemap index."""
    
    def __init__(self, user_agent=None, timeout=10):
        self._user_agent = user_agent or "FileFinder/1.0"
        self._timeout = timeout
        self._headers = {"User-Agent": self._user_agent}
        self._parsed_sitemaps = set()
        self._urls = []
    
    def discover_sitemaps(self, base_url):
        """Descubre sitemaps de un sitio."""
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        # URLs comunes de sitemaps
        common_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap-index.xml',
            '/wp-sitemap.xml',
            '/wp-sitemap-index.xml',
        ]
        
        discovered = []
        
        for path in common_paths:
            url = base + path
            try:
                response = requests.get(url, headers=self._headers, timeout=self._timeout)
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'xml' in content_type or response.text.strip().startswith('<?xml'):
                        discovered.append(url)
                        logger.info(f"Sitemap encontrado: {url}")
            except Exception as e:
                logger.debug(f"Error verificando sitemap {url}: {e}")
        
        # También intentar desde robots.txt
        try:
            robots_url = f"{base}/robots.txt"
            response = requests.get(robots_url, headers=self._headers, timeout=self._timeout)
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    if line.strip().lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        if sitemap_url not in discovered:
                            discovered.append(sitemap_url)
                            logger.info(f"Sitemap desde robots.txt: {sitemap_url}")
        except Exception:
            pass
        
        return discovered
    
    def parse(self, sitemap_url, depth=0):
        """Parsea un sitemap y extrae URLs."""
        if sitemap_url in self._parsed_sitemaps or depth > 5:
            return []
        
        self._parsed_sitemaps.add(sitemap_url)
        urls = []
        
        try:
            response = requests.get(sitemap_url, headers=self._headers, timeout=self._timeout)
            if response.status_code != 200:
                logger.warning(f"Error {response.status_code} al obtener sitemap: {sitemap_url}")
                return []
            
            content = response.text
            
            # Parsear XML
            root = ElementTree.fromstring(content)
            
            # Detectar si es sitemap index
            if self._is_sitemap_index(root):
                logger.info(f"Sitemap index detectado: {sitemap_url}")
                # Obtener sitemaps hijos
                for sitemap in root.findall('.//sm:sitemap', SITEMAP_NAMESPACES):
                    loc = sitemap.find('sm:loc', SITEMAP_NAMESPACES)
                    if loc is not None and loc.text:
                        child_urls = self.parse(loc.text.strip(), depth + 1)
                        urls.extend(child_urls)
            else:
                # Es un sitemap normal, extraer URLs
                for url_elem in root.findall('.//sm:url', SITEMAP_NAMESPACES):
                    loc = url_elem.find('sm:loc', SITEMAP_NAMESPACES)
                    if loc is not None and loc.text:
                        url_data = {
                            'url': loc.text.strip(),
                            'lastmod': None,
                            'changefreq': None,
                            'priority': None
                        }
                        
                        # Extraer metadatos opcionales
                        lastmod = url_elem.find('sm:lastmod', SITEMAP_NAMESPACES)
                        if lastmod is not None:
                            url_data['lastmod'] = lastmod.text
                        
                        changefreq = url_elem.find('sm:changefreq', SITEMAP_NAMESPACES)
                        if changefreq is not None:
                            url_data['changefreq'] = changefreq.text
                        
                        priority = url_elem.find('sm:priority', SITEMAP_NAMESPACES)
                        if priority is not None:
                            url_data['priority'] = priority.text
                        
                        urls.append(url_data)
                
                logger.info(f"Sitemap parseado: {sitemap_url} ({len(urls)} URLs)")
        
        except ElementTree.ParseError as e:
            logger.error(f"Error parseando XML de {sitemap_url}: {e}")
        except Exception as e:
            logger.error(f"Error procesando sitemap {sitemap_url}: {e}")
        
        return urls
    
    def _is_sitemap_index(self, root):
        """Verifica si el XML es un sitemap index."""
        # Buscar tag sitemapindex
        for tag in root.iter():
            if 'sitemapindex' in tag.tag.lower():
                return True
            if tag.tag.endswith('}sitemap'):
                return True
        return False
    
    def get_all_urls(self, base_url):
        """Obtiene todas las URLs de todos los sitemaps de un sitio."""
        all_urls = []
        
        # Descubrir sitemaps
        sitemaps = self.discover_sitemaps(base_url)
        
        # Parsear cada sitemap
        for sitemap_url in sitemaps:
            urls = self.parse(sitemap_url)
            all_urls.extend(urls)
        
        # Eliminar duplicados
        seen = set()
        unique_urls = []
        for url_data in all_urls:
            url = url_data['url']
            if url not in seen:
                seen.add(url)
                unique_urls.append(url_data)
        
        logger.info(f"Total URLs únicas de sitemaps: {len(unique_urls)}")
        return unique_urls
    
    def filter_by_extension(self, urls, extensions):
        """Filtra URLs por extensión de archivo."""
        filtered = []
        for url_data in urls:
            url = url_data['url'].lower()
            if any(url.endswith(ext) for ext in extensions):
                filtered.append(url_data)
        return filtered


class SmartSitemapCrawler:
    """Crawler que usa sitemaps para descubrir URLs primero."""
    
    def __init__(self, parser, target_extensions=None):
        self._parser = parser
        self._target_extensions = target_extensions or [
            '.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.csv'
        ]
    
    def discover_file_urls(self, base_url):
        """Descubre URLs de archivos usando sitemaps."""
        logger.info(f"Buscando archivos en sitemaps de {base_url}")
        
        # Obtener todas las URLs
        all_urls = self._parser.get_all_urls(base_url)
        
        # Filtrar por extensiones de archivo
        file_urls = self._parser.filter_by_extension(all_urls, self._target_extensions)
        
        logger.info(f"Archivos encontrados en sitemaps: {len(file_urls)}")
        
        return [
            {
                'url': url_data['url'],
                'source': 'sitemap',
                'lastmod': url_data.get('lastmod'),
                'priority': url_data.get('priority')
            }
            for url_data in file_urls
        ]