import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE INTERFAZ Y ESTILO ---
st.set_page_config(page_title="PAIC - Horizonte 2027", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 3.5em; 
        background-color: #2E7D32; color: white; 
        font-size: 20px; font-weight: bold; border: 2px solid #1B5E20;
    }
    .stMetric { 
        background-color: #F1F8E9; padding: 15px; 
        border-radius: 12px; border-bottom: 5px solid #5D4037; 
    }
    h1, h2, h3 { color: #3E2723; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (PYTHON + ESTADÍSTICA) ---
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
        df_pred = pd.DataFrame(lista_pred)
        df_completo = pd.concat([df, df_pred], ignore_index=True)
        return df_completo, ultima_f, stats
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None, None, None

df_total, hoy, calculos_python = motor_datos()

# --- 3. ESTRUCTURA DE PESTAÑAS ---
st.title("🌱 Plataforma Agro-Inteligente Cartago (PAIC)")
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs([
    "🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN 2027", "🧮 SUPER CALCULADORA", "🤖 CONSULTOR IA"
])

# --- PESTAÑA 1: INICIO ---
with t_inicio:
    st.header("🎯 Panel de Decisión Rápida")
    if df_total is not None:
        mes_real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        mes_prox = df_total[df_total['Origen'] == 'Predicción Python'].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🥔 Papa (Quintal)")
            st.metric("Precio Actual", f"₡{mes_real['Papa Blanca (quintal)']:,.0f}")
            st.metric("Próximo Mes", f"₡{mes_prox['Papa Blanca (quintal)']:,.0f}", f"{((mes_prox['Papa Blanca (quintal)']/mes_real['Papa Blanca (quintal)'])-1)*100:.1f}%")
        with c2:
            st.subheader("🧅 Cebolla (Kg)")
            st.metric("Precio Actual", f"₡{mes_real['Cebolla Amarilla (Kg)']:,.0f}")
            st.metric("Próximo Mes", f"₡{mes_prox['Cebolla Amarilla (Kg)']:,.0f}", f"{((mes_prox['Cebolla Amarilla (Kg)']/mes_real['Cebolla Amarilla (Kg)'])-1)*100:.1f}%")
        with c3:
            st.subheader("🍓 Fresa (Kg)")
            st.metric("Precio Actual", f"₡{mes_real['Fresa (Kg)']:,.0f}")
            st.metric("Próximo Mes", f"₡{mes_prox['Fresa (Kg)']:,.0f}", f"{((mes_prox['Fresa (Kg)']/mes_real['Fresa (Kg)'])-1)*100:.1f}%", delta_color="inverse")

# --- PESTAÑAS 2 Y 3: GRÁFICOS ---
def plot_agro(df_sub, k):
    prod = st.radio("Producto:", ["Todos", "Papa", "Cebolla", "Fresa"], horizontal=True, key=k)
    cols = ["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"]
    if prod != "Todos": cols = [c for c in cols if prod in c]
    fig = px.line(df_sub, x='Fecha', y=cols, color_discrete_map={"Papa Blanca (quintal)": "#D4A373", "Cebolla Amarilla (Kg)": "#FFB703", "Fresa (Kg)": "#E63946"})
    st.plotly_chart(fig, use_container_width=True)

with t_hist: st.header("📚 Histórico Real"); plot_agro(df_total[df_total['Origen'] == 'Histórico Real'], "h_b")
with t_pred: st.header("🔮 Predicción 2027"); plot_agro(df_total, "p_b")

# --- PESTAÑA 4: CALCULADORA ---
with t_calc:
    st.header("🧮 Simulador de Rentabilidad")
    col_a, col_b = st.columns(2)
    ing_p = col_a.number_input("Precio Venta (₡):", value=20000)
    cant = col_a.number_input("Cantidad Producida:", value=500)
    costo_ins = col_b.number_input("Costos Insumos (₡):", value=300000)
    costo_mo = col_b.number_input("Mano de Obra (₡):", value=150000)
    utilidad = (ing_p * cant) - (costo_ins + costo_mo)
    st.metric("Utilidad Estimada", f"₡{utilidad:,.2f}")

# --- PESTAÑA 5: IA (CORRECCIÓN 404) ---
with t_ia:
    st.header("🤖 Consultor IA PAIC")
    # Tu API Key real integrada
    USER_KEY = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"
    query = st.text_area("Haga su consulta técnica:")
    
    if st.button("ANALIZAR CON IA"):
        if query:
            try:
                genai.configure(api_key=USER_KEY)
                # CAMBIO CLAVE: Usamos 'gemini-pro' que es el nombre estable
                model = genai.GenerativeModel('gemini-pro')
                
                with st.spinner('Procesando...'):
                    # Enviamos contexto de datos para que la respuesta sea real
                    prompt = f"Basado en estos datos: {calculos_python.to_string()}. Responde: {query}"
                    response = model.generate_content(prompt)
                    st.success("Análisis completo")
                    st.write(response.text)
            except Exception as e:
                st.error(f"Error técnico: {e}")
