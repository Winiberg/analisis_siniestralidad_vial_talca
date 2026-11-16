import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score

# 1. Configurar rutas dinámicas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATOS = os.path.join(BASE_DIR, "data", "talca_con_clusters.csv")
RUTA_SALIDA_CSV = os.path.join(BASE_DIR, "data", "metricas_evaluacion_clustering.csv")
RUTA_SALIDA_IMG = os.path.join(BASE_DIR, "data", "grafico_codo_silueta.png")

print("Cargando dataset consolidado de Talca...")
df = pd.read_csv(RUTA_DATOS, low_memory=False)

# Extraer coordenadas válidas
coords = df[['Latitud', 'longitud']].dropna().values
print(f"Total de registros georreferenciados válidos para evaluación: {len(coords)}")

# 2. Evaluación experimental de K-Means para K en rango [2, 15]
resultados_kmeans = []
rango_k = range(2, 16)

print("\nEjecutando evaluación iterativa de K-Means (K=2 a K=15)...")
for k in rango_k:
    modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
    etiquetas = modelo.fit_predict(coords)
    
    inercia = modelo.inertia_
    silueta = silhouette_score(coords, etiquetas)
    davies_bouldin = davies_bouldin_score(coords, etiquetas)
    
    resultados_kmeans.append({
        "K_Clusters": k,
        "Inercia_WCSS": round(inercia, 4),
        "Silhouette_Score": round(silueta, 4),
        "Davies_Bouldin_Index": round(davies_bouldin, 4)
    })

df_resultados = pd.DataFrame(resultados_kmeans)
df_resultados.to_csv(RUTA_SALIDA_CSV, index=False)

print("\n--- TABLA DE MÉTRICAS DE CALIDAD (K-MEANS) ---")
print(df_resultados.to_string(index=False))

# 3. Benchmarking: Comparación K-Means (K=10) vs. DBSCAN (Densidad Espacial Haversine)
print("\nEjecutando Benchmarking: K-Means (K=10) vs. DBSCAN (radio ~350m)...")

# K-Means con K=10 (Configuración productiva)
km_10 = KMeans(n_clusters=10, random_state=42, n_init=10)
labels_km10 = km_10.fit_predict(coords)
sil_km10 = silhouette_score(coords, labels_km10)
db_km10 = davies_bouldin_score(coords, labels_km10)

# DBSCAN usando métrica Haversine (350 metros / 6371000 metros radio tierra)
coords_rad = np.radians(coords)
eps_radianes = 350 / 6371000.0
dbscan = DBSCAN(eps=eps_radianes, min_samples=30, metric='haversine')
labels_dbscan = dbscan.fit_predict(coords_rad)

# Filtrar ruido (-1) para calcular silueta válida en DBSCAN
n_clusters_dbscan = len(set(labels_dbscan)) - (1 if -1 in labels_dbscan else 0)
n_ruido_dbscan = list(labels_dbscan).count(-1)
pct_ruido = (n_ruido_dbscan / len(coords)) * 100

if n_clusters_dbscan > 1:
    mask_validos = labels_dbscan != -1
    sil_dbscan = silhouette_score(coords[mask_validos], labels_dbscan[mask_validos])
    db_dbscan = davies_bouldin_score(coords[mask_validos], labels_dbscan[mask_validos])
else:
    sil_dbscan, db_dbscan = np.nan, np.nan

print("\n--- COMPARATIVA DE ALGORITMOS DE AGRUPAMIENTO ---")
comparativa = pd.DataFrame([
    {
        "Algoritmo": "K-Means (K=10)",
        "Clusters_Generados": 10,
        "Siniestros_Excluidos_Ruido": "0 (0.0%)",
        "Silhouette_Score": round(sil_km10, 4),
        "Davies_Bouldin": round(db_km10, 4),
        "Idoneidad_Operativa": "Alta (Cobertura total y centroides fijos)"
    },
    {
        "Algoritmo": "DBSCAN (eps=350m, min=30)",
        "Clusters_Generados": n_clusters_dbscan,
        "Siniestros_Excluidos_Ruido": f"{n_ruido_dbscan} ({pct_ruido:.1f}%)",
        "Silhouette_Score": round(sil_dbscan, 4) if not np.isnan(sil_dbscan) else "N/A",
        "Davies_Bouldin": round(db_dbscan, 4) if not np.isnan(db_dbscan) else "N/A",
        "Idoneidad_Operativa": "Media (Descarta siniestros aislados graves)"
    }
])
print(comparativa.to_string(index=False))

# 4. Generar gráfico dual (Método del Codo + Coeficiente de Silueta)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Subgráfico 1: Método del Codo (Inercia)
ax1.plot(df_resultados["K_Clusters"], df_resultados["Inercia_WCSS"], marker='o', color='#003366', linewidth=2)
ax1.axvline(x=10, color='#D32F2F', linestyle='--', label='K = 10 Seleccionado')
ax1.set_title("Método del Codo (Inercia / WCSS)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Número de Clústeres (K)")
ax1.set_ylabel("Inercia (Suma de distancias al cuadrado)")
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend()

# Subgráfico 2: Coeficiente de Silueta
ax2.plot(df_resultados["K_Clusters"], df_resultados["Silhouette_Score"], marker='s', color='#1565C0', linewidth=2)
ax2.axvline(x=10, color='#D32F2F', linestyle='--', label='K = 10 Seleccionado')
ax2.set_title("Coeficiente de Silueta (Cohesión y Separación)", fontsize=12, fontweight='bold')
ax2.set_xlabel("Número de Clústeres (K)")
ax2.set_ylabel("Silhouette Score")
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend()

plt.tight_layout()
plt.savefig(RUTA_SALIDA_IMG, dpi=300)
print(f"\nArchivos generados exitosamente:\n1. {RUTA_SALIDA_CSV}\n2. {RUTA_SALIDA_IMG}")