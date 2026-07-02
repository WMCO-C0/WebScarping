import os
import sys
import streamlit as st
import pandas as pd
from urllib.parse import urlparse

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.crawler import crawl_page
from src.storage import save_results

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

st.set_page_config(
    page_title="File Finder",
    page_icon=" ",
    layout="wide"
)


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def main():
    st.title("  File Finder")
    st.markdown("Buscador de archivos en sitios web")
    st.divider()
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        max_depth = st.slider("Profundidad de rastreo", 1, 5, 2)
        max_pages = st.slider("Máximo de páginas", 10, 500, 100)
        delay = st.slider("Delay entre requests (seg)", 0.0, 2.0, 0.1, 0.1)
        concurrent = st.slider("Requests paralelos", 1, 20, 10)
        
        st.divider()
        st.markdown("**Extensiones buscadas:**")
        st.code(".pdf, .docx, .xlsx, .pptx, .zip, .csv")
    
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
        
        # Aplicar configuración
        import config
        config.MAX_DEPTH = max_depth
        config.MAX_PAGES = max_pages
        config.DELAY_BETWEEN_REQUESTS = delay
        config.MAX_CONCURRENT = concurrent
        
        # Ejecutar rastreo
        with st.spinner("Rastreando sitio web..."):
            visited = set()
            files_found = []
            pages_crawled = [0]
            
            # Capturar output del crawler
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                crawl_page(url, 0, visited, files_found, pages_crawled)
            
            output_log = f.getvalue()
        
        # Mostrar resultados
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Páginas rastreadas", pages_crawled[0])
        with col2:
            st.metric("Archivos encontrados", len(files_found))
        with col3:
            if files_found:
                st.metric("Tipos únicos", len(set(f.get('extension', '') for f in files_found)))
        
        if files_found:
            # Guardar resultados
            filename = output_name if output_name else None
            json_path, csv_path = save_results(files_found, OUTPUT_DIR, filename)
            
            # Mostrar tabla
            st.subheader(" Archivos encontrados")
            
            df = pd.DataFrame(files_found)
            df.columns = ["URL", "Extensión", "Página origen", "Tamaño", "Tipo"]
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                extensions = ["Todas"] + list(df["Extensión"].unique())
                ext_filter = st.selectbox("Filtrar por extensión", extensions)
            with col2:
                search = st.text_input("Buscar en URLs")
            
            # Aplicar filtros
            filtered_df = df.copy()
            if ext_filter != "Todas":
                filtered_df = filtered_df[filtered_df["Extensión"] == ext_filter]
            if search:
                filtered_df = filtered_df[filtered_df["URL"].str.contains(search, case=False, na=False)]
            
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
            
            # Log del crawler
            with st.expander(" Ver log del rastreo"):
                st.code(output_log, language=None)
        else:
            st.warning("No se encontraron archivos en el sitio especificado")
            
            with st.expander(" Posibles causas"):
                st.markdown("""
                - El sitio no contiene archivos con las extensiones buscadas
                - Los archivos están protegidos o requieren autenticación
                - La estructura del sitio impide el rastreo
                - Intenta aumentar la profundidad de rastreo
                """)


if __name__ == "__main__":
    main()