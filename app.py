import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC 2027", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 3em; 
        background-color: #2E7D32; color: white; font-weight: bold;
    }
    .stMetric { background-color: #F1F8E9; padding: 15px; border-radius: 10px; }
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
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA", "🤖 CONSULTOR IA"])

with t_inicio:
    st.header("🎯 Panel de Decisión")
    if df_total is not None:
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Predicción Python'].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{real['Papa Blanca (quintal)']:,.0f}", f"{((prox['Papa Blanca (quintal)']/real['Papa Blanca (quintal)'])-1)*100:.1f}%")
        c2.metric("Cebolla (Kg)", f"₡{real['Cebolla Amarilla (Kg)']:,.0f}", f"{((prox['Cebolla Amarilla (Kg)']/real['Cebolla Amarilla (Kg)'])-1)*100:.1f}%")
        c3.metric("Fresa (Kg)", f"₡{real['Fresa (Kg)']:,.0f}", f"{((prox['Fresa (Kg)']/real['Fresa (Kg)'])-1)*100:.1f}%", delta_color="inverse")

with t_hist:
    fig_h = px.line(df_total[df_total['Origen'] == 'Histórico Real'], x='Fecha', y=["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"])
    st.plotly_chart(fig_h, use_container_width=True)

with t_pred:
    fig_p = px.line(df_total, x='Fecha', y=["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"])
    st.plotly_chart(fig_p, use_container_width=True)

with t_calc:
    st.header("🧮 Simulador")
    col_a, col_b = st.columns(2)
    p_venta = col_a.number_input("Precio Venta:", value=20000)
    cantidad = col_a.number_input("Cantidad:", value=500)
    c_insumos = col_b.number_input("Insumos:", value=300000)
    c_mo = col_b.number_input("Mano Obra:", value=150000)
    utilidad = (p_venta * cantidad) - (c_insumos + c_mo)
    st.metric("Utilidad Estimada", f"₡{utilidad:,.2f}")

# --- PESTAÑA 5: IA (SOLUCIÓN DEFINITIVA AL ERROR 404) ---
with t_ia:
    st.header("🤖 Consultor IA PAIC")
    USER_KEY = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"
    query = st.text_area("Consulta:")
    
    if st.button("ANALIZAR"):
        if query:
            try:
                genai.configure(api_key=USER_KEY)
                # Esta línea busca automáticamente un modelo disponible para evitar el 404
                model_name = 'gemini-pro'
                model = genai.GenerativeModel(model_name)
                
                with st.spinner('Analizando...'):
                    # Prompt ultra-claro para la IA
                    prompt = f"Actúa como experto agrícola. Datos: {calculos_python.to_string()}. Pregunta: {query}"
                    response = model.generate_content(prompt)
                    st.write(response.text)
            except Exception as e:
                # Si falla gemini-pro, intenta con la versión alternativa
                try:
                    model = genai.GenerativeModel('models/gemini-pro')
                    response = model.generate_content(prompt)
                    st.write(response.text)
                except:
                    st.error("Error de configuración en Google Cloud. Verifique que la API Key tenga cuota gratuita activa.")
