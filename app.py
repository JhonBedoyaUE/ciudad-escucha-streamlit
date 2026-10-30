#!/usr/bin/env python
"""Dashboard interactivo para el proyecto Ciudad Escucha."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap, MiniMap
import json
from datetime import datetime
import numpy as np

# Configuración de página - layout wide para aprovechar espacio horizontal
st.set_page_config(
    page_title="Dashboard Ciudad Escucha - Villavicencio",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# TÍTULO Y ETIQUETA ÉTICA
# ==========================================
st.title("🏙️ Dashboard Ciudad Escucha - Villavicencio")
st.markdown("**Sistema de reporte de daños en espacio público** — Proyecto Académico")
st.markdown("---")

# Leyenda ética lateral
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
        if 'resuelta_en' not in df.columns:
            rng = np.random.default_rng(42)
            mask = df['estado_gestion'] == 'Resuelto'
            dias = rng.integers(1, 41, size=mask.sum())
            df.loc[mask, 'resuelta_en'] = (df.loc[mask, 'fecha_reporte'] +
                                           pd.to_timedelta(dias, unit='D')).dt.strftime('%Y-%m-%d %H:%M:%S')
        # Normalizar vacíos/NaN a cadena vacía: el resto del app compara contra ""
        df['resuelta_en'] = df['resuelta_en'].fillna('').astype(str).replace('nan', '')
        return df
    except FileNotFoundError:
        st.error("⚠️ Archivo dataset_simulado.csv no encontrado.")
        st.info("Ejecuta primero el script 'generar_dataset_gemini.py' para crear los datos.")
        return pd.DataFrame()


@st.cache_data
def cargar_veredas():
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

# ==========================================
# BARRA LATERAL DE FILTROS COMPACTA
# ==========================================
st.sidebar.header("🔍 Filtros de Búsqueda")

with st.sidebar:
    st.markdown("**Comuna**")
    comunas_opciones = ["Todas"] + sorted(df['comuna'].unique())
    comuna_seleccionada = st.selectbox("Comuna", comunas_opciones, key="f_comuna", label_visibility="collapsed")

    st.markdown("**Tipo de Daño**")
    tipo_opciones = ["Todos"] + sorted(df['tipo_dano'].unique())
    tipo_seleccionado = st.multiselect("Tipo de Daño", tipo_opciones, default=[], key="f_tipo", label_visibility="collapsed")

    st.markdown("**Canal de Reporte**")
    canal_opciones = ["Todos"] + sorted(df['canal_reporte'].unique())
    canal_seleccionado = st.multiselect("Canal de Reporte", canal_opciones, default=[], key="f_canal", label_visibility="collapsed")

    st.markdown("**Estado de Gestión**")
    estado_opciones = ["Todos"] + sorted(df['estado_gestion'].unique())
    estado_seleccionado = st.multiselect("Estado de Gestión", estado_opciones, default=[], key="f_estado", label_visibility="collapsed")

    st.markdown("**Rango de Fechas**")
    fecha_min = df['fecha_reporte'].min().date()
    fecha_max = df['fecha_reporte'].max().date()
    fecha_rango = st.date_input(
        "Rango de Fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
        key="f_fechas",
        label_visibility="collapsed"
    )

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Capas del Mapa")
mostrar_veredas = st.sidebar.checkbox(
    f"Límites de veredas ({N_VEREDAS} veredas QGIS 2024)", value=True, key="cb_veredas", label_visibility="collapsed")
mostrar_heatmap = st.sidebar.checkbox("Mapa de calor (densidad)", value=False, key="cb_heatmap", label_visibility="collapsed")

# Aplicar filtros al DataFrame
df_filtrado = df.copy()
if comuna_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['comuna'] == comuna_seleccionada]

# Selección vacía (o "Todos") = sin filtro: mostrar todas las categorías.
# OJO: `"Todos" not in []` es True, así que hay que comprobar la lista vacía primero.
def _aplicar_filtro(frame, columna, seleccion):
    if not seleccion or "Todos" in seleccion:
        return frame
    return frame[frame[columna].isin(seleccion)]


df_filtrado = _aplicar_filtro(df_filtrado, 'tipo_dano', tipo_seleccionado)
df_filtrado = _aplicar_filtro(df_filtrado, 'canal_reporte', canal_seleccionado)
df_filtrado = _aplicar_filtro(df_filtrado, 'estado_gestion', estado_seleccionado)

# st.date_input devuelve una tupla, o una fecha suelta si el usuario aún no
# eligió el extremo final del rango.
if isinstance(fecha_rango, (tuple, list)):
    fecha_desde = fecha_rango[0]
    fecha_hasta = fecha_rango[1] if len(fecha_rango) > 1 else fecha_rango[0]
else:
    fecha_desde = fecha_hasta = fecha_rango

fecha_inicio = pd.Timestamp(fecha_desde)
fecha_fin = pd.Timestamp(fecha_hasta) + pd.Timedelta(days=1)
df_filtrado = df_filtrado[
    (df_filtrado['fecha_reporte'] >= fecha_inicio) &
    (df_filtrado['fecha_reporte'] < fecha_fin)
]

# ==========================================
# ÁREA PRINCIPAL: distribucón en columnas
# ==========================================
st.markdown("---")

# Fila superior: dos gráficos apilados en la columna derecha, mapa a la izquierda
# Usamos columnas: [mapa, gráficos apilados]
col_mapa, col_graficos = st.columns([1, 1])

# --- Columna izquierda: Mapa (25% más alto) ---
with col_mapa:
    st.subheader("🗺️ Mapa Interactivo de Reportes")
    st.markdown(
        "Cada **círculo** es un reporte (color = tipo de daño). "
        "Haz clic en un punto para ver el detalle; usa el control de capas "
        "↗️ para alternar veredas y mapa de calor."
    )

    VILLAVICENCIO_LAT = 4.1425
    VILLAVICENCIO_LON = -73.6294

    m = folium.Map(
        location=[VILLAVICENCIO_LAT, VILLAVICENCIO_LON],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # Capa base: OpenStreetMap estándar
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="<a href='https://openstreetmap.org/copyright' target='_blank'>© OpenStreetMap contributors</a>",
        name="Mapa base OSM"
    ).add_to(m)

    # Overlay: límites de veredas del shapefile oficial (DANE 2024, filtrado en QGIS)
    if mostrar_veredas and veredas_geojson:
        folium.GeoJson(
            veredas_geojson,
            name="🛑 Veredas Villavicencio (DANE 2024)",
            style_function=lambda feat: {
                'fillOpacity': 0.0,
                'color': '#E67E22',
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

    # Control de capas y minimapa
    folium.LayerControl(collapsed=False).add_to(m)
    MiniMap(toggle_display=True).add_to(m)

    # Leyenda fija en la esquina inferior izquierda del mapa
    leyenda_html = """
    <div style="position: fixed; bottom: 80px; left: 20px; z-index: 9999;
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

    # Generar el HTML del mapa - altura aumentada 25% (aprox. 900px) con scrolling
    map_html = m._repr_html_()
    st.components.v1.html(map_html, height=900, scrolling=True)

