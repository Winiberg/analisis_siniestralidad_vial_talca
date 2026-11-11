import os
import pandas as pd

DATA_DIR = "../data"
ruta_entrada = os.path.join(DATA_DIR, "talca_consolidado.csv")
df = pd.read_csv(ruta_entrada, low_memory=False)

print("--- MUESTRA DE COLUMNAS DE COORDENADAS ---")
cols_geo = [c for c in ['Latitud', 'longitud', 'x', 'y', 'UBICACION', 'Calle_Uno'] if c in df.columns]
print(df[cols_geo].head(10))

print("\n--- TIPOS DE DATOS ---")
print(df[cols_geo].dtypes)

print("\n--- VALORES NO NULOS ---")
print(df[cols_geo].notnull().sum())