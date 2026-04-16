import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Horizonte 2027", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .stMetric { background-color: #F1F8E9; padding: 15px; border-radius: 12px; border-bottom: 5px solid #5D4037; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3em; background-color: #2E7D32; color: white; font-weight: bold; }
    h1, h2, h3 { color: #3E2723; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LLAVE DE SEGURIDAD ---
LLAVE_PAIC = "AQ.Ab8RN6KbGWiFXRO2zRRDzP6jz2dvgrd3MzPUnjAwPLx5TzfZ1A"

# --- 3. MOTOR DE DATOS Y PREDICCIONES ---
@st.cache_data
def cargar_y_predecir():
    try:
        # Carga del Excel
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Generar proyección hasta finales de 2027
        ultima_fecha = df['Fecha'].max()
        fechas_futuras = pd.date_range(start=ultima_fecha + timedelta(days=1), end="2027-12-31", freq='MS')
        
        proyecciones = []
        for i, fecha in enumerate(fechas_futuras):
            # Lógica estacional: busca el promedio histórico de ese mes específico
            mes = fecha.month
            promedios = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            
            # Factor de ajuste leve (inflación/crecimiento proyectado)
            ajuste = 1 + (i * 0.002) 
            
            proyecciones.append({
                'Fecha': fecha,
                'Papa Blanca (quintal)': promedios['Papa Blanca (quintal)'] * ajuste,
                'Cebolla Amarilla (Kg)': promedios['Cebolla Amarilla (Kg)'] * ajuste,
                'Fresa (Kg)': promedios['Fresa (Kg)'] * ajuste,
                'Origen': 'Proyección IA/Python'
            })
        
        df['Origen'] = 'Histórico Real'
        df_final = pd.concat([df, pd.DataFrame(proyecciones)], ignore_index=True)
        return df_final
    except Exception as e:
        st.error(f"Error al procesar datos: {e}")
        return None

df_total = cargar_y_predecir()

# --- 4. INTERFAZ DE USUARIO (PESTAÑAS) ---
st.title("🌱 Plataforma Agro-Inteligente Cartago")
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs([
    "🏠 INICIO", "📚 HISTÓRICO", "🔮 PROYECCIONES 2027", "🧮 CALCULADORA", "🤖 CONSULTOR IA"
])

# --- PESTAÑA INICIO: SEMÁFORO DE PRECIOS ---
with t_inicio:
    st.header("🎯 Resumen de Mercado Actual")
    if df_total is not None:
        actual = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{actual['Papa Blanca (quintal)']:,.0f}")
        c2.metric("Cebolla (Kg)", f"₡{actual['Cebolla Amarilla (Kg)']:,.0f}")
        c3.metric("Fresa (Kg)", f"₡{actual['Fresa (Kg)']:,.0f}")

# --- PESTAÑA HISTÓRICO: GRÁFICOS ---
with t_hist:
    st.header("📚 Análisis de Datos Históricos")
    if df_total is not None:
        fig_hist = px.line(df_total[df_total['Origen'] == 'Histórico Real'], 
                          x='Fecha', y=['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'],
                          title="Evolución de Precios en Cartago", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_hist, use_container_width=True)

# --- PESTAÑA PROYECCIONES: FUTURO 2027 ---
with t_pred:
    st.header("🔮 Horizonte de Precios 2026-2027")
    if df_total is not None:
        fig_pred = px.line(df_total, x='Fecha', y='Papa Blanca (quintal)', color='Origen',
                          title="Proyección de Precio: Papa Blanca")
        st.plotly_chart(fig_pred, use_container_width=True)

# --- PESTAÑA CALCULADORA: FINANZAS COMPLETAS ---
with t_calc:
    st.header("🧮 Simulador de Rentabilidad")
    col1, col2 = st.columns(2)
    with col1:
        hectareas = st.number_input("Hectáreas a sembrar:", value=1.0)
        costo_insumos = st.number_input("Insumos (Semilla, Abono) ₡:", value=350000)
        jornales = st.number_input("Costo Total de Jornales ₡:", value=250000)
    with col2:
        rendimiento = st.number_input("Rendimiento (Unidades por Ha):", value=600)
        precio_v = st.number_input("Precio de Venta Sugerido ₡:", value=18000)
        merma = st.slider("% Merma o Desperdicio:", 0, 40, 5)
    
    # Cálculos
    produccion_neta = (hectareas * rendimiento) * (1 - merma/100)
    ingreso_total = produccion_neta * precio_v
    egreso_total = costo_insumos + jornales
    utilidad = ingreso_total - egreso_total
    
    st.markdown("---")
    st.metric("UTILIDAD NETA ESTIMADA", f"₡{utilidad:,.2f}", delta=f"{((utilidad/egreso_total)*100):.1f}% ROI")

# --- PESTAÑA IA: EL CONSULTOR ---
with t_ia:
    st.header("🤖 Consultor Técnico IA")
    pregunta = st.text_area("Haga una consulta sobre su cultivo o los precios:")
    
    if st.button("ANALIZAR ESCENARIO"):
        if pregunta:
            try:
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-pro')
                
                # Le damos contexto a la IA para que sea más inteligente
                contexto = f"Contexto: Agricultor en Cartago. Utilidad calculada: {utilidad}. Pregunta: {pregunta}"
                
                with st.spinner('Procesando análisis técnico...'):
                    response = model.generate_content(contexto)
                    st.success("Análisis PAIC:")
                    st.info(response.text)
            except Exception as e:
                st.error(f"Error de conexión con la IA: {e}")
