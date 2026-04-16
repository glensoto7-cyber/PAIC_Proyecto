import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO AVANZADO ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    /* Branding Persistente */
    .branding-banner {
        background-color: #1B5E20;
        padding: 20px;
        color: white;
        text-align: center;
        border-radius: 15px;
        margin-bottom: 25px;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Botón Flotante de AGRI */
    .agri-float {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #2E7D32;
        color: white;
        padding: 15px 25px;
        border-radius: 50px;
        font-weight: bold;
        z-index: 1000;
        box-shadow: 2px 5px 15px rgba(0,0,0,0.3);
        cursor: pointer;
        border: 2px solid white;
    }
    
    /* Estilos de Tarjetas del Dashboard */
    .dash-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-top: 10px solid #1B5E20;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Error: Configure GROQ_API_KEY en Secrets.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        ultima_f = df['Fecha'].max()
        # Generar proyecciones hasta Dic 2027
        fechas_proy = pd.date_range(start=ultima_f + timedelta(days=1), end="2027-12-31", freq='MS')
        proy_list = []
        for i, f in enumerate(fechas_proy):
            mes = f.month
            proms = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            proy_list.append({
                'Fecha': f, 'Papa Blanca (quintal)': proms['Papa Blanca (quintal)'] * 1.05,
                'Cebolla Amarilla (Kg)': proms['Cebolla Amarilla (Kg)'] * 1.05,
                'Fresa (Kg)': proms['Fresa (Kg)'] * 1.05, 'Origen': 'Proyección'
            })
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy_list)], ignore_index=True)
    except: return None

df = cargar_datos()

if df is not None:
    # --- MENÚ LATERAL (SIDEBAR) ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2329/2329865.png", width=100)
    st.sidebar.title("🎮 Panel de Control")
    
    st.sidebar.markdown("---")
    # Filtros Globales
    st.sidebar.subheader("🎯 Selección de Producto")
    producto_sel = st.sidebar.selectbox("¿Qué desea analizar?", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    
    st.sidebar.subheader("📅 Horizonte de Tiempo")
    rango_proy = st.sidebar.select_slider("Proyectar hasta:", options=df[df['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # --- BRANDING ---
    st.markdown("<div class='branding-banner'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)

    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTORIAL/PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "📅 CALENDARIO", "🤖 ASISTENTE"])

    # --- 1. DASHBOARD ---
    with tabs[0]:
        st.subheader(f"Estado Actual: {producto_sel}")
        real_val = df[df['Origen']=='Histórico Real'].iloc[-1][producto_sel]
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f"<div class='dash-card'><h4>💰 Ganancia Est.</h4><h2>₡1.2M</h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='dash-card'><h4>📊 Costo Total</h4><h2>₡500k</h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='dash-card'><h4>📈 Ingreso</h4><h2>₡1.7M</h2></div>", unsafe_allow_html=True)
        with c4: st.markdown(f"<div class='dash-card'><h4>📉 ROI</h4><h2>35%</h2></div>", unsafe_allow_html=True)
        
        st.info(f"📍 Precio actual de feria para {producto_sel}: ₡{real_val:,.0f}")

    # --- 2. COMPARATIVA ---
    with tabs[1]:
        st.subheader("Comparativa de Mercado")
        target_date = pd.to_datetime(rango_proy)
        futuro_val = df[df['Fecha'] == target_date].iloc[0][producto_sel]
        
        col_a, col_b = st.columns(2)
        col_a.metric("Precio Hoy", f"₡{real_val:,.0f}")
        col_b.metric(f"Precio en {rango_proy}", f"₡{futuro_val:,.0f}", f"{((futuro_val/real_val)-1)*100:+.1f}%")
        
        fig_comp = px.bar(x=['Hoy', rango_proy], y=[real_val, futuro_val], color=['Hoy', 'Futuro'], title="Diferencia de Ingreso")
        st.plotly_chart(fig_comp, use_container_width=True)

    # --- 3. HISTÓRICO Y PREDICCIÓN (UNIFICADOS) ---
    with tabs[2]:
        st.subheader(f"Tendencia de {producto_sel}")
        df_plot = df[df['Fecha'] <= target_date]
        fig_trend = px.line(df_plot, x="Fecha", y=producto_sel, color="Origen", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.write("📋 **Datos de la consulta:**")
        st.dataframe(df_plot[['Fecha', producto_sel, 'Origen']], use_container_width=True)

    # --- 4. PATRONES ---
    with tabs[3]:
        st.subheader("Análisis de Estacionalidad")
        modo_h = st.sidebar.radio("Fuente del Mapa:", ["Histórico Real", "Proyección"], key="h1")
        df_h = df[df['Origen'] == modo_h]
        df_h['Mes'] = df_h['Fecha'].dt.month
        heat_data = df_h.groupby('Mes').mean(numeric_only=True)[[producto_sel]]
        
        st.plotly_chart(px.imshow(heat_data.T, color_continuous_scale='RdYlGn', text_auto=True), use_container_width=True)
        st.success(f"Análisis: El mes de {rango_proy.split()[0]} históricamente tiene precios {'ALTOS' if futuro_val > real_val else 'BAJOS'}.")

    # --- 5. CALCULADORA ---
    with tabs[4]:
        st.subheader("Calculadora Modular")
        with st.expander("🌱 Producción", expanded=True):
            ha = st.number_input("Hectáreas", 0.1, 50.0, 1.0)
            rend = st.number_input("Rendimiento Esperado (unidades)", value=600)
        with st.expander("🧾 Costos"):
            c1, c2 = st.columns(2)
            ins = c1.number_input("Insumos (₡)", value=250000)
            mano = c1.number_input("Mano de Obra (₡)", value=150000)
            maq = c2.number_input("Maquinaria (₡)", value=60000)
            log = c2.number_input("Logística (₡)", value=40000)
        
        costo_total = ins + mano + maq + log
        ingreso_total = ha * rend * real_val
        st.divider()
        st.metric("GANANCIA FINAL", f"₡{ingreso_total - costo_total:,.2f}")

    # --- 6. CALENDARIO ---
    with tabs[5]:
        st.subheader("Precios Semanales de Feria")
        # Simulación de desglose semanal del mes seleccionado
        base_p = real_val
        semanas = [f"Semana {i+1}" for i in range(4)]
        precios_s = [base_p * (1 + (i*0.01)) for i in range(4)]
        st.table(pd.DataFrame({"Período": semanas, "Estimado Feria ₡": precios_s}))

    # --- 7. AGRI ---
    with tabs[6]:
        st.markdown("### 🤖 Hola, soy Agri. ¿En qué puedo ayudarte?")
        pregunta = st.chat_input("Escribe tu duda sobre el cultivo o los precios...")
        if pregunta:
            with st.spinner("Agri está pensando..."):
                res = client.chat.completions.create(
                    messages=[{"role": "system", "content": "Eres Agri, experto agrónomo de Cartago. Usa datos reales."},
                              {"role": "user", "content": f"Contexto: {producto_sel} a ₡{real_val}. Pregunta: {pregunta}"}],
                    model="llama-3.3-70b-versatile"
                )
                st.chat_message("assistant").write(res.choices[0].message.content)

# Botón Flotante AGRI (Visual)
st.markdown("<div class='agri-float'>💬 Agri Online</div>", unsafe_allow_html=True)
