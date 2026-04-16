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
        background-size: cover; background-position: center; height: 180px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 15px; margin-bottom: 20px; color: white;
        font-size: 2.2rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
    }}
    .product-card {{
        background-size: cover; background-position: center; height: 200px;
        border-radius: 15px; display: flex; flex-direction: column;
        justify-content: flex-end; padding: 15px; color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3); margin-bottom: 15px;
    }}
    .overlay {{ background: rgba(0, 0, 0, 0.6); padding: 8px; border-radius: 8px; font-size: 0.9rem; }}
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
    # Sidebar Global
    st.sidebar.title("🎮 Panel PAIC")
    prod_sel = st.sidebar.selectbox("Producto Principal:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    
    # Lista de meses para el slider
    opciones_meses = df_total[df_total['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique()
    mes_proy_txt = st.sidebar.select_slider("Mes para Comparar/Proyectar:", options=opciones_meses)

    # Banner
    st.markdown(f'<div class="hero-banner">🌱 PAIC - Cartago 2026</div>', unsafe_allow_html=True)

    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTORIAL", "🔮 PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI"])

    # Datos de referencia
    real_f = df_total[df_total['Origen']=='Real'].iloc[-1]
    # Buscamos la fila exacta de la proyección
    fecha_busqueda = pd.to_datetime(mes_proy_txt)
    proy_f = df_total[df_total['Fecha'] == fecha_busqueda].iloc[0]

    with tabs[0]:
        st.subheader("Precios Actuales")
        c1, c2, c3 = st.columns(3)
        for col, p_name, img in zip([c1, c2, c3], ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'], [fotos['Papa Blanca (quintal)'], fotos['Cebolla Amarilla (Kg)'], fotos['Fresa (Kg)']]):
            col.markdown(f"""<div class="product-card" style="background-image: url('{img}');">
                <div class="overlay"><b>{p_name.split(' (')[0].upper()}</b><br>₡{real_f[p_name]:,.0f}</div>
            </div>""", unsafe_allow_html=True)

    # --- 📊 COMPARATIVA (REPARADA) ---
    with tabs[1]:
        st.subheader(f"Comparativa: Hoy vs {mes_proy_txt}")
        col_m1, col_m2 = st.columns(2)
        
        # Métricas claras
        val_hoy = real_f[prod_sel]
        val_fut = proy_f[prod_sel]
        cambio = ((val_fut / val_hoy) - 1) * 100
        
        col_m1.metric("Precio Hoy", f"₡{val_hoy:,.0f}")
        col_m2.metric(f"Precio {mes_proy_txt}", f"₡{val_fut:,.0f}", f"{cambio:+.1f}%")
        
        # Gráfico de barras comparativo
        fig_bar = px.bar(
            x=['Hoy', mes_proy_txt], 
            y=[val_hoy, val_fut],
            color=['Hoy', 'Proyección'],
            labels={'x': 'Tiempo', 'y': 'Precio ₡'},
            text_auto='.2s'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with tabs[2]:
        st.plotly_chart(px.line(df_total[df_total['Origen']=='Real'], x="Fecha", y=prod_sel, markers=True), use_container_width=True)

    with tabs[3]:
        df_pred = df_total[df_total['Fecha'] <= fecha_busqueda]
        st.plotly_chart(px.line(df_pred, x="Fecha", y=prod_sel, color="Origen", title=f"Proyección de {prod_sel}"), use_container_width=True)

    with tabs[4]:
        st.subheader("Patrones Estacionales")
        df_h = df_total[df_total['Origen']=='Real'].copy()
        df_h['Mes'] = df_h['Fecha'].dt.month
        heat = df_h.groupby('Mes')[['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']].mean()
        st.plotly_chart(px.imshow(heat.T, color_continuous_scale='RdYlGn', text_auto=True), use_container_width=True)

    with tabs[5]:
        st.subheader("Calculadora de Rentabilidad")
        c_ha, c_ins = st.columns(2)
        hect = c_ha.number_input("Hectáreas:", 0.1, 10.0, 1.0)
        insu = c_ins.number_input("Costos de Insumos (₡):", value=300000)
        p_v_sim = st.slider(f"Precio Venta Simulado {prod_sel}:", 1000, 30000, int(val_hoy))
        
        utilidad = (hect * 600 * p_v_sim) - insu
        st.metric("UTILIDAD NETA", f"₡{utilidad:,.2f}", f"{(utilidad/insu)*100:.1f}% ROI")

    with tabs[6]:
        msg = st.chat_input("Consulta a Agri...")
        if msg:
            res = client.chat.completions.create(messages=[{"role":"system","content":"Eres Agri, experto agrónomo de Cartago."}, {"role":"user","content":msg}], model="llama-3.3-70b-versatile")
            st.write(res.choices[0].message.content)

else:
    st.error("Error al cargar datos.")
