import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="PAIC - Cartago 2027", layout="wide", page_icon="🌱")

# --- 2. MOTOR DE DATOS (Predicciones Python) ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        u_f = df['Fecha'].max()
        futuro = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
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
        return df_completo, df[df['Fecha'].dt.month == (u_f.month + 1 if u_f.month < 12 else 1)].mean(numeric_only=True)
    except: return None, None

df_total, calculos_python = motor_datos()

# --- 3. ESTRUCTURA DE NAVEGACIÓN ---
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs([
    "🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN 2027", "🧮 CALCULADORA", "🤖 CONSULTOR IA"
])

# INICIO: MÉTRICAS RÁPIDAS
with t_inicio:
    st.header("🎯 Resumen de Precios")
    if df_total is not None:
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Predicción Python'].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{real['Papa Blanca (quintal)']:,.0f}", f"{((prox['Papa Blanca (quintal)']/real['Papa Blanca (quintal)'])-1)*100:.1f}%")
        c2.metric("Cebolla (Kg)", f"₡{real['Cebolla Amarilla (Kg)']:,.0f}", f"{((prox['Cebolla Amarilla (Kg)']/real['Cebolla Amarilla (Kg)'])-1)*100:.1f}%")
        c3.metric("Fresa (Kg)", f"₡{real['Fresa (Kg)']:,.0f}", f"{((prox['Fresa (Kg)']/real['Fresa (Kg)'])-1)*100:.1f}%", delta_color="inverse")

# CALCULADORA: FINANZAS AGRÍCOLAS
with t_calc:
    st.header("🧮 Simulador de Rentabilidad")
    col1, col2 = st.columns(2)
    hectareas = col1.number_input("Hectáreas:", value=1.0)
    rend = col2.number_input("Rendimiento (Unid/Ha):", value=500)
    p_venta = col1.number_input("Precio Venta (₡):", value=20000)
    merma = col2.slider("% Merma (Pérdida):", 0, 50, 5)
    
    insumos = col1.number_input("Insumos ₡:", value=300000)
    jornales = col2.number_input("Costo de Jornales ₡:", value=300000)
    
    utilidad = ((hectareas * rend * (1 - merma/100)) * p_venta) - (insumos + jornales)
    st.markdown("---")
    st.metric("UTILIDAD NETA ESTIMADA", f"₡{utilidad:,.2f}")

# CONSULTOR IA: CONEXIÓN GOOGLE
with t_ia:
    st.header("🤖 Consultor Inteligente PAIC")
    # TU LLAVE COPIADA
    LLAVE_FINAL = "AQ.Ab8RN6KbGWiFXRO2zRRDzP6jz2dvgrd3MzPUnjAwPLx5TzfZ1A"
    
    pregunta = st.text_area("Haga una pregunta sobre los datos o su cultivo:")
    
    if st.button("ANALIZAR ESCENARIO"):
        if pregunta:
            try:
                genai.configure(api_key=LLAVE_FINAL)
                model = genai.GenerativeModel('gemini-1.5-flash')
                contexto = f"Datos promedio: {calculos_python}. Utilidad actual: {utilidad}. Pregunta: {pregunta}"
                
                with st.spinner('Consultando con la IA...'):
                    response = model.generate_content(contexto)
                    st.success("Análisis de la IA:")
                    st.info(response.text)
            except Exception as e:
                st.error(f"Error de conexión: {e}")
