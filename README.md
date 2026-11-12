## Plataforma en Vivo
Explora el dashboard interactivo directamente desde tu navegador:
**[Plataforma de Analítica de Siniestralidad Vial - Comuna de Talca](https://siniestralidadvialtalca.streamlit.app)**
# Plataforma de Analítica e Identificación de Zonas de Riesgo Vial — Comuna de Talca (2020-2025)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Visor_Web-FF4B4B?style=flat&logo=streamlit)
![Folium](https://img.shields.io/badge/Folium-Geospatial-green?style=flat)
![Status](https://img.shields.io/badge/Status-Validated-success)

Proyecto desarrollado para el **Módulo Integrador II** de la **Universidad Católica del Maule (UCM)**. Consiste en la ingesta, limpieza, modelamiento geoespacial y desarrollo de una plataforma interactiva para el análisis de siniestralidad vial en la comuna de Talca, basado en datos consolidados de CONASET y Carabineros de Chile.

---

## Descripción del Proyecto

El sistema procesa **4.562 registros oficiales** de siniestros viales ocurridos en Talca entre los años 2020 y 2025. Utiliza algoritmos de agrupamiento no supervisado (*K-Means*) para determinar los 10 principales centroides de concentración de riesgo urbano (Hotspots), categorizados mediante un **Índice de Severidad Acumulada (ISA)** a nivel de evento.

### Key Metrics del Proyecto:
- **Registros Analizados:** 4.562 siniestros comunales.
- **Víctimas Fatales:** 30 fallecidos.
- **Lesionados Graves:** 222 personas.
- **Puntaje de Severidad Acumulada:** 4.264 puntos (Enfoque de Riesgo Espacial/Vial).

---

## Stack Tecnológico

- **Lenguaje:** Python
- **Procesamiento de Datos:** `Pandas`, `NumPy`
- **Machine Learning Espacial:** `Scikit-Learn` (K-Means Clustering)
- **Visualización y Mapping:** `Streamlit`, `Folium`, `Streamlit-Folium`
- **Auditoría & Cross-Validation:** Microsoft Excel (Tablas Dinámicas & Power Query)

---

## Metodología de Severidad (Enfoque B - Evento Base)

Para priorizar las zonas de riesgo según el impacto en la infraestructura vial, el **Índice de Severidad Acumulada (ISA)** se pondera según la consecuencia máxima alcanzada por el siniestro:
- **Fallecido:** 10 pts
- **Lesionado Grave:** 5 pts
- **Lesionado Menos Grave:** 3 pts
- **Solo Daños Materiales / Base:** 1 pt

> **Auditoría de Datos:** Todas las métricas fueron sometidas a un proceso riguroso de *Cross-Validation* contrastando el pipeline de Python contra auditorías en Excel, logrando una coincidencia del 100% en volumen de ingesta, conteo de víctimas y puntaje ponderado.

---

## Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/analisis-siniestralidad-vial-talca.git](https://github.com/TU_USUARIO/analisis-siniestralidad-vial-talca.git)
   cd analisis-siniestralidad-vial-talca

2. **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt

3. **Ejecutar la plataforma Streamlit:**
    ```bash
    streamlit run src/app.py

    