# Plataforma de Analítica e Identificación de Zonas de Riesgo Vial — Comuna de Talca (2020-2025)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Visor_Web-FF4B4B?style=flat&logo=streamlit)
![Folium](https://img.shields.io/badge/Folium-Geospatial-green?style=flat)
![Status](https://img.shields.io/badge/Status-Validated-success)

## Plataforma en Vivo
Explora el dashboard interactivo directamente desde tu navegador:
 **[Plataforma de Analítica de Siniestralidad Vial - Comuna de Talca](https://siniestralidadvialtalca.streamlit.app)**

---

## Descripción del Proyecto

El sistema procesa **4.562 registros oficiales** de siniestros viales ocurridos en Talca entre los años 2020 y 2025. Utiliza algoritmos de agrupamiento no supervisado (*K-Means*) para determinar los 10 principales centroides de concentración de riesgo urbano (Hotspots), categorizados mediante un **Índice de Severidad Acumulada (ISA)** a nivel de evento.

### Métricas Clave del Dataset Consolidado:
- **Registros Analizados:** 4.562 siniestros comunales.
- **Víctimas Fatales:** 30 fallecidos.
- **Lesionados Graves:** 222 personas.
- **Puntaje de Severidad Acumulada:** 4.264 puntos (Enfoque de Riesgo Espacial/Vial).

---

## Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Procesamiento de Datos (ETL):** `Pandas`, `NumPy`
- **Machine Learning y Evaluación Espacial:** `Scikit-Learn` (*K-Means*, *DBSCAN*, *Silhouette Score*, Inercia/WCSS)
- **Visualización y Mapping:** `Streamlit`, `Folium`, `Streamlit-Folium`
- **Control de Calidad de Ingesta:** Microsoft Excel (Tablas Dinámicas)

---

## Metodología y Rigor Analítico

### 1. Modelamiento y Evaluación de Clustering (`src/03_evaluacion_clustering.py`)
Para evitar una selección arbitraria del número de agrupamientos ($K$), el proyecto incorpora un pipeline experimental de evaluación de clustering no supervisado sobre las coordenadas geográficas (`Latitud`, `longitud`):
- **Determinación del $K$ Óptimo:** Evaluación iterativa en el rango $K \in [2, 15]$ mediante el **Método del Codo (Inercia / WCSS)** y el **Coeficiente de Silueta (*Silhouette Score*)** para medir la cohesión y separación de los clústeres urbanos.
- **Benchmarking de Algoritmos:** Contraste experimental entre **K-Means** (particional basado en centroides, ideal para delimitar zonas de intervención de radio fijo) y **DBSCAN** (basado en densidad espacial con métrica Haversine), documentando sus métricas de calidad y comportamiento frente a ruido espacial.

### 2. Índice de Severidad Acumulada
Para priorizar las zonas críticas según el impacto en la infraestructura vial sin distorsiones por densidad de ocupantes por vehículo, el **ISA** se pondera según la consecuencia máxima o carga de gravedad del siniestro:
- **Fallecido:** 10 pts por víctima
- **Lesionado Grave:** 5 pts por víctima
- **Lesionado Menos Grave:** 3 pts por víctima
- **Siniestro Base / Solo Daños Materiales:** 1 pt por registro

### 3. Reconciliación de Datos y Control de Calidad ETL
Como paso previo al modelamiento, los datos procesados en Python fueron sometidos a una **reconciliación de integridad ETL** mediante tablas dinámicas en Microsoft Excel sobre las bases originales de CONASET, verificando exactitud en el filtrado comunal (4.562 registros), suma de víctimas y cálculo del puntaje ponderado (4.264 pts).

---

## Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/Winiberg/analisis-siniestralidad-vial-talca.git](https://github.com/Winiberg/analisis-siniestralidad-vial-talca.git)
   cd analisis-siniestralidad-vial-talca

2. **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt

3. **Ejecutar el análisis experimental de calidad de clustering (opcional)**
    ```bash
    python src/03_evaluacion_clustering.py

3. **Ejecutar la plataforma Streamlit:**
    ```bash
    streamlit run src/app.py

    