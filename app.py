#!/usr/bin/env python
"""Dashboard interactivo para el proyecto Ciudad Escucha."""
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap, MiniMap
import json
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Dashboard Ciudad Escucha",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🏙️ Dashboard Ciudad Escucha - Villavicencio")
st.markdown("**Sistema de reporte de daños en espacio público** — Proyecto Académico")
st.markdown("---")

# Leyenda ética
st.sidebar.markdown("---")
st.sidebar.info(
    "📌 **MARCA ÉTICA**: Estos datos son SIMULADOS con fines académicos.\n"
    "Proyecto: Ciudad Escucha — Asignatura: Habilidades Gerenciales\n"
    "Autor: Jhon Bedoya — Rol: Analista"
)

# Configuración de colores por tipo de daño
COLOR_TIPO = {
    'Vías': '#C0392B',
    'Alumbrado público': '#2980B9',
    'Basuras': '#27AE60',
    'Alcantarillado': '#E67E22',
    'Otro': '#95A5A6'
}
# Colores para folium (circlemarker acepta CSS/nombres)
COLOR_TIPO_FOLIUM = {
    'Vías': 'red',
    'Alumbrado público': '#2980B9',
    'Basuras': 'green',
    'Alcantarillado': 'orange',
    'Otro': 'purple'
}


@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('data/generated/dataset_simulado.csv', encoding='utf-8')
        df['fecha_reporte'] = pd.to_datetime(df['fecha_reporte'])
        return df
    except FileNotFoundError:
        st.error("⚠️ Archivo dataset_simulado.csv no encontrado.")
        st.info("Ejecuta primero el script 'generar_dataset_gemini.py' para crear los datos.")
        return pd.DataFrame()


@st.cache_data
def cargar_veredas():
    """GeoJSON ligero de veredas de Villavicencio (exportado con filtro desde QGIS)."""
    try:
        with open('data/generated/veredas_villavicencio_simpl.geojson', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


df = cargar_datos()
veredas_geojson = cargar_veredas()
if veredas_geojson:
    N_VEREDAS = len(veredas_geojson.get('features', []))
else:
    N_VEREDAS = 0

if df.empty:
    st.stop()

# --- Barra lateral de filtros ---
st.sidebar.header("🔍 Filtros de Búsqueda")

comunas_opciones = ["Todas"] + sorted(df['comuna'].unique())
comuna_seleccionada = st.sidebar.selectbox("Comuna", comunas_opciones)

tipo_opciones = ["Todos"] + sorted(df['tipo_dano'].unique())
tipo_seleccionado = st.sidebar.multiselect("Tipo de Daño", tipo_opciones, default=tipo_opciones)

canal_opciones = ["Todos"] + sorted(df['canal_reporte'].unique())
canal_seleccionado = st.sidebar.multiselect("Canal de Reporte", canal_opciones, default=canal_opciones)

estado_opciones = ["Todos"] + sorted(df['estado_gestion'].unique())
estado_seleccionado = st.sidebar.multiselect("Estado de Gestión", estado_opciones, default=estado_opciones)

fecha_min = df['fecha_reporte'].min().date()
fecha_max = df['fecha_reporte'].max().date()
fecha_rango = st.sidebar.date_input(
    "Rango de Fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

# Controles del mapa
st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Capas del Mapa")
mostrar_veredas = st.sidebar.checkbox(
    f"Límites de veredas ({N_VEREDAS} veredas QGIS 2024)", value=True)
mostrar_heatmap = st.sidebar.checkbox("Mapa de calor (densidad)", value=False)

df_filtrado = df.copy()
if comuna_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['comuna'] == comuna_seleccionada]

if "Todos" not in tipo_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['tipo_dano'].isin(tipo_seleccionado)]

if "Todos" not in canal_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['canal_reporte'].isin(canal_seleccionado)]

if "Todos" not in estado_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['estado_gestion'].isin(estado_seleccionado)]

fecha_inicio = pd.Timestamp(fecha_rango[0])
fecha_fin = pd.Timestamp(fecha_rango[1]) + pd.Timedelta(days=1)
df_filtrado = df_filtrado[
    (df_filtrado['fecha_reporte'] >= fecha_inicio) &
    (df_filtrado['fecha_reporte'] < fecha_fin)
]

# --- Contenedor principal ---
st.header("📊 Indicadores Principales")

