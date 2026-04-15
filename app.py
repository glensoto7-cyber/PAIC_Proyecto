import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="PAIC - Cartago", layout="wide")
st.title("🌱 Plataforma Agro-Inteligente Cartago (PAIC)")
st.markdown("Apoyo a la toma de decisiones para productores de Cartago.")

# --- 2. CARGA DE DATOS (CORREGIDO PARA EXCEL) ---
@st.cache_data
def cargar_datos():
    # El nombre debe ser idéntico al que subiste a GitHub
    nombre_archivo = "Precios historicos 15 ABRIL.xlsx"
    # Cargamos el Excel usando openpyxl
    df = pd.read_excel(nombre_archivo, engine='openpyxl')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df

try:
    df = cargar_datos()
    ultimo = df.iloc[-1]
    promedio = df.mean(numeric_only=True)
except Exception as e:
    st.error(f"⚠️ Error al cargar el archivo de Excel: {e}")
    st.info("Asegúrate de que el archivo se llame exactamente 'Precios historicos 15 ABRIL.xlsx' en tu GitHub.")
    st.stop()

# --- 3. CREACIÓN DE LAS PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📊 Semáforo de Precios", "🧮 Calculadora de Costos", "🤖 Asistente IA"])

with tab1:
    st.header("Estado de Precios (CENADA)")
    st.write("Precios actuales comparados con el promedio histórico de Cartago.")
    c1, c2, c3 = st.columns(3)
    
    def semaforo(act, prom):
        if act > prom * 1.1: return "🟢 ALTO"
        elif act < prom * 0.9: return "🔴 BAJO"
        else: return "🟡 NORMAL"
    
    c1.metric("Papa Blanca (Quintal)", f"₡{ultimo['Papa Blanca (quintal)']}", semaforo(ultimo['Papa Blanca (quintal)'], promedio['Papa Blanca (quintal)']))
    c2.metric("Cebolla Amarilla (Kg)", f"₡{ultimo['Cebolla Amarilla (Kg)']}", semaforo(ultimo['Cebolla Amarilla (Kg)'], promedio['Cebolla Amarilla (Kg)']))
    c3.metric("Fresa (Kg)", f"₡{ultimo['Fresa (Kg)']}", semaforo(ultimo['Fresa (Kg)'], promedio['Fresa (Kg)']))

with tab2:
    st.header("Calculadora de Producción")
    col_a, col_b = st.columns(2)
    with col_a:
        area = st.number_input("Área (hectáreas)", value=1.0)
        jornales = st.number_input("Cantidad de Jornales", value=10)
    with col_b:
        precio_jornal = st.number_input("Precio por Jornal (₡)", value=15000)
        otros_costos = st.number_input("Semillas y Fertilizantes (₡)", value=200000)
    
    total = (jornales * precio_jornal) + otros_costos
    st.success(f"### Costo Total Estimado: ₡{total:,.2f}")

with tab3:
    st.header("Asistente Agrícola con IA")
    st.write("Usa tu API Key de Gemini para recibir consejos basados en los datos.")
    clave = st.text_input("1. Pega aquí tu API Key de Gemini:", type="password")
    pregunta = st.text_area("2. Haz tu consulta (Ej: ¿Es buen momento para sembrar papa?)")
    
    if st.button("Consultar Asistente"):
        if clave and pregunta:
            try:
                genai.configure(api_key=clave)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                contexto = f"""
                Eres un experto agrícola de Cartago. 
                Precios actuales: Papa ₡{ultimo['Papa Blanca (quintal)']}, Cebolla ₡{ultimo['Cebolla Amarilla (Kg)']}, Fresa ₡{ultimo['Fresa (Kg)']}.
                Pregunta: {pregunta}
                Responde de forma sencilla y motivadora para el agricultor.
                """
                
                res = model.generate_content(contexto)
                st.info(res.text)
            except Exception as e:
                st.error(f"Error de conexión con Gemini: {e}")
        else:
            st.warning("Completa la clave y la pregunta.")
      
