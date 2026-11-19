import os
import numpy as np
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
from scipy.spatial import ConvexHull
from streamlit_folium import st_folium

# 1. Configuración de página
st.set_page_config(
    page_title="Siniestralidad Vial - Comuna de Talca",
    layout="wide",
)

# Estilo CSS institucional UCM
st.markdown("""
    <style>
    .main-header {
        font-size: 2.05rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.02rem;
        color: #475569;
        margin-bottom: 0.6rem;
    }
    .institution-tag {
        font-size: 0.85rem;
        font-weight: 700;
        color: #003366;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stImage"] img {
        border-radius: 0px !important;
        object-fit: contain !important;
    }
    .footer-ucm {
        background-color: #002B66;
        color: #FFFFFF;
        text-align: center;
        padding: 20px 12px;
        border-radius: 6px;
        margin-top: 30px;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .footer-subtext {
        color: #CBD5E1;
        font-size: 0.8rem;
        margin-top: 6px;
    }
    </style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def cargar_datos():
    df = pd.read_csv(os.path.join(DATA_DIR, "talca_con_clusters.csv"), low_memory=False)
    hotspots = pd.read_csv(os.path.join(DATA_DIR, "hotspots_centroides.csv"))

    # Estandarizar intersección ordenada alfabéticamente (unifica "A & B" con "B & A")
    if "Calle_Uno" in df.columns and "Calle_Dos" in df.columns:
        c1 = df["Calle_Uno"].fillna("").astype(str).str.strip()
        c2 = df["Calle_Dos"].fillna("").astype(str).str.strip()
        tiene_cruce = (c2 != "") & (c2.str.upper() != "NAN") & (c2 != "0")
        cruce_ordenado = [
            " & ".join(sorted([a, b])) if ok else a
            for a, b, ok in zip(c1, c2, tiene_cruce)
        ]
        df["INTERSECCION"] = cruce_ordenado
    else:
        df["INTERSECCION"] = df.get("UBICACION", "SIN DIRECCIÓN").fillna("SIN DIRECCIÓN").astype(str)

    return df, hotspots


def cargar_csv_opcional(nombre_archivo):
    ruta = os.path.join(DATA_DIR, nombre_archivo)
    if os.path.exists(ruta):
        return pd.read_csv(ruta)
    return None


try:
    df, hotspots_base = cargar_datos()
except Exception as e:
    st.error("No fue posible cargar los archivos procesados de siniestralidad. Verifica la carpeta data/.")
    st.stop()

# 2. Cabecera Institucional
col_header, col_logo_ucm = st.columns([3.8, 1.2])

with col_header:
    st.markdown('<div class="institution-tag">Universidad Católica del Maule | Facultad de Ciencias de la Ingeniería</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-header">Plataforma de Analítica de Siniestralidad Vial — Talca</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Análisis Espacio-Temporal y Concentración de Severidad Vial en 7 Zonas Urbanas PLADECO (Años: 2020, 2021, 2022 y 2025)</div>',
        unsafe_allow_html=True,
    )

with col_logo_ucm:
    ruta_ucm = os.path.join(BASE_DIR, "src", "assets", "logo_ucm_horizontal.png")
    if not os.path.exists(ruta_ucm):
        ruta_ucm = os.path.join(DATA_DIR, "logo_ucm_horizontal.png")
    if os.path.exists(ruta_ucm):
        st.image(ruta_ucm, use_container_width=True)

st.divider()

# 3. Barra Lateral (Filtros ordenados y completos)
st.sidebar.header("Filtros de Análisis")

anios_disponibles = sorted(df["AÑO"].dropna().unique().astype(int))
anios_seleccionados = st.sidebar.multiselect(
    "Año de Ocurrencia (disponibles CONASET):",
    options=anios_disponibles,
    default=anios_disponibles,
)

orden_severidad = [
    "Fatal",
    "Grave",
    "Lesionados Leves / Menos Graves",
    "Solo Daños Materiales",
]
severidades_presentes = [s for s in orden_severidad if s in df["CATEGORIA_SEVERIDAD"].unique()]
severidad_seleccionada = st.sidebar.multiselect(
    "Categoría de Severidad:",
    options=severidades_presentes,
    default=severidades_presentes,
)

orden_horarios = [
    "Madrugada (00:00 - 05:59)",
    "Mañana (06:00 - 11:59)",
    "Tarde (12:00 - 17:59)",
    "Noche (18:00 - 23:59)",
]
horarios_presentes = [h for h in orden_horarios if h in df["BLOQUE_HORARIO"].unique()]
horario_seleccionado = st.sidebar.multiselect(
    "Bloque Horario:",
    options=horarios_presentes,
    default=horarios_presentes,
)

causas_top = df["CAUSA_NUEV"].value_counts().index.tolist() if "CAUSA_NUEV" in df.columns else []
causas_seleccionadas = st.sidebar.multiselect(
    "Causa Basal del Siniestro (opcional = todas):",
    options=causas_top,
    default=[],
)

# Aplicar filtros
condicion = (
    df["AÑO"].isin(anios_seleccionados)
    & df["CATEGORIA_SEVERIDAD"].isin(severidad_seleccionada)
    & df["BLOQUE_HORARIO"].isin(horario_seleccionado)
)
if causas_seleccionadas:
    condicion = condicion & df["CAUSA_NUEV"].isin(causas_seleccionadas)

df_filtrado = df[condicion].copy()

if len(df_filtrado) == 0:
    st.warning("Sin resultados para la combinación de filtros seleccionada. Ajusta los criterios en la barra lateral.")
    st.stop()

# 4. KPIs Principales (Completos y consistentes con el glosario oficial)
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Siniestros Filtrados", f"{len(df_filtrado):,}")
    c2.metric("Fallecidos", f"{int(df_filtrado['FALLECIDOS'].sum()):,}")
    c3.metric("Lesionados Graves", f"{int(df_filtrado['GRAVES'].sum()):,}")
    c4.metric("Total Lesionados", f"{int(df_filtrado['TOTAL_LESI'].sum()):,}")
    c5.metric("Severidad Acumulada (ISA)", f"{int(df_filtrado['PUNTAJE_SEVERIDAD'].sum()):,}")

st.write("")

# 5. Pestañas principales
tab_operativa, tab_experta = st.tabs([
    "Visor Operativo y Zonas Urbanas PLADECO (K=7)",
    "Analítica Avanzada, Validación y Calidad del Modelo (Expertos)",
])

with tab_operativa:
    st.subheader("Mapa de Densidad y Concentración por Zonas Urbanas de Talca (#1 al #7)")

    # Recalcular métricas dinámicamente por CLUSTER_ID según filtros activos (C2)
    agg_dinamica = (
        df_filtrado.groupby("CLUSTER_ID", as_index=False)
        .agg(
            TOTAL_SINIESTROS=("CLUSTER_ID", "size"),
            TOTAL_FALLECIDOS=("FALLECIDOS", "sum"),
            TOTAL_GRAVES=("GRAVES", "sum"),
            TOTAL_MENOS_GRAV=("MENOS_GRAV", "sum"),
            TOTAL_LEVES=("LEVES", "sum"),
            TOTAL_LESI=("TOTAL_LESI", "sum"),
            SEVERIDAD_ACUMULADA=("PUNTAJE_SEVERIDAD", "sum"),
        )
    )

    zonas_dinamicas = hotspots_base[
        ["CLUSTER_ID", "NOMBRE_ZONA", "LATITUD_CENTRO", "LONGITUD_CENTRO", "RADIO_MEDIANO_M"]
    ].merge(agg_dinamica, on="CLUSTER_ID", how="left").fillna(0)

    for col_int in ["TOTAL_SINIESTROS", "TOTAL_FALLECIDOS", "TOTAL_GRAVES", "TOTAL_MENOS_GRAV", "TOTAL_LEVES", "TOTAL_LESI", "SEVERIDAD_ACUMULADA"]:
        zonas_dinamicas[col_int] = zonas_dinamicas[col_int].astype(int)

    zonas_dinamicas = zonas_dinamicas.sort_values(
        by=["SEVERIDAD_ACUMULADA", "TOTAL_SINIESTROS"], ascending=False
    ).reset_index(drop=True)
    zonas_dinamicas["RANKING_SEVERIDAD"] = range(1, len(zonas_dinamicas) + 1)

    centro_talca = [-35.426, -71.655]
    m = folium.Map(location=centro_talca, zoom_start=13, tiles="OpenStreetMap")

    # Capa de Mapa de Calor
    datos_calor = df_filtrado[["Latitud", "longitud"]].dropna().values.tolist()
    if len(datos_calor) > 0:
        HeatMap(datos_calor, radius=12, blur=15, min_opacity=0.4).add_to(m)

    def obtener_color_ranking(rank):
        if rank <= 2:
            return "#D32F2F"  # Rojo: Mayor severidad acumulada (#1-#2)
        elif rank <= 5:
            return "#E65100"  # Naranja: Severidad intermedia (#3-#5)
        else:
            return "#1565C0"  # Azul: Menor severidad relativa (#6-#7)

    for _, row in zonas_dinamicas.iterrows():
        cid = int(row["CLUSTER_ID"])
        rank = int(row["RANKING_SEVERIDAD"])
        bg_color = obtener_color_ranking(rank)
        nombre_zona = row["NOMBRE_ZONA"]
        lat, lng = row["LATITUD_CENTRO"], row["LONGITUD_CENTRO"]

        # Dibujar polígono real (envolvente convexa) de los siniestros de la zona (C4)
        pts_zona = df_filtrado[df_filtrado["CLUSTER_ID"] == cid][["Latitud", "longitud"]].dropna().values
        if len(pts_zona) >= 3:
            try:
                hull = ConvexHull(pts_zona)
                poligono_latlon = pts_zona[hull.vertices].tolist()
                folium.Polygon(
                    locations=poligono_latlon,
                    color=bg_color,
                    weight=1.8,
                    fill=True,
                    fill_color=bg_color,
                    fill_opacity=0.12,
                    tooltip=f"Área de cobertura espacial: {nombre_zona}",
                ).add_to(m)
            except Exception:
                pass

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
        <div style='font-family: sans-serif; min-width: 220px;'>
            <b>Lugar #{rank}: {nombre_zona}</b><br><hr style='margin:4px 0;'>
            • <b>Siniestros (filtro actual):</b> {row['TOTAL_SINIESTROS']:,}<br>
            • <b>Fallecidos:</b> {row['TOTAL_FALLECIDOS']:,}<br>
            • <b>Lesionados Graves:</b> {row['TOTAL_GRAVES']:,}<br>
            • <b>Total Lesionados:</b> {row['TOTAL_LESI']:,}<br>
            • <b>Severidad Acumulada (ISA):</b> {row['SEVERIDAD_ACUMULADA']:,} pts<br>
            • <b>Radio mediano de dispersión:</b> {int(row['RADIO_MEDIANO_M'])} m
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            icon=folium.DivIcon(html=icon_html),
            popup=folium.Popup(popup_text, max_width=320),
        ).add_to(m)

    st_folium(m, use_container_width=True, height=520, returned_objects=[])

    # Leyenda visual explícita (M1)
    st.caption(
        "Leyenda de marcadores (Ranking de Severidad Acumulada): "
        "🔴 Rojo (#1–#2: Mayor concentración de severidad) | "
        "🟠 Naranja (#3–#5: Severidad intermedia) | "
        "🔵 Azul (#6–#7: Menor severidad relativa). "
        "Los polígonos delimitan la envolvente convexa real de los siniestros asignados a cada zona."
    )

    st.write("")

    # Tabla resumen de las 7 Zonas Urbanas
    with st.container(border=True):
        st.subheader("Tabla de Concentración y Severidad por Zona Urbana PLADECO (K = 7)")

        st.info("""
        **Notas metodológicas de lectura:**  
        • **Delimitación espacial:** Los 7 clústeres fueron obtenidos mediante *K-Means* en coordenadas métricas UTM Zona 19S y corresponden a las 7 zonas urbanas definidas en el PLADECO Talca 2024–2028 (pp. 46–47). El marcador indica el centroide matemático y el polígono representa la envolvente real de sus eventos.  
        • **Índice de Severidad Acumulada (ISA):** Indicador ponderado por víctima: **Fallecido (10 pts)**, **Lesionado Grave (5 pts)**, **Lesionado Menos Grave (3 pts)** y **Lesionado Leve (1 pt)**; siniestros solo con daños materiales suman **0 pts**.  
        • **Alcance del indicador:** Al no disponerse de conteos de flujo vehicular (exposición), las métricas reflejan concentración y severidad registrada por Carabineros/CONASET, no probabilidad individual de accidente.
        """)

        tabla_zonas = zonas_dinamicas[[
            "RANKING_SEVERIDAD", "NOMBRE_ZONA", "TOTAL_SINIESTROS",
            "TOTAL_FALLECIDOS", "TOTAL_GRAVES", "TOTAL_LESI", "SEVERIDAD_ACUMULADA",
        ]].copy()

        tabla_zonas.columns = [
            "Ranking", "Zona Urbana (PLADECO)", "Total Siniestros",
            "Fallecidos", "Lesionados Graves", "Total Lesionados", "Severidad Acumulada (ISA)",
        ]

        st.dataframe(tabla_zonas, use_container_width=True, hide_index=True)

        csv_zonas = tabla_zonas.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar Tabla de Zonas Filtradas (CSV)",
            data=csv_zonas,
            file_name="zonas_siniestralidad_talca_filtradas.csv",
            mime="text/csv",
        )

    st.write("")

    # Dimensión Temporal y Top 10 Intersecciones Específicas (A8, M6)
    col_temp1, col_temp2 = st.columns(2)

    with col_temp1:
        with st.container(border=True):
            st.markdown("#### Evolución Anual de Siniestros (Años Disponibles)")
            serie_anual = (
                df_filtrado.groupby("AÑO", as_index=False)
                .agg(Siniestros=("AÑO", "size"), Severidad_ISA=("PUNTAJE_SEVERIDAD", "sum"))
                .sort_values("AÑO")
            )
            serie_anual["AÑO"] = serie_anual["AÑO"].astype(str)
            st.bar_chart(serie_anual.set_index("AÑO")[["Siniestros", "Severidad_ISA"]])
            st.caption("Nota: Fuente CONASET contiene registros oficiales para 2020, 2021, 2022 y 2025 (sin publicación 2023–2024).")

    with col_temp2:
        with st.container(border=True):
            st.markdown("#### Distribución por Bloque Horario")
            serie_hora = (
                df_filtrado.groupby("BLOQUE_HORARIO", as_index=False)
                .agg(Siniestros=("BLOQUE_HORARIO", "size"))
            )
            serie_hora["Orden"] = serie_hora["BLOQUE_HORARIO"].apply(
                lambda x: orden_horarios.index(x) if x in orden_horarios else 99
            )
            serie_hora = serie_hora.sort_values("Orden")
            st.bar_chart(serie_hora.set_index("BLOQUE_HORARIO")["Siniestros"])

    with st.container(border=True):
        st.markdown("#### Top 10 Intersecciones / Tramos Específicos con Mayor Severidad (Filtro Actual)")
        top_inter = (
            df_filtrado.groupby(["INTERSECCION", "NOMBRE_ZONA"], as_index=False)
            .agg(
                Siniestros=("INTERSECCION", "size"),
                Fallecidos=("FALLECIDOS", "sum"),
                Graves=("GRAVES", "sum"),
                Severidad_ISA=("PUNTAJE_SEVERIDAD", "sum"),
            )
            .sort_values(by=["Severidad_ISA", "Siniestros"], ascending=False)
            .head(10)
            .reset_index(drop=True)
        )
        top_inter.insert(0, "Lugar", range(1, len(top_inter) + 1))
        top_inter.columns = [
            "Lugar", "Intersección / Vía", "Zona Urbana PLADECO",
            "Siniestros", "Fallecidos", "Lesionados Graves", "Severidad (ISA)",
        ]
        st.dataframe(top_inter, use_container_width=True, hide_index=True)

with tab_experta:
    st.subheader("Evaluación Experimental de Clustering, Validación Temporal y Calidad de Datos")
    st.markdown("""
    Esta sección reúne la evidencia empírica producida por los scripts `03_evaluacion_clustering.py`, 
    `04_visualizar_clusters.py` y `05_validacion_y_sensibilidad.py` en **espacio métrico UTM Zona 19S (EPSG:32719)**.
    """)

    # 1. Benchmarking de Algoritmos (leído desde CSV real)
    with st.container(border=True):
        st.markdown("#### 1. Benchmarking de Algoritmos Espaciales en UTM 19S: K-Means vs. DBSCAN")
        df_bench = cargar_csv_opcional("benchmark_algoritmos.csv")
        if df_bench is not None:
            st.dataframe(df_bench, use_container_width=True, hide_index=True)
        else:
            st.warning("Ejecuta `python src/03_evaluacion_clustering.py` para generar `benchmark_algoritmos.csv`.")

    st.write("")

    # 2. Selección Multi-Criterio de K (K=2..15)
    with st.container(border=True):
        st.markdown("#### 2. Análisis Multi-Criterio de Selección de $K$ ($K=2$ a $K=15$ en UTM 19S)")

        ruta_grafico_utm = os.path.join(DATA_DIR, "grafico_decision_k_utm.png")
        if os.path.exists(ruta_grafico_utm):
            st.image(
                ruta_grafico_utm,
                caption="Figura 1: Curva de Inercia (km²), Cohesión (Silhouette), Estabilidad (ARI) y Radio Mediano (m) en UTM 19S.",
                use_container_width=True,
            )

        st.info("""
        **Justificación Metodológica de $K = 7$:**  
        • **Alineación territorial oficial (Validez de dominio):** El Plan de Desarrollo Comunal (PLADECO) de Talca 2024–2028 (Ilustración 10 y Tabla 8, pp. 46–47) divide el área urbana de la comuna exactamente en **7 zonas urbanas** (*Centro, Pericentro, Norte, Nororiente, Suroriente-Carlos Trupp, Suroriente-Las Colines y Surponiente*).  
        • **Desempeño estadístico y estabilidad:** Aunque el máximo geométrico puro ocurre en $K=4$ (Silhouette = $0,4413$) y el punto de inflexión Kneedle en $K=5$, avanzar a **$K=7$** recupera cohesión (Silhouette = **$0,3970$**), alcanza una reproducibilidad casi determinista (**ARI = $0,9913$**, superior a $K=5$ [$0,9455$] y $K=8$ [$0,9452$]) y ajusta la escala operativa a un radio mediano de **$653,6\\text{ m}$** (frente a $866,5\\text{ m}$ en $K=4$).
        """)

        ruta_grafico_hull = os.path.join(DATA_DIR, "exploracion_visual_clusters.png")
        if os.path.exists(ruta_grafico_hull):
            st.image(
                ruta_grafico_hull,
                caption="Figura 2: Evolución geométrica de las envolventes convexas para K = 4, 5, 7 (Seleccionado) y 8.",
                use_container_width=True,
            )

        df_metricas_k = cargar_csv_opcional("metricas_evaluacion_clustering.csv")
        if df_metricas_k is not None:
            st.markdown("##### Tabla Completa de Métricas por Cantidad de Clústeres ($K$)")
            st.dataframe(df_metricas_k, use_container_width=True, hide_index=True)
            st.download_button(
                label="Descargar Tabla Multi-Criterio de Clustering (CSV)",
                data=df_metricas_k.to_csv(index=False).encode("utf-8"),
                file_name="metricas_evaluacion_clustering_talca_utm.csv",
                mime="text/csv",
            )

    st.write("")

    # 3. Validación Temporal Predictiva y Sensibilidad del ISA
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        with st.container(border=True):
            st.markdown("#### 3. Validación Temporal (2020–2022 → 2025)")
            df_temp = cargar_csv_opcional("validacion_temporal_2025.csv")
            if df_temp is not None:
                st.dataframe(df_temp, use_container_width=True, hide_index=True)
                st.caption("Porcentaje de siniestros y severidad ISA ocurridos en 2025 capturados por los 7 centroides entrenados exclusivamente con 2020–2022.")

    with col_v2:
        with st.container(border=True):
            st.markdown("#### 4. Sensibilidad de Ponderadores ISA (Spearman)")
            df_sens = cargar_csv_opcional("sensibilidad_pesos_isa.csv")
            if df_sens is not None:
                cols_rank = ["NOMBRE_ZONA"] + [c for c in df_sens.columns if c.startswith("Rank_")]
                st.dataframe(df_sens[cols_rank], use_container_width=True, hide_index=True)
                st.caption("Correlación de rango de Spearman: rho = 1,0000 frente a esquemas severos (20/10/3/1 y 12/6/3/1) y rho = 0,8929 frente a frecuencia pura.")

    st.write("")

    # 4. Perfilado de Calidad de Datos
    with st.container(border=True):
        st.markdown("#### 5. Perfilado de Calidad y Reconciliación ETL")
        df_perf = cargar_csv_opcional("perfilado_calidad_datos.csv")
        if df_perf is not None:
            st.dataframe(df_perf, use_container_width=True, hide_index=True)

# 6. Pie de Página Institucional
st.markdown("""
    <div class="footer-ucm">
        <strong>Escuela de Ingeniería de Ejecución en Computación e Informática</strong><br>
        Facultad de Ciencias de la Ingeniería — Universidad Católica del Maule<br>
        <div class="footer-subtext">
            Módulo Integrador II (ECI-324) | Fuente: CONASET / Carabineros de Chile (Años: 2020, 2021, 2022 y 2025) |
            Nota: Los registros oficiales cubren siniestros con intervención policial; eventos menores sin denuncia pueden presentar subregistro.
        </div>
    </div>
""", unsafe_allow_html=True)