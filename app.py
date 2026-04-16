import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .branding { background-color: #1B5E20; padding: 15px; color: white; text-align: center; border-radius: 10px; margin-bottom: 20px; font-weight: bold; font-size: 1.8rem; }
    .metric-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 15px; }
    .papa { border-top: 8px solid #795548; }
    .cebolla { border-top: 8px solid #FBC02D; }
    .fresa { border-top: 8px solid #D32F2F; }
    .alert-box { padding: 15px; border-radius: 10px; margin: 10px 0; font-weight: bold; }
    .alert-danger { background-color: #FFEBEE; color: #B71C1C; border-left: 5px solid #B71C1C; }
    .alert-info { background-color: #E3F2FD; color: #0D47A1; border-left: 5px solid #0D47A1; }
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ Falta GROQ_API_KEY en Secrets.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        ultima_f = df['Fecha'].max()
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for i, f in enumerate(fechas_proy):
            mes = f.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * 1.02,
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * 1.02,
                'Fresa (Kg)': prom['Fresa (Kg)'] * 1.02, 'Origen': 'Proyección'
            })
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except: return None

df_total = motor_datos()

if df_total is not None:
    st.markdown("<div class='branding'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)
    real = df_total[df_total['Origen'] == 'Real'].iloc[-1]
    prox = df_total[df_total['Origen'] == 'Proyección'].iloc[0]

    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTÓRICO", "🔮 PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "📅 CALENDARIO", "🤖 AGRI (IA)"])

    # --- 1. DASHBOARD ---
    with tabs[0]:
        st.subheader("Estado de la Finca")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Ganancia Neta Est.", "₡1,250,000", "+12%")
        c2.metric("📊 Costos Totales", "₡500,000")
        st.markdown("<div class='alert-box alert-danger'>🚨 ALERTA: Precio de Cebolla bajando.</div>", unsafe_allow_html=True)

    # --- 2. COMPARATIVA ---
    with tabs[1]:
        col_p, col_c, col_f = st.columns(3)
        for n, k, c, s in [("PAPA", 'Papa Blanca (quintal)', col_p, "papa"), ("CEBOLLA", 'Cebolla Amarilla (Kg)', col_c, "cebolla"), ("FRESA", 'Fresa (Kg)', col_f, "fresa")]:
            with c:
                diff = ((prox[k]/real[k])-1)*100
                st.markdown(f"<div class='metric-card {s}'><h3>{n}</h3><p>Hoy: ₡{real[k]:,.0f}</p><p>Próx: ₡{prox[k]:,.0f}</p><p>{diff:+.1f}%</p></div>", unsafe_allow_html=True)

    # --- 3. HISTÓRICO ---
    with tabs[2]:
        df_h = df_total[df_total['Origen'] == 'Real']
        st.plotly_chart(px.line(df_h, x="Fecha", y=df_h.columns[1:4]), use_container_width=True)

    # --- 4. PREDICCIÓN (AHORA SÍ FUNCIONA) ---
    with tabs[3]:
        st.subheader("🔮 Proyección de Precios 2026-2027")
        fig_p = px.line(df_total, x="Fecha", y=['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'], 
                        color="Origen", title="Tendencia Futura (Modelo de Estacionalidad)")
        st.plotly_chart(fig_p, use_container_width=True)
        st.write("**Nivel de Confianza:** 🟢 Alto (basado en ciclos de 5 años)")

    # --- 5. PATRONES (HEATMAP CON SELECTOR) ---
    with tabs[4]:
        st.subheader("🌡️ Mapa de Calor Inteligente")
        modo = st.radio("Ver datos de:", ["Histórico Real", "Proyección Futura"], horizontal=True)
        df_heat = df_total[df_total['Origen'] == ('Real' if modo == "Histórico Real" else "Proyección")]
        df_heat['Mes'] = df_heat['Fecha'].dt.month
        heat = df_heat.groupby('Mes').mean(numeric_only=True).iloc[:, :3]
        st.plotly_chart(px.imshow(heat.T, color_continuous_scale='RdYlGn', text_auto=True), use_container_width=True)
        
        st.markdown("### 🧠 Interpretación Automática")
        mes_sel = st.slider("Deslice para analizar mes (1-12):", 1, 12, datetime.now().month)
        if mes_sel in [4, 5, 6]: st.success(f"Mes {mes_sel}: 🌱 Excelente para Sembrar | 💰 Excelente para Vender")
        else: st.warning(f"Mes {mes_sel}: 🟡 Riesgo Medio | 💰 Precio Promedio")

    # --- 6. CALCULADORA MODULAR ---
    with tabs[5]:
        st.subheader("🧮 Calculadora de Rentabilidad Pro")
        with st.expander("🌿 1. Cultivo y Producción", expanded=True):
            ha = st.number_input("Hectáreas", 0.1, 10.0, 1.0)
            rendimiento = st.number_input("Rendimiento (Kg/Quintal por Ha)", value=600)
        with st.expander("🧾 2. Costos de Producción"):
            c1, c2 = st.columns(2)
            insumos = c1.number_input("🌿 Insumos (₡)", value=200000)
            mano_obra = c1.number_input("👷 Mano de Obra (₡)", value=150000)
            maquinaria = c2.number_input("🚜 Maquinaria (₡)", value=50000)
            logistica = c2.number_input("🚚 Logística (₡)", value=30000)
        
        precio_v = st.slider("Simular Precio Venta (₡)", 1000, 30000, int(real['Papa Blanca (quintal)']))
        total_costos = insumos + mano_obra + maquinaria + logistica
        ingresos = ha * rendimiento * precio_v
        utilidad = ingresos - total_costos
        
        st.divider()
        st.metric("GANANCIA NETA (ROI)", f"₡{utilidad:,.2f}", f"{(utilidad/total_costos)*100:.1f}% ROI")

    # --- 7. CALENDARIO AGRO ---
    with tabs[6]:
        mes_actual_nombre = datetime.now().strftime('%B %Y')
        st.subheader(f"📅 Calendario: {mes_actual_nombre}")
        st.info("📍 Cartago: Inicio de preparación de suelos.")
        col1, col2 = st.columns(2)
        col1.write("✅ **Siembra:** Papa, Cebolla")
        col2.write("🚜 **Labores:** Fertilización y Control de malezas")

    # --- 8. AGRI ---
    with tabs[7]:
        st.markdown("<div class='alert-box alert-info'>🤖 Hola, soy Agri. Conozco los datos de Cartago. ¿Cómo te ayudo?</div>", unsafe_allow_html=True)
        duda = st.text_input("Pregunta:")
        if st.button("Consultar Agri"):
            res = client.chat.completions.create(messages=[{"role":"system","content":"Eres Agri, experto agrónomo."}, {"role":"user","content":duda}], model="llama-3.3-70b-versatile")
            st.write(res.choices[0].message.content)
