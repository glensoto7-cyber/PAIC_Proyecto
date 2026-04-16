import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN BÁSICA
st.set_page_config(page_title="PAIC - Cartago", layout="wide", page_icon="🌱")

# Tu llave Maestra (La que empieza con AIzaSy)
LLAVE_PAIC = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"

# 2. MOTOR DE DATOS (A PRUEBA DE ERRORES)
@st.cache_data
def cargar_datos_seguro():
    try:
        # Cargamos el Excel que tenés en GitHub
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Crear proyecciones básicas para que la app tenga vida
        u_f = df['Fecha'].max()
        fechas_futuras = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for i, f in enumerate(fechas_futuras):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * (1 + i*0.002),
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * (1 + i*0.002),
                'Fresa (Kg)': prom['Fresa (Kg)'] * (1 + i*0.002), 'Origen': 'Proyección'
            })
        df['Origen'] = 'Histórico'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return str(e)

# Ejecutar carga
df_total = cargar_datos_seguro()

# 3. DISEÑO DE LA INTERFAZ
st.title("🌱 Plataforma Agro-Inteligente Cartago")

if isinstance(df_total, str):
    st.error(f"❌ Error al leer el Excel: {df_total}")
    st.info("Revisá que el nombre del archivo en GitHub sea exactamente: Precios historicos 15 ABRIL.xlsx")
else:
    t1, t2, t3, t4 = st.tabs(["🏠 INICIO", "🔮 PREDICCIÓN 2027", "🧮 CALCULADORA", "🤖 IA CONSULTOR"])

    with t1:
        st.header("🎯 Precios Actuales")
        actual = df_total[df_total['Origen'] == 'Histórico'].iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{actual['Papa Blanca (quintal)']:,.0f}")
        c2.metric("Cebolla (Kg)", f"₡{actual['Cebolla Amarilla (Kg)']:,.0f}")
        c3.metric("Fresa (Kg)", f"₡{actual['Fresa (Kg)']:,.0f}")
        st.line_chart(df_total[df_total['Origen'] == 'Histórico'].set_index('Fecha')[['Papa Blanca (quintal)']])

    with t3:
        st.header("🧮 Simulador de Rentabilidad")
        col1, col2 = st.columns(2)
        h = col1.number_input("Hectáreas:", value=1.0)
        p = col2.number_input("Precio Venta Sugerido ₡:", value=18000)
        costos = col1.number_input("Costos (Insumos + Jornales) ₡:", value=500000)
        
        utilidad = (h * 600 * p) - costos
        st.metric("UTILIDAD ESTIMADA", f"₡{utilidad:,.2f}")

    with t4:
        st.header("🤖 Consultor IA")
        pregunta = st.text_input("Haga su consulta técnica:")
        if st.button("ANALIZAR"):
            try:
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Agricultor Cartago pregunta: {pregunta}. Contexto: Utilidad {utilidad}")
                st.info(res.text)
            except Exception as e:
                st.error(f"Error de IA: {e}")