# --- Columna derecha: dos gráficos apilados ---
with col_graficos:
    st.subheader("📊 Reclamos por Tipo de Daño")
    fig_tipo = px.bar(
        df_filtrado.groupby('tipo_dano').size().reset_index(name='cantidad'),
        x='tipo_dano',
        y='cantidad',
        title="Cantidad de Reportes por Tipo de Daño",
        color='tipo_dano',
        color_discrete_map=COLOR_TIPO
    )
    fig_tipo.update_layout(showlegend=False,
                           xaxis_title="Tipo de Daño",
                           yaxis_title="Cantidad",
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
                           font_color="#dfe6ee",
                           margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_tipo, width='stretch')

    st.markdown("---")  # separador entre los dos gráficos apilados

    st.subheader("📱 Canal de Reporte")
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
    fig_canal.update_traces(textposition='inside', textinfo='percent+label',
                           marker=dict(line=dict(color='#20262f', width=1)))
    fig_canal.update_layout(showlegend=True,
                           legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                       xanchor="right", x=1),
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor='rgba(0,0,0,0)',
                           font_color="#dfe6ee",
                           margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_canal, width='stretch')

# ==========================================
# KPIs ABAJO DEL MAPA (sin tarjetas, solo texto)
# ==========================================
st.markdown("---")

