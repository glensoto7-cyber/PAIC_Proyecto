import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# 📸 RUTAS DE GITHUB (Verificadas)
repo_raw = "https://raw.githubusercontent.com/glensoto7-cyber/PAIC_Proyecto/main/assets/"
fotos = {
    "banner": repo_raw + "agricultores.jpg",
    "Papa Blanca (quintal)": repo_raw + "agricultor.jpg",
    "Cebolla Amarilla (Kg)": repo_raw + "cebolla%20imagen.jpeg",
    "Fresa (Kg)": repo_raw + "Fresa.jpg"
}

st.markdown(f"""
    <style>
    .hero-banner {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('{fotos["banner"]}');
        background-size: cover; background-position: center; height: 200px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 15px; margin-bottom: 20px; color: white;
        font-size: 2.5rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
    }}
    .product-card {{
        background-size: cover; background-position: center; height: 220px;
        border-radius: 15px; display: flex; flex-direction: column;
        justify-content: flex-end; padding: 15px; color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3); margin-bottom: 20px;
    }}
    .overlay {{ background: rgba(0, 0, 0, 0.6); padding: 10px; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Falta API Key.")

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
        for f in fechas_p:
            proms = df[df['Fecha'].dt.month == f.month].mean(numeric_only=True)
            proy.append({
                'Fecha': f, 
                'Papa Blanca (quintal)': proms['Papa Blanca (quintal)'] * 1.03,
                'Cebolla Amarilla (Kg)': proms['Cebolla Amarilla (Kg)'] * 1.03,
                'Fresa (Kg)': proms['Fresa (Kg)'] * 1.03,
                'Origen': 'Proyección'
            })
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except: return None

df_total = cargar_datos()

if df_total is not None:
    # Sidebar
    st.sidebar.title("🎮 Panel PAIC")
    prod_sel = st.sidebar.selectbox("Producto:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    mes_proy_txt = st.sidebar.select_slider("Proyección:", options=df_total[df_total['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # Banner
    st.markdown(f'<div class="hero-banner">🌱 PAIC - Cartago 2026</div>', unsafe_allow_html=True)

    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTORIAL", "🔮 PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI"])

    real_f = df_total[df_total['Origen']=='Real'].iloc[-1]
    proy_f = df_total[df_total['Fecha'] == pd.to_datetime(mes_proy_txt)].iloc[0]

    with tabs[0]:
        st.subheader("Estado de Cultivos")
        c1, c2, c3 = st.columns(3)
        for col, p_name, img in zip([c1, c2, c3], ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'], [fotos['Papa Blanca (quintal)'], fotos['Cebolla Amarilla (Kg)'], fotos['Fresa (Kg)']]):
            col.markdown(f"""<div class="product-card" style="background-image: url('{img}');">
                <div class="overlay"><b>{p_name.split(' (')[0].upper()}</b><br>₡{real_f[p_name]:,.0f}</div>
            </div>""", unsafe_allow_html=True)

    with tabs[2]:
        st.plotly_chart(px.line(df_total[df_total['Origen']=='Real'], x="Fecha", y=prod_sel, title=f"Historial: {prod_sel}"), use_container_width=True)

    with tabs[3]:
        st.plotly_chart(px.line(df_total[df_total['Fecha'] <= pd.to_datetime(mes_proy_txt)], x="Fecha", y=prod_sel, color="Origen", title="Predicción"), use_container_width=True)

    # --- 🌡️ PATRONES (REPARADO) ---
    with tabs[4]:
        st.subheader("Análisis de Estacionalidad")
        df_h = df_total[df_total['Origen']=='Real'].copy()
        df_h['Mes'] = df_h['Fecha'].dt.month
        # Agrupamos y quitamos columnas no numéricas explícitamente
        heat_data = df_h.groupby('Mes')[['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']].mean()
        fig_heat = px.imshow(heat_data.T, color_continuous_scale='RdYlGn', text_auto=True, title="Mapa de Calor: Rojo (Bajo) | Verde (Alto)")
        st.plotly_chart(fig_heat, use_container_width=True)
        st.info("💡 Este mapa muestra en qué meses del año el producto suele estar más caro (verde) o más barato (rojo).")

    # --- 🧮 CALCULADORA (REPARADA) ---
    with tabs[5]:
        st.subheader("🧮 Calculadora de Rentabilidad Modular")
        with st.expander("📝 Configuración de Costos", expanded=True):
            col1, col2 = st.columns(2)
            ha = col1.number_input("Hectáreas:", value=1.0, step=0.1)
            insumos = col1.number_input("🌿 Insumos/Semilla (₡):", value=250000)
            mano_obra = col2.number_input("👷 Mano de Obra (₡):", value=150000)
            transporte = col2.number_input("🚚 Logística/Flete (₡):", value=50000)
        
        precio_v = st.slider(f"Simular Precio Venta {prod_sel} (₡):", 1000, 30000, int(real_f[prod_sel]))
        
        costo_t = insumos + mano_obra + transporte
        # Estimación: 600 unidades (kilos o quintales) por hectárea
        ingreso_t = ha * 600 * precio_v
        utilidad = ingreso_t - costo_t
        
        st.divider()
        res1, res2 = st.columns(2)
        res1.metric("COSTO TOTAL", f"₡{costo_t:,.2f}")
        res2.metric("UTILIDAD ESTIMADA", f"₡{utilidad:,.2f}", f"{(utilidad/costo_t)*100:.1f}% ROI")

    with tabs[6]:
        msg = st.chat_input("Consulta a Agri...")
        if msg:
            res = client.chat.completions.create(messages=[{"role":"system","content":"Eres Agri, experto agrónomo de Cartago."}, {"role":"user","content":msg}], model="llama-3.3-70b-versatile")
            st.write(res.choices[0].message.content)

else:
    st.error("Error al cargar datos. Verifique su Excel.")
