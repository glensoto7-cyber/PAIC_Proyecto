import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago", layout="wide", page_icon="🌱")

# Tu clave API que ya validamos
LLAVE_PAIC = "AQ.Ab8RN6KbGWiFXRO2zRRDzP6jz2dvgrd3MzPUnjAwPLx5TzfZ1A"

# --- 2. MOTOR DE DATOS REFORZADO ---
@st.cache_data
def cargar_datos_con_prediccion():
    try:
        # 1. Leer el archivo (Asegúrate que el nombre en GitHub sea idéntico)
        archivo = "Precios historicos 15 ABRIL.xlsx"
        df = pd.read_excel(archivo, engine='openpyxl')
        
        # 2. Limpieza de fechas
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        # 3. Lógica de Predicción Real (2026-2027)
        ultima_f = df['Fecha'].max()
        # Creamos un rango de fechas desde hoy hasta dic 2027
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        
        lista_proy = []
        for i, fecha in enumerate(fechas_proy):
            mes_objetivo = fecha.month
            # Sacamos el promedio histórico de ese mes para mantener la estacionalidad de Cartago
            promedios = df[df['Fecha'].dt.month == mes_objetivo].mean(numeric_only=True)
            
            # Aplicamos un factor de tendencia (inflación leve del 0.3% mensual)
            factor = 1 + (i * 0.003)
            
            lista_proy.append({
                'Fecha': fecha,
                'Papa Blanca (quintal)': promedios['Papa Blanca (quintal)'] * factor,
                'Cebolla Amarilla (Kg)': promedios['Cebolla Amarilla (Kg)'] * factor,
                'Fresa (Kg)': promedios['Fresa (Kg)'] * factor,
                'Origen': 'Predicción PAIC 2027'
            })
        
        df['Origen'] = 'Histórico Real'
        df_completo = pd.concat([df, pd.DataFrame(lista_proy)], ignore_index=True)
        return df_completo, None
    except Exception as e:
        return None, str(e)

# Ejecutar carga
df_final, error_log = cargar_datos_con_prediccion()

# --- 3. INTERFAZ DE USUARIO ---
st.title("🌱 Plataforma Agro-Inteligente Cartago")

if error_log:
    st.error(f"❌ Error Crítico: No se pudo procesar el historial.")
    st.warning(f"Detalle técnico: {error_log}")
    st.info("Revisa que el archivo 'Precios historicos 15 ABRIL.xlsx' esté en la carpeta principal de GitHub.")
else:
    t_inicio, t_proy, t_calc, t_ia = st.tabs(["🏠 INICIO", "🔮 PREDICCIONES 2027", "🧮 CALCULADORA", "🤖 CONSULTOR IA"])

    with t_inicio:
        st.header("📊 Situación Actual del Mercado")
        actual = df_final[df_final['Origen'] == 'Histórico Real'].iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Papa (Quintal)", f"₡{actual['Papa Blanca (quintal)']:,.0f}")
        c2.metric("Cebolla (Kg)", f"₡{actual['Cebolla Amarilla (Kg)']:,.0f}")
        c3.metric("Fresa (Kg)", f"₡{actual['Fresa (Kg)']:,.0f}")
        
        # Gráfico histórico
        fig = px.line(df_final[df_final['Origen'] == 'Histórico Real'], x='Fecha', 
                      y=['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'],
                      title="Evolución Histórica de Precios")
        st.plotly_chart(fig, use_container_width=True)

    with t_proy:
        st.header("🔮 Proyección de Precios Horizonte 2027")
        producto = st.selectbox("Seleccione producto para ver la predicción:", 
                                ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
        
        fig_proy = px.line(df_final, x='Fecha', y=producto, color='Origen',
                          title=f"Tendencia Esperada: {producto}",
                          color_discrete_map={'Histórico Real': 'blue', 'Predicción PAIC 2027': 'red'})
        st.plotly_chart(fig_proy, use_container_width=True)

    with t_calc:
        st.header("🧮 Simulador de Rentabilidad")
        col1, col2 = st.columns(2)
        hectareas = col1.number_input("Hectáreas:", value=1.0)
        p_venta = col2.number_input("Precio Venta Sugerido ₡:", value=int(actual['Papa Blanca (quintal)']))
        costos = col1.number_input("Costos de Producción ₡:", value=500000)
        
        utilidad = (hectareas * 600 * p_venta) - costos
        st.metric("UTILIDAD ESTIMADA", f"₡{utilidad:,.2f}")

    with t_ia:
        st.header("🤖 Consultor IA")
        pregunta = st.text_input("Pregunte a la IA sobre estos datos:")
        if st.button("ANALIZAR"):
            try:
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Soy agricultor en Cartago. Utilidad: {utilidad}. Precios: {actual.to_dict()}. Pregunta: {pregunta}")
                st.info(res.text)
            except Exception as e:
                st.error(f"Error de conexión con IA: {e}")
