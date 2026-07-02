"""
Crawler principal v2 - Integración completa de todos los módulos.
"""
import time
import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup

from config import (MAX_DEPTH, DELAY_BETWEEN_REQUESTS, TIMEOUT, MAX_PAGES,
                    MAX_CONCURRENT, DEFAULT_HEADERS, TARGET_EXTENSIONS)
from src.detector import (is_file_link, is_document_page, check_headers,
                          extract_file_info, extract_embedded_files)
from src.wordpress import is_wordpress, crawl_wordpress
from src.resilience import RateLimiter, CircuitBreaker, SmartDelay
from src.robots import RobotsParser
from src.useragents import UserAgentRotator, DynamicHeaders, DelayGenerator
from src.sitemaps import SitemapParser, SmartSitemapCrawler
from src.logger import CrawlMetrics, setup_logging, log_operation

logger = logging.getLogger(__name__)


class SmartCrawler:
    """Crawler inteligente con todas las optimizaciones."""
    
    def __init__(self, config=None):
        # Configuración
        self._max_depth = config.get('max_depth', MAX_DEPTH) if config else MAX_DEPTH
        self._max_pages = config.get('max_pages', MAX_PAGES) if config else MAX_PAGES
        self._max_concurrent = config.get('max_concurrent', MAX_CONCURRENT) if config else MAX_CONCURRENT
        self._timeout = config.get('timeout', TIMEOUT) if config else TIMEOUT
        
        # Módulos de resiliencia
        self._rate_limiter = RateLimiter()
        self._circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self._smart_delay = SmartDelay(initial_delay=DELAY_BETWEEN_REQUESTS)
        
        # Robots.txt
        self._robots_parser = RobotsParser()
        
        # User-Agents
        self._ua_rotator = UserAgentRotator(strategy="random")
        self._headers_generator = DynamicHeaders()
        self._delay_generator = DelayGenerator(min_delay=0.5, max_delay=2.0)
        
        # Sitemaps
        self._sitemap_parser = SitemapParser(user_agent="FileFinder/1.0")
        self._sitemap_crawler = SmartSitemapCrawler(self._sitemap_parser, TARGET_EXTENSIONS)
        
        # Métricas
        self._metrics = CrawlMetrics()
        
        # Estado
        self._visited = set()
        self._files_found = []
        self._session = requests.Session()
    
    def crawl(self, seed_url, output_name=None):
        """
        Rastrea un sitio web buscando archivos.
        
        Args:
            seed_url: URL inicial
            output_name: Nombre para archivos de salida (opcional)
        
        Returns:
            Lista de archivos encontrados
        """
        # Configurar logging
        setup_logging(level="INFO")
        
        logger.info(f"Iniciando rastreo de: {seed_url}")
        self._metrics.reset()
        
        # Fase 1: Descubrir URLs de sitemaps
        logger.info("Fase 1: Buscando URLs en sitemaps...")
        sitemap_urls = []
        try:
            sitemap_urls = self._sitemap_crawler.discover_file_urls(seed_url)
            logger.info(f"URLs encontradas en sitemaps: {len(sitemap_urls)}")
        except Exception as e:
            logger.warning(f"Error al buscar sitemaps: {e}")
        
        # Agregar archivos de sitemaps
        for url_data in sitemap_urls:
            file_info = extract_file_info(url_data['url'], source_url=seed_url)
            file_info['source'] = 'sitemap'
            self._files_found.append(file_info)
            self._metrics.record_file(url_data['url'], file_info.get('extension', ''))
        
        # Fase 2: Rastreo tradicional
        logger.info("Fase 2: Rastreo de páginas...")
        
        # Cargar robots.txt
        self._robots_parser.fetch(seed_url)
        
        # Verificar robots.txt
        if not self._robots_parser.can_fetch(seed_url):
            logger.warning(f"robots.txt prohíbe rastrear {seed_url}")
        
        # Iniciar rastreo
        self._crawl_page(seed_url, 0)
        
        # Resumen
        self._metrics.print_summary()
        
        return self._files_found
    
    def _crawl_page(self, url, depth):
        """Rastrea una página individual."""
        if depth > self._max_depth or self._metrics.pages_crawled >= self._max_pages:
            return
        
        # Normalizar URL
        normalized = self._normalize_url(url)
        if normalized in self._visited:
            return
        
        # Verificar robots.txt
        if not self._robots_parser.can_fetch(url):
            logger.debug(f"Saltando (robots.txt): {url}")
            self._metrics.record_skip()
            return
        
        # Verificar circuit breaker
        domain = urlparse(url).netloc
        if self._circuit_breaker.is_open(domain):
            logger.warning(f"Circuit breaker abierto para {domain}, saltando: {url}")
            self._metrics.record_skip()
            return
        
        # Rate limiting
        self._rate_limiter.wait(domain)
        
        # Delay inteligente
        delay = self._smart_delay.get_delay(domain)
        time.sleep(delay)
        
        # Preparar request
        self._visited.add(normalized)
        self._visited.add(url)
        self._metrics.pages_crawled += 1
        
        # Obtener headers dinámicos
        user_agent = self._ua_rotator.get()
        headers = self._headers_generator.get_headers(user_agent)
        
        logger.info(f"[Profundidad {depth}] Rastreando: {url}")
        
        try:
            start_time = time.time()
            response = self._session.get(url, headers=headers, timeout=self._timeout)
            response_time = time.time() - start_time
            
            # Registrar métricas
            self._metrics.record_page(url, response.status_code, response_time)
            
            # Verificar rate limit
            if response.status_code == 429:
                self._metrics.record_rate_limit()
                self._smart_delay.update(domain, False, 429)
                logger.warning(f"Rate limited en {domain}")
                return
            
            # Verificar errores
            if response.status_code >= 400:
                self._circuit_breaker.record_failure(domain)
                self._smart_delay.update(domain, False, response.status_code)
                logger.warning(f"Error {response.status_code} en {url}")
                return
            
            # Éxito
            self._circuit_breaker.record_success(domain)
            self._smart_delay.update(domain, True)
            
            # Verificar content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Detectar WordPress
            if depth == 0 and is_wordpress(html_content, url):
                wp_files = crawl_wordpress(url, html_content)
                for file_url in wp_files:
                    if not any(f['url'] == file_url for f in self._files_found):
                        file_info = extract_file_info(file_url, source_url=url)
                        self._files_found.append(file_info)
                        self._metrics.record_file(file_url, file_info.get('extension', ''))
                        logger.info(f"WordPress: {file_url}")
            
            # Buscar archivos embebidos
            for file_url in extract_embedded_files(html_content, url):
                if not any(f['url'] == file_url for f in self._files_found):
                    file_info = extract_file_info(file_url, source_url=url)
                    self._files_found.append(file_info)
                    self._metrics.record_file(file_url, file_info.get('extension', ''))
                    logger.info(f"Archivo embebido: {file_url}")
            
            # Recopilar enlaces
            internal_links = []
            doc_page_urls = []
            
            for a in soup.find_all('a', href=True):
                full_url = urljoin(url, a['href'])
                
                if self._should_skip_url(full_url):
                    continue
                
                if is_file_link(full_url):
                    if not any(f['url'] == full_url for f in self._files_found):
                        file_info = extract_file_info(full_url, source_url=url)
                        self._files_found.append(file_info)
                        self._metrics.record_file(full_url, file_info.get('extension', ''))
                        logger.info(f"Archivo encontrado: {full_url}")
                
                elif is_document_page(full_url):
                    norm = self._normalize_url(full_url)
                    if norm not in self._visited:
                        self._visited.add(norm)
                        self._visited.add(full_url)
                        doc_page_urls.append(full_url)
                
                elif self._is_internal_link(full_url, domain):
                    norm = self._normalize_url(full_url)
                    if norm not in self._visited:
                        internal_links.append(full_url)
            
            # Procesar páginas de documento en paralelo
            if doc_page_urls:
                logger.info(f"Procesando {len(doc_page_urls)} páginas de documento...")
                with ThreadPoolExecutor(max_workers=self._max_concurrent) as executor:
                    futures = {
                        executor.submit(self._fetch_document_page, doc_url, url): doc_url
                        for doc_url in doc_page_urls
                    }
                    for future in as_completed(futures):
                        doc_url = futures[future]
                        try:
                            results = future.result()
                            for file_info in results:
                                if not any(f['url'] == file_info['url'] for f in self._files_found):
                                    self._files_found.append(file_info)
                                    self._metrics.record_file(
                                        file_info['url'], 
                                        file_info.get('extension', '')
                                    )
                                    logger.info(f"Archivo de documento: {file_info['url']}")
                        except Exception as e:
                            logger.debug(f"Error procesando documento: {e}")
                        self._metrics.pages_crawled += 1
            
            # Rastrear enlaces internos recursivamente
            for link in internal_links:
                if self._metrics.pages_crawled >= self._max_pages:
                    break
                self._crawl_page(link, depth + 1)
        
        except requests.RequestException as e:
            self._circuit_breaker.record_failure(domain)
            self._smart_delay.update(domain, False)
            logger.error(f"Error de request en {url}: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en {url}: {e}")
    
    def _fetch_document_page(self, url, source_url):
        """Obtiene una página de documento y extrae archivos embebidos."""
        try:
            user_agent = self._ua_rotator.get()
            headers = self._headers_generator.get_headers(user_agent)
            
            response = self._session.get(url, headers=headers, timeout=self._timeout)
            if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                embedded_files = extract_embedded_files(response.text, url)
                results = []
                for file_url in embedded_files:
                    info = extract_file_info(file_url, source_url=source_url)
                    results.append(info)
                return results
        except Exception:
            pass
        return []
    
    def _normalize_url(self, url):
        """Normaliza una URL para evitar duplicados."""
        parsed = urlparse(url)
        non_content_params = ['lan', 'lang', 'language', 'hl', 'refresh', 'nocache', 't']
        params = parse_qs(parsed.query)
        filtered_params = {k: v for k, v in params.items() if k.lower() not in non_content_params}
        filtered_query = urlencode(filtered_params, doseq=True)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if filtered_query:
            normalized += f"?{filtered_query}"
        return normalized
    
    def _is_internal_link(self, url, base_domain):
        """Verifica si una URL es interna."""
        parsed = urlparse(url)
        return parsed.netloc == base_domain or parsed.netloc == ''
    
    def _should_skip_url(self, url):
        """Determina si una URL debe ser saltada."""
        skip_patterns = [
            'javascript:', 'mailto:', 'tel:', 'whatsapp:',
            'facebook.com/sharer', 'x.com/share', 'twitter.com/share',
            'linkedin.com/share', 'plus.google.com', '#',
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.ico', '.woff', '.woff2', '.ttf', '.eot',
        ]
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in skip_patterns)


def crawl_page(url, depth, visited, files_found, pages_crawled):
    """
    Función de compatibilidad con el código anterior.
    Wrapper para SmartCrawler.
    """
    crawler = SmartCrawler()
    crawler._visited = visited
    crawler._files_found = files_found
    crawler._metrics.pages_crawled = pages_crawled[0] if pages_crawled else 0
    
    crawler._crawl_page(url, depth)
    
    # Actualizar páginas rastreadas
    if pages_crawled:
        pages_crawled[0] = crawler._metrics.pages_crawled