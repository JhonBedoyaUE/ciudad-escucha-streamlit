"""Genera dataset geocodificado para Ciudad Escucha usando modelo Gemini Deep Research."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generar_datos_ciudad_escucha(num_reportes=1000, semilla=42):
    """
    Genera un dataset sintético geocodificado de reportes de daños
    en el espacio público para Villavicencio, Colombia, optimizado para Streamlit.
    """
    # Fijar semillas para reproducibilidad determinística del ejercicio académico
    np.random.seed(semilla)
    random.seed(semilla)

    # 1. Definición de la estructura comunal y pesos poblacionales (DANE 2026)
    # Se utilizan Bounding Boxes empíricas para limitar la generación a áreas habitadas
    comunas_info = {
        1: {"peso": 0.050, "bounds": {"lat": (4.1480, 4.1600), "lon": (-73.6450, -73.6300)}},
        2: {"peso": 0.040, "bounds": {"lat": (4.1380, 4.1500), "lon": (-73.6400, -73.6280)}},
        3: {"peso": 0.040, "bounds": {"lat": (4.1380, 4.1520), "lon": (-73.6280, -73.6100)}},
        4: {"peso": 0.154, "bounds": {"lat": (4.1150, 4.1400), "lon": (-73.6250, -73.6000)}},
        5: {"peso": 0.215, "bounds": {"lat": (4.1050, 4.1300), "lon": (-73.6550, -73.6250)}},
        6: {"peso": 0.040, "bounds": {"lat": (4.1300, 4.1450), "lon": (-73.6600, -73.6400)}},
        7: {"peso": 0.141, "bounds": {"lat": (4.0950, 4.1250), "lon": (-73.6150, -73.5800)}},
        8: {"peso": 0.112, "bounds": {"lat": (4.0800, 4.1100), "lon": (-73.6650, -73.6350)}},
        9: {"peso": 0.105, "bounds": {"lat": (4.1500, 4.1750), "lon": (-73.6200, -73.5950)}},
        10: {"peso": 0.067, "bounds": {"lat": (4.1550, 4.1800), "lon": (-73.6700, -73.6400)}}
    }

    # 2. Definición de la matriz de problemas (espacio público)
    tipos_dano = ["Vías", "Alumbrado público", "Basuras", "Alcantarillado", "Otro"]
    pesos_dano = [0.30, 0.25, 0.20, 0.15, 0.10]  # Probabilidades de ocurrencia global

    # 3. Modelado de Brecha Digital y Canales de Recepción
    canales = ["App Ciudad Escucha", "WhatsApp", "Portal Web", "Físico/PQRSD Telefónico"]
    pesos_canales = [0.45, 0.35, 0.15, 0.05]

    # 4. Estados operativos para el seguimiento gerencial en el Dashboard
    estados = ["Reportado", "En revisión", "Programado", "Resuelto"]
    pesos_estados = [0.40, 0.30, 0.15, 0.15]

    # 1. Cálculo preciso de la distribución espacial basada en demografía
    comunas_lista = list(comunas_info.keys())
    pesos_brutos = np.array([0.050, 0.040, 0.040, 0.154, 0.215, 0.040, 0.141, 0.112, 0.105, 0.067])
    pesos_poblacion = pesos_brutos / pesos_brutos.sum()
    distribucion_comunas = [int(num_reportes * p) for p in pesos_poblacion]

    # Corrección de redondeo fraccional para garantizar exactamente num_reportes
    diferencia = num_reportes - sum(distribucion_comunas)
    if diferencia > 0:
        # Ordenar por peso descendente para distribuir los extras a las más pobladas
        indices_ordenados = sorted(range(len(comunas_lista)), key=lambda i: comunas_info[comunas_lista[i]]["peso"], reverse=True)
        for i in range(min(diferencia, len(indices_ordenados))):
            distribucion_comunas[indices_ordenados[i]] += 1

    # 3. Inicialización del almacenamiento de registros
    datos = []
    id_counter = 1000  # Inicia secuencia de IDs
    fecha_base = datetime.now() - timedelta(days=90)  # Ventana analítica de 3 meses

    # Bucle principal de generación stratificada
    for idx, comuna in enumerate(comunas_lista):
        n_puntos = distribucion_comunas[idx]
        bounds = comunas_info[comuna]["bounds"]

        # Generación vectorial hiper-eficiente de coordenadas distribuidas uniformemente
        # dentro de las cotas límite (Bounding Box) de la comuna específica
        lats = np.random.uniform(low=bounds["lat"][0], high=bounds["lat"][1], size=n_puntos)
        lons = np.random.uniform(low=bounds["lon"][0], high=bounds["lon"][1], size=n_puntos)

        for i in range(n_puntos):
            # Asignación de dispersión temporal aleatoria
            fecha_reporte = fecha_base + timedelta(
                days=random.randint(0, 90),
                minutes=random.randint(0, 1440)
            )

            # Muestreo probabilístico categórico
            tipo = np.random.choice(tipos_dano, p=pesos_dano)
            canal = np.random.choice(canales, p=pesos_canales)
            estado = np.random.choice(estados, p=pesos_estados)

            # Construcción de identificadores alfanuméricos estandarizados
            id_reporte = f"CE-2026-{id_counter}"
            id_counter += 1

            # Estructuración final de la fila de datos
            datos.append({
                "id_reporte": id_reporte,
                "fecha_reporte": fecha_reporte.strftime("%Y-%m-%d %H:%M:%S"),
                "latitud": round(lats[i], 6),
                "longitud": round(lons[i], 6),
                "comuna": f"Comuna {comuna}",
                "tipo_dano": tipo,
                "canal_reporte": canal,
                "estado_gestion": estado,
                "origen_datos": "SIMULADO_ACADEMICO"
            })

    # Transformación a estructura tabular y sanitización
    df = pd.DataFrame(datos)

    # Aleatorización del índice para simular el flujo orgánico de ingreso de datos
    df = df.sample(frac=1, random_state=semilla).reset_index(drop=True)

    return df

if __name__ == "__main__":
    # Generación y exportación a formato de valores separados por comas
    dataset_simulado = generar_datos_ciudad_escucha(1000)
    dataset_simulado.to_csv("data/generated/dataset_simulado.csv", index=False)
    print(f"Éxito: Se han exportado {len(dataset_simulado)} registros georreferenciados.")
    
    # Mostrar resumen
    print("\n--- Resumen del Dataset Generado ---")
    print(f"Total de reportes: {len(dataset_simulado)}")
    print("\nDistribución por Comuna:")
    print(dataset_simulado['comuna'].value_counts().sort_index())
    print(f"\nSuma de reportes por comuna: {dataset_simulado['comuna'].value_counts().sort_index().sum()}")
    print("\nDistribución por Tipo de Daño:")
    print(dataset_simulado['tipo_dano'].value_counts())
    print("\nDistribución por Canal de Reporte:")
    print(dataset_simulado['canal_reporte'].value_counts())
    print("\nDistribución por Estado de Gestión:")
    print(dataset_simulado['estado_gestion'].value_counts())
    print("\nRango geográfico:")
    print(f"Latitud: {dataset_simulado['latitud'].min():.4f} - {dataset_simulado['latitud'].max():.4f}")
    print(f"Longitud: {dataset_simulado['longitud'].min():.4f} - {dataset_simulado['longitud'].max():.4f}")
    print(f"\nPromedio lat: {dataset_simulado['latitud'].mean():.4f}, Promedio lon: {dataset_simulado['longitud'].mean():.4f}")
