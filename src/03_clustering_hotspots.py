import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# 1. Cargar el dataset limpio
DATA_DIR = "../data"
ruta_entrada = os.path.join(DATA_DIR, "talca_limpio_final.csv")
df = pd.read_csv(ruta_entrada, low_memory=False)

print(f"Cargando {len(df)} registros para clustering espacial...")

# 2. Extraer matriz de coordenadas
coords = df[['Latitud', 'longitud']].values

# 3. Aplicar K-Means (10 clústeres principales)
N_CLUSTERS = 10
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
df['CLUSTER_ID'] = kmeans.fit_predict(coords)

# 4. Calcular métricas por Clúster
resumen_clusters = df.groupby('CLUSTER_ID').agg(
    LATITUD_CENTRO=('Latitud', 'mean'),
    LONGITUD_CENTRO=('longitud', 'mean'),
    TOTAL_ACCIDENTES=('FID', 'count'),
    TOTAL_FALLECIDOS=('FALLECIDOS', 'sum'),
    TOTAL_GRAVES=('GRAVES', 'sum'),
    TOTAL_LESI=('TOTAL_LESI', 'sum'),
    SEVERIDAD_ACUMULADA=('PUNTAJE_SEVERIDAD', 'sum')
).reset_index()

# Ordenar por severidad acumulada
resumen_clusters = resumen_clusters.sort_values(by='SEVERIDAD_ACUMULADA', ascending=False)
resumen_clusters['RANKING_RIESGO'] = range(1, len(resumen_clusters) + 1)

# Nombres exactos de sectores urbanos de Talca ajustados por el equipo
nombres_zonas = {
    1: "Sector Centro / 6 Oriente (2 y 3 Norte)",
    2: "Sector Terminal de Buses / Hospital (1 Sur - 12 Oriente)",
    3: "Acceso Norte / Av. Lircay",
    4: "Sector 2 Norte / Av. San Miguel",
    5: "Sector Plaza de Armas / 1 Sur (2 y 3 Poniente)",
    6: "Sector Sur / 16 Sur (5 Oriente)",
    7: "Sector Av. Circunvalación 30 Oriente / 8 Sur",
    8: "Sector Av. Colín / Mall Go Florida",
    9: "Sector Las Rastras / UCM (2 Norte)",
    10: "Sector Bicentenario / 26 Oriente"
}

resumen_clusters['NOMBRE_ZONA'] = resumen_clusters['RANKING_RIESGO'].map(nombres_zonas)

# Guardar archivos resultantes
ruta_salida_df = os.path.join(DATA_DIR, "talca_con_clusters.csv")
df.to_csv(ruta_salida_df, index=False)

ruta_salida_hotspots = os.path.join(DATA_DIR, "hotspots_centroides.csv")
resumen_clusters.to_csv(ruta_salida_hotspots, index=False)

print("\n¡Clustering y nombres urbanos de Talca actualizados exitosamente!")