import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Horizonte 2027", layout="wide", page_icon="🌱")

# Estilo profesional para la interfaz
st.markdown("""
    <style>
    .stMetric { background-color: #F1F8E9; padding: 15px; border-radius: 12px; border-bottom: 5px solid #5D4037; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3em; background-color: #2E7D32; color: white; font-weight: bold; }
    h1, h2, h3 { color: #3E2723; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LLAVE DE SEGURIDAD (ACTUALIZADA) ---
LLAVE_PAIC = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"

# --- 3. MOTOR DE DATOS Y PREDICCIONES ---
@st.cache_data
def cargar_y_predecir():
    try:
        # Carga del Excel - Asegúrate que el nombre del archivo sea idéntico en tu GitHub
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Generar proyección hasta finales de 2027
        ultima_fecha = df['Fecha'].max()
        fechas_futuras = pd.date_range(start=ultima_fecha + timedelta(days=1), end="2027-12-31", freq='MS')
        
        proyecciones = []
        for i, fecha in enumerate(fechas_futuras):
            mes = fecha.month
            # Promedio histórico mensual para mantener estacionalidad
            promedios = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            
            # Factor de ajuste por inflación proyectada (0.2% mensual acumulado)
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
        st.error(f"Error al procesar datos del Excel: {e}")
        return None

df_total = cargar_y_predecir()

# --- 4. INTERFAZ DE USUARIO ---
st.title("🌱 Plataforma Agro-Inteligente Cartago (PAIC)")
t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs([
    "🏠 INICIO", "📚 HISTÓRICO", "🔮 PROYECCIONES 2027", "🧮 CALCULADORA", "🤖 CONSULTOR IA"
])

# --- PESTAÑA INICIO ---
with t_inicio:
    st.header("🎯 Resumen de Mercado Actual")
    if df_total is not None:
        actual = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{actual['Papa Blanca (quintal)']:,.0f}")
        c2.metric("Cebolla (Kg)", f"₡{actual['Cebolla Amarilla (Kg)']:,.0f}")
        c3.metric("Fresa (Kg)", f"₡{actual['Fresa (Kg)']:,.0f}")

# --- PESTAÑA HISTÓRICO ---
with t_hist:
    st.header("📚 Análisis de Datos Históricos")
    if df_total is not None:
        fig_hist = px.line(df_total[df_total['Origen'] == 'Histórico Real'], 
                          x='Fecha', y=['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'],
                          title="Evolución de Precios en Cartago",
                          labels={'value': 'Precio en Colones', 'variable': 'Producto'})
        st.plotly_chart(fig_hist, use_container_width=True)

# --- PESTAÑA PROYECCIONES ---
with t_pred:
    st.header("🔮 Horizonte de Precios 2026-2027")
    if df_total is not None:
        producto_sel = st.selectbox("Seleccione producto para ver tendencia:", 
                                   ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
        fig_pred = px.line(df_total, x='Fecha', y=producto_sel, color='Origen',
                          title=f"Proyección de Precio: {producto_sel}")
        st.plotly_chart(fig_pred, use_container_width=True)

# --- PESTAÑA CALCULADORA ---
with t_calc:
    st.header("🧮 Simulador de Rentabilidad Agrícola")
    col1, col2 = st.columns(2)
    with col1:
        hectareas = st.number_input("Hectáreas a sembrar:", value=1.0, step=0.5)
        costo_insumos = st.number_input("Insumos (Semilla, Abono, Riego) ₡:", value=350000)
        jornales = st.number_input("Costo Total de Mano de Obra (Jornales) ₡:", value=250000)
    with col2:
        rendimiento = st.number_input("Rendimiento Esperado (Unidades por Ha):", value=600)
        precio_v = st.number_input("Precio de Venta Estimado ₡:", value=18000)
        merma = st.slider("% Merma o Desperdicio (Post-cosecha):", 0, 40, 5)
    
    # Cálculo de Utilidad
    produccion_neta = (hectareas * rendimiento) * (1 - merma/100)
    ingreso_total = produccion_neta * precio_v
    egreso_total = costo_insumos + jornales
    utilidad = ingreso_total - egreso_total
    
    st.markdown("---")
    if utilidad > 0:
        st.success(f"PROYECTO RENTABLE")
    else:
        st.error(f"RIESGO DE PÉRDIDA")
        
    st.metric("UTILIDAD NETA ESTIMADA", f"₡{utilidad:,.2f}", 
              delta=f"{((utilidad/egreso_total)*100 if egreso_total > 0 else 0):.1f}% ROI")

# --- PESTAÑA IA ---
with t_ia:
    st.header("🤖 Consultor Técnico IA")
    pregunta = st.text_area("Haga una consulta técnica (Ej: ¿Cómo afecta el clima el precio de la papa?):")
    
    if st.button("ANALIZAR CON GEMINI"):
        if pregunta:
            try:
                # Conexión con la llave proporcionada por el usuario
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Contexto enriquecido para la IA
                contexto = f"Actúa como un experto agrícola en Cartago, Costa Rica. Datos técnicos: Utilidad proyectada ₡{utilidad}. Pregunta del usuario: {pregunta}"
                
                with st.spinner('Conectando con el cerebro de Google...'):
                    response = model.generate_content(contexto)
                    st.write("---")
                    st.markdown("### 💡 Recomendación PAIC:")
                    st.info(response.text)
            except Exception as e:
                st.error(f"Error de conexión con la IA: {e}")
