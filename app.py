import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# CARGAR LLAVE DESDE LOS SECRETOS (NO TOCAR ESTA LÍNEA)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception:
    st.warning("⚠️ Configuración de seguridad pendiente: Inserte su GOOGLE_API_KEY en los Secretos de Streamlit Cloud.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        # Proyecciones a 2027
        u_f = df['Fecha'].max()
        fechas_proy = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for i, f in enumerate(fechas_proy):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * (1 + i*0.002),
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * (1 + i*0.002),
                'Fresa (Kg)': prom['Fresa (Kg)'] * (1 + i*0.002), 'Origen': 'Proyección PAIC'
            })
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return str(e)

df_total = motor_datos()

# --- 3. INTERFAZ ---
if isinstance(df_total, str):
    st.error(f"Error en datos: {df_total}")
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
        
        # Semáforo dinámico
        if utilidad > 200000: st.success("🟢 RENTABLE")
        elif utilidad > 0: st.warning("🟡 AJUSTADO")
        else: st.error("🔴 PÉRDIDA")

    with t5:
        st.header("🤖 Consultor IA PAIC")
        pregunta = st.text_area("Pregunta técnica:")
        if st.button("ANALIZAR"):
            if pregunta and "GOOGLE_API_KEY" in st.secrets:
                model = genai.GenerativeModel('gemini-1.5-flash')
                ctx = f"Eres experto agrónomo de Cartago. Utilidad: ₡{utilidad}. Pregunta: {pregunta}"
                res = model.generate_content(ctx)
                st.info(res.text)
            else:
                st.warning("Escriba su pregunta o verifique la llave API.")
