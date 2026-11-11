import os
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# 1. Configuración de página
st.set_page_config(
    page_title="Siniestralidad Vial - Comuna de Talca",
    layout="wide"
)

# Estilo CSS personalizado institucional
st.markdown("""
    <style>
    /* Estilos del Header */
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 0.8rem;
    }
    .institution-tag {
        font-size: 0.85rem;
        font-weight: 700;
        color: #003366;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* REGLA ESPECÍFICA: Elimina bordes redondeados y recortes únicamente para el logo */
    [data-testid="stImage"] img {
        border-radius: 0px !important;
        object-fit: contain !important;
    }
    
    /* Footer Institucional Azul UCM */
    .footer-ucm {
        background-color: #002B66;
        color: #FFFFFF;
        text-align: center;
        padding: 20px 10px;
        border-radius: 6px;
        margin-top: 30px;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .footer-ucm strong {
        color: #FFFFFF;
    }
    .footer-subtext {
        color: #94A3B8;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Cargar los datos
@st.cache_data
def cargar_datos():
    ruta_df = os.path.join("..", "data", "talca_con_clusters.csv")
    ruta_hotspots = os.path.join("..", "data", "hotspots_centroides.csv")
    df = pd.read_csv(ruta_df, low_memory=False)
    hotspots = pd.read_csv(ruta_hotspots)
    return df, hotspots

try:
    df, hotspots = cargar_datos()
except Exception as e:
    st.error(f"Error al cargar los datos CSV: {e}")
    st.stop()

# 3. Cabecera Institucional (Logo UCM con bordes rectos y sin recortes)
col_header, col_logo_ucm = st.columns([3.8, 1.2])

with col_header:
    st.markdown('<div class="institution-tag">Universidad Católica del Maule | Facultad de Ciencias de la Ingeniería</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-header">Plataforma de Analítica de Siniestralidad Vial</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Monitoreo Espacio-Temporal y Análisis de Zonas de Riesgo en la Comuna de Talca</div>', unsafe_allow_html=True)

with col_logo_ucm:
    ruta_ucm = os.path.join("assets", "logo_ucm_horizontal.png")
    if not os.path.exists(ruta_ucm):
        ruta_ucm = os.path.join("..", "data", "logo_ucm_horizontal.png")
        
    if os.path.exists(ruta_ucm):
        st.image(ruta_ucm, use_container_width=True)

st.divider()

# 4. Barra Lateral (Filtros Limpios)
st.sidebar.header("Filtros de Análisis")

anios_disponibles = sorted(df['AÑO'].dropna().unique().astype(int))
anios_seleccionados = st.sidebar.multiselect("Año de Ocurrencia:", options=anios_disponibles, default=anios_disponibles)

severidades_disponibles = df['CATEGORIA_SEVERIDAD'].dropna().unique().tolist()
severidad_seleccionada = st.sidebar.multiselect("Categoría de Severidad:", options=severidades_disponibles, default=severidades_disponibles)

horarios_disponibles = df['BLOQUE_HORARIO'].dropna().unique().tolist()
horario_seleccionado = st.sidebar.multiselect("Bloque Horario:", options=horarios_disponibles, default=horarios_disponibles)

df_filtrado = df[
    (df['AÑO'].isin(anios_seleccionados)) &
    (df['CATEGORIA_SEVERIDAD'].isin(severidad_seleccionada)) &
    (df['BLOQUE_HORARIO'].isin(horario_seleccionado))
]

# 5. Sección Contenedora de Métricas Rápidas (KPIs)
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Accidentes Filtrados", f"{len(df_filtrado):,}")
    col2.metric("Fallecidos", f"{int(df_filtrado['FALLECIDOS'].sum()):,}")
    col3.metric("Lesionados Graves", f"{int(df_filtrado['GRAVES'].sum()):,}")
    col4.metric("Severidad Acumulada", f"{int(df_filtrado['PUNTAJE_SEVERIDAD'].sum()):,}")

st.write("")

# 6. Mapa con Marcadores Numerados y Círculos de Cobertura
st.subheader("Mapa de Densidad y Zonas Críticas Numeradas (#1 al #10)")

centro_talca = [-35.426, -71.655]
m = folium.Map(location=centro_talca, zoom_start=13, tiles="OpenStreetMap")

# Capa de Mapa de Calor
datos_calor = df_filtrado[['Latitud', 'longitud']].dropna().values.tolist()
if len(datos_calor) > 0:
    HeatMap(datos_calor, radius=12, blur=15, min_opacity=0.4).add_to(m)

def obtener_color_ranking(rank):
    if rank <= 3:
        return "#D32F2F"
    elif rank <= 7:
        return "#E65100"
    else:
        return "#1565C0"

for _, row in hotspots.iterrows():
    rank = int(row['RANKING_RIESGO'])
    bg_color = obtener_color_ranking(rank)
    nombre_zona = row.get('NOMBRE_ZONA', f'Zona #{rank}')
    lat, lng = row['LATITUD_CENTRO'], row['LONGITUD_CENTRO']

    folium.Circle(
        location=[lat, lng],
        radius=350,
        color=bg_color,
        fill=True,
        fill_color=bg_color,
        fill_opacity=0.15,
        weight=1.5,
        popup=f"Área de cobertura: {nombre_zona}"
    ).add_to(m)

    icon_html = f"""
    <div style="
        background-color: {bg_color};
        color: white;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 13px;
        border: 2px solid white;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.4);
    ">
        {rank}
    </div>
    """

    popup_text = f"""
    <div style='font-family: sans-serif;'>
        <b>Lugar #{rank}: {nombre_zona}</b><br><hr style='margin:4px 0;'>
        • <b>Accidentes Totales:</b> {int(row['TOTAL_ACCIDENTES'])}<br>
        • <b>Fallecidos:</b> {int(row['TOTAL_FALLECIDOS'])}<br>
        • <b>Lesionados Graves:</b> {int(row['TOTAL_GRAVES'])}<br>
        • <b>Puntaje Severidad:</b> {int(row['SEVERIDAD_ACUMULADA'])}
    </div>
    """

    folium.Marker(
        location=[lat, lng],
        icon=folium.DivIcon(html=icon_html),
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

st_folium(m, width=1200, height=520)

st.write("")

# 7. Sección Contenedora para la Tabla de Riesgo
with st.container(border=True):
    st.subheader("Tabla de Riesgo por Zonas de Talca")

    st.info("""
    **Nota explicativa sobre las métricas:**  
    • **Área de Zona (Círculos en el mapa):** El marcador numerado representa el centroide de una zona de concentración de siniestros de ~350 metros a la redonda.  
    • **Severidad Acumulada:** Indicador ponderado de riesgo según la gravedad del evento: Fallecido (10 pts), Lesionado Grave (5 pts), Lesionado Menos Grave (3 pts) y Evento Base / Solo Daños Materiales (1 pt).
    """)

    tabla_ciudadana = hotspots[[
        'RANKING_RIESGO', 'NOMBRE_ZONA', 'TOTAL_ACCIDENTES', 
        'TOTAL_FALLECIDOS', 'TOTAL_GRAVES', 'SEVERIDAD_ACUMULADA'
    ]].copy()

    tabla_ciudadana.columns = [
        'Lugar (Ranking)', 'Zona / Sector de Talca', 
        'Total Accidentes', 'Fallecidos', 'Lesionados Graves', 'Severidad Acumulada'
    ]

    st.dataframe(tabla_ciudadana, use_container_width=True, hide_index=True)

# 8. Pie de Página Institucional en Azul UCM (#002B66)
st.markdown("""
    <div class="footer-ucm">
        <strong>Escuela de Ingeniería de Ejecución en Computación e Informática</strong><br>
        Facultad de Ciencias de la Ingeniería — Universidad Católica del Maule<br>
        <div class="footer-subtext">
            Módulo Integrador II (ECI-324) | Fuente de datos: CONASET / Carabineros de Chile
        </div>
    </div>
""", unsafe_allow_html=True)