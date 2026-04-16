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
    # Carga de base de datos desde tu GitHub
    df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    stats = df.describe(include=[np.number])
    
    ultima_f = df['Fecha'].max()
    # Horizonte a Diciembre 2027
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

df_total, hoy, calculos_python = motor_datos()

# --- 3. ESTRUCTURA DE PESTAÑAS ---
st.title("🌱 Plataforma Agro-Inteligente Cartago (PAIC)")
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs([
    "🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN 2027", "🧮 SUPER CALCULADORA", "🤖 CONSULTOR IA"
])

# --- PESTAÑA 1: INICIO (Comparativa Solicitada) ---
with t_inicio:
    st.header("🎯 Panel de Decisión Rápida")
    mes_real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
    mes_prox = df_total[df_total['Origen'] == 'Predicción Python'].iloc[0]
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🥔 Papa (Quintal)")
        st.metric("Precio Actual", f"₡{mes_real['Papa Blanca (quintal)']:,.0f}")
        st.metric("Estimado Próx. Mes", f"₡{mes_prox['Papa Blanca (quintal)']:,.0f}", 
                  f"{((mes_prox['Papa Blanca (quintal)']/mes_real['Papa Blanca (quintal)'])-1)*100:.1f}%")

    with c2:
        st.subheader("🧅 Cebolla (Kg)")
        st.metric("Precio Actual", f"₡{mes_real['Cebolla Amarilla (Kg)']:,.0f}")
        st.metric("Estimado Próx. Mes", f"₡{mes_prox['Cebolla Amarilla (Kg)']:,.0f}", 
                  f"{((mes_prox['Cebolla Amarilla (Kg)']/mes_real['Cebolla Amarilla (Kg)'])-1)*100:.1f}%")

    with c3:
        st.subheader("🍓 Fresa (Kg)")
        st.metric("Precio Actual", f"₡{mes_real['Fresa (Kg)']:,.0f}")
        st.metric("Estimado Próx. Mes", f"₡{mes_prox['Fresa (Kg)']:,.0f}", 
                  f"{((mes_prox['Fresa (Kg)']/mes_real['Fresa (Kg)'])-1)*100:.1f}%", delta_color="inverse")

# --- PESTAÑAS 2 Y 3: GRÁFICOS CON BOTONES Y LEYENDA ---
def plot_interactivo(df_sub, k):
    st.write("💡 *Use los botones para aislar un producto o toque la leyenda para filtrar.*")
    sel = st.radio("Filtro rápido:", ["Todos", "Papa", "Cebolla", "Fresa"], horizontal=True, key=k)
    cols = ["Papa Blanca (quintal)", "Cebolla Amarilla (Kg)", "Fresa (Kg)"]
    if sel != "Todos": cols = [c for c in cols if sel in c]
    
    fig = px.line(df_sub, x='Fecha', y=cols, 
                 color_discrete_map={"Papa Blanca (quintal)": "#D4A373", "Cebolla Amarilla (Kg)": "#FFB703", "Fresa (Kg)": "#E63946"})
    fig.update_traces(line=dict(width=4))
    st.plotly_chart(fig, use_container_width=True)

with t_hist: st.header("📚 Registro Histórico (2020-2026)"); plot_interactivo(df_total[df_total['Origen'] == 'Histórico Real'], "h_btn")
with t_pred: st.header("🔮 Estimación de Precios a Diciembre 2027"); plot_interactivo(df_total, "p_btn")

# --- PESTAÑA 4: SUPER CALCULADORA (Diseño detallado) ---
with t_calc:
    st.header("🧮 Simulador de Rentabilidad Agrícola")
    with st.expander("🌱 CULTIVO Y COMERCIALIZACIÓN", expanded=True):
        c1, c2, c3 = st.columns(3)
        crop_name = c1.selectbox("Tipo de Cultivo:", ["Papa", "Cebolla", "Fresa"])
        hectareas = c2.number_input("Área (Ha):", value=1.0)
        rend = c3.number_input("Rendimiento (Unid/Ha):", value=500)
        precio_v = c1.number_input("Precio Venta Sugerido (₡):", value=20000 if crop_name=="Papa" else 800)
        merma = c2.slider("% Pérdida por Clima/Merma:", 0, 50, 5)

    with st.expander("🌿 COSTOS DE PRODUCCIÓN"):
        c_a, c_b = st.columns(2)
        insumos = c_a.number_input("Insumos (Semilla, Abono, Químicos) ₡:", value=300000)
        jornales = c_a.number_input("Cantidad de Jornales:", value=20)
        pago_j = c_a.number_input("Salario por Jornada ₡:", value=15000)
        maquina = c_b.number_input("Maquinaria y Combustible ₡:", value=100000)
        otros_gastos = c_b.number_input("Alquiler, Riego y Otros ₡:", value=120000)

    # CÁLCULOS FINANCIEROS
    prod_neta = (hectareas * rend) * (1 - merma/100)
    ingresos = prod_neta * precio_v
    costos = insumos + (jornales * pago_j) + maquina + otros_gastos
    utilidad = ingresos - costos
    margen = (utilidad / ingresos * 100) if ingresos > 0 else 0

    st.markdown(f"### 📊 Resultado Financiero: {'🟢 RENTABLE' if utilidad > 0 else '🔴 PÉRDIDA'}")
    r1, r2, r3 = st.columns(3)
    r1.metric("Utilidad Neta", f"₡{utilidad:,.2f}")
    r2.metric("Margen de Ganancia", f"{margen:.1f}%")
    r3.metric("Costo por Unidad", f"₡{(costos/prod_neta if prod_neta>0 else 0):,.2f}")

# --- PESTAÑA 5: CONSULTOR IA ---
with t_ia:
    st.header("🤖 Consultor IA PAIC")
    USER_API_KEY = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"
    
    query = st.text_area("Haga su consulta técnica al Asistente:", height=150)
    
    if st.button("ANALIZAR CON INTELIGENCIA ARTIFICIAL"):
        if query:
            try:
                genai.configure(api_key=USER_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                ctx = f"CÁLCULOS PYTHON: {calculos_python.to_string()}. ESCENARIO ACTUAL: Utilidad ₡{utilidad}. Pregunta: {query}"
                
                with st.spinner('Procesando datos con Google Gemini...'):
                    res = model.generate_content(ctx)
                    st.info(res.text)
            except Exception as e:
                st.error(f"Error de conexión: {str(e)}")
