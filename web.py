"""
Web UI con estadísticas de SQLite.
"""
import os
import sys
import streamlit as st
import pandas as pd
from urllib.parse import urlparse

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.crawler import SmartCrawler
from src.storage import save_results
from src.database import CombinedStorage
from src.logger import setup_logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

st.set_page_config(
    page_title="File Finder v2",
    page_icon=" ",
    layout="wide"
)


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def show_historical_stats():
    """Muestra estadísticas históricas de SQLite."""
    db_path = os.path.join(OUTPUT_DIR, "crawl_history.db")
    
    if not os.path.exists(db_path):
        st.info("No hay historial de rastreos previos.")
        return
    
    try:
        storage = CombinedStorage(output_dir=OUTPUT_DIR, db_path=db_path)
        stats = storage.get_stats()
        
        st.subheader(" Estadísticas Históricas")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Archivos", stats.get('total_files', 0))
        with col2:
            st.metric("Total Sesiones", stats.get('total_sessions', 0))
        
        # Archivos por extensión
        if stats.get('by_extension'):
            st.subheader(" Archivos por Extensión")
            df_ext = pd.DataFrame([
                {"Extensión": ext, "Cantidad": count}
                for ext, count in stats['by_extension'].items()
            ])
            st.dataframe(df_ext, use_container_width=True)
    except Exception as e:
        st.warning(f"No se pudieron cargar estadísticas: {e}")


def main():
    st.title("  File Finder v2.0")
    st.markdown("Buscador de archivos con resiliencia completa")
    st.divider()
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        max_depth = st.slider("Profundidad de rastreo", 1, 5, 3)
        max_pages = st.slider("Máximo de páginas", 10, 500, 100)
        delay = st.slider("Delay entre requests (seg)", 0.0, 2.0, 0.5, 0.1)
        concurrent = st.slider("Requests paralelos", 1, 20, 10)
        
        st.divider()
        st.markdown("**Resiliencia activada:**")
        st.markdown("""
        -  Retry con backoff
        -  Robots.txt
        -  User-Agent rotación
        -  SQLite persistencia
        -  Sitemaps
        -  Structured logging
        """)
        
        st.divider()
        st.markdown("**Extensiones buscadas:**")
        st.code(".pdf, .docx, .xlsx, .pptx, .zip, .csv")
    
    # Tabs
    tab1, tab2 = st.tabs(["  Buscar", "  Historial"])
    
    with tab1:
        # Formulario principal
        col1, col2 = st.columns([3, 1])
        
        with col1:
            url = st.text_input(
                " URL del sitio a rastrear",
                placeholder="https://ejemplo.com/documentos",
                label_visibility="visible"
            )
        
        with col2:
            output_name = st.text_input(
                "Nombre de salida",
                placeholder="mi_busqueda",
                label_visibility="visible"
            )
        
        # Botón de búsqueda
        if st.button("  Buscar archivos", type="primary", use_container_width=True):
            if not url:
                st.error("Por favor ingresa una URL")
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if not validate_url(url):
                st.error("URL no válida. Asegúrate de incluir http:// o https://")
                return
            
            # Configuración
            crawler_config = {
                'max_depth': max_depth,
                'max_pages': max_pages,
                'max_concurrent': concurrent,
                'timeout': 30,
            }
            
            # Storage con SQLite
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            storage = CombinedStorage(
                output_dir=OUTPUT_DIR,
                db_path=os.path.join(OUTPUT_DIR, "crawl_history.db")
            )
            
            # Ejecutar rastreo
            with st.spinner("Rastreando sitio web..."):
                setup_logging(level="WARNING")
                crawler = SmartCrawler(crawler_config)
                files_found = crawler.crawl(url, output_name)
            
            # Mostrar resultados
            st.divider()
            
            summary = crawler._metrics.get_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Páginas rastreadas", summary['pages_crawled'])
            with col2:
                st.metric("Archivos encontrados", summary['files_found'])
            with col3:
                st.metric("Errores", summary['errors'])
            with col4:
                st.metric("Páginas/seg", summary['pages_per_second'])
            
            if files_found:
                # Guardar en storage
                session_id = storage.start_session(url)
                for file_info in files_found:
                    storage.save_file(file_info, session_id)
                storage.end_session(session_id, summary['pages_crawled'], summary['files_found'])
                
                filename = output_name if output_name else None
                json_path, csv_path = save_results(files_found, OUTPUT_DIR, filename)
                
                # Mostrar tabla
                st.subheader("  Archivos encontrados")
                
                df = pd.DataFrame(files_found)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    extensions = ["Todas"] + list(df["extension"].unique()) if "extension" in df.columns else ["Todas"]
                    ext_filter = st.selectbox("Filtrar por extensión", extensions)
                with col2:
                    search = st.text_input("Buscar en URLs")
                
                # Aplicar filtros
                filtered_df = df.copy()
                if ext_filter != "Todas" and "extension" in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df["extension"] == ext_filter]
                if search and "url" in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df["url"].str.contains(search, case=False, na=False)]
                
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )
                
                # Botones de descarga
                col1, col2 = st.columns(2)
                with col1:
                    with open(json_path, 'r') as f:
                        st.download_button(
                            "  Descargar JSON",
                            f.read(),
                            file_name=os.path.basename(json_path),
                            mime="application/json"
                        )
                with col2:
                    with open(csv_path, 'r') as f:
                        st.download_button(
                            "  Descargar CSV",
                            f.read(),
                            file_name=os.path.basename(csv_path),
                            mime="text/csv"
                        )
            else:
                st.warning("No se encontraron archivos en el sitio especificado")
    
    with tab2:
        show_historical_stats()


if __name__ == "__main__":
    main()