import os
import pandas as pd

# 1. Definir la ruta de la carpeta de datos y los archivos
DATA_DIR = "../data" # Ajusta si tu carpeta se llama distinto
archivos = [
    "Base_SINIESTROS_2020_2025_-3174842490189112332.csv", # Reemplaza con los nombres exactos de tus archivos
    "Base_SINIESTROS_2020_2025_-927440716653130631.csv",
    "Base_SINIESTROS_2020_2025_3184543823866369420.csv",
    "Base_SINIESTROS_2020_2025_-4651003952728958805.csv"
]

lista_dfs = []

# 2. Cargar y consolidar los archivos
for archivo in archivos:
    ruta_completa = os.path.join(DATA_DIR, archivo)
    if os.path.exists(ruta_completa):
        print(f"Cargando {archivo}...")
        # Si tus archivos son Excel (.xlsx), cambia pd.read_csv por pd.read_excel
        df_temp = pd.read_csv(ruta_completa, low_memory=False) 
        lista_dfs.append(df_temp)
    else:
        print(f"¡Atención! No se encontró el archivo: {ruta_completa}")

# Unir todos los registros en un solo DataFrame
df_nacional = pd.concat(lista_dfs, ignore_index=True)
print(f"\nTotal registros nacionales combinados: {len(df_nacional)}")

# 3. Inspeccionar nombres de columnas para identificar la columna de Comuna
print("\nColumnas disponibles en la base de datos:")
print(df_nacional.columns.tolist())

# 4. Filtrar por la Comuna de Talca
# NOTA: Reemplaza 'COMUNA' por el nombre exacto que aparezca en el print de columnas
# (Ejemplo: 'Comuna', 'COMUNA', 'Comuna_Ocurrencia', etc.)
columna_comuna = 'COMUNA' 

# Convertimos a texto y limpiamos espacios o mayúsculas/minúsculas para evitar omisiones
df_talca = df_nacional[
    df_nacional[columna_comuna].astype(str).str.strip().str.upper() == 'TALCA'
].copy()

print(f"\nTotal registros filtrados para TALCA: {len(df_talca)}")

# 5. Guardar el dataset filtrado de Talca
ruta_salida = os.path.join(DATA_DIR, "talca_consolidado.csv")
df_talca.to_csv(ruta_salida, index=False)
print(f"\n¡Éxito! Dataset de Talca guardado en: {ruta_salida}")