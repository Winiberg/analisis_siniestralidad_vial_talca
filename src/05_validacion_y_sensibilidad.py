import os
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from scipy.stats import spearmanr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


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


def main():
    ruta_clusters = os.path.join(DATA_DIR, "talca_con_clusters.csv")
    df = pd.read_csv(ruta_clusters, low_memory=False)

    # =========================================================================
    # 1. VALIDACIÓN TEMPORAL PREDICTIVA (Entrenamiento 2020-2022 -> Test 2025)
    # =========================================================================
    df_train = df[df["AÑO"].isin([2020, 2021, 2022])].copy()
    df_test = df[df["AÑO"] == 2025].copy()

    coords_train = latlon_a_utm19s(df_train["Latitud"].values, df_train["longitud"].values)
    coords_test = latlon_a_utm19s(df_test["Latitud"].values, df_test["longitud"].values)

    modelo_hist = KMeans(n_clusters=7, random_state=42, n_init=20).fit(coords_train)
    centroides_hist = modelo_hist.cluster_centers_

    # Distancia en metros de cada siniestro de 2025 al centroide histórico más cercano
    distancias_2025 = np.min(
        np.linalg.norm(coords_test[:, None, :] - centroides_hist[None, :, :], axis=2),
        axis=1,
    )
    df_test["DIST_CENTROIDE_HIST_M"] = distancias_2025

    res_temporal = []
    for radio in [350, 500, 650, 800, 1000]:
        en_radio = df_test[df_test["DIST_CENTROIDE_HIST_M"] <= radio]
        pct_siniestros = (len(en_radio) / len(df_test)) * 100
        pct_isa = (en_radio["PUNTAJE_SEVERIDAD"].sum() / df_test["PUNTAJE_SEVERIDAD"].sum()) * 100
        res_temporal.append({
            "Radio_Cobertura_m": radio,
            "Siniestros_2025_Capturados": len(en_radio),
            "Total_Siniestros_2025": len(df_test),
            "Tasa_Acierto_Siniestros_Pct": round(pct_siniestros, 1),
            "Tasa_Acierto_ISA_Pct": round(pct_isa, 1),
        })

    df_temporal = pd.DataFrame(res_temporal)
    df_temporal.to_csv(os.path.join(DATA_DIR, "validacion_temporal_2025.csv"), index=False)

    print("\n--- 1. VALIDACIÓN TEMPORAL PREDICTIVA (ENTRENADO 2020-2022 -> EVALUADO EN 2025) ---")
    print(df_temporal.to_string(index=False))

    # =========================================================================
    # 2. ANÁLISIS DE SENSIBILIDAD DE PONDERADORES DEL ISA (Correlación Spearman)
    # =========================================================================
    esquemas = {
        "ISA_Actual (10/5/3/1)": (10, 5, 3, 1),
        "Frecuencia_Pura (1/1/1/1)": (1, 1, 1, 1),
        "Severidad_Extrema (20/10/3/1)": (20, 10, 3, 1),
        "EPDO_Modificado (12/6/3/1)": (12, 6, 3, 1),
    }

    df_sens = df.groupby(["CLUSTER_ID", "NOMBRE_ZONA"], as_index=False).agg(
        Siniestros=("CLUSTER_ID", "size"),
        Fallecidos=("FALLECIDOS", "sum"),
        Graves=("GRAVES", "sum"),
        Menos_Graves=("MENOS_GRAV", "sum"),
        Leves=("LEVES", "sum"),
    )

    for nombre, (wf, wg, wmg, wl) in esquemas.items():
        if nombre == "Frecuencia_Pura (1/1/1/1)":
            df_sens[nombre] = df_sens["Siniestros"]
        else:
            df_sens[nombre] = (
                df_sens["Fallecidos"] * wf
                + df_sens["Graves"] * wg
                + df_sens["Menos_Graves"] * wmg
                + df_sens["Leves"] * wl
            )
        df_sens[f"Rank_{nombre}"] = df_sens[nombre].rank(ascending=False, method="min").astype(int)

    df_sens = df_sens.sort_values("Rank_ISA_Actual (10/5/3/1)").reset_index(drop=True)
    df_sens.to_csv(os.path.join(DATA_DIR, "sensibilidad_pesos_isa.csv"), index=False)

    print("\n--- 2. ANÁLISIS DE SENSIBILIDAD DEL RANKING DE ZONAS (SPEARMAN) ---")
    rank_base = df_sens["Rank_ISA_Actual (10/5/3/1)"]
    for nombre in esquemas:
        if nombre != "ISA_Actual (10/5/3/1)":
            rho, pval = spearmanr(rank_base, df_sens[f"Rank_{nombre}"])
            print(f"  • Correlación Spearman vs {nombre}: rho = {rho:.4f} (p = {pval:.4f})")

    # =========================================================================
    # 3. TOP 10 INTERSECCIONES / PUNTOS EXACTOS MÁS CRÍTICOS DE TALCA
    # =========================================================================
    if "Calle_Uno" in df.columns and "Calle_Dos" in df.columns:
        c1 = df["Calle_Uno"].fillna("").astype(str).str.strip()
        c2 = df["Calle_Dos"].fillna("").astype(str).str.strip()
        df["INTERSECCION"] = np.where(
            (c2 != "") & (c2.str.upper() != "NAN") & (c2 != "0"),
            c1 + " & " + c2,
            c1,
        )
    else:
        df["INTERSECCION"] = df["UBICACION"].fillna("SIN DIRECCIÓN").astype(str).str.strip()

    top_inter = (
        df.groupby(["INTERSECCION", "NOMBRE_ZONA"], as_index=False)
        .agg(
            Latitud=("Latitud", "median"),
            Longitud=("longitud", "median"),
            Total_Siniestros=("INTERSECCION", "size"),
            Fallecidos=("FALLECIDOS", "sum"),
            Graves=("GRAVES", "sum"),
            Severidad_ISA=("PUNTAJE_SEVERIDAD", "sum"),
        )
        .sort_values(by=["Severidad_ISA", "Total_Siniestros"], ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    top_inter["Ranking"] = range(1, len(top_inter) + 1)
    top_inter.to_csv(os.path.join(DATA_DIR, "top_intersecciones_talca.csv"), index=False)

    print("\n--- 3. TOP 10 INTERSECCIONES / TRAMOS ESPECÍFICOS DE TALCA ---")
    print(top_inter[["Ranking", "INTERSECCION", "NOMBRE_ZONA", "Total_Siniestros", "Severidad_ISA"]].to_string(index=False))


if __name__ == "__main__":
    main()