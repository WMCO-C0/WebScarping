import os
import re
import requests
from urllib.parse import urlparse, unquote, urljoin
from config import TARGET_EXTENSIONS, DOCUMENT_PAGE_PATTERNS, DOCUMENT_PARAMS, TIMEOUT, DEFAULT_HEADERS


def is_file_link(url):
    """Verifica si la URL termina en una extensión de archivo conocida."""
    parsed = urlparse(url)
    path = unquote(parsed.path).lower()
    for ext in TARGET_EXTENSIONS:
        if path.endswith(ext):
            return True
    return False


def is_document_page(url):
    """Verifica si la URL parece ser una página de documento dinámico (ej: documento.php?id=XXX)."""
    parsed = urlparse(url)
    path = unquote(parsed.path).lower()
    query = parsed.query.lower()
    
    # Verificar si el path coincide con algún patrón de documento
    for pattern in DOCUMENT_PAGE_PATTERNS:
        if re.search(pattern, path):
            # Verificar si tiene parámetros que sugieran un documento específico
            for param in DOCUMENT_PARAMS:
                if param in query:
                    return True
    
    return False


def get_file_extension(url):
    """Extrae la extensión del archivo de la URL."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    _, ext = os.path.splitext(path)
    return ext.lower() if ext else None


def extract_embedded_files(html_content, base_url):
    """Extrae archivos embebidos (PDFs, etc.) del contenido HTML."""
    embedded_files = []
    
    # Buscar en tags <embed>, <object>, <iframe>
    patterns = [
        r'<embed[^>]+src=["\']([^"\']+)["\']',
        r'<object[^>]+data=["\']([^"\']+)["\']',
        r'<iframe[^>]+src=["\']([^"\']+)["\']',
        r'<pdf[^>]+src=["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            full_url = urljoin(base_url, match)
            if is_file_link(full_url) or full_url.lower().endswith('.pdf'):
                embedded_files.append(full_url)
    
    # Buscar enlaces directos a PDFs
    pdf_pattern = r'href=["\']([^"\']*\.pdf[^"\']*)["\']'
    pdf_matches = re.findall(pdf_pattern, html_content, re.IGNORECASE)
    for match in pdf_matches:
        full_url = urljoin(base_url, match)
        embedded_files.append(full_url)
    
    # Buscar en JavaScript
    js_pdf_pattern = r'["\']([^"\']+\.pdf[^"\']*)["\']'
    js_matches = re.findall(js_pdf_pattern, html_content, re.IGNORECASE)
    for match in js_matches:
        if match.startswith('http') or match.startswith('/'):
            full_url = urljoin(base_url, match)
            embedded_files.append(full_url)
    
    return list(set(embedded_files))  # Eliminar duplicados


def check_headers(url):
    """Realiza un request HEAD para verificar Content-Type y Content-Disposition."""
    try:
        response = requests.head(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', '0')
            content_disposition = response.headers.get('Content-Disposition', '')
            
            # Verificar si parece un archivo por Content-Type
            file_types = ['application/pdf', 'application/msword', 'application/zip', 
                         'application/x-rar', 'application/vnd.openxmlformats', 
                         'text/csv', 'application/vnd.ms-excel']
            
            for ft in file_types:
                if ft in content_type:
                    return {
                        'content_type': content_type,
                        'size': content_length,
                        'disposition': content_disposition
                    }
            
            # Si tiene Content-Disposition con filename, probablemente es un archivo
            if 'filename' in content_disposition:
                return {
                    'content_type': content_type,
                    'size': content_length,
                    'disposition': content_disposition
                }
        
        return None
    except (requests.RequestException, Exception):
        return None


def extract_file_info(url, source_url=None, headers_info=None):
    """Extrae información del archivo."""
    ext = get_file_extension(url)
    info = {
        'url': url,
        'extension': ext,
        'source_page': source_url,
        'size': None,
        'content_type': None
    }
    
    if headers_info:
        info['size'] = headers_info.get('size', None)
        info['content_type'] = headers_info.get('content_type', None)
    
    return info