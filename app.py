import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 📸 RUTAS DIRECTAS (Ajustadas a tu usuario de GitHub)
# Nota: Si cambias el nombre de tu usuario o repo, solo ajusta estas URLs
repo_base = "https://raw.githubusercontent.com/glensoto7-cyber/PAIC_Proyecto/main/assets/"
banner_url = repo_base + "agricultores.jpg"
papa_url = repo_base + "agricultor.jpg"
cebolla_url = repo_base + "cebolla%20imagen.jpeg" # El %20 es por el espacio en el nombre

st.markdown(f"""
    <style>
    .hero-banner {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('{banner_url}');
        background-size: cover;
        background-position: center;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
    }}
    .product-card {{
        background-size: cover;
        background-position: center;
        height: 220px;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding: 15px;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        background-repeat: no-repeat;
    }}
    .overlay {{
        background: rgba(0, 0, 0, 0.6);
        padding: 10px;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Falta API Key en Secrets.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        u_f = df['Fecha'].max()
        fechas_p = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = [{'Fecha': f, 
                 'Papa Blanca (quintal)': df[df['Fecha'].dt.month == f.month].mean(numeric_only=True)['Papa Blanca (quintal)'] * 1.03,
                 'Cebolla Amarilla (Kg)': df[df['Fecha'].dt.month == f.month].mean(numeric_only=True)['Cebolla Amarilla (Kg)'] * 1.03,
                 'Fresa (Kg)': df[df['Fecha'].dt.month == f.month].mean(numeric_only=True)['Fresa (Kg)'] * 1.03,
                 'Origen': 'Proyección'} for f in fechas_p]
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except: return None

df = cargar_datos()

if df is not None:
    # Sidebar
    st.sidebar.title("🎮 Panel PAIC")
    prod_sel = st.sidebar.selectbox("Producto:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    mes_proy = st.sidebar.select_slider("Proyección:", options=df[df['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # Banner
    st.markdown(f'<div class="hero-banner">🌱 PAIC - Cartago 2026</div>', unsafe_allow_html=True)

    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📈 HISTORIAL", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI (IA)"])

    real_f = df[df['Origen']=='Real'].iloc[-1]
    proy_f = df[df['Fecha'] == pd.to_datetime(mes_proy)].iloc[0]

    with tabs[0]:
        st.subheader("Estado de Cultivos")
        c1, c2, c3 = st.columns(3)
        
        # Papa Card
        c1.markdown(f"""<div class="product-card" style="background-image: url('{papa_url}');">
            <div class="overlay"><b>PAPA BLANCA</b><br>₡{real_f['Papa Blanca (quintal)']:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        
        # Cebolla Card
        c2.markdown(f"""<div class="product-card" style="background-image: url('{cebolla_url}');">
            <div class="overlay"><b>CEBOLLA AMARILLA</b><br>₡{real_f['Cebolla Amarilla (Kg)']:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        
        # Fresa (Metric normal hasta que subas foto)
        c3.metric("FRESA (Kg)", f"₡{real_f['Fresa (Kg)']:,.0f}")

    # Pestañas funcionales
    with tabs[1]: st.plotly_chart(px.bar(x=['Hoy', mes_proy], y=[real_f[prod_sel], proy_f[prod_sel]], color=['Hoy', 'Futuro']), use_container_width=True)
    with tabs[2]: st.plotly_chart(px.line(df[df['Fecha'] <= pd.to_datetime(mes_proy)], x="Fecha", y=prod_sel, color="Origen"), use_container_width=True)
    with tabs[3]: 
        m_num = pd.to_datetime(mes_proy).month
        st.plotly_chart(px.imshow(df[df['Origen']=='Real'].groupby(df['Fecha'].dt.month).mean(numeric_only=True)[[prod_sel]].T, color_continuous_scale='RdYlGn'), use_container_width=True)
        st.info(f"Análisis Mes {m_num}: {'Excelente para vender' if proy_f[prod_sel] > real_f[prod_sel] else 'Precio promedio'}")
    with tabs[4]:
        st.subheader("Calculadora Modular")
        costos = st.number_input("Costos Totales (₡)", value=500000)
        ha = st.slider("Hectáreas", 0.1, 5.0, 1.0)
        util = (ha * 600 * real_f[prod_sel]) - costos
        st.metric("Utilidad Estimada", f"₡{util:,.2f}")
    with tabs[5]:
        msg = st.chat_input("Consulta a Agri...")
        if msg:
            res = client.chat.completions.create(messages=[{"role":"system","content":"Eres Agri, agrónomo de Cartago."}, {"role":"user","content":msg}], model="llama-3.3-70b-versatile")
            st.write(res.choices[0].message.content)

else:
    st.error("Error al cargar datos. Verifique el Excel.")
