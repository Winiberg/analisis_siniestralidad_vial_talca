import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from scipy.spatial import ConvexHull

# 1. Cargar datos reales de Talca
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATOS = os.path.join(BASE_DIR, "data", "talca_con_clusters.csv")
RUTA_SALIDA_IMG = os.path.join(BASE_DIR, "data", "exploracion_visual_clusters.png")

df = pd.read_csv(RUTA_DATOS, low_memory=False)
coords = df[['longitud', 'Latitud']].dropna().values  # X = Longitud (Este-Oeste), Y = Latitud (Norte-Sur)

# 2. Comparar visualmente los 4 escenarios clave de decisión de K
# K=4 (Óptimo geométrico), K=5 (Codo Kneedle), K=7 (PLADECO - Seleccionado), K=8 (Sobre-segmentación)
valores_k = [4, 5, 7, 8]
fig, axes = plt.subplots(2, 2, figsize=(15, 13))
axes = axes.flatten()

# Paleta cualitativa de alto contraste (ideal para hasta 10 clústeres)
colores = plt.cm.tab10(np.linspace(0, 0.9, 10))

for idx, k in enumerate(valores_k):
    ax = axes[idx]
    
    # Ejecutar K-Means
    modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
    etiquetas = modelo.fit_predict(coords)
    centroides = modelo.cluster_centers_

    # Dibujar cada clúster y su envolvente convexa (polígono real)
    for cluster_id in range(k):
        puntos_cluster = coords[etiquetas == cluster_id]
        color = colores[cluster_id]

        # Puntos de siniestros
        ax.scatter(
            puntos_cluster[:, 0], puntos_cluster[:, 1],
            s=12, color=color, alpha=0.55, label=f'Zona {cluster_id+1}' if k == 7 else ""
        )

        # Polígono envolvente (Convex Hull) si hay al menos 3 puntos no colineales
        if len(puntos_cluster) >= 3:
            try:
                hull = ConvexHull(puntos_cluster)
                poligono = puntos_cluster[hull.vertices]
                ax.fill(poligono[:, 0], poligono[:, 1], color=color, alpha=0.18)
                # Cerrar el borde del polígono
                poligono_cerrado = np.vstack([poligono, poligono[0]])
                ax.plot(poligono_cerrado[:, 0], poligono_cerrado[:, 1], color=color, linewidth=1.2, alpha=0.8)
            except Exception:
                pass

    # Dibujar los centroides (el centro matemático de cada polígono)
    ax.scatter(
        centroides[:, 0], centroides[:, 1],
        s=140, c='black', marker='X', edgecolor='white', linewidth=1.5,
        zorder=10, label='Centroide'
    )

    # Etiquetar cada centroide (Z1..Zk) para facilitar su identificación espacial
    for cluster_id, (cx, cy) in enumerate(centroides):
        ax.annotate(
            f"Z{cluster_id + 1}",
            (cx, cy),
            textcoords="offset points",
            xytext=(0, 8),
            ha='center',
            fontsize=9,
            fontweight='bold',
            color='black',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='gray', alpha=0.85),
            zorder=11
        )

    # Ajustar zoom al núcleo urbano de Talca para ver bien los polígonos
    ax.set_xlim(-71.70, -71.60)
    ax.set_ylim(-35.46, -35.39)

    # Destacar visualmente el panel seleccionado (K = 7)
    if k == 7:
        ax.set_title(f"Partición Espacial con K = {k} Clústeres (Seleccionado - PLADECO)", fontsize=13, fontweight='bold', color='#1b4f72')
        for spine in ax.spines.values():
            spine.set_edgecolor('#1b4f72')
            spine.set_linewidth(2.2)
        ax.legend(loc='lower right', fontsize=8.5, framealpha=0.9, ncol=2)
    else:
        subtitulo = {4: "Máx. Silhouette", 5: "Codo Kneedle", 8: "Caída ARI"}.get(k, "")
        ax.set_title(f"Partición Espacial con K = {k} Clústeres ({subtitulo})", fontsize=13, fontweight='bold')

    ax.set_xlabel("Longitud (Oeste - Este)")
    ax.set_ylabel("Latitud (Sur - Norte)")
    ax.grid(True, linestyle='--', alpha=0.4)

plt.suptitle("Evolución Geométrica de K-Means sobre el Núcleo Urbano de Talca (Envolventes Convexas)", fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig(RUTA_SALIDA_IMG, dpi=300)
print(f"Imagen generada exitosamente en: {RUTA_SALIDA_IMG}")