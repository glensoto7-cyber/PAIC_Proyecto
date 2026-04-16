import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
from datetime import timedelta

# --- 1. CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# Variable global segura
model = None
utilidad = 0

# --- 2. CONFIGURACIÓN DE IA ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")  # modelo actual
    else:
        st.warning("⚠️ Configure GOOGLE_API_KEY en Secrets.")
except Exception as e:
    st.error(f"Error inicializando IA: {e}")

# --- ESTILOS ---
st.markdown("""
<style>
.rentable { color: #2E7D32; background-color: #E8F5E9; padding: 15px; border-radius: 10px; text-align: center; }
.ajustado { color: #FBC02D; background-color: #FFFDE7; padding: 15px; border-radius: 10px; text-align: center; }
.perdida { color: #D32F2F; background-color: #FFEBEE; padding: 15px; border-radius: 10px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 3. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')

        if df.empty:
            return "No hay datos en el archivo."

        ultima = df['Fecha'].max()
        fechas = pd.date_range(start=ultima + timedelta(days=1), end="2027-12-31", freq='MS')

        proy = []
        for i, f in enumerate(fechas):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)

            if prom.isnull().any():
                continue

            ajuste = 1 + (i * 0.002)

            proy.append({
                'Fecha': f,
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * ajuste,
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * ajuste,
                'Fresa (Kg)': prom['Fresa (Kg)'] * ajuste,
                'Origen': 'Proyección PAIC'
            })

        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)

    except Exception as e:
        return f"Error en datos: {e}"

df_total = motor_datos()

# --- 4. INTERFAZ ---
if isinstance(df_total, str):
    st.error(df_total)
else:

    tabs = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA", "🤖 IA"])
    prods = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']

    # --- INICIO ---
    with tabs[0]:
        st.header("🎯 Comparativa Mensual")

        df_real = df_total[df_total['Origen'] == 'Histórico Real']
        df_proy = df_total[df_total['Origen'] == 'Proyección PAIC']

        if not df_real.empty and not df_proy.empty:
            real = df_real.iloc[-1]
            prox = df_proy.iloc[0]

            cols = st.columns(3)
            for p, col in zip(prods, cols):
                var = ((prox[p] / real[p]) - 1) * 100
                col.metric(p, f"₡{real[p]:,.0f}", f"Próx: {prox[p]:,.0f} ({var:+.1f}%)")
        else:
            st.warning("No hay suficientes datos.")

    # --- HISTÓRICO ---
    with tabs[1]:
        st.header("📚 Histórico")
        fig = px.line(df_total[df_total['Origen']=="Histórico Real"], x="Fecha", y=prods)
        st.plotly_chart(fig, use_container_width=True)

    # --- PREDICCIÓN ---
    with tabs[2]:
        st.header("🔮 Predicción")
        prod_sel = st.selectbox("Producto:", prods)
        fig = px.line(df_total, x="Fecha", y=prod_sel, color="Origen")
        st.plotly_chart(fig, use_container_width=True)

    # --- CALCULADORA ---
    with tabs[3]:
        st.header("🧮 Rentabilidad")

        ha = st.number_input("Hectáreas", value=1.0)
        precio = st.number_input("Precio ₡", value=30000)
        costos = st.number_input("Costos ₡", value=500000)

        produccion = ha * 600
        ingreso = produccion * precio
        utilidad = ingreso - costos

        st.metric("Ganancia Neta", f"₡{utilidad:,.0f}")

        if utilidad > 200000:
            st.markdown("<div class='rentable'><h3>🟢 RENTABLE</h3></div>", unsafe_allow_html=True)
        elif utilidad > 0:
            st.markdown("<div class='ajustado'><h3>🟡 AJUSTADO</h3></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='perdida'><h3>🔴 PÉRDIDA</h3></div>", unsafe_allow_html=True)

    # --- IA ---
    with tabs[4]:
        st.header("🤖 Consultor IA")

        pregunta = st.text_area("Haga su consulta:")

        if st.button("Analizar"):

            if not pregunta.strip():
                st.warning("Escriba una pregunta.")
            
            elif model is None:
                st.error("IA no disponible. Revise API Key.")

            else:
                try:
                    prompt = f"""
                    Eres un asesor agrícola experto en Cartago, Costa Rica.

                    Datos:
                    - Utilidad actual: ₡{utilidad:,.0f}

                    Da recomendaciones claras, prácticas y realistas.

                    Pregunta:
                    {pregunta}
                    """

                    with st.spinner("Analizando..."):
                        response = model.generate_content(prompt)

                        if response and hasattr(response, "text"):
                            st.success(response.text)
                        else:
                            st.warning("No se obtuvo respuesta.")

                except Exception as e:
                    st.error(f"Error IA: {e}")
