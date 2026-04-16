import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Horizonte 2027", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 3.5em; 
        background-color: #2E7D32; color: white; font-weight: bold; border: 2px solid #1B5E20;
    }
    .stMetric { background-color: #F1F8E9; padding: 15px; border-radius: 12px; border-bottom: 5px solid #5D4037; }
    h1, h2, h3 { color: #3E2723; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        stats = df.describe(include=[np.number])
        ultima_f = df['Fecha'].max()
        futuro = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        lista_pred = []
        for f in futuro:
            mes_actual = f.month
            promedio_mes = df[df['Fecha'].dt.month == mes_actual].mean(numeric_only=True)
            factor = 1 + (len(lista_pred) * 0.0015) 
            lista_pred.append({
                'Fecha': f, 'Papa Blanca (quintal)': promedio_mes['Papa Blanca (quintal)'] * factor,
                'Cebolla Amarilla (Kg)': promedio_mes['Cebolla Amarilla (Kg)'] * factor,
                'Fresa (Kg)': promedio_mes['Fresa (Kg)'] * factor, 'Origen': 'Predicción Python'
            })
        df['Origen'] = 'Histórico Real'
        df_completo = pd.concat([df, pd.DataFrame(lista_pred)], ignore_index=True)
        return df_completo, ultima_f, stats
    except: return None, None, None

df_total, hoy, calculos_python = motor_datos()

# --- 3. PESTAÑAS ---
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN 2027", "🧮 SUPER CALCULADORA", "🤖 CONSULTOR IA"])

# INICIO
with t_inicio:
    st.header("🎯 Panel de Decisión Rápida")
    if df_total is not None:
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Predicción Python'].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{real['Papa Blanca (quintal)']:,.0f}", f"{((prox['Papa Blanca (quintal)']/real['Papa Blanca (quintal)'])-1)*100:.1f}%")
        c2.metric("Cebolla (Kg)", f"₡{real['Cebolla Amarilla (Kg)']:,.0f}", f"{((prox['Cebolla Amarilla (Kg)']/real['Cebolla Amarilla (Kg)'])-1)*100:.1f}%")
        c3.metric("Fresa (Kg)", f"₡{real['Fresa (Kg)']:,.0f}", f"{((prox['Fresa (Kg)']/real['Fresa (Kg)'])-1)*100:.1f}%", delta_color="inverse")

# GRÁFICOS INTERACTIVOS (Histórico y Predicción)
def graficar(df_sub, k):
    prod = st.radio("Filtrar por:", ["Todos", "Papa", "Cebolla", "Fresa"], horizontal=True, key=k)
    cols = ["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"]
    if prod != "Todos": cols = [c for c in cols if prod in c]
    fig = px.line(df_sub, x='Fecha', y=cols, color_discrete_map={"Papa Blanca (quintal)": "#D4A373", "Cebolla Amarilla (Kg)": "#FFB703", "Fresa (Kg)": "#E63946"})
    fig.update_traces(line=dict(width=4))
    st.plotly_chart(fig, use_container_width=True)

with t_hist: st.header("📚 Registro Histórico"); graficar(df_total[df_total['Origen'] == 'Histórico Real'], "h_b")
with t_pred: st.header("🔮 Predicción a Diciembre 2027"); graficar(df_total, "p_b")

# SUPER CALCULADORA (Aquí está todo lo que pidió Glen)
with t_calc:
    st.header("🧮 Simulador Financiero Completo")
    with st.expander("🌱 1. CULTIVO Y PRODUCCIÓN", expanded=True):
        col1, col2, col3 = st.columns(3)
        crop = col1.selectbox("Producto:", ["Papa", "Cebolla", "Fresa"])
        hectareas = col2.number_input("Hectáreas:", value=1.0)
        rend = col3.number_input("Rendimiento (Unid/Ha):", value=500)
        p_venta = col1.number_input("Precio Venta (₡):", value=20000 if crop=="Papa" else 800)
        merma = col2.slider("% Pérdida Estimada:", 0, 50, 5)

    with st.expander("🌿 2. COSTOS DE PRODUCCIÓN"):
        ca, cb = st.columns(2)
        insumos = ca.number_input("Insumos (Semilla, Abono, Químicos) ₡:", value=300000)
        jornales = ca.number_input("Cantidad de Jornales:", value=20)
        pago_j = ca.number_input("Salario por Jornada ₡:", value=15000)
        maquina = cb.number_input("Maquinaria y Combustible ₡:", value=100000)
        otros_c = cb.number_input("Otros Gastos ₡:", value=120000)

    p_neta = (hectareas * rend) * (1 - merma/100)
    ingreso = p_neta * p_venta
    costo = insumos + (jornales * pago_j) + maquina + otros_c
    utilidad = ingreso - costo
    
    st.markdown(f"### 📊 Resultado: {'🟢 RENTABLE' if utilidad > 0 else '🔴 PÉRDIDA'}")
    r1, r2 = st.columns(2)
    r1.metric("Utilidad Neta", f"₡{utilidad:,.2f}")
    r2.metric("Margen", f"{(utilidad/ingreso*100):.1f}%" if ingreso > 0 else "0%")

# IA: SOLUCIÓN FINAL AL ERROR 404
with t_ia:
    st.header("🤖 Consultor IA PAIC")
    USER_KEY = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"
    query = st.text_area("Consulta técnica:")
    
    if st.button("EJECUTAR ANÁLISIS"):
        if query:
            try:
                genai.configure(api_key=USER_KEY.strip())
                # RUTA TÉCNICA FORZADA PARA EVITAR EL 404
                model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
                
                prompt = f"Actúa como experto agrícola en Cartago. Datos: {calculos_python.to_string()}. Escenario Calculadora: Utilidad ₡{utilidad}. Responde: {query}"
                with st.spinner('Motor de IA calculando...'):
                    response = model.generate_content(prompt)
                    st.info(response.text)
            except Exception as e:
                # Si falla Flash, intentamos con Pro
                try:
                    model = genai.GenerativeModel(model_name='models/gemini-pro')
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except:
                    st.error("Error de conexión. Verifique su API Key en Google AI Studio.")