# Indicadores rápidos estilo tarjeta pero sin bordes complejos
pct_resueltos = (
    (df_filtrado['estado_gestion'] == 'Resuelto').sum() / len(df_filtrado) * 100
    if len(df_filtrado) else 0
)

c1, c2, c3 = st.columns(3)
with c1:
    st.caption(f"📊 **{len(df_filtrado)}** reportes")
with c2:
    st.caption(f"% **{pct_resueltos:.1f}** resueltos")
with c3:
    st.caption(f"🏘️ **{df_filtrado['comuna'].nunique()}** comunas")

# ==========================================
# ÁREA INFERIOR: GRÁFICOS DE EVOLUCIÓN (visible al hacer scroll)
# ==========================================
st.markdown("---")

st.subheader("📈 Evolución Acumulada: Reportes Abiertos vs Cerrados")

# Preparar datos de evolución diaria usando el campo resuelta_en
evol = df_filtrado.copy()
evol["FECHA"] = pd.to_datetime(evol["fecha_reporte"])

# Conteo diario de nuevos reportes
diario = evol.groupby(evol["FECHA"].dt.date).size().reset_index(name="nuevos")
diario["FECHA"] = pd.to_datetime(diario["FECHA"])
diario = diario.sort_values("FECHA")
diario["acum_nuevos"] = diario["nuevos"].cumsum()

# Calcular abiertos vs cerrados acumulados usando resuelta_en
total_resueltos = len(df_filtrado[df_filtrado["resuelta_en"] != ""])
if total_resueltos > 0:
    resueltos_hasta_ahora_list = []
    for fecha in diario["FECHA"]:
        r = int(df_filtrado[
            (df_filtrado["estado_gestion"] == "Resuelto") & 
            (df_filtrado["resuelta_en"] != "")
        ]["resuelta_en"].apply(lambda x: pd.to_datetime(x) <= fecha).sum())
        resueltos_hasta_ahora_list.append(r)
else:
    resueltos_hasta_ahora_list = [0] * len(diario)

abiertos_acum = []
cerrados_acum = []

for i, fecha in enumerate(diario["FECHA"]):
    abiertos_hoy = int(diario[diario["FECHA"] <= fecha]["acum_nuevos"].iloc[-1]) if len(diario[diario["FECHA"] <= fecha]) else 0
    cerrados_hoy = resueltos_hasta_ahora_list[i] if i < len(resueltos_hasta_ahora_list) else 0
    abiertos_acum.append(abiertos_hoy)
    cerrados_acum.append(cerrados_hoy)

diario["abiertos_acum"] = abiertos_acum
diario["cerrados_acum"] = cerrados_acum

# Graficar con Plotly
fig_evol = go.Figure()

fig_evol.add_trace(go.Scatter(
    x=diario["FECHA"],
    y=diario["abiertos_acum"],
    mode='lines+markers',
    name='Abiertos Acumulados',
    line=dict(color='#E74C3C', width=3),
    marker=dict(size=6),
    hovertemplate="Fecha: %{x|%d/%m}<br>Abiertos: %{y}<extra></extra>"
))

fig_evol.add_trace(go.Scatter(
    x=diario["FECHA"],
    y=diario["cerrados_acum"],
    mode='lines+markers',
    name='Cerrados Acumulados',
    line=dict(color='#1ABC9C', width=3),
    marker=dict(size=6),
    hovertemplate="Fecha: %{x|%d/%m}<br>Cerrados: %{y}<extra></extra>"
))

fig_evol.update_layout(
    title="Informe de Gestión: Saldo de Abiertos vs Cerrados",
    xaxis_title="Fecha",
    yaxis_title="Cantidad acumulada",
    legend_title="Estado",
    hovermode="x unified",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color="#dfe6ee",
    margin=dict(l=50, r=50, t=40, b=50),
    height=400
)

st.plotly_chart(fig_evol, width='stretch')

# ==========================================
# PIE DE PÁGINA
# ==========================================
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
st.sidebar.caption(f"📋 Versión: 3.1 — Analista Jhon Bedoya (layout: mapa izq, gráficos der, evolución abajo)")