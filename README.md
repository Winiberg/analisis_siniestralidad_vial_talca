# Plataforma de Analítica y Concentración de Severidad Vial — Comuna de Talca (2020, 2021, 2022 y 2025)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Visor_Web-FF4B4B?style=flat&logo=streamlit)
![Folium](https://img.shields.io/badge/Folium-Geospatial-green?style=flat)

## Plataforma en Vivo
Explora el dashboard interactivo directamente desde tu navegador:  
**[Plataforma de Analítica de Siniestralidad Vial — Comuna de Talca](https://siniestralidadvialtalca.streamlit.app)**

---

## 1. Descripción y Alcance del Proyecto

El sistema procesa **4.562 registros oficiales** de siniestros viales atendidos por Carabineros de Chile y consolidados por el Observatorio de Datos de **CONASET** (descargados en noviembre de 2026) para la comuna de Talca correspondientes a los años **2020, 2021, 2022 y 2025** (4 periodos anuales disponibles; sin registros publicados para 2023–2024 en la fuente).

Mediante proyección cartográfica a **UTM Zona 19 Sur (EPSG:32719)** y agrupamiento espacial no supervisado (*K-Means* con $K=7$), la plataforma agrupa los eventos en **7 zonas de concentración espacial aproximadamente asimilables a las 7 macrozonas urbanas definidas en el Plan de Desarrollo Comunal (PLADECO) de Talca 2024–2028**, jerarquizándolas según su **Índice de Severidad Acumulada (ISA)** y desagregando las intersecciones viales más críticas.

### Métricas Clave del Dataset Consolidado
* **Registros Analizados:** 4.562 siniestros comunales (4.532 en zona urbana y 30 en sector rural).
* **Víctimas Fatales:** 30 fallecidos.
* **Lesionados Graves:** 222 personas.
* **Lesionados Menos Graves:** 200 personas.
* **Lesionados Leves:** 2.254 personas (Total lesionados: 2.676).
* **Siniestros Solo Daños Materiales:** 2.739 eventos.
* **Severidad Acumulada Total (ISA):** 4.264 puntos.

> **Alcance analítico:** Al no disponerse de conteos oficiales de flujo vehicular (exposición), las métricas reflejan **concentración y severidad registrada** en los puntos de ocurrencia (geocodificados a nivel de intersección/tramo, con 1.577 coordenadas únicas), y no probabilidad individual de accidente. Asimismo, los registros administrativos pueden presentar subregistro en colisiones menores sin intervención policial.

---

## 2. Arquitectura del Pipeline y Orden de Ejecución

```text
proyecto_siniestralidad_talca/
├── data/                                    # Artefactos procesados y tablas de evaluación
├── src/
│   ├── 01_filtrar_talca.py                  # Ingesta multianual nacional (217.333) y filtrado comunal (4.562)
│   ├── 02_limpieza_y_metricas.py            # Validación geográfica, cálculo de ISA, variables temporales y perfilado
│   ├── 03_evaluacion_clustering.py          # Evaluación multi-criterio K∈[2,15] y contraste con DBSCAN (UTM 19S)
│   ├── 03_clustering_hotspots.py            # Partición K=7 en UTM 19S y etiquetado territorial PLADECO
│   ├── 04_visualizar_clusters.py            # Visualización comparativa de envolventes convexas (K=4, 5, 7 y 8)
│   ├── 05_validacion_y_sensibilidad.py      # Estabilidad intertemporal (2020-2022 -> 2025) y sensibilidad Spearman
│   └── app.py                               # Visor web interactivo en Streamlit + Folium
├── requirements.txt
└── README.md
```

---

## 3. Metodología y Evidencia Empírica

### 3.1. Definición Formal del Índice de Severidad Acumulada (ISA)
Para jerarquizar las zonas según el daño humano registrado, el **ISA** pondera el número de víctimas de cada siniestro $i$ mediante la expresión:

$$\text{ISA}_i = 10 \cdot \text{Fallecidos}_i + 5 \cdot \text{Graves}_i + 3 \cdot \text{MenosGraves}_i + 1 \cdot \text{Leves}_i$$

* **Ejemplo de cálculo:** Un siniestro con 1 fallecido, 2 lesionados graves y 0 leves obtiene $10(1) + 5(2) + 3(0) + 1(0) = 20\text{ puntos}$. Un siniestro sin víctimas (solo daños materiales) obtiene $0\text{ puntos}$.
* **Reconciliación y composición:** $(30 \times 10) + (222 \times 5) + (200 \times 3) + (2.254 \times 1) = 300 + 1.110 + 600 + 2.254 = \mathbf{4.264\text{ puntos}}$. Los lesionados leves aportan el 52,9% del puntaje total, los graves el 26,0%, los menos graves el 14,1% y los fallecidos el 7,0%, por lo que el indicador refleja principalmente volumen de lesionados ponderado por gravedad.
* **Sensibilidad de ponderadores:** Al evaluar esquemas alternativos de mayor severidad (`20/10/3/1` y `12/6/3/1`), el ordenamiento de las 7 zonas no varía ($\rho = 1,0000$), y frente a frecuencia pura (`1/1/1/1`) mantiene una correlación de rango de Spearman de $\rho = 0,8929$.

### 3.2. Espacio Métrico y Selección de $K = 7$ (`src/03_evaluacion_clustering.py`)
Para evitar la distorsión geométrica del ~18% que produce la distancia euclidiana sobre grados decimales a la latitud de Talca ($-35,42^\circ$), todas las coordenadas fueron proyectadas a **UTM Zona 19 Sur (EPSG:32719)** en metros. Se evaluó *K-Means* (`random_state=42`, `n_init=20`) en el rango completo $K \in [2, 15]$:

| K | Inercia ($\text{km}^2$) | Silhouette | Davies-Bouldin | Calinski-Harabasz | ARI (Semillas) | Radio Mediano (m) | Score Kneedle |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2 | 11.817,76 | 0,3829 | 0,9703 | 2.891,4 | 0,9997 | 1.099,6 | 0,0000 |
| 3 | 7.481,40 | 0,4108 | 0,8544 | 3.604,4 | 0,9979 | 1.022,6 | 0,2438 |
| 4 | 5.335,44 | **0,4413** | **0,7589** | **3.979,7** | **1,0000** | 866,5 | 0,3369 |
| 5 | 4.420,48 | 0,3810 | 0,8394 | 3.839,6 | 0,9455 | 761,9 | **0,3455** |
| 6 | 3.712,37 | 0,3859 | 0,8667 | 3.828,7 | 0,9949 | 690,2 | 0,3398 |
| 7 | 3.249,90 | 0,3970 | 0,8540 | 3.751,9 | 0,9913 | 653,6 | 0,3172 |
| 8 | 2.853,23 | 0,3961 | 0,8242 | 3.752,6 | 0,9452 | 641,1 | 0,2901 |
| 9 | 2.499,03 | 0,4083 | 0,7773 | 3.828,7 | 0,9980 | 588,0 | 0,2600 |
| 10 | 2.257,12 | 0,3871 | 0,7963 | 3.821,5 | 0,9461 | 548,7 | 0,2223 |
| 11 | 2.060,53 | 0,3802 | 0,8276 | 3.810,0 | 0,9359 | 521,2 | 0,1814 |
| 12 | 1.884,19 | 0,3918 | 0,8002 | 3.825,7 | 0,8968 | 490,2 | 0,1391 |
| 13 | 1.740,57 | 0,3927 | 0,7891 | 3.826,8 | 0,9394 | 475,3 | 0,0946 |
| 14 | 1.626,74 | 0,3863 | 0,7999 | 3.804,1 | 0,8757 | 447,5 | 0,0480 |
| 15 | 1.534,28 | 0,3932 | 0,7968 | 3.763,3 | 0,8457 | 433,0 | 0,0000 |

**Criterio de selección ($K = 7$):** Ninguna métrica interna distingue a $K=7$ como óptimo matemático aislado ($K=4$ maximiza Silhouette con $0,4413$ y $K=9$ mejora las métricas internas en particiones más finas). Se eligió **$K=7$** por **correspondencia con la zonificación comunal del PLADECO Talca 2024–2028 (Ilustración 10 y Tabla 8, pp. 46–47)** y porque presenta estabilidad aceptable tanto ante reinicios de semilla ($\text{ARI} = 0,9913$) como ante submuestreo del 80% de los datos ($\text{ARI} = 0,966 \pm 0,041$, superior a $K=5$ [$0,699$] y $K=10$ [$0,857$]), ajustando además la escala espacial a un radio mediano operativo de **$653,6\text{ m}$**. Se aclara que la partición responde a celdas de proximidad a centroides (Voronoi) aproximadamente asimilables a las macrozonas oficiales, y no a límites administrativos vectoriales exactos.

### 3.3. Rol Complementario de K-Means vs. DBSCAN
Se contrastó **K-Means ($K=7$)** frente a **DBSCAN** ($\varepsilon = 350\text{ m}$, $\text{min\_samples} = 30$) en UTM 19S. Mientras DBSCAN excluye el 6,3% de los eventos periféricos como ruido (287 siniestros) y concentra el casco urbano en un solo bloque (4 clústeres, Silhouette $-0,0149$), K-Means garantiza una partición exhaustiva del 100% de la comuna en 7 zonas de gestión. Ambos enfoques cumplen roles distintos: DBSCAN es útil a escalas menores ($\varepsilon = 100-150\text{ m}$) para aislar micro-focos puntuales, mientras K-Means estructura la zonificación territorial completa.

### 3.4. Estabilidad Espacial Intertemporal (2020–2022 $\rightarrow$ 2025)
Al entrenar los 7 centroides exclusivamente con los registros `2020–2022` ($n = 3.268$) y medir la captura espacial sobre `2025` ($n = 1.294$):
* **Radio de $650\text{ m}$:** Captura el **47,4%** de los siniestros y el **47,8%** del puntaje ISA de 2025 (frente a una línea base aleatoria de $36,5\%$ promedio y $46,4\%$ en el percentil 95, alcanzando el nivel de centroides entrenados directamente en 2025: $46,3\%$).
* **Radio de $1.000\text{ m}$:** Captura el **79,9%** de los siniestros (`1.034` eventos) y el **78,7%** del puntaje ISA (frente a $57,9\%$ promedio y $68,5\%$ P95 al azar).

### 3.5. Control de Calidad de Datos y Reconciliación ETL
Se ejecutó una reconciliación independiente mediante Tablas Dinámicas en Microsoft Excel sobre las bases de CONASET (`data/perfilado_calidad_datos.csv`), comprobando 0 registros duplicados por `ID`, 0 coordenadas nulas o fuera de rango comunal y coincidencia exacta en los conteos anuales (`2020`: 907; `2021`: 1.017; `2022`: 1.344; `2025`: 1.294) y víctimas totales.

---

## 4. Diccionario de Datos Principales (`data/talca_con_clusters.csv`)

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| `AÑO` | `int` | Año de ocurrencia del siniestro (`2020, 2021, 2022, 2025`). |
| `Latitud`, `longitud` | `float` | Coordenadas geográficas en sistema WGS84. |
| `UTM_X`, `UTM_Y` | `float` | Coordenadas proyectadas en metros (UTM Zona 19S, EPSG:32719). |
| `FALLECIDOS`, `GRAVES`, `MENOS_GRAV`, `LEVES` | `int` | Cantidad de víctimas según clasificación policial de gravedad. |
| `PUNTAJE_SEVERIDAD` | `int` | Puntaje individual del Índice de Severidad Acumulada (ISA). |
| `CATEGORIA_SEVERIDAD` | `str` | Clasificación ordinal (`Fatal`, `Grave`, `Lesionados Leves / Menos Graves`, `Solo Daños Materiales`). |
| `BLOQUE_HORARIO` | `str` | Tramo horario de ocurrencia (`Madrugada`, `Mañana`, `Tarde`, `Noche`). |
| `CAUSA_NUEV` | `str` | Causa basal registrada en el parte policial. |
| `CLUSTER_ID`, `NOMBRE_ZONA`, `RANKING_SEVERIDAD` | `int/str` | Clúster asignado ($0..6$), zona urbana PLADECO asimilada y posición según ISA total. |

---

## 5. Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/Winiberg/analisis_siniestralidad_vial_talca.git](https://github.com/Winiberg/analisis_siniestralidad_vial_talca.git)
   cd analisis_siniestralidad_vial_talca
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el pipeline completo (requiere los 4 CSV anuales de CONASET en `data/`; los CSV procesados ya están incluidos en `data/`):**
   ```bash
   python src/01_filtrar_talca.py
   python src/02_limpieza_y_metricas.py
   python src/03_evaluacion_clustering.py
   python src/03_clustering_hotspots.py
   python src/04_visualizar_clusters.py
   python src/05_validacion_y_sensibilidad.py
   ```

4. **Ejecutar la plataforma web Streamlit:**
   ```bash
   streamlit run src/app.py
   ```

---

## 6. Problemas Conocidos y Resueltos (Bitácora de Despliegue)

* **Resolución de rutas en Streamlit Cloud:** Se implementó resolución dinámica de rutas mediante `os.path.abspath(__file__)`, eliminando errores de archivo no encontrado al ejecutar desde la raíz del contenedor nube.
* **Control de recargas en Folium:** Se acotó `returned_objects=[]` en `st_folium` para evitar re-renderizados innecesarios en cada interacción de zoom/paneo. Mediante auditoría en DevTools se confirmó ausencia de errores de aplicación (`4xx/5xx` propios).
* **Consistencia entre espacio de distancia y zonificación:** Se migró el clustering de coordenadas geográficas (grados) a UTM 19S (metros) y se vinculó $K=7$ con la macro-zonificación urbana del PLADECO Talca 2024–2028.