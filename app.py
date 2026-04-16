import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .branding-banner { 
        background-color: #1B5E20; 
        padding: 15px; 
        color: white; 
        text-align: center; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        font-size: 1.8rem; 
        font-weight: bold; 
    }
    .metric-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
        border-top: 8px solid #1B5E20; 
        text-align: center; 
    }
    /* Estilo para las pestañas */
    .stTabs [data-baseweb="tab"] {
        font-weight: bold;
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Error: Configure la API Key en los secretos de Streamlit.")

# --- LÓGICA DE FOTOS (TU REPOSITORIO) ---
assets = "assets"
fotos = {
    "banner": os.path.join(assets, "agricultores.jpg"),
    "Papa Blanca (quintal)": os.path.join(assets, "agricultor.jpg"),
    "Cebolla Amarilla (Kg)": os.path.join(assets, "cebolla imagen.jpeg"),
    "Fresa (Kg)": os.path.join(assets, "fresa.jpg")
}

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        u_f = df['Fecha'].max()
        fechas_p = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for i, f in enumerate(fechas_p):
            m = f.month
            proms = df[df['Fecha'].dt.month == m].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 'Papa Blanca (quintal)': proms['Papa Blanca (quintal)'] * 1.03,
                'Cebolla Amarilla (Kg)': proms['Cebolla Amarilla (Kg)'] * 1.03,
                'Fresa (Kg)': proms['Fresa (Kg)'] * 1.03, 'Origen': 'Proyección'
            })
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except: return None

df = cargar_datos()

if df is not None:
    # --- SIDEBAR CONTROL ---
    st.sidebar.title("🎮 Panel PAIC")
    prod_sel = st.sidebar.selectbox("Producto:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    
    # Foto del producto en la barra lateral
    if os.path.exists(fotos[prod_sel]):
        st.sidebar.image(fotos[prod_sel], use_container_width=True)

    mes_proy = st.sidebar.select_slider("Proyectar hasta:", options=df[df['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # --- BRANDING ---
    st.markdown("<div class='branding-banner'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)
    
    # Banner principal (agricultores.jpg)
    if os.path.exists(fotos["banner"]):
        st.image(fotos["banner"], use_container_width=True, caption="Impulsando el agro de Cartago.")

    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTORIAL", "🔮 PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI (IA)"])

    real_f = df[df['Origen']=='Real'].iloc[-1]
    proy_f = df[df['Fecha'] == pd.to_datetime(mes_proy)].iloc[0]

    # --- 1. DASHBOARD ---
    with tabs[0]:
        st.subheader(f"Resumen Actual: {prod_sel}")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Precio Hoy", f"₡{real_f[prod_sel]:,.0f}")
        c2.metric("🔮 En {0}".format(mes_proy), f"₡{proy_f[prod_sel]:,.0f}")
        var = ((proy_f[prod_sel]/real_f[prod_sel])-1)*100
        c3.metric("📈 Variación", f"{var:+.1f}%")

    # --- 2. COMPARATIVA ---
    with tabs[1]:
        st.plotly_chart(px.bar(x=['Hoy', mes_proy], y=[real_f[prod_sel], proy_f[prod_sel]], color=['Hoy', 'Futuro'], title="Comparativa Directa"), use_container_width=True)

    # --- 3. HISTÓRICO ---
    with tabs[2]:
        df_real = df[df['Origen']=='Real']
        st.plotly_chart(px.line(df_real, x="Fecha", y=prod_sel, markers=True, title="Historial de Precios Registrados"), use_container_width=True)

    # --- 4. PREDICCIÓN ---
    with tabs[3]:
        df_pred = df[df['Fecha'] <= pd.to_datetime(mes_proy)]
        st.plotly_chart(px.line(df_pred, x="Fecha", y=prod_sel, color="Origen", title="Curva de Proyección 2026-2027"), use_container_width=True)

    # --- 5. PATRONES ---
    with tabs[4]:
        st.subheader("Mapa de Estacionalidad")
        df_h = df[df['Origen']=='Real'].copy()
        df_h['Mes'] = df_h['Fecha'].dt.month
        heat = df_h.groupby('Mes').mean(numeric_only=True)[[prod_sel]]
        st.plotly_chart(px.imshow(heat.T, color_continuous_scale='RdYlGn', text_auto=True), use_container_width=True)

    # --- 6. CALCULADORA ---
    with tabs[5]:
        st.subheader("Simulador de Rentabilidad Modular")
        with st.expander("💼 Desglose de Costos", expanded=True):
            col1, col2 = st.columns(2)
            ins = col1.number_input("Insumos y Semillas (₡)", value=300000)
            jornal = col1.number_input("Mano de Obra (₡)", value=150000)
            flete = col2.number_input("Logística y Flete (₡)", value=50000)
            otros = col2.number_input("Otros Gastos (₡)", value=20000)
        
        ha = st.slider("Hectáreas", 0.1, 10.0, 1.0)
        p_v = st.slider("Precio Venta (₡)", 1000, 30000, int(real_f[prod_sel]))
        
        costo_t = ins + jornal + flete + otros
        util = (ha * 600 * p_v) - costo_t
        st.metric("UTILIDAD NETA", f"₡{util:,.2f}", f"{(util/costo_t)*100:.1f}% ROI")

    # --- 7. AGRI ---
    with tabs[6]:
        st.subheader("🤖 Agri - Tu Asistente Inteligente")
        msg = st.chat_input("Escribe tu consulta aquí...")
        if msg:
            res = client.chat.completions.create(
                messages=[{"role":"system","content":"Eres Agri, experto agrónomo de Cartago. Responde breve."}, {"role":"user","content":msg}],
                model="llama-3.3-70b-versatile"
            )
            st.chat_message("assistant").write(res.choices[0].message.content)

# Pie de página
st.markdown("---")
st.caption("PAIC - Cartago 2026 | Sistema de Inteligencia para el Agricultor")
