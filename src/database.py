"""
Módulo de almacenamiento SQLite para persistencia y deduplicación.
"""
import os
import json
import csv
import sqlite3
import hashlib
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """Almacenamiento persistente con SQLite y deduplicación."""
    
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "output", "filefinder.db")
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    url_hash TEXT NOT NULL,
                    extension TEXT,
                    source_page TEXT,
                    content_type TEXT,
                    size INTEGER,
                    title TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    crawl_session TEXT,
                    status TEXT DEFAULT 'discovered'
                );
                
                CREATE TABLE IF NOT EXISTS crawl_sessions (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    pages_crawled INTEGER DEFAULT 0,
                    files_found INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running'
                );
                
                CREATE TABLE IF NOT EXISTS crawl_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    url TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES crawl_sessions(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_files_url_hash ON files(url_hash);
                CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
                CREATE INDEX IF NOT EXISTS idx_files_discovered ON files(discovered_at);
                CREATE INDEX IF NOT EXISTS idx_crawl_log_session ON crawl_log(session_id);
            """)
    
    @contextmanager
    def _get_connection(self):
        """Obtiene una conexión a la base de datos."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _hash_url(self, url):
        """Genera hash de una URL para deduplicación."""
        normalized = url.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def start_session(self, seed_url):
        """Inicia una nueva sesión de rastreo."""
        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(seed_url) % 10000}"
        
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO crawl_sessions (id, url) VALUES (?, ?)",
                (session_id, seed_url)
            )
        
        logger.info(f"Sesión iniciada: {session_id}")
        return session_id
    
    def end_session(self, session_id, pages_crawled, files_found):
        """Finaliza una sesión de rastreo."""
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE crawl_sessions 
                   SET completed_at = CURRENT_TIMESTAMP, 
                       pages_crawled = ?, 
                       files_found = ?,
                       status = 'completed'
                   WHERE id = ?""",
                (pages_crawled, files_found, session_id)
            )
        
        logger.info(f"Sesión finalizada: {session_id}")
    
    def save_file(self, file_info, session_id=None):
        """Guarda un archivo encontrado (con deduplicación)."""
        url = file_info.get('url', '')
        url_hash = self._hash_url(url)
        
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO files 
                       (url, url_hash, extension, source_page, content_type, size, 
                        title, crawl_session)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        url,
                        url_hash,
                        file_info.get('extension'),
                        file_info.get('source_page'),
                        file_info.get('content_type'),
                        file_info.get('size'),
                        file_info.get('title'),
                        session_id
                    )
                )
                return True
            except sqlite3.IntegrityError:
                # URL ya existe
                return False
    
    def save_files(self, files, session_id=None):
        """Guarda múltiples archivos."""
        saved = 0
        for file_info in files:
            if self.save_file(file_info, session_id):
                saved += 1
        return saved
    
    def file_exists(self, url):
        """Verifica si un archivo ya fue encontrado."""
        url_hash = self._hash_url(url)
        
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM files WHERE url_hash = ?",
                (url_hash,)
            ).fetchone()
            return result[0] > 0
    
    def get_files(self, extension=None, session_id=None, limit=1000):
        """Obtiene archivos filtrados."""
        query = "SELECT * FROM files WHERE 1=1"
        params = []
        
        if extension:
            query += " AND extension = ?"
            params.append(extension)
        
        if session_id:
            query += " AND crawl_session = ?"
            params.append(session_id)
        
        query += " ORDER BY discovered_at DESC LIMIT ?"
        params.append(limit)
        
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]
    
    def get_stats(self, session_id=None):
        """Obtiene estadísticas de la base de datos."""
        with self._get_connection() as conn:
            stats = {}
            
            # Total de archivos
            if session_id:
                result = conn.execute(
                    "SELECT COUNT(*) FROM files WHERE crawl_session = ?",
                    (session_id,)
                ).fetchone()
            else:
                result = conn.execute("SELECT COUNT(*) FROM files").fetchone()
            stats['total_files'] = result[0]
            
            # Por extensión
            query = "SELECT extension, COUNT(*) as count FROM files"
            if session_id:
                query += " WHERE crawl_session = ?"
                params = (session_id,)
            else:
                params = ()
            query += " GROUP BY extension ORDER BY count DESC"
            
            stats['by_extension'] = {
                row['extension']: row['count'] 
                for row in conn.execute(query, params).fetchall()
            }
            
            # Sesiones
            result = conn.execute("SELECT COUNT(*) FROM crawl_sessions").fetchone()
            stats['total_sessions'] = result[0]
            
            return stats
    
    def log_request(self, session_id, url, status_code, response_time, error=None):
        """Registra un request en el log."""
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO crawl_log 
                   (session_id, url, status_code, response_time, error_message)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, url, status_code, response_time, error)
            )


class CombinedStorage:
    """Almacenamiento combinado: SQLite + JSON/CSV."""
    
    def __init__(self, output_dir, db_path=None):
        self._output_dir = output_dir
        self._sqlite = SQLiteStorage(db_path)
        self._files_buffer = []
        self._buffer_size = 100
    
    def start_session(self, seed_url):
        return self._sqlite.start_session(seed_url)
    
    def end_session(self, session_id, pages_crawled, files_found):
        self._sqlite.end_session(session_id, pages_crawled, files_found)
        self._flush_buffer(session_id)
    
    def save_file(self, file_info, session_id=None):
        # Guardar en SQLite
        saved = self._sqlite.save_file(file_info, session_id)
        
        # Agregar al buffer
        if saved:
            self._files_buffer.append(file_info)
            if len(self._files_buffer) >= self._buffer_size:
                self._flush_buffer(session_id)
        
        return saved
    
    def _flush_buffer(self, session_id):
        """Exporta el buffer a JSON/CSV."""
        if not self._files_buffer:
            return
        
        # Aquí podrías exportar incrementalmente si es necesario
        self._files_buffer = []
    
    def export_json(self, filename=None):
        """Exporta todos los archivos a JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}.json"
        
        filepath = os.path.join(self._output_dir, filename)
        files = self._sqlite.get_files(limit=999999)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exportado JSON: {filepath}")
        return filepath
    
    def export_csv(self, filename=None):
        """Exporta todos los archivos a CSV."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}.csv"
        
        filepath = os.path.join(self._output_dir, filename)
        files = self._sqlite.get_files(limit=999999)
        
        if files:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=files[0].keys())
                writer.writeheader()
                writer.writerows(files)
        
        logger.info(f"Exportado CSV: {filepath}")
        return filepath
    
    def get_stats(self, session_id=None):
        return self._sqlite.get_stats(session_id)