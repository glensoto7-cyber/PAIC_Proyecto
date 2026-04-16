import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO GLOBAL ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# Inyección de CSS Profesional (Diseño Centrado en Agricultores)
st.markdown("""
    <style>
    /* Estilo General */
    .main { background-color: #f8f9fa; }
    .stApp header { visibility: hidden; } /* Limpiar interfaz */
    
    /* Branding Persistente */
    .branding {
        background-color: #1B5E20;
        padding: 10px;
        color: white;
        text-align: center;
        border-radius: 0 0 15px 15px;
        margin-bottom: 20px;
        font-weight: bold;
        font-size: 1.5rem;
    }

    /* Tarjetas del Dashboard y Comparativa */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-top: 5px solid #1B5E20;
        text-align: center;
    }
    .fresa { border-top: 8px solid #D32F2F; }
    .cebolla { border-top: 8px solid #FBC02D; }
    .papa { border-top: 8px solid #795548; }
    
    /* Alertas */
    .alert-box {
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        font-weight: bold;
    }
    .alert-danger { background-color: #FFEBEE; color: #B71C1C; border-left: 5px solid #B71C1C; }
    .alert-info { background-color: #E3F2FD; color: #0D47A1; border-left: 5px solid #0D47A1; }

    /* Botones Grandes */
    .stButton>button {
        width: 100%;
        height: 3em;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- IA Y SEGURIDAD ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Error: Configure la API Key de Groq.")

# --- MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        ultima_f = df['Fecha'].max()
        # Generar Proyecciones
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for i, f in enumerate(fechas_proy):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 'Papa Blanca (quintal)': prom['Papa Blanca (quintal)']*1.02,
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)']*1.02,
                'Fresa (Kg)': prom['Fresa (Kg)']*1.02, 'Origen': 'Proyección'
            })
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except: return None

df_total = motor_datos()

# --- INTERFAZ PRINCIPAL ---
if df_total is not None:
    # Branding en todas las pestañas
    st.markdown("<div class='branding'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)

    # Navegación Principal (Iconos y Nombres Claros)
    tabs = st.tabs([
        "🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTÓRICO", 
        "🔮 PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", 
        "📅 CALENDARIO", "🤖 AGRI (IA)"
    ])

    # Variables globales de cálculo para simulador
    real = df_total[df_total['Origen'] == 'Real'].iloc[-1]
    prox = df_total[df_total['Origen'] == 'Proyección'].iloc[0]

    # --- 1. DASHBOARD ---
    with tabs[0]:
        st.subheader("Estado General de la Finca")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Ganancia Neta Est.", "₡1.2M", "12%")
        c2.metric("📊 Costos Totales", "₡850k")
        c3.metric("📈 Ingresos", "₡2.05M")
        c4.metric("📉 Margen", "58%")

        st.markdown("### 🚨 Alertas del Mercado")
        st.markdown("<div class='alert-box alert-danger'>⚠️ ALERTA: Precio de Cebolla en tendencia a la baja (-5%)</div>", unsafe_allow_html=True)
        st.markdown("<div class='alert-box alert-info'>ℹ️ INFO: Buen momento para fertilización según ciclo de lluvia</div>", unsafe_allow_html=True)

    # --- 2. COMPARATIVA INTELIGENTE ---
    with tabs[1]:
        st.subheader("Comparativa Mensual: Hoy vs Proyección")
        col_p, col_c, col_f = st.columns(3)
        productos = [
            ("PAPA BLANCA", 'Papa Blanca (quintal)', col_p, "papa"),
            ("CEBOLLA AMARILLA", 'Cebolla Amarilla (Kg)', col_c, "cebolla"),
            ("FRESA", 'Fresa (Kg)', col_f, "fresa")
        ]
        for nombre, key, col, css in productos:
            with col:
                diff = ((prox[key]/real[key])-1)*100
                color = "green" if diff > 0 else "red"
                st.markdown(f"""<div class='metric-card {css}'>
                    <h3>{nombre}</h3>
                    <p><b>Abril:</b> ₡{real[key]:,.0f}</p>
                    <p><b>Mayo (Proy.):</b> ₡{prox[key]:,.0f}</p>
                    <p style='color:{color}; font-weight:bold;'>{diff:+.1f}% {'🔼' if diff>0 else '🔽'}</p>
                </div>""", unsafe_allow_html=True)

    # --- 3. HISTÓRICO INTERACTIVO ---
    with tabs[2]:
        st.subheader("Exploración de Datos")
        df_real = df_total[df_total['Origen'] == 'Real']
        st.plotly_chart(px.line(df_real, x="Fecha", y=df_real.columns[1:4], markers=True), use_container_width=True)
        st.dataframe(df_real, use_container_width=True)

    # --- 5. PATRONES (HEATMAP) ---
    with tabs[4]:
        st.subheader("Mapa de Calor Inteligente")
        df_real['MesNum'] = df_real['Fecha'].dt.month
        heatmap = df_real.groupby('MesNum').mean(numeric_only=True).iloc[:, :3]
        fig_h = px.imshow(heatmap.T, color_continuous_scale='RdYlGn', labels=dict(x="Mes", y="Producto"))
        st.plotly_chart(fig_h, use_container_width=True)
        
        sel_mes = st.selectbox("Seleccione un mes para ver recomendaciones:", range(1,13))
        if sel_mes in [4, 5, 6]:
            st.success("🌱 SIEMBRA: Mes Excelente | 💰 VENTA: Precios Altos")
        else:
            st.warning("🟡 SIEMBRA: Riesgo Medio | 💰 VENTA: Precios Promedio")

    # --- 6. CALCULADORA Y SIMULADOR ---
    with tabs[5]:
        st.subheader("🧮 Calculadora de Rentabilidad Modular")
        with st.form("calc"):
            c_ha, c_ins, c_mano = st.columns(3)
            hectareas = c_ha.number_input("Hectáreas", value=1.0)
            insumos = c_ins.number_input("Costo Insumos (₡)", value=200000)
            mano_obra = c_mano.number_input("Mano de Obra (₡)", value=150000)
            
            p_v_sim = st.slider("Simular Precio Venta (₡)", min_value=1000, max_value=30000, value=int(real[1]))
            if st.form_submit_button("CALCULAR"):
                utilidad = (hectareas * 600 * p_v_sim) - (insumos + mano_obra)
                st.metric("GANANCIA NETA SIMULADA", f"₡{utilidad:,.2f}")

    # --- 7. CALENDARIO ---
    with tabs[6]:
        st.subheader("📅 Calendario Agrícola Cartago")
        st.info("Abril: Inicio de preparación de suelos en Tierra Blanca y Llano Grande.")
        st.write("- **Papa:** Época de cosecha fuerte.")
        st.write("- **Cebolla:** Monitoreo de humedad.")

    # --- 8. ASISTENTE AGRI ---
    with tabs[7]:
        st.markdown(f"""<div style='background-color:#E8F5E9; padding:20px; border-radius:15px; border-left:10px solid #2E7D32;'>
            <h4>🤖 Hola, soy Agri</h4>
            <p>Conozco los patrones de Cartago y el historial de precios. ¿En qué te ayudo hoy?</p>
        </div>""", unsafe_allow_html=True)
        
        pregunta = st.text_input("Pregunta a Agri (ej: ¿Es buen momento para vender papa?)")
        if st.button("CONSULTAR A AGRI"):
            res = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres Agri, experto agrónomo de Cartago. Responde breve y directo."},
                    {"role": "user", "content": f"Datos: Papa ₡{real[1]}. Pregunta: {pregunta}"}
                ],
                model="llama-3.3-70b-versatile",
            )
            st.success(res.choices[0].message.content)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.caption("PAIC - Cartago 2026 | Sistema de Apoyo al Agricultor")
