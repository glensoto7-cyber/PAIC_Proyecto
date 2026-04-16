import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 🔒 SEGURIDAD: Carga de API Key de Groq desde Secrets
try:
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    else:
        st.warning("⚠️ Configure GROQ_API_KEY en los Secretos de Streamlit.")
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
        
        ultima_f = df['Fecha'].max()
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        
        proy = []
        for i, f in enumerate(fechas_proy):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 
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
    st.error(df_total)
else:
    t1, t2, t3, t4, t5 = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA PRO", "🤖 IA"])

    with t1:
        st.header("🎯 Comparativa Mensual")
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
        c1, c2, c3 = st.columns(3)
        for p, col in zip(['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'], [c1, c2, c3]):
            v = ((prox[p]/real[p])-1)*100
            col.metric(p, f"₡{real[p]:,.0f}", f"Próx: {prox[p]:,.0f} ({v:+.1f}%)")

    with t4:
        st.header("🧮 Calculadora de Rentabilidad")
        ha = st.number_input("Hectáreas:", value=1.0)
        p_v = st.number_input("Precio Venta ₡:", value=int(real['Papa Blanca (quintal)']))
        costos = st.number_input("Costos Totales ₡:", value=500000)
        utilidad = (ha * 600 * p_v) - costos
        st.metric("GANANCIA NETA", f"₡{utilidad:,.2f}")
        
        if utilidad > 200000: st.markdown("<div class='rentable'><h3>🟢 RENTABLE</h3></div>", unsafe_allow_html=True)
        elif utilidad > 0: st.markdown("<div class='ajustado'><h3>🟡 AJUSTADO</h3></div>", unsafe_allow_html=True)
        else: st.markdown("<div class='perdida'><h3>🔴 PÉRDIDA</h3></div>", unsafe_allow_html=True)

    with t5:
        st.header("🤖 Consultor IA PAIC (Powered by Groq)")
        pregunta = st.text_area("Consulta técnica:")
        
        if st.button("ANALIZAR"):
            if pregunta and "GROQ_API_KEY" in st.secrets:
                try:
                    with st.spinner('Análisis ultra-rápido en progreso...'):
                        chat_completion = client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Eres un experto agrónomo de Cartago, Costa Rica. Analiza datos financieros y da consejos técnicos breves."
                                },
                                {
                                    "role": "user",
                                    "content": f"Datos: Utilidad ₡{utilidad}. Pregunta: {pregunta}",
                                }
                            ],
                            model="llama3-8b-8192", # El modelo más estable de Groq
                        )
                        st.info(chat_completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error con Groq: {e}")
            else:
                st.warning("Escriba su pregunta o verifique su GROQ_API_KEY en Secrets.")
