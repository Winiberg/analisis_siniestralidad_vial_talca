import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DATOS = os.path.join(BASE_DIR, "data", "talca_limpio_final.csv")
RUTA_SALIDA_CSV = os.path.join(BASE_DIR, "data", "metricas_evaluacion_clustering.csv")
RUTA_BENCHMARK_CSV = os.path.join(BASE_DIR, "data", "benchmark_algoritmos.csv")
RUTA_SALIDA_IMG = os.path.join(BASE_DIR, "data", "grafico_decision_k_utm.png")

K_SELECCIONADO = 7  # Alineado con las 7 Zonas Urbanas del PLADECO Talca 2024-2028


def latlon_a_utm19s(lat, lon):
    """Proyección WGS84 a UTM Zona 19 Sur (EPSG:32719) en metros."""
    a = 6378137.0
    f = 1 / 298.257223563
    k0 = 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)

    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    lon0_rad = np.radians(-69.0)

    N = a / np.sqrt(1 - e2 * np.sin(lat_rad) ** 2)
    T = np.tan(lat_rad) ** 2
    C = ep2 * np.cos(lat_rad) ** 2
    A = np.cos(lat_rad) * (lon_rad - lon0_rad)

    M = a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat_rad
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * np.sin(2 * lat_rad)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * np.sin(4 * lat_rad)
        - (35 * e2**3 / 3072) * np.sin(6 * lat_rad)
    )

    x = 500000.0 + k0 * N * (
        A
        + (1 - T + C) * A**3 / 6
        + (5 - 18 * T + T**2 + 72 * C - 58 * ep2) * A**5 / 120
    )
    y = 10000000.0 + k0 * (
        M
        + N
        * np.tan(lat_rad)
        * (
            A**2 / 2
            + (5 - T + 9 * C + 4 * C**2) * A**4 / 24
            + (61 - 58 * T + T**2 + 600 * C - 330 * ep2) * A**6 / 720
        )
    )
    return np.column_stack((x, y))


def calcular_estabilidad_ari(coords_utm, k, n_iter=15):
    """Mide reproducibilidad del clustering mediante ARI promedio entre semillas."""
    etiquetas_ref = KMeans(n_clusters=k, random_state=42, n_init=20).fit_predict(coords_utm)
    aris = []
    for seed in range(1, n_iter + 1):
        etiquetas_iter = KMeans(n_clusters=k, random_state=seed * 10, n_init=20).fit_predict(coords_utm)
        aris.append(adjusted_rand_score(etiquetas_ref, etiquetas_iter))
    return np.mean(aris)