pct_resueltos = (
    (df_filtrado['estado_gestion'] == 'Resuelto').sum() / len(df_filtrado) * 100
    if len(df_filtrado) else 0
)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Reportes", len(df_filtrado))
with col2:
    st.metric("Comunas con Reportes", df_filtrado['comuna'].nunique())
with col3:
    st.metric("Tipos de Daño", df_filtrado['tipo_dano'].nunique())
with col4:
    st.metric("Canales Usados", df_filtrado['canal_reporte'].nunique())
with col5:
    st.metric("% Resueltos", f"{pct_resueltos:.1f}%")

st.markdown("---")

# ==========================================
# VISUALIZACIÓN 1: Mapa Folium con círculos
# ==========================================
st.subheader("🗺️ Visualización 1: Mapa Interactivo de Reportes")
st.markdown(
    "Cada **círculo** es un reporte (color = tipo de daño). "
    "Haz clic en un punto para ver el detalle; usa el control de capas "
    "↗️ para alternar veredas y mapa de calor."
)

# Coordenadas centroide de Villavicencio
VILLAVICENCIO_LAT = 4.1425
VILLAVICENCIO_LON = -73.6294

# Creamos el mapa Folium con fondo de calles mas otro fondo satelital
m = folium.Map(
    location=[VILLAVICENCIO_LAT, VILLAVICENCIO_LON],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)

# Overlay: límites de veredas del shapefile oficial (DANE 2024, filtrado en QGIS)
if mostrar_veredas and veredas_geojson:
    folium.GeoJson(
        veredas_geojson,
        name="🛑 Veredas Villavicencio (DANE 2024)",
        style_function=lambda feat: {
            'fillOpacity': 0.0,          # solo contorno, no tapa los puntos
            'color': '#E67E22',          # borde naranja
            'weight': 1.4,
            'dashArray': '4,4',
        },
        highlight_function=lambda feat: {
            'fillColor': '#F39C12', 'fillOpacity': 0.08, 'weight': 2.5
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["NOMBRE_VER", "CODIGO_VER"],
            aliases=["Vereda:", "Código DIVIPOLA:"],
            localize=True,
            sticky=False,
        ),
    ).add_to(m)

# Mapa de calor de densidad de reportes
if mostrar_heatmap and len(df_filtrado):
    HeatMap(
        df_filtrado[['latitud', 'longitud']].values.tolist(),
        name="🌡️ Mapa de calor",
        radius=14,
        blur=18,
        min_opacity=0.25,
    ).add_to(m)

# Capa de círculos: uno por reporte, coloreado por tipo de daño
capa_puntos = folium.FeatureGroup(name="📍 Reportes (círculos por tipo de daño)")

for _, row in df_filtrado.iterrows():
    folium.CircleMarker(
        location=[row['latitud'], row['longitud']],
        radius=6,
        weight=1.2,
        color=COLOR_TIPO_FOLIUM.get(row['tipo_dano'], 'gray'),
        fill=True,
        fill_color=COLOR_TIPO_FOLIUM.get(row['tipo_dano'], 'gray'),
        fill_opacity=0.75,
        popup=folium.Popup(
            f"""
            <b>ID:</b> {row['id_reporte']}<br>
            <b>Comuna:</b> {row['comuna']}<br>
            <b>Tipo Daño:</b> {row['tipo_dano']}<br>
            <b>Canal:</b> {row['canal_reporte']}<br>
            <b>Estado:</b> {row['estado_gestion']}<br>
            <b>Fecha:</b> {row['fecha_reporte'].strftime('%Y-%m-%d %H:%M')}<br>
            <b>Origen:</b> {row['origen_datos']}
            """,
            max_width=260,
        ),
        tooltip=row['tipo_dano'],
    ).add_to(capa_puntos)

capa_puntos.add_to(m)

# Leyenda de colores personalizada sobre el mapa
leyenda_html = """
<div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
            background-color: rgba(255,255,255,0.92); padding: 10px 14px;
            border: 2px solid #bbb; border-radius: 6px; font-size: 13px;
            font-family: sans-serif;">
  <b>📊 Tipo de daño</b><br>
  <span style="color:#C0392B;">&#9679;</span> Vías &nbsp;
  <span style="color:#2980B9;">&#9679;</span> Alumbrado público<br>
  <span style="color:#27AE60;">&#9679;</span> Basuras &nbsp;
  <span style="color:#E67E22;">&#9679;</span> Alcantarillado<br>
  <span style="color:#95A5A6;">&#9679;</span> Otro<br>
  <span style="border-top:2px dashed #E67E22; display:block; width:34px;
       height:0; margin-top:6px;"></span> Límites de vereda (DANE 2024)
</div>
"""
m.get_root().html.add_child(folium.Element(leyenda_html))

