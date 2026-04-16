import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- CONFIG ---
st.set_page_config(page_title="PAIC IA", layout="wide")

# --- IA SETUP ---
model = None

try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ modelo correcto
    else:
        st.warning("⚠️ Falta configurar GOOGLE_API_KEY en Secrets")
except Exception as e:
    st.error(f"Error inicializando IA: {e}")

# --- DATOS ---
@st.cache_data
def cargar_datos():
    df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine="openpyxl")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df = df.sort_values("Fecha")
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"Error cargando Excel: {e}")
    st.stop()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["Inicio", "Histórico", "Calculadora", "IA"])

# --- INICIO ---
with t1:
    st.header("Resumen actual")
    ultima = df.iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Papa", f"₡{ultima['Papa Blanca (quintal)']:,.0f}")
    col2.metric("Cebolla", f"₡{ultima['Cebolla Amarilla (Kg)']:,.0f}")
    col3.metric("Fresa", f"₡{ultima['Fresa (Kg)']:,.0f}")

# --- HISTÓRICO ---
with t2:
    st.header("Precios históricos")
    fig = px.line(df, x="Fecha", y=[
        "Papa Blanca (quintal)",
        "Cebolla Amarilla (Kg)",
        "Fresa (Kg)"
    ])
    st.plotly_chart(fig, use_container_width=True)

# --- CALCULADORA ---
with t3:
    st.header("Calculadora de rentabilidad")

    ha = st.number_input("Hectáreas", value=1.0)
    precio = st.number_input("Precio ₡", value=30000)
    costos = st.number_input("Costos ₡", value=500000)

    produccion = ha * 600
    ingreso = produccion * precio
    utilidad = ingreso - costos

    st.metric("Ganancia Neta", f"₡{utilidad:,.0f}")

    if utilidad > 200000:
        st.success("🟢 RENTABLE")
    elif utilidad > 0:
        st.warning("🟡 AJUSTADO")
    else:
        st.error("🔴 PÉRDIDA")

# --- IA ---
with t4:
    st.header("Consultor IA agrícola")

    pregunta = st.text_area("Haga su pregunta:")

    if st.button("Analizar"):
        if not pregunta.strip():
            st.warning("Escriba una pregunta")
        elif model is None:
            st.error("IA no disponible")
        else:
            try:
                prompt = f"""
Eres un asesor agrícola en Cartago, Costa Rica.

Datos:
- Ganancia actual: ₡{utilidad:,.0f}

Da recomendaciones claras, prácticas y accionables.

Pregunta:
{pregunta}
"""

                with st.spinner("Analizando..."):
                    response = model.generate_content(prompt)

                    if response and hasattr(response, "text") and response.text:
                        st.success(response.text)
                    else:
                        st.warning("La IA no devolvió respuesta válida")

            except Exception as e:
                st.error(f"Error IA: {e}")
