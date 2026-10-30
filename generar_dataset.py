"""Genera el dataset simulado para el proyecto Ciudad Escucha."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Inicializar semilla
np.random.seed(42)

num_registros = 1000

# 1. Pesos poblacionales normalizados
comunas = [f'Comuna {i}' for i in range(1, 11)]
pesos_brutos = np.array([0.05, 0.04, 0.04, 0.154, 0.215, 0.04, 0.141, 0.112, 0.105, 0.067])
pesos_poblacion = pesos_brutos / pesos_brutos.sum()

# 2. Generación de fechas con estacionalidad (lluvias abril-mayo)
def generar_fecha_estacional():
    inicio = datetime(2025, 1, 1)
    dias_totales = 545
    if np.random.rand() < 0.3:  # 30% forzado a época de lluvias
        dias_random = np.random.randint(90, 150)
        anyo = np.random.choice([2025, 2026])
        return inicio.replace(year=anyo) + timedelta(days=dias_random)
    else:
        dias_random = np.random.randint(0, dias_totales)
        return inicio + timedelta(days=dias_random)

# 3. Tipos de daño y canales con distribuciones probabilistic
tipo_dano_opciones = ['Via', 'Alumbrado publico', 'Basuras', 'Alcantarillado', 'Otro']
pesos_tipo = [0.40, 0.25, 0.20, 0.10, 0.05]

canal_opciones = ['App Ciudadana', 'PQRSD Web', 'Linea Telefonica', 'Redes Sociales']
pesos_canal = [0.50, 0.20, 0.15, 0.15]

# 4. Dependencias asignadas por tipo de daño (basado en entrevista escrita)
dependencia_map = {
    'Via': 'Secretaria de Movilidad',
    'Alumbrado publico': 'Alborada',
    'Basuras': 'Secretaria de Aseo',
    'Alcantarillado': 'Empresa de acueducto y alcantarillado',
    'Otro': 'Dependencia variables'
}

# 5. Tiempo de respuesta estimado por tipo de daño (dias)
tiempo_promedio = {'Via': 5, 'Alumbrado publico': 3, 'Basuras': 7, 'Alcantarillado': 10, 'Otro': 4}

# 6. Construccion del DataFrame usando lista de diccionarios
registros = []
for i in range(num_registros):
    fd = generar_fecha_estacional()
    tipo = np.random.choice(tipo_dano_opciones, p=pesos_tipo)
    canal = np.random.choice(canal_opciones, p=pesos_canal)
    fila = {
        'id_reporte': f'REP-{1000 + i}',
        'fecha_reporte': fd,
        'comuna': np.random.choice(comunas, p=pesos_poblacion),
        'tipo_dano': tipo,
        'canal': canal,
        'dependencia_asignada': dependencia_map[tipo],
        'dias_respuesta': tiempo_promedio[tipo],
        'fecha_resolucion': datetime(2025, 1, 1) + timedelta(days=np.random.randint(1, 30)),
        'reporte_repetido': np.random.choice([True, False], p=[0.2, 0.8])
    }
    registros.append(fila)

df = pd.DataFrame(registros)
df = df.sort_values(by='fecha_reporte').reset_index(drop=True)
df['origen_datos'] = 'DATOS SIMULADOS - PROYECTO ACADÉMICO'

# 7. Guardar dataset principal
df.to_csv('data/generated/dataset_simulado.csv', index=False, encoding='utf-8')

# 8. Mostrar resumen en consola
print("Dataset generado exitosamente!")
print(f"Total de registros: {len(df)}")
print("Distribucion por Comuna:")
print(df['comuna'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
print("\nMuestra de datos:")
print(df.head())

# 9. Guardar metadatos (usando valores simples, no arrays)
fechas_str = f"{df['fecha_reporte'].min().strftime('%Y-%m-%d')} a {df['fecha_reporte'].max().strftime('%Y-%m-%d')}"
metadatos = {
    'num_registros': [num_registros],
    'fechas': [fechas_str],
    'comunas': [len(comunas)],
    'tipos_dano': [tipo_dano_opciones],
    'canales': [canal_opciones],
    'fecha_generacion': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
}
pd.DataFrame(metadatos).to_csv('data/generated/metadatos_dataset.csv', index=False)

print("Guardado en data/generated/")
