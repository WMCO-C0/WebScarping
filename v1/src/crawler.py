import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from config import (MAX_DEPTH, DELAY_BETWEEN_REQUESTS, TIMEOUT, MAX_PAGES,
                    MAX_CONCURRENT, DEFAULT_HEADERS)
from src.detector import (is_file_link, is_document_page, check_headers,
                          extract_file_info, extract_embedded_files)
from src.wordpress import is_wordpress, crawl_wordpress


def normalize_url(url, base_url):
    return urljoin(base_url, url)


def normalize_url_for_crawling(url):
    parsed = urlparse(url)
    non_content_params = ['lan', 'lang', 'language', 'hl', 'refresh', 'nocache', 't']
    params = parse_qs(parsed.query)
    filtered_params = {k: v for k, v in params.items() if k.lower() not in non_content_params}
    filtered_query = urlencode(filtered_params, doseq=True)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if filtered_query:
        normalized += f"?{filtered_query}"
    return normalized


def is_internal_link(url, base_domain):
    parsed = urlparse(url)
    return parsed.netloc == base_domain or parsed.netloc == ''


def should_skip_url(url):
    skip_patterns = [
        'javascript:', 'mailto:', 'tel:', 'whatsapp:',
        'facebook.com/sharer', 'x.com/share', 'twitter.com/share',
        'linkedin.com/share', 'plus.google.com', '#',
        '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
        '.ico', '.woff', '.woff2', '.ttf', '.eot',
    ]
    url_lower = url.lower()
    for pattern in skip_patterns:
        if pattern in url_lower:
            return True
    return False


def fetch_document_page(url, source_url):
    """Obtiene una página de documento y extrae archivos embebidos."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
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


def crawl_page(url, depth, visited, files_found, pages_crawled):
    if depth > MAX_DEPTH or pages_crawled[0] >= MAX_PAGES:
        return

    normalized = normalize_url_for_crawling(url)
    if normalized in visited:
        return

    visited.add(normalized)
    visited.add(url)
    pages_crawled[0] += 1

    print(f"[Profundidad {depth}] Rastreando: {url}")

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            return

        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        base_domain = urlparse(url).netloc

        # Detectar WordPress en la primera página
        if depth == 0 and is_wordpress(html_content, url):
            wp_files = crawl_wordpress(url, html_content)
            for file_url in wp_files:
                if not any(f['url'] == file_url for f in files_found):
                    file_info = extract_file_info(file_url, source_url=url)
                    files_found.append(file_info)
                    print(f"  → WordPress: {file_url}")

        if is_document_page(url):
            for info in extract_embedded_files(html_content, url):
                if not any(f['url'] == info for f in files_found):
                    file_info = extract_file_info(info, source_url=url)
                    files_found.append(file_info)
                    print(f"  → Archivo encontrado: {info}")
            return

        # Archivos embebidos directos
        for file_url in extract_embedded_files(html_content, url):
            if not any(f['url'] == file_url for f in files_found):
                file_info = extract_file_info(file_url, source_url=url)
                files_found.append(file_info)
                print(f"  → Archivo embebido: {file_url}")

        # Recopilar enlaces
        internal_links = []
        doc_page_urls = []

        for a in soup.find_all('a', href=True):
            full_url = normalize_url(a['href'], url)
            if should_skip_url(full_url):
                continue
            if is_file_link(full_url):
                if not any(f['url'] == full_url for f in files_found):
                    file_info = extract_file_info(full_url, source_url=url)
                    files_found.append(file_info)
                    print(f"  → Archivo encontrado: {full_url}")
            elif is_document_page(full_url):
                norm = normalize_url_for_crawling(full_url)
                if norm not in visited:
                    visited.add(norm)
                    visited.add(full_url)
                    doc_page_urls.append(full_url)
            elif is_internal_link(full_url, base_domain):
                norm = normalize_url_for_crawling(full_url)
                if norm not in visited:
                    internal_links.append(full_url)

        # Procesar páginas de documento en paralelo
        if doc_page_urls:
            print(f"  → Procesando {len(doc_page_urls)} páginas de documento en paralelo...")
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
                futures = {executor.submit(fetch_document_page, doc_url, url): doc_url
                          for doc_url in doc_page_urls}
                for future in as_completed(futures):
                    doc_url = futures[future]
                    try:
                        results = future.result()
                        for file_info in results:
                            if not any(f['url'] == file_info['url'] for f in files_found):
                                files_found.append(file_info)
                                print(f"  → Archivo de documento: {file_info['url']}")
                    except Exception:
                        pass
                    pages_crawled[0] += 1

        # Rastrear enlaces internos (no documentos) recursivamente
        for link in internal_links:
            if pages_crawled[0] >= MAX_PAGES:
                break
            time.sleep(DELAY_BETWEEN_REQUESTS)
            crawl_page(link, depth + 1, visited, files_found, pages_crawled)

    except requests.RequestException as e:
        print(f"  → Error al acceder a {url}: {e}")
    except Exception as e:
        print(f"  → Error inesperado en {url}: {e}")