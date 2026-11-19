import os
import pandas as pd

# Ruta base dinámica (funciona desde la raíz del proyecto o desde src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

ARCHIVOS_ANUALES = {
    2020: "Base_SINIESTROS_2020_2025_-3174842490189112332.csv",
    2021: "Base_SINIESTROS_2020_2025_-927440716653130631.csv",
    2022: "Base_SINIESTROS_2020_2025_3184543823866369420.csv",
    2025: "Base_SINIESTROS_2020_2025_-4651003952728958805.csv",
}


def main():
    lista_dfs = []
    resumen_ingesta = []

    for anio, archivo in ARCHIVOS_ANUALES.items():
        ruta_completa = os.path.join(DATA_DIR, archivo)
        if not os.path.exists(ruta_completa):
            raise FileNotFoundError(
                f"Archivo obligatorio no encontrado para el año {anio}: {ruta_completa}"
            )

        print(f"Cargando dataset nacional {anio}: {archivo}...")
        df_temp = pd.read_csv(ruta_completa, low_memory=False)
        lista_dfs.append(df_temp)

    df_nacional = pd.concat(lista_dfs, ignore_index=True)
    print(f"\nTotal registros nacionales combinados: {len(df_nacional):,}")

    columna_comuna = "COMUNA"
    if columna_comuna not in df_nacional.columns:
        raise KeyError(f"La columna '{columna_comuna}' no existe en el dataset.")

    df_talca = df_nacional[
        df_nacional[columna_comuna].astype(str).str.strip().str.upper() == "TALCA"
    ].copy()

    # Auditoría básica por año
    conteo_anual = df_talca["AÑO"].value_counts().sort_index().to_dict()
    print(f"\nTotal registros filtrados para TALCA: {len(df_talca):,}")
    print("Desglose por año disponible (sin registros 2023-2024 en fuente CONASET):")
    for anio, total in conteo_anual.items():
        print(f"  • Año {int(anio)}: {total:,} siniestros")
        resumen_ingesta.append({"Anio": int(anio), "Registros_Talca": int(total)})

    ruta_salida = os.path.join(DATA_DIR, "talca_consolidado.csv")
    df_talca.to_csv(ruta_salida, index=False)
    print(f"\nDataset consolidado de Talca guardado en: {ruta_salida}")


if __name__ == "__main__":
    main()