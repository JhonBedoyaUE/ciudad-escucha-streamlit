# Ciudad Escucha — Dashboard Streamlit

Dashboard interactivo del **proyecto Ciudad Escucha** (asignatura Habilidades
Gerenciales, autor: **Jhon Bedoya — Analista**). Sistema de reporte de daños en
espacio público de Villavicencio, Meta, Colombia.

> 🚨 **DATOS SIMULADOS · PROYECTO ACADÉMICO**
> 1,000 registros sintéticos geocodificados en 10 comunas, etiquetados como
> `SIMULADO_ACADEMICO` en la columna `origen_datos`.

## ✨ Características

- 🗺️ **Mapa Folium** interactivo (OpenStreetMap) con puntos-círculo coloreados por tipo de daño
- 🛑 **Capa de veredas** del shapefile DANE 2024 (filtrada en QGIS con expresión `NOMB_MPIO='VILLAVICENCIO'`)
- 🌡️ **Mapa de calor** de densidad (toggle)
- 📊 5 visualizaciones: mapa, tipo de daño, tendencia temporal, comuna, canal
- 🎚️ Filtros laterales: comuna, tipo, canal, **estado de gestión** y rango de fechas
- 📈 KPIs con **% de resueltos**
- 📋 Tabla expander de los reportes filtrados
- 🎨 Leyenda flotante, control de capas y minimapa

## 🚀 Arranque local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8507
# → http://localhost:8507
```

## ☁️ Deploy en Streamlit Community Cloud

1. Fork o usa este repo directamente
2. Inicia sesión en https://share.streamlit.io con tu cuenta de GitHub
3. **Create app** → repo `ciudad-escucha-streamlit` → branch `master` → archivo `app.py`
4. Listo: la app sirve la capa de veredas desde `data/processed/` (GeoJSON de 0.2 MB)

## 📁 Estructura

```
├── app.py                              # dashboard Streamlit
├── requirements.txt
├── data/generated/dataset_simulado.csv # 1,000 registros sintéticos geocodificados
├── data/generated/metadatos_dataset.csv
├── data/processed/veredas_villavicencio_simpl.geojson
├── generar_dataset_gemini.py           # generador del dataset sintético
└── scripts/preparar_veredas_geojson.py # simplificación del GeoJSON de veredas
```

## 🔒 Ética de datos

Dataset simulado por fines académicos. Ningún registro proviene de reportes
reales. La capa de veredas es oficial (DANE 2024, Resolución Simple) y se usa
solo como referencia cartográfica.

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).