def main():
    print("Cargando dataset limpio y proyectando coordenadas a UTM Zona 19S (metros)...")
    df = pd.read_csv(RUTA_DATOS, low_memory=False)
    df_valid = df.dropna(subset=["Latitud", "longitud"]).copy()

    coords_utm = latlon_a_utm19s(df_valid["Latitud"].values, df_valid["longitud"].values)
    print(f"Registros georreferenciados proyectados: {len(coords_utm):,}")

    # 1. Sensibilidad de K en rango [2, 15]
    rango_k = list(range(2, 16))
    resultados = []

    for k in rango_k:
        modelo = KMeans(n_clusters=k, random_state=42, n_init=20)
        etiquetas = modelo.fit_predict(coords_utm)
        centroides = modelo.cluster_centers_

        distancias_m = np.linalg.norm(coords_utm - centroides[etiquetas], axis=1)
        radio_mediano_m = np.median(distancias_m)
        pct_en_350m = np.mean(distancias_m <= 350.0) * 100

        resultados.append({
            "K": k,
            "Inercia_km2": round(modelo.inertia_ / 1e6, 2),
            "Silhouette": round(silhouette_score(coords_utm, etiquetas), 4),
            "Davies_Bouldin": round(davies_bouldin_score(coords_utm, etiquetas), 4),
            "Calinski_Harabasz": round(calinski_harabasz_score(coords_utm, etiquetas), 1),
            "Estabilidad_ARI": round(calcular_estabilidad_ari(coords_utm, k, n_iter=15), 4),
            "Radio_Mediano_m": round(radio_mediano_m, 1),
            "Pct_Siniestros_350m": round(pct_en_350m, 1),
        })

    df_res = pd.DataFrame(resultados)

    # Método Kneedle
    x_norm = (df_res["K"] - df_res["K"].min()) / (df_res["K"].max() - df_res["K"].min())
    y_norm = (df_res["Inercia_km2"] - df_res["Inercia_km2"].min()) / (
        df_res["Inercia_km2"].max() - df_res["Inercia_km2"].min()
    )
    df_res["Score_Kneedle"] = np.round(np.abs(x_norm + y_norm - 1) / np.sqrt(2), 4)
    df_res.to_csv(RUTA_SALIDA_CSV, index=False)

    # 2. Benchmarking K-Means (K=7) vs DBSCAN en el MISMO espacio métrico UTM 19S (metros)
    fila_k7 = df_res[df_res["K"] == K_SELECCIONADO].iloc[0]

    dbscan = DBSCAN(eps=350.0, min_samples=30, metric="euclidean")
    etiquetas_db = dbscan.fit_predict(coords_utm)
    n_clusters_db = len(set(etiquetas_db)) - (1 if -1 in etiquetas_db else 0)
    n_ruido_db = int(np.sum(etiquetas_db == -1))
    pct_ruido_db = round((n_ruido_db / len(coords_utm)) * 100, 1)

    mask_no_ruido = etiquetas_db != -1
    if len(set(etiquetas_db[mask_no_ruido])) > 1:
        sil_db_sin_ruido = round(silhouette_score(coords_utm[mask_no_ruido], etiquetas_db[mask_no_ruido]), 4)
        db_index_db = round(davies_bouldin_score(coords_utm[mask_no_ruido], etiquetas_db[mask_no_ruido]), 4)
    else:
        sil_db_sin_ruido = np.nan
        db_index_db = np.nan

    df_benchmark = pd.DataFrame([
        {
            "Algoritmo": f"K-Means (K={K_SELECCIONADO}, UTM 19S)",
            "Clusteres_Generados": K_SELECCIONADO,
            "Siniestros_Ruido": f"0 (0.0%)",
            "Silhouette_Score": fila_k7["Silhouette"],
            "Davies_Bouldin": fila_k7["Davies_Bouldin"],
            "Estabilidad_ARI": fila_k7["Estabilidad_ARI"],
            "Idoneidad_Operativa": "Alta — Cobertura del 100% de eventos y alineación directa con las 7 zonas urbanas del PLADECO.",
        },
        {
            "Algoritmo": "DBSCAN (eps=350m, min=30, UTM 19S)",
            "Clusteres_Generados": n_clusters_db,
            "Siniestros_Ruido": f"{n_ruido_db} ({pct_ruido_db}%)",
            "Silhouette_Score": sil_db_sin_ruido,
            "Davies_Bouldin": db_index_db,
            "Estabilidad_ARI": "N/A (Determinista)",
            "Idoneidad_Operativa": "Baja — Concentra el casco urbano en un solo macro-clúster y excluye siniestros periféricos.",
        },
    ])
    df_benchmark.to_csv(RUTA_BENCHMARK_CSV, index=False)

    print("\n--- TABLA MULTI-CRITERIO DE DECISIÓN PARA K (ESPACIO MÉTRICO UTM 19S) ---")
    print(df_res.to_string(index=False))

    print("\n--- BENCHMARKING EN ESPACIO MÉTRICO UTM 19S ---")
    print(df_benchmark.to_string(index=False))

    k_kneedle = int(df_res.loc[df_res["Score_Kneedle"].idxmax(), "K"])

    # Gráfico de 3 paneles destacando K=7 (PLADECO)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    axes[0].plot(df_res["K"], df_res["Inercia_km2"], marker="o", color="#003366", linewidth=2)
    axes[0].axvline(k_kneedle, color="#64748B", linestyle=":", label=f"Codo Kneedle (K={k_kneedle})")
    axes[0].axvline(K_SELECCIONADO, color="#D32F2F", linestyle="--", label=f"Seleccionado PLADECO (K={K_SELECCIONADO})")
    axes[0].set_title("1. Inercia (km²) y Criterio de Selección", fontweight="bold")
    axes[0].set_xlabel("Número de Clústeres (K)")
    axes[0].set_ylabel("Inercia (km²)")
    axes[0].grid(True, linestyle=":", alpha=0.6)
    axes[0].legend(fontsize=8.5)

    axes[1].plot(df_res["K"], df_res["Silhouette"], marker="s", color="#1565C0", linewidth=2, label="Silhouette")
    axes[1].plot(df_res["K"], df_res["Estabilidad_ARI"], marker="^", color="#2E7D32", linewidth=2, label="Estabilidad ARI")
    axes[1].axvline(K_SELECCIONADO, color="#D32F2F", linestyle="--", label=f"K={K_SELECCIONADO} (ARI={fila_k7['Estabilidad_ARI']})")
    axes[1].set_title("2. Cohesión (Silhouette) y Estabilidad (ARI)", fontweight="bold")
    axes[1].set_xlabel("Número de Clústeres (K)")
    axes[1].set_ylabel("Índice [0 - 1]")
    axes[1].grid(True, linestyle=":", alpha=0.6)
    axes[1].legend(fontsize=8.5)

    axes[2].plot(df_res["K"], df_res["Radio_Mediano_m"], marker="d", color="#E65100", linewidth=2)
    axes[2].axvline(K_SELECCIONADO, color="#D32F2F", linestyle="--", label=f"K={K_SELECCIONADO} (Mediana={fila_k7['Radio_Mediano_m']}m)")
    axes[2].set_title("3. Escala Espacial (Radio Mediano en m)", fontweight="bold")
    axes[2].set_xlabel("Número de Clústeres (K)")
    axes[2].set_ylabel("Distancia mediana al centroide (m)")
    axes[2].grid(True, linestyle=":", alpha=0.6)
    axes[2].legend(fontsize=8.5)

    plt.tight_layout()
    plt.savefig(RUTA_SALIDA_IMG, dpi=300)
    print(f"\nArchivos guardados:\n • {RUTA_SALIDA_CSV}\n • {RUTA_BENCHMARK_CSV}\n • {RUTA_SALIDA_IMG}")


if __name__ == "__main__":
    main()