import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO AVANZADO (CSS INYECTADO) ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 📸 RUTAS DIRECTAS DE GITHUB (Sincronizadas con tus archivos reales)
repo_base = "https://raw.githubusercontent.com/glensoto7-cyber/PAIC_Proyecto/main/assets/"
banner_url = repo_base + "agricultores.jpg"
papa_url = repo_base + "agricultor.jpg"
cebolla_url = repo_base + "cebolla%20imagen.jpeg" # Manejo del espacio en el nombre
fresa_url = repo_base + "fresa.jpg" # NUEVA FOTO ACTIVADA

st.markdown(f"""
    <style>
    /* Fondo Global de Finca (Usando foto de trabajo) */
    .stApp {{
        background-color: #fdfdfd;
    }}
    
    /* Hero Banner Principal con Título Flotante */
    .hero-banner {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('{banner_url}');
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
    
    .hero-text {{
        color: white;
        font-size: 3rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}

    /* Tarjetas de Producto Visuales (DASHBOARD) */
    .product-card {{
        background-size: cover;
        background-position: center;
        height: 250px;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        justify-content: flex-end; /* Texto abajo */
        padding: 20px;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: transform 0.3s;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }}
    
    .product-card:hover {{
        transform: scale(1.03);
    }}
    
    /* Superposición oscura para que se lea el texto */
    .product-overlay {{
        position: absolute;
        bottom: 0; left: 0; right: 0; top: 0;
        background: linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,0.8));
        border-radius: 15px;
        z-index: 1;
    }}
    
    .product-text-container {{
        z-index: 2; /* Encima del overlay */
    }}
    
    .product-title-visual {{
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
        text-transform: uppercase;
    }}
    
    .product-price-visual {{
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        color: #f1f8e9;
    }}

    /* Estilo de Pestañas Uniformes */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #E8F5E9;
        border-radius: 10px;
        padding: 10px 20px;
        color: #1B5E20;
        font-weight: bold;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #1B5E20 !important;
        color: white !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Error: Revise su GROQ_API_KEY en Secrets.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def motor_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        
        # Generar Proyecciones Simples
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
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None

df = motor_datos()

if df is not None:
    # --- SIDEBAR DE CONTROL ---
    st.sidebar.title("🎮 Panel PAIC")
    prod_sel = st.sidebar.selectbox("Producto Principal:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    
    # Horizonte de proyección hasta fin de 2027
    mes_proy = st.sidebar.select_slider("Horizonte de Proyección:", options=df[df['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # --- 1. HERO BANNER PRINCIPAL ---
    st.markdown(f"""
        <div class="hero-banner">
            <div class="hero-text">🌱 PAIC - Cartago 2026</div>
        </div>
        """, unsafe_allow_html=True)
    
    tabs = st.tabs(["🏠 DASHBOARD VISUAL", "📊 COMPARATIVA", "📉 HISTORIAL/PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI (IA)"])

    real_f = df[df['Origen']=='Real'].iloc[-1]
    proy_f = df[df['Fecha'] == pd.to_datetime(mes_proy)].iloc[0]

    # --- 1. DASHBOARD VISUAL (NUEVO DISEÑO PREMIUM) ---
    with tabs[0]:
        st.subheader("Estado Actual de los Cultivos Clave (Con Fotos Reales)")
        col_p, col_c, col_f = st.columns(3)
        
        # TARJETA VISUAL PAPA (agricultor.jpg)
        with col_p:
            st.markdown(f"""
                <div class="product-card" style="background-image: url('{papa_url}');">
                    <div class="product-overlay"></div>
                    <div class="product-text-container">
                        <p class="product-title-visual">PAPA BLANCA</p>
                        <p class="product-price-visual">₡{real_f['Papa Blanca (quintal)']:,.0f}</p>
                        <small>(Quintal)</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # TARJETA VISUAL CEBOLLA (cebolla imagen.jpeg)
        with col_c:
            st.markdown(f"""
                <div class="product-card" style="background-image: url('{cebolla_url}');">
                    <div class="product-overlay"></div>
                    <div class="product-text-container">
                        <p class="product-title-visual">CEBOLLA AMARILLA</p>
                        <p class="product-price-visual">₡{real_f['Cebolla Amarilla (Kg)']:,.0f}</p>
                        <small>(Kilo)</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        # TARJETA VISUAL FRESA (fresa.jpg) - ¡ACTIVADA!
        with col_f:
            st.markdown(f"""
                <div class="product-card" style="background-image: url('{fresa_url}');">
                    <div class="product-overlay"></div>
                    <div class="product-text-container">
                        <p class="product-title-visual">FRESA</p>
                        <p class="product-price-visual">₡{real_f['Fresa (Kg)']:,.0f}</p>
                        <small>(Kilo)</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.info("💡 Estas tarjetas visuales usan las fotografías reales de los agricultores de Cartago, cortesía de la comunidad PAIC.")

    # Resto de pestañas (sin cambios técnicos, funcionando con el motor sincronizado)
    with tabs[1]: st.plotly_chart(px.bar(x=['Hoy', mes_proy], y=[real_f[prod_sel], proy_f[prod_sel]], color=['Hoy', 'Futuro'], text_auto='.2s'), use_container_width=True)
    with tabs[2]: st.plotly_chart(px.line(df[df['Fecha'] <= pd.to_datetime(mes_proy)], x="Fecha", y=prod_sel, color="Origen", markers=True), use_container_width=True)
    with tabs[3]: st.plotly_chart(px.imshow(df[df['Origen']=='Real'].groupby(df['Fecha'].dt.month).mean(numeric_only=True)[[prod_sel]].T, color_continuous_scale='RdYlGn', text_auto=True), use_container_width=True)
    with tabs[4]: st.metric("UTILIDAD NETA ESTIMADA", f"₡{( (st.number_input('Hectáreas', value=1.0) * 600 * st.slider('Precio de Venta (₡)', 1000, 30000, int(real_f[prod_sel])) ) - st.number_input('Costos Totales ₡', value=500000) ):,.2f}")
    with tabs[5]:
        msg = st.chat_input("Pregunte a Agri...")
        if msg:
            res = client.chat.completions.create(messages=[{"role":"system","content":"Eres Agri, experto agrónomo de Cartago. Responde breve."}, {"role":"user","content":msg}], model="llama-3.3-70b-versatile")
            st.chat_message("assistant").write(res.choices[0].message.content)
