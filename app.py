import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 📸 RUTAS DE TUS FOTOS (Ajustadas a tus nombres reales en GitHub)
repo_raw = "https://raw.githubusercontent.com/glensoto7-cyber/PAIC_Proyecto/main/assets/"

# Diccionario de fotos con los nombres EXACTOS de tu repositorio
fotos = {
    "banner": repo_raw + "agricultores.jpg",
    "Papa Blanca (quintal)": repo_raw + "agricultor.jpg",
    "Cebolla Amarilla (Kg)": repo_raw + "cebolla%20imagen.jpeg", # El %20 reemplaza el espacio
    "Fresa (Kg)": repo_raw + "Fresa.jpg" # Ojo con la F mayúscula si así está en GitHub
}

st.markdown(f"""
    <style>
    /* Hero Banner Principal */
    .hero-banner {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('{fotos["banner"]}');
        background-size: cover;
        background-position: center;
        height: 250px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    }}
    
    .hero-text {{ color: white; font-size: 3rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.7); }}

    /* Tarjetas de Producto Visuales */
    .product-card {{
        background-size: cover;
        background-position: center;
        height: 250px;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }}
    
    .product-overlay {{
        position: absolute;
        bottom: 0; left: 0; right: 0; top: 0;
        background: linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,0.8));
        z-index: 1;
    }}
    
    .product-text-container {{ z-index: 2; }}
    .product-title-visual {{ font-size: 1.5rem; font-weight: bold; margin: 0; }}
    .product-price-visual {{ font-size: 2.5rem; font-weight: bold; margin: 0; }}
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Falta GROQ_API_KEY en Secrets.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        u_f = df['Fecha'].max()
        fechas_p = pd.date_range(start=u_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy = []
        for f in fechas_p:
            proms = df[df['Fecha'].dt.month == f.month].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 'Papa Blanca (quintal)': proms['Papa Blanca (quintal)'] * 1.03,
                'Cebolla Amarilla (Kg)': proms['Cebolla Amarilla (Kg)'] * 1.03,
                'Fresa (Kg)': proms['Fresa (Kg)'] * 1.03, 'Origen': 'Proyección'
            })
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except: return None

df = motor_datos()

if df is not None:
    # --- INTERFAZ ---
    st.sidebar.title("🎮 Panel PAIC")
    prod_sel = st.sidebar.selectbox("Producto:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    mes_proy = st.sidebar.select_slider("Proyectar:", options=df[df['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # HERO BANNER
    st.markdown(f'<div class="hero-banner"><div class="hero-text">🌱 PAIC - Cartago 2026</div></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTORIAL", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI (IA)"])

    real_f = df[df['Origen']=='Real'].iloc[-1]
    proy_f = df[df['Fecha'] == pd.to_datetime(mes_proy)].iloc[0]

    with tabs[0]:
        st.subheader("Estado de Cultivos")
        col_p, col_c, col_f = st.columns(3)
        
        # Tarjeta Papa
        col_p.markdown(f"""<div class="product-card" style="background-image: url('{fotos['Papa Blanca (quintal)']}');">
            <div class="product-overlay"></div><div class="product-text-container">
            <p class="product-title-visual">PAPA BLANCA</p>
            <p class="product-price-visual">₡{real_f['Papa Blanca (quintal)']:,.0f}</p></div>
        </div>""", unsafe_allow_html=True)

        # Tarjeta Cebolla
        col_c.markdown(f"""<div class="product-card" style="background-image: url('{fotos['Cebolla Amarilla (Kg)']}');">
            <div class="product-overlay"></div><div class="product-text-container">
            <p class="product-title-visual">CEBOLLA AMARILLA</p>
            <p class="product-price-visual">₡{real_f['Cebolla Amarilla (Kg)']:,.0f}</p></div>
        </div>""", unsafe_allow_html=True)
        
        # Tarjeta Fresa
        col_f.markdown(f"""<div class="product-card" style="background-image: url('{fotos['Fresa (Kg)']}');">
            <div class="product-overlay"></div><div class="product-text-container">
            <p class="product-title-visual">FRESA</p>
            <p class="product-price-visual">₡{real_f['Fresa (Kg)']:,.0f}</p></div>
        </div>""", unsafe_allow_html=True)

    # Resto de pestañas
    with tabs[1]: st.plotly_chart(px.bar(x=['Hoy', mes_proy], y=[real_f[prod_sel], proy_f[prod_sel]], color=['Hoy', 'Futuro']), use_container_width=True)
    with tabs[2]: st.plotly_chart(px.line(df[df['Fecha'] <= pd.to_datetime(mes_proy)], x="Fecha", y=prod_sel, color="Origen"), use_container_width=True)
    with tabs[5]:
        msg = st.chat_input("Consulta a Agri...")
        if msg:
            res = client.chat.completions.create(messages=[{"role":"system","content":"Eres Agri, experto agrónomo de Cartago."}, {"role":"user","content":msg}], model="llama-3.3-70b-versatile")
            st.write(res.choices[0].message.content)

else:
    st.error("Error cargando el Excel.")
