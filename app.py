import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_style("whitegrid")

import streamlit as st

# ---------------------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Calidad del Aire en Colombia", layout="wide")

st.title("🌎 Calidad del Aire en Colombia")
st.markdown(
    "Dashboard interactivo basado en el Análisis Exploratorio de Datos (EDA) del "
    "dataset **Calidad del Aire en Colombia (Promedio Anual)** — IDEAM / datos.gov.co."
)

# ---------------------------------------------------------------------------
# Carga de datos (con caché para no releer el CSV en cada interacción)
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("kekd-7v7h.csv")
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "No se encontró el archivo 'kekd-7v7h.csv'. Verifica que esté en la "
        "misma carpeta que app.py (en el repositorio de GitHub)."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar - Filtros interactivos
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")

    variables_disponibles = sorted(df["variable"].unique().tolist())
    default_vars = [v for v in ["PM10", "PM2.5"] if v in variables_disponibles]
    if not default_vars:
        default_vars = variables_disponibles[:2]

    variables_seleccionadas = st.multiselect(
        "Contaminante(s) / variable(s):",
        options=variables_disponibles,
        default=default_vars,
    )

    anio_min = int(df["a_o"].min())
    anio_max = int(df["a_o"].max())
    rango_anios = st.slider(
        "Rango de años:",
        min_value=anio_min,
        max_value=anio_max,
        value=(anio_min, anio_max),
    )

    st.markdown("---")
    st.caption(
        "Los gráficos y métricas se actualizan automáticamente según los "
        "filtros seleccionados arriba."
    )

# Si el usuario deja el filtro vacío, usamos todas las variables para que la app no se rompa
if not variables_seleccionadas:
    st.sidebar.warning(
        "No seleccionaste ningún contaminante: mostrando todos por defecto."
    )
    variables_seleccionadas = variables_disponibles

df_filtrado = df[
    (df["variable"].isin(variables_seleccionadas))
    & (df["a_o"] >= rango_anios[0])
    & (df["a_o"] <= rango_anios[1])
]

tab_exploracion, tab_visualizaciones, tab_validacion, tab_hallazgos = st.tabs(
    ["📋 Exploración de datos", "📊 Visualizaciones", "🔬 Validación estadística", "💡 Hallazgos"]
)

