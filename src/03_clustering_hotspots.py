import os
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
N_CLUSTERS = 7  # Zonas urbanas oficiales según PLADECO Talca 2024-2028 (pp. 46-47)


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


def asignar_macrozona_pladeco(lat, lon):
    """
    Asigna la zona urbana del PLADECO Talca 2024-2028 (Tabla 8, p. 47)
    según las coordenadas geográficas reales del centroide.
    """
    if lat > -35.412 and lon < -71.640:
        return "Zona Norte (Alameda Norte / Av. Lircay)"
    elif lon >= -71.630 and lat >= -35.432:
        return "Zona Nororiente (Las Rastras / Av. San Miguel)"
    elif lon >= -71.642 and lat < -35.432:
        return "Zona Suroriente - Carlos Trupp (30 Oriente / 8 Sur)"
    elif -71.653 <= lon < -71.630 and -35.435 <= lat <= -35.412:
        return "Zona Pericentro (Terminal / Hospital / Ruta 5)"
    elif lon < -71.672 and lat < -35.432:
        return "Zona Surponiente (Av. Colín / La Florida)"
    elif lat < -35.435 and -71.672 <= lon < -71.642:
        return "Zona Suroriente - Las Colines (16 Sur / 5 Oriente)"
    else:
        return "Zona Centro (Casco Histórico / 1 Sur - 6 Oriente)"


def main():
    ruta_entrada = os.path.join(DATA_DIR, "talca_limpio_final.csv")
    df = pd.read_csv(ruta_entrada, low_memory=False)
    print(f"Cargando {len(df):,} registros válidos para clustering espacial (K={N_CLUSTERS}, UTM 19S)...")

    # Proyectar a UTM 19S (metros) antes de agrupar
    coords_utm = latlon_a_utm19s(df["Latitud"].values, df["longitud"].values)
    df["UTM_X"] = coords_utm[:, 0]
    df["UTM_Y"] = coords_utm[:, 1]

    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20)
    df["CLUSTER_ID"] = kmeans.fit_predict(coords_utm)

    # Calcular distancia en metros de cada siniestro a su centroide UTM
    centroides_utm = kmeans.cluster_centers_
    df["DIST_CENTROIDE_M"] = np.linalg.norm(
        coords_utm - centroides_utm[df["CLUSTER_ID"].values], axis=1
    )

    # Resumen agregado por CLUSTER_ID (sin dependencia del orden de ranking)
    resumen_clusters = (
        df.groupby("CLUSTER_ID")
        .agg(
            LATITUD_CENTRO=("Latitud", "mean"),
            LONGITUD_CENTRO=("longitud", "mean"),
            UTM_X_CENTRO=("UTM_X", "mean"),
            UTM_Y_CENTRO=("UTM_Y", "mean"),
            RADIO_MEDIANO_M=("DIST_CENTROIDE_M", "median"),
            RADIO_P90_M=("DIST_CENTROIDE_M", lambda s: np.percentile(s, 90)),
            TOTAL_SINIESTROS=("CLUSTER_ID", "size"),
            TOTAL_FALLECIDOS=("FALLECIDOS", "sum"),
            TOTAL_GRAVES=("GRAVES", "sum"),
            TOTAL_MENOS_GRAV=("MENOS_GRAV", "sum"),
            TOTAL_LEVES=("LEVES", "sum"),
            TOTAL_LESI=("TOTAL_LESI", "sum"),
            SEVERIDAD_ACUMULADA=("PUNTAJE_SEVERIDAD", "sum"),
        )
        .reset_index()
    )

    # Asignar nombre geográfico basado en las coordenadas reales del CLUSTER_ID
    resumen_clusters["NOMBRE_ZONA"] = resumen_clusters.apply(
        lambda r: asignar_macrozona_pladeco(r["LATITUD_CENTRO"], r["LONGITUD_CENTRO"]),
        axis=1,
    )

    # Ordenar por Severidad Acumulada (C7: evitamos el término 'riesgo' sin exposición)
    resumen_clusters = resumen_clusters.sort_values(
        by="SEVERIDAD_ACUMULADA", ascending=False
    ).reset_index(drop=True)
    resumen_clusters["RANKING_SEVERIDAD"] = range(1, len(resumen_clusters) + 1)

    # Mapear NOMBRE_ZONA y RANKING_SEVERIDAD de vuelta al dataset individual
    mapa_nombres = dict(zip(resumen_clusters["CLUSTER_ID"], resumen_clusters["NOMBRE_ZONA"]))
    mapa_ranking = dict(zip(resumen_clusters["CLUSTER_ID"], resumen_clusters["RANKING_SEVERIDAD"]))
    df["NOMBRE_ZONA"] = df["CLUSTER_ID"].map(mapa_nombres)
    df["RANKING_SEVERIDAD"] = df["CLUSTER_ID"].map(mapa_ranking)

    # Guardar artefactos
    ruta_salida_df = os.path.join(DATA_DIR, "talca_con_clusters.csv")
    df.to_csv(ruta_salida_df, index=False)

    ruta_salida_hotspots = os.path.join(DATA_DIR, "hotspots_centroides.csv")
    resumen_clusters.to_csv(ruta_salida_hotspots, index=False)

    print("\n--- RESUMEN DE LOS 7 CLÚSTERES (UTM 19S + PLADECO) ---")
    for _, row in resumen_clusters.iterrows():
        cid = int(row["CLUSTER_ID"])
        sub = df[df["CLUSTER_ID"] == cid]
        top_dirs = sub["UBICACION"].value_counts().head(2).index.tolist() if "UBICACION" in sub.columns else []
        print(
            f"#{int(row['RANKING_SEVERIDAD'])} [ID={cid}] {row['NOMBRE_ZONA']} | "
            f"Lat={row['LATITUD_CENTRO']:.5f}, Lon={row['LONGITUD_CENTRO']:.5f} | "
            f"Siniestros={int(row['TOTAL_SINIESTROS'])} | ISA={int(row['SEVERIDAD_ACUMULADA'])} | "
            f"Mediana={row['RADIO_MEDIANO_M']:.0f}m | Top vías: {top_dirs}"
        )


if __name__ == "__main__":
    main()