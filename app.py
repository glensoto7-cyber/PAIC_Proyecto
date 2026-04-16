import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 🔒 SEGURIDAD: Configuración de Groq desde Secrets
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        st.warning("⚠️ Configuración de seguridad pendiente: Inserte su GROQ_API_KEY en los Secretos de Streamlit Cloud.")
except Exception as e:
    st.error(f"Error de configuración: {e}")

# --- Estilos de Semáforo ---
st.markdown("""
    <style>
    .rentable { color: #2E7D32; background-color: #E8F5E9; padding: 15px; border-radius: 10px; border: 2px solid #2E7D32; text-align: center; }
    .ajustado { color: #FBC02D; background-color: #FFFDE7; padding: 15px; border-radius: 10px; border: 2px solid #FBC02D; text-align: center; }
    .perdida { color: #D32F2F; background-color: #FFEBEE; padding: 15px; border-radius: 10px; border: 2px solid #D32F2F; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        if df.empty: return "Archivo vacío"

        ultima_f = df['Fecha'].max()
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        
        proy = []
        for i, fecha in enumerate(fechas_proy):
            mes = fecha.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': fecha,
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * (1 + i * 0.002),
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * (1 + i * 0.002),
                'Fresa (Kg)': prom['Fresa (Kg)'] * (1 + i * 0.002),
                'Origen': 'Proyección PAIC'
            })
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return f"Error: {e}"

df_total = motor_datos()

# --- 3. INTERFAZ ---
if isinstance(df_total, str):
    st.error(f"Error en datos: {df_total}")
else:
    t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA PRO", "🤖 IA"])

    with t_inicio:
        st.header("🎯 Comparativa Mensual")
        datos_reales = df_total[df_total['Origen'] == 'Histórico Real']
        if not datos_reales.empty:
            real = datos_reales.iloc[-1]
            prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            prods = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']
            for p, col in zip(prods, [c1, c2, c3]):
                var = ((prox[p] / real[p]) - 1) * 100
                col.metric(p, f"₡{real[p]:,.0f}", f"Próx: {prox[p]:,.0f} ({var:+.1f}%)")

    with t_calc:
        st.header("🧮 Simulador de Rentabilidad")
        with st.expander("Configuración de Cosecha", expanded=True):
            ha = st.number_input("Hectáreas:", value=1.0)
            precio = st.number_input("Precio Venta ₡:", value=int(real['Papa Blanca (quintal)']))
            costos = st.number_input("Costos Totales ₡:", value=500000)
        
        utilidad = (ha * 600 * precio) - costos
        st.metric("GANANCIA NETA", f"₡{utilidad:,.2f}")

        if utilidad > 200000:
            st.markdown("<div class='rentable'><h3>🟢 RENTABLE</h3></div>", unsafe_allow_html=True)
        elif utilidad > 0:
            st.markdown("<div class='ajustado'><h3>🟡 AJUSTADO</h3></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='perdida'><h3>🔴 PÉRDIDA</h3></div>", unsafe_allow_html=True)

    with t_ia:
        st.header("🤖 Consultor PAIC Pro (IA)")
        pregunta = st.text_area("Escriba su consulta para el experto agrónomo:")
        
        if st.button("ANALIZAR ESCENARIO"):
            if not pregunta:
                st.warning("⚠️ Por favor, escriba una pregunta primero.")
            elif "GROQ_API_KEY" not in st.secrets:
                st.error("❌ No se encontró la API Key.")
            else:
                try:
                    with st.spinner('Consultando con el cerebro de Llama 3.3...'):
                        chat_completion = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": "Eres un experto agrónomo de Cartago, Costa Rica. Analiza datos financieros y da consejos técnicos breves."},
                                {"role": "user", "content": f"Contexto: Utilidad calculada ₡{utilidad}. Pregunta: {pregunta}"}
                            ],
                            model="llama-3.3-70b-versatile", # MODELO DEFINITIVO
                        )
                        st.info(chat_completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error con Groq: {e}")
