import os
import pandas as pd
import numpy as np

# 1. Cargar el dataset filtrado de Talca
DATA_DIR = "../data"
ruta_entrada = os.path.join(DATA_DIR, "talca_consolidado.csv")
df = pd.read_csv(ruta_entrada, low_memory=False)

print(f"Registros iniciales de Talca: {len(df)}")

# 2. Asegurar formato numérico en coordenadas
df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')

# Filtrar coordenadas válidas para Talca (~ -35.4 Latitud, ~ -71.6 Longitud)
df_geo = df.dropna(subset=['Latitud', 'longitud']).copy()
df_geo = df_geo[(df_geo['Latitud'] < -34.0) & (df_geo['Latitud'] > -36.0)]
df_geo = df_geo[(df_geo['longitud'] < -70.5) & (df_geo['longitud'] > -72.5)]

print(f"Registros con coordenadas válidas dentro del rango de Talca: {len(df_geo)}")

# 3. Limpieza de Variables Numéricas de Víctimas
columnas_victimas = ['FALLECIDOS', 'GRAVES', 'MENOS_GRAV', 'LEVES', 'TOTAL_LESI']
for col in columnas_victimas:
    if col in df_geo.columns:
        df_geo[col] = pd.to_numeric(df_geo[col], errors='coerce').fillna(0).astype(int)

# 4. Creación del Índice de Severidad
df_geo['PUNTAJE_SEVERIDAD'] = (
    (df_geo['FALLECIDOS'] * 10) + 
    (df_geo['GRAVES'] * 5) + 
    (df_geo['MENOS_GRAV'] * 3) + 
    (df_geo['LEVES'] * 1)
)

def categorizar_severidad(row):
    if row['FALLECIDOS'] > 0:
        return 'Fatal'
    elif row['GRAVES'] > 0:
        return 'Grave'
    elif row['TOTAL_LESI'] > 0:
        return 'Con Lesionados'
    else:
        return 'Solo Daños Materiales'

df_geo['CATEGORIA_SEVERIDAD'] = df_geo.apply(categorizar_severidad, axis=1)

# 5. Formatear Hora y Bloques Horarios
def obtener_bloque_horario(hora_str):
    try:
        h = int(str(hora_str).split(':')[0])
        if 0 <= h < 6:
            return 'Madrugada (00:00 - 05:59)'
        elif 6 <= h < 12:
            return 'Mañana (06:00 - 11:59)'
        elif 12 <= h < 18:
            return 'Tarde (12:00 - 17:59)'
        else:
            return 'Noche (18:00 - 23:59)'
    except:
        return 'Sin Información'

df_geo['BLOQUE_HORARIO'] = df_geo['Hora'].apply(obtener_bloque_horario)

# 6. Guardar el dataset limpio final
ruta_salida = os.path.join(DATA_DIR, "talca_limpio_final.csv")
df_geo.to_csv(ruta_salida, index=False)

print(f"\n¡Proceso completado exitosamente!")
print(f"Dataset final guardado en: {ruta_salida}")
print("\nResumen de Categorías de Severidad en Talca:")
print(df_geo['CATEGORIA_SEVERIDAD'].value_counts())
print("\nResumen por Bloque Horario:")
print(df_geo['BLOQUE_HORARIO'].value_counts())