import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 🔒 SEGURIDAD: Carga la llave desde los Secretos de Streamlit Cloud
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.warning("⚠️ Configuración pendiente: Inserte GOOGLE_API_KEY en Secrets de Streamlit.")
except Exception as e:
    st.error(f"Error de configuración: {e}")

# --- Estilos Visuales ---
st.markdown("""
    <style>
    .rentable { color: #2E7D32; background-color: #E8F5E9; padding: 15px; border-radius: 10px; border: 2px solid #2E7D32; text-align: center; }
    .ajustado { color: #FBC02D; background-color: #FFFDE7; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #FBC02D; }
    .perdida { color: #D32F2F; background-color: #FFEBEE; padding: 15px; border-radius: 10px; border: 2px solid #D32F2F; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        # Proyecciones a 2027
        u_f = df['Fecha'].max()
        fechas_proy = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for i, f in enumerate(fechas_proy):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * (1 + i * 0.002),
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * (1 + i * 0.002),
                'Fresa (Kg)': prom['Fresa (Kg)'] * (1 + i * 0.002), 
                'Origen': 'Proyección PAIC'
            })
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return str(e)

df_total = motor_datos()

# --- 3. INTERFAZ ---
if isinstance(df_total, str):
    st.error(f"Error en datos: {df_total}")
else:
    t1, t2, t3, t4, t5 = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA PRO", "🤖 IA"])

    with t1:
        st.header("🎯 Comparativa Mensual")
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
        c1, c2, c3 = st.columns(3)
        prods = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']
        for p, col in zip(prods, [c1, c2, c3]):
            v = ((prox[p]/real[p])-1)*100
            col.metric(p, f"₡{real[p]:,.0f}", f"Próx: {prox[p]:,.0f} ({v:+.1f}%)")

    with t4:
        st.header("🧮 Calculadora de Rentabilidad")
        with st.expander("Configuración del Cultivo", expanded=True):
            ha = st.number_input("Hectáreas:", value=1.0)
            p_v = st.number_input("Precio Venta ₡:", value=int(real['Papa Blanca (quintal)']))
            costos = st.number_input("Costos Totales ₡:", value=500000)
        
        utilidad = (ha * 600 * p_v) - costos
        st.metric("GANANCIA NETA", f"₡{utilidad:,.2f}")
        
        if utilidad > 200000: st.markdown("<div class='rentable'><h3>🟢 RENTABLE</h3></div>", unsafe_allow_html=True)
        elif utilidad > 0: st.markdown("<div class='ajustado'><h3>🟡 AJUSTADO</h3></div>", unsafe_allow_html=True)
        else: st.markdown("<div class='perdida'><h3>🔴 PÉRDIDA</h3></div>", unsafe_allow_html=True)

    with t5:
        st.header("🤖 Consultor IA PAIC")
        pregunta = st.text_area("Pregunta técnica para la IA:")
        
        if st.button("ANALIZAR ESCENARIO"):
            if pregunta and "GOOGLE_API_KEY" in st.secrets:
                try:
                    # CORRECCIÓN NotFound: Usar la ruta completa del modelo
                    model = genai.GenerativeModel('models/gemini-1.5-flash')
                    ctx = f"Eres experto agrónomo de Cartago. Utilidad calculada: ₡{utilidad}. Pregunta: {pregunta}"
                    
                    with st.spinner('Consultando a Gemini...'):
                        res = model.generate_content(ctx)
                        st.info(res.text)
                except Exception as e:
                    st.error(f"Falla en el modelo principal: {e}")
                    st.info("Intentando conectar con modelo de respaldo...")
                    try:
                        model_alt = genai.GenerativeModel('models/gemini-1.0-pro')
                        res_alt = model_alt.generate_content(ctx)
                        st.info(res_alt.text)
                    except:
                        st.error("No se pudo conectar con los servicios de Google. Verifique su API Key.")
            else:
                st.warning("Escriba su pregunta o configure la clave API en los Secrets.")
