# Extensiones de archivos a buscar
TARGET_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx', '.zip', '.csv', '.rar', '.7z', '.txt', '.odt', '.ods', '.odp']

# Patrones de URLs que parecen páginas de documentos dinámicos
DOCUMENT_PAGE_PATTERNS = [
    r'documento\.php',
    r'doc\.php',
    r'article\.php',
    r'page\.php',
    r'view\.php',
    r'item\.php',
    r'content\.php',
    r'news\.php',
    r'post\.php',
    r'download\.php',
    r'file\.php',
]

# Parámetros GET que sugieren un documento específico
DOCUMENT_PARAMS = ['id', 'doc', 'document', 'file', 'item', 'page', 'content']

# Configuración de WordPress
WORDPRESS_ENABLED = True  # Buscar en /wp-content/uploads/
WORDPRESS_CHECK_API = True  # Usar REST API de WordPress
WORDPRESS_CHECK_SITEMAPS = True  # Buscar en sitemaps
WORDPRESS_UPLOAD_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]  # Años a revisar

# Configuración de rastreo
MAX_DEPTH = 2
DELAY_BETWEEN_REQUESTS = 0.1  # segundos
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
TIMEOUT = 10  # segundos para requests
MAX_PAGES = 200  # límite de páginas a rastrear
MAX_CONCURRENT = 10  # requests paralelos para páginas de documento

# Configuración de headers para requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.8,*/*;q=0.7',
    'Accept-Language': 'es,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}