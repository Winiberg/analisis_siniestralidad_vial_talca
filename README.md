# Plataforma de Analítica y Concentración de Severidad Vial — Comuna de Talca (2020, 2021, 2022 y 2025)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Visor_Web-FF4B4B?style=flat&logo=streamlit)
![Folium](https://img.shields.io/badge/Folium-Geospatial-green?style=flat)

## Plataforma en Vivo
Explora el dashboard interactivo directamente desde tu navegador:  
**[Plataforma de Analítica de Siniestralidad Vial — Comuna de Talca](https://siniestralidadvialtalca.streamlit.app)**

---

## 1. Descripción y Alcance del Proyecto

El sistema procesa **4.562 registros oficiales** de siniestros viales atendidos por Carabineros de Chile y consolidados por el Observatorio de Datos de **CONASET** para la comuna de Talca correspondientes a los años **2020, 2021, 2022 y 2025** (4 periodos anuales disponibles; sin registros publicados para 2023–2024 en la fuente).

Mediante proyección cartográfica a **UTM Zona 19 Sur (EPSG:32719)** y agrupamiento espacial no supervisado (*K-Means* con $K=7$), la plataforma delimita las **7 macrozonas urbanas definidas en el Plan de Desarrollo Comunal (PLADECO) de Talca 2024–2028**, jerarquizándolas según su **Índice de Severidad Acumulada (ISA)**.

### Métricas Clave del Dataset Consolidado
* **Registros Analizados:** 4.562 siniestros comunales (100% con coordenadas válidas).
* **Víctimas Fatales:** 30 fallecidos.
* **Lesionados Graves:** 222 personas.
* **Lesionados Menos Graves:** 200 personas.
* **Lesionados Leves:** 2.254 personas (Total lesionados: 2.676).
* **Siniestros Solo Daños Materiales:** 2.739 eventos.
* **Severidad Acumulada Total (ISA):** 4.264 puntos.

> **Alcance analítico:** Al no disponerse de conteos oficiales de flujo vehicular (exposición), las métricas reflejan **concentración y severidad registrada** en los puntos de ocurrencia, y no probabilidad individual de accidente. Asimismo, los registros administrativos pueden presentar subregistro en colisiones menores sin intervención policial.

---

## 2. Arquitectura del Pipeline y Orden de Ejecución

```text
proyecto_siniestralidad_talca/
├── data/                                    # Artefactos procesados y tablas de evaluación
├── src/
│   ├── 01_filtrar_talca.py                  # Ingesta multianual nacional (217.333) y filtrado comunal (4.562)
│   ├── 02_limpieza_y_metricas.py            # Validación geográfica, cálculo de ISA, variables temporales y perfilado
│   ├── 03_evaluacion_clustering.py          # Evaluación multi-criterio K∈[2,15] y benchmarking K-Means vs DBSCAN (UTM 19S)
│   ├── 03_clustering_hotspots.py            # Asignación definitiva K=7 en UTM 19S y mapeo a Zonas Urbanas PLADECO
│   ├── 04_visualizar_clusters.py            # Generación de envolventes convexas comparativas (K=4, 5, 7 y 8)
│   ├── 05_validacion_y_sensibilidad.py      # Validación temporal (2020-2022 -> 2025), sensibilidad Spearman y Top intersecciones
│   └── app.py                               # Visor web interactivo en Streamlit + Folium
├── requirements.txt
└── README.md
```

---

## 3. Metodología y Evidencia Empírica

### 3.1. Definición Formal del Índice de Severidad Acumulada (ISA)
Para priorizar las zonas según el daño humano registrado, el **ISA** pondera el número de víctimas de cada siniestro $i$ mediante la expresión:

$$\text{ISA}_i = 10 \cdot \text{Fallecidos}_i + 5 \cdot \text{Graves}_i + 3 \cdot \text{MenosGraves}_i + 1 \cdot \text{Leves}_i$$

* **Ejemplo de cálculo:** Un siniestro con 1 fallecido, 2 lesionados graves y 0 leves obtiene $10(1) + 5(2) + 3(0) + 1(0) = 20\text{ puntos}$. Un siniestro sin víctimas (solo daños materiales) obtiene $0\text{ puntos}$.
* **Reconciliación aritmética:** $(30 \times 10) + (222 \times 5) + (200 \times 3) + (2.254 \times 1) = 300 + 1.110 + 600 + 2.254 = \mathbf{4.264\text{ puntos}}$.
* **Sensibilidad de ponderadores:** Al evaluar esquemas alternativos (`20/10/3/1` y `12/6/3/1`), el ordenamiento de las 7 zonas presenta una correlación de rango de Spearman de **$\rho = 1,0000$ ($p < 0,0001$)**, y frente a frecuencia pura (`1/1/1/1`) alcanza **$\rho = 0,8929$ ($p = 0,0068$)**.

### 3.2. Espacio Métrico y Selección de $K = 7$ (`src/03_evaluacion_clustering.py`)
Para evitar la distorsión geométrica del ~18% que produce la distancia euclidiana sobre grados decimales a la latitud de Talca ($-35,42^\circ$), todas las coordenadas fueron proyectadas a **UTM Zona 19 Sur (EPSG:32719)** en metros.

| K | Inercia ($\text{km}^2$) | Silhouette | Davies-Bouldin | Calinski-Harabasz | Estabilidad ARI | Radio Mediano (m) | Score Kneedle |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 4 | 5.335,44 | **0,4413** | **0,7589** | **3.979,7** | **1,0000** | 866,5 | 0,3369 |
| 5 | 4.420,48 | 0,3810 | 0,8394 | 3.839,6 | 0,9455 | 761,9 | **0,3455** |
| **7 (Elegido)** | **3.249,90** | **0,3970** | **0,8540** | **3.751,9** | **0,9913** | **653,6** | **0,3172** |
| 8 | 2.853,23 | 0,3961 | 0,8242 | 3.752,6 | 0,9452 | 641,1 | 0,2901 |
| 10 | 2.257,12 | 0,3871 | 0,7963 | 3.821,5 | 0,9461 | 548,7 | 0,2223 |

**Criterio de decisión:** Si bien los máximos puramente geométricos ocurren en $K=4$ ($\text{Silhouette} = 0,4413$) y el punto de inflexión Kneedle en $K=5$, se adoptó **$K=7$** bajo un enfoque multi-criterio:
1. **Validez de dominio:** Coincide exactamente con las **7 zonas urbanas** definidas en el PLADECO Talca 2024–2028 (Ilustración 10 y Tabla 8, pp. 46–47).
2. **Estabilidad estructural:** Presenta una reproducibilidad casi determinista (**$\text{ARI} = 0,9913$**), superando a $K=5$ ($0,9455$) y $K=8$ ($0,9452$).
3. **Escala operativa:** Reduce el radio mediano de dispersión a **$653,6\text{ m}$** (frente a $866,5\text{ m}$ en $K=4$).

### 3.3. Benchmarking de Algoritmos en Espacio Métrico UTM 19S

| Algoritmo | Clústeres | Siniestros Ruido | Silhouette Score | Davies-Bouldin | Estabilidad ARI |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **K-Means ($K=7$, UTM 19S)** | 7 | 0 (0,0%) | **0,3970** | 0,8540 | **0,9913** |
| **DBSCAN ($\varepsilon=350\text{ m}$, $\text{min}=30$)** | 4 | 287 (6,3%) | -0,0149 | 0,8213 | Determinista |

### 3.4. Validación Temporal Predictiva (2020–2022 $\rightarrow$ 2025)
Al entrenar los 7 centroides exclusivamente con los registros históricos `2020–2022` y evaluar su capacidad de captura espacial sobre los `1.294` siniestros ocurridos en `2025`:
* **Radio de $650\text{ m}$ (escala mediana del modelo):** Captura el **47,4%** de los siniestros de 2025 y el **47,8%** del puntaje ISA.
* **Radio de $800\text{ m}$:** Captura el **64,6%** de los siniestros y el **64,9%** del puntaje ISA.
* **Radio de $1.000\text{ m}$:** Captura el **79,9%** de los siniestros (`1.034` eventos) y el **78,7%** del puntaje ISA.

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
| `CLUSTER_ID`, `NOMBRE_ZONA`, `RANKING_SEVERIDAD` | `int/str` | Clúster asignado ($0..6$), macrozona PLADECO correspondiente y posición según ISA total. |

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

3. **Ejecutar los módulos analíticos (opcional; los CSV procesados ya están incluidos en `data/`):**
   ```bash
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
* **Consistencia entre espacio de distancia y zonificación:** Se migró el clustering de coordenadas geográficas (grados) a UTM 19S (metros) y se vinculó $K=7$ con la macro-zonificación oficial del PLADECO Talca 2024–2028.