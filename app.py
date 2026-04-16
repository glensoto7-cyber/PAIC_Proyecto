import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 🔒 SEGURIDAD: Intentar leer la clave desde los Secretos de Streamlit
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception:
    st.warning("⚠️ Configuración de seguridad pendiente: Inserte su GOOGLE_API_KEY en los Secretos de Streamlit Cloud.")

# --- Estilos de Semáforo ---
st.markdown("""
    <style>
    .rentable { color: #2E7D32; background-color: #E8F5E9; padding: 15px; border-radius: 10px; border: 2px solid #2E7D32; text-align: center; }
    .ajustado { color: #FBC02D; background-color: #FFFDE7; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #FBC02D; }
    .perdida { color: #D32F2F; background-color: #FFEBEE; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #D32F2F; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (CON PROTECCIÓN ILOC) ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        if df.empty: return "Archivo vacío"

        ultima_f = df['Fecha'].max()
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        
        proy = []
        for i, fecha in enumerate(fechas_proy):
            mes = fecha.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': fecha,
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * (1 + i * 0.002),
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * (1 + i * 0.002),
                'Fresa (Kg)': prom['Fresa (Kg)'] * (1 + i * 0.002),
                'Origen': 'Proyección PAIC'
            })
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return f"Error: {e}"

df_total = motor_datos()

# --- 3. INTERFAZ ---
if isinstance(df_total, str):
    st.error(f"Error en datos: {df_total}")
else:
    t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA PRO", "🤖 IA"])

    with t_inicio:
        st.header("🎯 Comparativa Mensual")
        # Protección de datos
        datos_reales = df_total[df_total['Origen'] == 'Histórico Real']
        if not datos_reales.empty:
            real = datos_reales.iloc[-1]
            prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            prods = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']
            for p, col in zip(prods, [c1, c2, c3]):
                var = ((prox[p] / real[p]) - 1) * 100
                col.metric(p, f"₡{real[p]:,.0f}", f"Próx: {prox[p]:,.0f} ({var:+.1f}%)")

    with t_calc:
        st.header("🧮 Simulador de Rentabilidad")
        with st.expander("Configuración", expanded=True):
            ha = st.number_input("Hectáreas:", value=1.0)
            precio = st.number_input("Precio Venta ₡:", value=int(real['Papa Blanca (quintal)']) if not datos_reales.empty else 15000)
            costos = st.number_input("Costos Totales ₡:", value=500000)
        
        utilidad = (ha * 600 * precio) - costos
        st.metric("GANANCIA NETA", f"₡{utilidad:,.2f}")

        if utilidad > 200000:
            st.markdown("<div class='rentable'><h3>🟢 RENTABLE</h3></div>", unsafe_allow_html=True)
        elif utilidad > 0:
            st.markdown("<div class='ajustado'><h3>🟡 AJUSTADO</h3></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='perdida'><h3>🔴 PÉRDIDA</h3></div>", unsafe_allow_html=True)

    with t_ia:
        st.header("🤖 Consultor PAIC Pro")
        pregunta = st.text_area("Escriba su consulta técnica:")
        
        # Validación de entrada y de Clave API
        if st.button("ANALIZAR ESCENARIO"):
            if not pregunta:
                st.warning("⚠️ Por favor, escriba una pregunta primero.")
            elif "GOOGLE_API_KEY" not in st.secrets:
                st.error("❌ No se encontró la API Key en los secretos de Streamlit.")
            else:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # Prompt mejorado (Ingeniería de Prompts)
                    prompt = f"""
                    Eres un experto agrónomo de Cartago, Costa Rica. 
                    Analiza los siguientes datos financieros de un agricultor:
                    - Utilidad: ₡{utilidad}
                    - Cultivo: Papa/Cebolla/Fresa
                    - Pregunta: {pregunta}
                    Proporciona consejos prácticos, cortos y basados en la realidad de Cartago.
                    """
                    with st.spinner('Consultando con Gemini...'):
                        res = model.generate_content(prompt)
                        st.info(res.text)
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
