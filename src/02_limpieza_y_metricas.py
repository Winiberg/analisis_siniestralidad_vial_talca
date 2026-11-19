import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def categorizar_severidad(row):
    if row["FALLECIDOS"] > 0:
        return "Fatal"
    elif row["GRAVES"] > 0:
        return "Grave"
    elif row["TOTAL_LESI"] > 0:
        return "Lesionados Leves / Menos Graves"
    else:
        return "Solo Daños Materiales"


def obtener_bloque_horario(hora_str):
    try:
        h = int(str(hora_str).split(":")[0])
        if 0 <= h < 6:
            return "Madrugada (00:00 - 05:59)"
        elif 6 <= h < 12:
            return "Mañana (06:00 - 11:59)"
        elif 12 <= h < 18:
            return "Tarde (12:00 - 17:59)"
        else:
            return "Noche (18:00 - 23:59)"
    except (ValueError, TypeError, IndexError):
        return "Sin Información"


def extraer_hora_numerica(hora_str):
    try:
        return int(str(hora_str).split(":")[0])
    except (ValueError, TypeError, IndexError):
        return pd.NA


def main():
    ruta_entrada = os.path.join(DATA_DIR, "talca_consolidado.csv")
    df = pd.read_csv(ruta_entrada, low_memory=False)
    total_inicial = len(df)
    print(f"Registros iniciales de Talca: {total_inicial:,}")

    # 1. Duplicados por ID
    duplicados_id = int(df["ID"].duplicated().sum()) if "ID" in df.columns else 0

    # 2. Validación geográfica (delimitador comunal de Talca: Lat [-35.60, -35.30], Lon [-71.85, -71.40])
    df["Latitud"] = pd.to_numeric(df["Latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")

    nulos_coord = int(df[["Latitud", "longitud"]].isna().any(axis=1).sum())
    en_rango_talca = (
        df["Latitud"].between(-35.60, -35.30)
        & df["longitud"].between(-71.85, -71.40)
    )
    fuera_rango = int((~en_rango_talca & df[["Latitud", "longitud"]].notna().all(axis=1)).sum())

    df["COORD_VALIDA"] = en_rango_talca

    # 3. Limpieza de variables de víctimas
    columnas_victimas = ["FALLECIDOS", "GRAVES", "MENOS_GRAV", "LEVES", "TOTAL_LESI"]
    for col in columnas_victimas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # 4. Índice de Severidad Acumulada (ISA) ponderado por víctima:
    # Fallecido = 10 pts | Grave = 5 pts | Menos Grave = 3 pts | Leve = 1 pt | Solo Daños = 0 pts
    df["PUNTAJE_SEVERIDAD"] = (
        (df["FALLECIDOS"] * 10)
        + (df["GRAVES"] * 5)
        + (df["MENOS_GRAV"] * 3)
        + (df["LEVES"] * 1)
    )

    df["CATEGORIA_SEVERIDAD"] = df.apply(categorizar_severidad, axis=1)

    # 5. Variables temporales estructuradas
    if "FECHA" in df.columns:
        fecha_dt = pd.to_datetime(df["FECHA"], errors="coerce")
        df["MES_NUM"] = fecha_dt.dt.month
        df["DIA_SEMANA_NUM"] = fecha_dt.dt.dayofweek

    df["HORA_NUM"] = df["Hora"].apply(extraer_hora_numerica)
    df["BLOQUE_HORARIO"] = df["Hora"].apply(obtener_bloque_horario)

    if "CAUSA_NUEV" in df.columns:
        df["CAUSA_NUEV"] = df["CAUSA_NUEV"].fillna("SIN INFORMACIÓN").astype(str).str.strip()

    # Subconjunto georreferenciado válido para análisis espacial
    df_geo = df[df["COORD_VALIDA"]].copy()

    # 6. Guardar perfilado de calidad de datos
    perfilado = pd.DataFrame([
        {"Metrica_Calidad": "Total registros comunales (CONASET)", "Valor": total_inicial},
        {"Metrica_Calidad": "Registros duplicados por ID", "Valor": duplicados_id},
        {"Metrica_Calidad": "Registros sin coordenadas (nulos)", "Valor": nulos_coord},
        {"Metrica_Calidad": "Registros fuera del bounding box de Talca", "Valor": fuera_rango},
        {"Metrica_Calidad": "Registros georreferenciados válidos", "Valor": len(df_geo)},
        {"Metrica_Calidad": "Total Fallecidos", "Valor": int(df_geo["FALLECIDOS"].sum())},
        {"Metrica_Calidad": "Total Lesionados Graves", "Valor": int(df_geo["GRAVES"].sum())},
        {"Metrica_Calidad": "Total Lesionados Menos Graves", "Valor": int(df_geo["MENOS_GRAV"].sum())},
        {"Metrica_Calidad": "Total Lesionados Leves", "Valor": int(df_geo["LEVES"].sum())},
        {"Metrica_Calidad": "Puntaje Total ISA (4.264 pts)", "Valor": int(df_geo["PUNTAJE_SEVERIDAD"].sum())},
    ])
    ruta_perfilado = os.path.join(DATA_DIR, "perfilado_calidad_datos.csv")
    perfilado.to_csv(ruta_perfilado, index=False)

    # Guardar dataset limpio final
    ruta_salida = os.path.join(DATA_DIR, "talca_limpio_final.csv")
    df_geo.to_csv(ruta_salida, index=False)

    print(f"Registros georreferenciados válidos conservados: {len(df_geo):,} (descartados: {total_inicial - len(df_geo)})")
    print(f"Puntaje Total ISA calculado: {int(df_geo['PUNTAJE_SEVERIDAD'].sum()):,} pts")
    print(f"Dataset limpio guardado en: {ruta_salida}")
    print(f"Perfilado de calidad guardado en: {ruta_perfilado}")


if __name__ == "__main__":
    main()