# ---------------------------------------------------------------------------
# Sección: Exploración de datos
# ---------------------------------------------------------------------------
with tab_exploracion:
    col1, col2, col3 = st.columns(3)
    col1.metric("Registros filtrados", f"{len(df_filtrado):,}")
    col2.metric(
        "Promedio de concentración",
        f"{df_filtrado['promedio'].mean():.2f}" if len(df_filtrado) else "N/D",
    )
    col3.metric(
        "Desviación estándar",
        f"{df_filtrado['promedio'].std():.2f}" if len(df_filtrado) else "N/D",
    )

    with st.expander("Ver tabla de datos filtrados"):
        st.dataframe(
            df_filtrado[
                [
                    "estaci_n",
                    "nombre_del_departamento",
                    "nombre_del_municipio",
                    "variable",
                    "a_o",
                    "promedio",
                    "tipo_de_estaci_n",
                ]
            ],
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# Sección: Visualizaciones
# ---------------------------------------------------------------------------
with tab_visualizaciones:
    graf_col1, graf_col2 = st.columns(2)

    with graf_col1:
        st.subheader("Tendencia anual del promedio")
        if len(df_filtrado):
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            sns.lineplot(
                data=df_filtrado, x="a_o", y="promedio", hue="variable", marker="o", ax=ax1
            )
            ax1.set_xlabel("Año")
            ax1.set_ylabel("Promedio (µg/m³ u otra unidad según variable)")
            ax1.set_title("Evolución anual por contaminante")
            st.pyplot(fig1)
            plt.close(fig1)
        else:
            st.info("No hay datos para los filtros seleccionados.")

    with graf_col2:
        st.subheader("Distribución por tipo de estación")
        if len(df_filtrado):
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            sns.boxplot(data=df_filtrado, x="tipo_de_estaci_n", y="promedio", ax=ax2)
            ax2.set_xlabel("Tipo de estación")
            ax2.set_ylabel("Promedio")
            ax2.set_title("Promedio por tipo de estación")
            st.pyplot(fig2)
            plt.close(fig2)
        else:
            st.info("No hay datos para los filtros seleccionados.")

    st.subheader("Comparación anual entre contaminantes seleccionados")
    if len(df_filtrado):
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        sns.barplot(data=df_filtrado, x="a_o", y="promedio", hue="variable", ax=ax3)
        ax3.set_xlabel("Año")
        ax3.set_ylabel("Promedio")
        ax3.set_title("Promedio anual por contaminante")
        plt.setp(ax3.get_xticklabels(), rotation=45, ha="right")
        st.pyplot(fig3)
        plt.close(fig3)
    else:
        st.info("No hay datos para los filtros seleccionados.")

    st.subheader("Proporción de estaciones por tipo (dataset completo, no se filtra)")
    fig4, ax4 = plt.subplots(figsize=(5, 5))
    df["tipo_de_estaci_n"].value_counts().plot.pie(autopct="%1.1f%%", ax=ax4)
    ax4.set_ylabel("")
    ax4.set_title("Fija vs. Indicativa")
    st.pyplot(fig4)
    plt.close(fig4)

# ---------------------------------------------------------------------------
# Sección: Validación estadística
# ---------------------------------------------------------------------------
with tab_validacion:
    st.markdown(
        """
**Pregunta analizada:** ¿El promedio de PM2.5 es diferente entre las estaciones
de monitoreo permanentes (Fija) y las temporales (Indicativa)?

Se comparó el promedio de PM2.5 entre ambos tipos de estación con una prueba
t de Welch (adecuada cuando los dos grupos tienen tamaños y variabilidad
distintos). El resultado obtenido en el análisis fue:
"""
    )

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("Diferencia detectada", "Sí, significativa")
    stat_col2.metric("Probabilidad de que sea azar", "Prácticamente 0%")
    stat_col3.metric("Magnitud del efecto", "Moderada")

    st.success(
        "**En palabras simples:** las estaciones fijas registran, en promedio, "
        "niveles de PM2.5 más altos que las estaciones indicativas (17.1 µg/m³ "
        "frente a 14.5 µg/m³). La diferencia es estadísticamente consistente "
        "(no parece producto del azar), aunque su tamaño es moderado: el tipo "
        "de estación influye en el nivel registrado, pero no es el único factor "
        "que explica la contaminación del aire."
    )

# ---------------------------------------------------------------------------
# Sección: Hallazgos / Acerca del análisis
# ---------------------------------------------------------------------------
with tab_hallazgos:
    st.markdown(
        """
**¿Qué analicé?**
Se estudiaron los registros anuales de calidad del aire recopilados por el
IDEAM en estaciones de monitoreo de todo el país entre los años disponibles
en el dataset, con énfasis en dos de los contaminantes más monitoreados:
PM10 y PM2.5 (partículas finas en suspensión).

**¿Qué encontré?**
La contaminación por partículas (PM10 y PM2.5) muestra una tendencia a la
baja sostenida en los últimos años, especialmente marcada desde 2017. Además,
las estaciones permanentes ("Fijas") registran en promedio niveles de PM2.5
más altos que las estaciones temporales ("Indicativas"), una diferencia que
el análisis estadístico confirma que no se debe simplemente al azar.

**¿Qué significa?**
La mejora sostenida en los niveles de PM10 y PM2.5 sugiere que las medidas de
control ambiental aplicadas en el país en la última década han tenido un
impacto positivo real. Por otro lado, que las estaciones fijas —ubicadas de
forma permanente, típicamente en zonas urbanas de mayor exposición como vías
o zonas industriales— reporten niveles más altos, indica que la ubicación
del monitoreo importa: una red de estaciones concentrada solo en zonas fijas
podría estar sobreestimando (o, si se concentrara solo en zonas indicativas,
subestimando) la exposición real de la población.

**¿Qué se recomendaría?**
Se recomienda mantener y, de ser posible, ampliar la red de estaciones de
monitoreo —combinando estaciones fijas e indicativas— para obtener una
imagen más representativa de la calidad del aire en distintos contextos
geográficos. También se recomienda dar seguimiento prioritario a las zonas
con estaciones fijas de alta exposición, ya que es allí donde se concentran
los niveles más altos de contaminación por partículas finas.
"""
    )

    st.markdown("---")
    st.subheader("Relación entre el nivel general de contaminación y los episodios más extremos")
    st.markdown(
        """
En los datos analizados, las estaciones y años con un nivel promedio de
contaminación más alto también tendieron a presentar los episodios de
contaminación más severos (una relación fuerte, de 0.80 en una escala de 0 a
1). Esto no prueba que uno cause el otro: ambos valores podrían estar
respondiendo a un mismo factor de fondo, como la actividad industrial o el
tráfico vehicular de la zona. Lo que sí sugiere este patrón es que vigilar de
cerca el promedio de contaminación de una estación puede servir como una
señal de alerta temprana de posibles picos graves en esa misma zona. Se
recomienda usar esta relación como una guía de monitoreo prioritario, no como
una garantía: antes de invertir recursos asumiendo que bajar el promedio
reducirá automáticamente los picos extremos, conviene confirmar esta
hipótesis con un análisis adicional enfocado en las estaciones de mayor
riesgo.
"""
    )

st.caption(
    "Dashboard construido con Streamlit a partir del EDA desarrollado en la "
    "Tarea 3 del curso Programación para el análisis de datos (203008069) - UNAD."
)
