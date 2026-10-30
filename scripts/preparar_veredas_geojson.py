#!/usr/bin/env python
"""Simplifica el GeoJSON de veredas exportado desde QGIS para el dashboard."""
import geopandas as gpd
import os

IN = "data/generated/veredas_villavicencio.geojson"
OUT = "data/generated/veredas_villavicencio_simpl.geojson"

gdf = gpd.read_file(IN)
print("Veredas:", len(gdf), "| CRS:", gdf.crs)
gdf["geometry"] = gdf.geometry.simplify(0.0003, preserve_topology=True)
gdf = gdf[["NOMBRE_VER", "CODIGO_VER", "NOMB_MPIO", "geometry"]]
gdf.to_file(OUT, driver="GeoJSON")
print("Guardado:", os.path.getsize(OUT) / 1e6, "MB")
