import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE INTERFAZ Y COLORES ---
st.set_page_config(page_title="PAIC - Horizonte 2027", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stButton>button { 
        width: 100%; border-radius: 20px; height: 5em; 
        background-color: #2E7D32; color: white; 
        font-size: 22px; font-weight: bold; border: 3px solid #1B5E20;
    }
    .stMetric { 
        background-color: #F1F8E9; padding: 20px; 
        border-radius: 15px; border-bottom: 8px solid #5D4037; 
    }
    h1, h2, h3 { color: #3E2723; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (Cálculos Python con límite a Diciembre 2027) ---
@st.cache_data
def motor_de_datos_python():
    df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    stats = df.describe(include=[np.number])
    
    ultima_f = df['Fecha'].max()
    # PREDICCIÓN HASTA DICIEMBRE 2027
    futuro = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
    
    lista_pred = []
    for f in futuro:
        mes_actual = f.month
        promedio_mes = df[df['Fecha'].dt.month == mes_actual].mean(numeric_only=True)
        factor = 1 + (len(lista_pred) * 0.0015)
        lista_pred.append({
            'Fecha': f,
            'Papa Blanca (quintal)': promedio_mes['Papa Blanca (quintal)'] * factor,
            'Cebolla Amarilla (Kg)': promedio_mes['Cebolla Amarilla (Kg)'] * factor,
            'Fresa (Kg)': promedio_mes['Fresa (Kg)'] * factor,
            'Origen': 'Predicción Python'
        })
    
    df['Origen'] = 'Histórico Real'
    df_pred = pd.DataFrame(lista_pred)
    return pd.concat([df, df_pred], ignore_index=True), ultima_f, stats

try:
    df_total, hoy, calculos_python = motor_de_datos_python()
except Exception as e:
    st.error("⚠️ Error: Verifique que el archivo Excel esté en GitHub.")
    st.stop()

# --- 3. ESTRUCTURA DE MÓDULOS ---
st.title("🌱 Plataforma Agro-Inteligente Cartago (PAIC)")
st.subheader("Análisis Predictivo: Horizonte Diciembre 2027")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN 2027", "🧮 RENTABILIDAD", "🤖 CONSULTOR IA"
])

with tab1:
    st.header("🎯 Dashboard de Decisión Rápida")
    col1, col2, col3 = st.columns(3)
    
    p_p = df_total[df_total['Origen'] == 'Predicción Python']['Papa Blanca (quintal)'].iloc[0]
    p_c = df_total[df_total['Origen'] == 'Predicción Python']['Cebolla Amarilla (Kg)'].iloc[0]
    p_f = df_total[df_total['Origen'] == 'Predicción Python']['Fresa (Kg)'].iloc[0]

    col1.metric("Papa (Proy. Mes)", f"₡{p_p:,.0f}", "Estable")
    col2.metric("Cebolla (Proy. Mes)", f"₡{p_c:,.0f}", "📈 Tendencia Alza")
    col3.metric("Fresa (Proy. Mes)", f"₡{p_f:,.0f}", "📉 Estacionalidad", delta_color="inverse")
    
    st.info(f"**Motor Python:** Última actualización de datos reales: {hoy.strftime('%d/%m/%Y')}.")

with tab2:
    st.header("📈 Historial Real (2020-2026)")
    fig_h = px.line(df_total[df_total['Origen'] == 'Histórico Real'], x='Fecha', 
                  y=["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"],
                  color_discrete_map={"Papa Blanca (quintal)": "#D4A373", "Cebolla Amarilla (Kg)": "#FFB703", "Fresa (Kg)": "#E63946"})
    st.plotly_chart(fig_h, use_container_width=True)

with tab3:
    st.header("🔮 Predicción del Mercado (2026 - 2027)")
    fig_p = px.line(df_total, x='Fecha', y=["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"],
                  title="Tendencia calculada por Python hasta Diciembre 2027")
    fig_p.add_vline(x=hoy.timestamp() * 1000, line_dash="dash", line_color="green")
    st.plotly_chart(fig_p, use_container_width=True)

with tab4:
    st.header("🧮 Calculadora de Costos")
    c1, c2 = st.columns(2)
    jornal = c1.number_input("Inversión en Mano de Obra (₡):", value=150000)
    insumos = c2.number_input("Inversión en Insumos (₡):", value=200000)
    st.error(f"### Inversión Total: ₡{jornal + insumos:,.2f}")

with tab5:
    st.header("🤖 Consultor IA (Basado en Python)")
    # TU API KEY YA INTEGRADA
    API_KEY = "AIzaSyB" + "..." # Asegúrate que sea tu clave real
    
    p = st.text_area("Haga su consulta técnica al sistema:", height=150)
    
    if st.button("ANALIZAR CON INTELIGENCIA ARTIFICIAL"):
        if p:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-pro')
                ctx = f"CÁLCULOS TÉCNICOS PYTHON: {calculos_python.to_string()}. Pregunta: {p}"
                res = model.generate_content(ctx)
                st.markdown("---")
                st.success("✅ Análisis Basado en Datos")
                st.write(res.text)
            except Exception as e:
                st.error("Error en conexión de IA.")
