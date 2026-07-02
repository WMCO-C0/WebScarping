import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config import (DEFAULT_HEADERS, TIMEOUT, TARGET_EXTENSIONS,
                    WORDPRESS_ENABLED, WORDPRESS_CHECK_API, WORDPRESS_CHECK_SITEMAPS,
                    WORDPRESS_UPLOAD_YEARS)


def is_wordpress(html_content, url):
    """Detecta si un sitio es WordPress."""
    indicators = [
        'wp-content',
        'wp-includes',
        'wp-json',
        'wordpress',
        'wp-embed.min.js',
        'wp-includes/js/',
        'content="WordPress"',
        '/wp-admin/',
    ]
    
    html_lower = html_content.lower()
    
    for indicator in indicators:
        if indicator in html_lower:
            return True
    
    # Verificar meta generator
    soup = BeautifulSoup(html_content, 'lxml')
    meta_gen = soup.find('meta', attrs={'name': 'generator'})
    if meta_gen and 'wordpress' in str(meta_gen.get('content', '')).lower():
        return True
    
    return False


def get_wp_version(html_content):
    """Extrae la versión de WordPress si está disponible."""
    patterns = [
        r'content="WordPress\s+([\d.]+)"',
        r'wp-includes/js/wp-emoji-release\.min\.js\?ver=([\d.]+)',
        r'ver=([\d.]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
    
    return None


def find_wp_uploads(base_url):
    """Busca archivos en /wp-content/uploads/."""
    files = []
    
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # Construir paths de uploads
    upload_paths = ['/wp-content/uploads/']
    for year in WORDPRESS_UPLOAD_YEARS:
        upload_paths.append(f'/wp-content/uploads/{year}/')
    
    for path in upload_paths:
        url = base + path
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Buscar enlaces a archivos
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(url, href)
                    
                    # Verificar si es un archivo
                    if any(full_url.lower().endswith(ext) for ext in TARGET_EXTENSIONS):
                        files.append(full_url)
                    
                    # Si es subcarpeta de fecha (MM), explorarla
                    if re.match(r'.*/\d{2}/$', href):
                        sub_url = urljoin(url, href)
                        files.extend(find_wp_month_files(sub_url))
        
        except Exception:
            continue
    
    return list(set(files))


def find_wp_month_files(month_url):
    """Busca archivos en un mes específico de uploads."""
    files = []
    
    try:
        response = requests.get(month_url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(month_url, href)
                
                if any(full_url.lower().endswith(ext) for ext in TARGET_EXTENSIONS):
                    files.append(full_url)
    except Exception:
        pass
    
    return files


def find_wp_rest_api(base_url):
    """Busca archivos usando la REST API de WordPress."""
    if not WORDPRESS_CHECK_API:
        return []
    
    files = []
    
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # Endpoint de media de WordPress
    api_url = f"{base}/wp-json/wp/v2/media?per_page=100"
    
    try:
        response = requests.get(api_url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            
            for item in data:
                if 'source_url' in item:
                    files.append(item['source_url'])
    
    except Exception:
        pass
    
    return files


def find_wp_sitemaps(base_url):
    """Busca archivos en sitemaps de WordPress."""
    if not WORDPRESS_CHECK_SITEMAPS:
        return []
    
    files = []
    
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # URLs de sitemaps comunes
    sitemap_urls = [
        f"{base}/wp-sitemap.xml",
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
    ]
    
    for sitemap_url in sitemap_urls:
        try:
            response = requests.get(sitemap_url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                
                # Buscar URLs de archivos
                for loc in soup.find_all('loc'):
                    url = loc.text.strip()
                    if any(url.lower().endswith(ext) for ext in TARGET_EXTENSIONS):
                        files.append(url)
                
                # Buscar sub-sitemaps
                for sitemap in soup.find_all('sitemap'):
                    sub_loc = sitemap.find('loc')
                    if sub_loc:
                        sub_files = find_wp_sitemaps(sub_loc.text.strip())
                        files.extend(sub_files)
        
        except Exception:
            continue
    
    return list(set(files))


def crawl_wordpress(url, html_content):
    """Rastrea un sitio WordPress buscando archivos."""
    if not WORDPRESS_ENABLED:
        return []
    
    files = []
    
    # Obtener versión de WordPress
    wp_version = get_wp_version(html_content)
    if wp_version:
        print(f"  → WordPress v{wp_version} detectado")
    else:
        print("  → Sitio WordPress detectado")
    
    # 1. Buscar en la página actual
    soup = BeautifulSoup(html_content, 'lxml')
    for a in soup.find_all('a', href=True):
        full_url = urljoin(url, a['href'])
        if any(full_url.lower().endswith(ext) for ext in TARGET_EXTENSIONS):
            files.append(full_url)
    
    # 2. Buscar en uploads
    print("  → Buscando en /wp-content/uploads/...")
    wp_files = find_wp_uploads(url)
    files.extend(wp_files)
    print(f"    Encontrados {len(wp_files)} archivos en uploads")
    
    # 3. Buscar en REST API
    print("  → Buscando en REST API...")
    api_files = find_wp_rest_api(url)
    files.extend(api_files)
    print(f"    Encontrados {len(api_files)} archivos en API")
    
    # 4. Buscar en sitemaps
    print("  → Buscando en sitemaps...")
    sitemap_files = find_wp_sitemaps(url)
    files.extend(sitemap_files)
    print(f"    Encontrados {len(sitemap_files)} archivos en sitemaps")
    
    return list(set(files))