# Control de capas y minimapa
folium.LayerControl(collapsed=False).add_to(m)
MiniMap(toggle_display=True).add_to(m)

# Generar el HTML del mapa
map_html = m._repr_html_()

# Mostrar el mapa usando st.components.v1.html
st.components.v1.html(map_html, height=700, scrolling=True)

with st.expander("➕ Ver tabla de reportes del mapa (primeras 20 filas)"):
    st.dataframe(
        df_filtrado[['id_reporte', 'comuna', 'tipo_dano', 'canal_reporte',
                     'estado_gestion', 'fecha_reporte']].head(20)
    )

st.markdown("---")

# Visualización 2: Distribución por Tipo de Daño
st.subheader("📊 Visualización 2: Distribución por Tipo de Daño")
fig_tipo = px.bar(
    df_filtrado.groupby('tipo_dano').size().reset_index(name='cantidad'),
    x='tipo_dano',
    y='cantidad',
    title="Cantidad de Reportes por Tipo de Daño",
    color='tipo_dano',
    color_discrete_map=COLOR_TIPO
)
fig_tipo.update_layout(showlegend=False)
st.plotly_chart(fig_tipo, width='stretch')

# Visualización 3: Tendencia Temporal
st.subheader("📈 Visualización 3: Tendencia Temporal de Reportes")
fechas_diarias = df_filtrado.groupby(
    df_filtrado['fecha_reporte'].dt.date).size().reset_index(name='cantidad')
fig_linea = px.line(
    fechas_diarias,
    x='fecha_reporte',
    y='cantidad',
    title="Evolución Diaria de Reportes",
    markers=True
)
st.plotly_chart(fig_linea, width='stretch')

# Visualización 4: Distribución por Comuna
st.subheader("👥 Visualización 4: Distribución por Comuna")
df_comuna = df_filtrado.groupby('comuna').size().reset_index(name='cantidad')
df_comuna['comuna_num'] = (
    df_comuna['comuna'].str.extract(r'(\d+)').astype(float)
)
df_comuna = df_comuna.sort_values('comuna_num')
fig_comuna = px.bar(
    df_comuna,
    x='comuna',
    y='cantidad',
    title="Reportes por Comuna (Distribución Poblacional)",
    color='cantidad',
    color_continuous_scale=['#FF6B6B', '#4ECDC4', '#45B7D1']
)
st.plotly_chart(fig_comuna, width='stretch')

# Visualización 5: Canal de Reporte
st.subheader("📱 Visualización 5: Canal de Reporte")
fig_canal = px.pie(
    df_filtrado.groupby('canal_reporte').size().reset_index(name='cantidad'),
    values='cantidad',
    names='canal_reporte',
    title="Distribución de Reportes por Canal",
    color_discrete_map={
        'App Ciudad Escucha': '#27AE60',
        'WhatsApp': '#2980B9',
        'Portal Web': '#F1C40F',
        'Físico/PQRSD Telefónico': '#E74C3C'
    }
)
st.plotly_chart(fig_canal, width='stretch')

# --- Pie de página ---
st.markdown("---")
st.caption(
    "🚨 **DATOS SIMULADOS - PROYECTO ACADÉMICO** — "
    "Este dashboard es una herramienta de visualización para el proyecto "
    "'Ciudad Escucha' de la asignatura Habilidades Gerenciales. "
    "Los datos son sintéticos y declarados explícitamente como simulados. "
    "Capa de veredas: shapefile oficial DANE (2024) filtrado en QGIS."
)

st.sidebar.markdown("---")
st.sidebar.caption(f"📅 Fecha generación: {datetime.now().strftime('%d/%m/%Y')}")
st.sidebar.caption(f"📊 Total filtrado: {len(df_filtrado)} reportes")
st.sidebar.caption(f"🏙️ Comunas: {df_filtrado['comuna'].nunique()}")
st.sidebar.caption(f"🗺️ Veredas en mapa: {N_VEREDAS}")
st.sidebar.caption(f"📋 Versión: 2.0 — Analista Jhon Bedoya")
