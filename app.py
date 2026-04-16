import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Cartago 2027", layout="wide", page_icon="🌱")

# Tu llave Maestra
LLAVE_MAESTRA = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"

# Estilo visual
st.markdown("""
    <style>
    .stMetric { background-color: #F1F8E9; padding: 15px; border-radius: 12px; border-bottom: 5px solid #5D4037; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3em; background-color: #2E7D32; color: white; font-weight: bold; }
    h1, h2, h3 { color: #3E2723; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        # Intentamos cargar el archivo
        nombre_archivo = "Precios historicos 15 ABRIL.xlsx"
        df = pd.read_excel(nombre_archivo, engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Generamos proyecciones básicas
        u_f = df['Fecha'].max()
        fechas_futuras = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        
        proyecciones = []
        for i, f in enumerate(fechas_futuras):
            mes = f.month
            promedios = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            ajuste = 1 + (i * 0.002)
            proyecciones.append({
                'Fecha': f,
                'Papa Blanca (quintal)': promedios['Papa Blanca (quintal)'] * ajuste,
                'Cebolla Amarilla (Kg)': promedios['Cebolla Amarilla (Kg)'] * ajuste,
                'Fresa (Kg)': promedios['Fresa (Kg)'] * ajuste,
                'Origen': 'Proyección PAIC'
            })
        
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proyecciones)], ignore_index=True)
    except Exception as e:
        st.error(f"⚠️ Error cargando el Excel: {e}")
        return None

df_total = cargar_datos()

# --- 3. INTERFAZ ---
st.title("🌱 Plataforma Agro-Inteligente Cartago")

if df_total is not None:
    t1, t2, t3, t4, t5 = st.tabs(["🏠 INICIO", "📚 HISTORIAL", "🔮 2027", "🧮 CALCULADORA", "🤖 CONSULTOR IA"])
    
    with t1:
        st.header("🎯 Resumen de Mercado")
        actual = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{actual['Papa Blanca (quintal)']:,.0f}")
        c2.metric("Cebolla (Kg)", f"₡{actual['Cebolla Amarilla (Kg)']:,.0f}")
        c3.metric("Fresa (Kg)", f"₡{actual['Fresa (Kg)']:,.0f}")

    with t4:
        st.header("🧮 Simulador de Rentabilidad")
        col1, col2 = st.columns(2)
        h = col1.number_input("Hectáreas:", value=1.0)
        r = col2.number_input("Rendimiento (Unid/Ha):", value=600)
        p = col1.number_input("Precio de Venta ₡:", value=18000)
        m = col2.slider("% Merma:", 0, 40, 5)
        
        ins = col1.number_input("Costos Insumos ₡:", value=350000)
        jor = col2.number_input("Costo Jornales ₡:", value=250000)
        
        utilidad = ((h * r * (1 - m/100)) * p) - (ins + jor)
        st.metric("UTILIDAD ESTIMADA", f"₡{utilidad:,.2f}")

    with t5:
        st.header("🤖 Consultor IA")
        pregunta = st.text_area("Haga su consulta técnica:")
        if st.button("ANALIZAR"):
            try:
                genai.configure(api_key=LLAVE_MAESTRA)
                model = genai.GenerativeModel('gemini-1.5-flash')
                contexto = f"Agricultor Cartago. Utilidad: {utilidad}. Pregunta: {pregunta}"
                with st.spinner('Consultando...'):
                    res = model.generate_content(contexto)
                    st.info(res.text)
            except Exception as e:
                st.error(f"Error IA: {e}")
else:
    st.warning("Por favor, sube el archivo Excel a tu repositorio de GitHub para que la app funcione.")
