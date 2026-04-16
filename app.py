import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    .branding-banner { background-color: #1B5E20; padding: 15px; color: white; text-align: center; border-radius: 10px; margin-bottom: 20px; font-size: 1.8rem; font-weight: bold; }
    .metric-card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-top: 8px solid #1B5E20; text-align: center; }
    #agri-float { position: fixed; bottom: 20px; right: 20px; background: #2E7D32; color: white; padding: 15px; border-radius: 50px; z-index: 99; border: 2px solid white; font-weight: bold; text-decoration: none; }
    </style>
    <a id="agri-float" href="#agri-seccion">🤖 Hablar con Agri</a>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Error: Revise su GROQ_API_KEY en Secrets.")

# --- 2. MOTOR DE DATOS (Simplificado) ---
@st.cache_data
def cargar_datos():
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
    except: return None

df = cargar_datos()

if df is not None:
    # --- SIDEBAR DE CONTROL ---
    st.sidebar.header("🕹️ Menú de Control")
    prod = st.sidebar.selectbox("Seleccione Producto:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    mes_proy = st.sidebar.select_slider("Mes de Proyección:", options=df[df['Origen']=='Proyección']['Fecha'].dt.strftime('%b %Y').unique())

    # --- BRANDING ---
    st.markdown("<div class='branding-banner'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)
    
    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTÓRICO/PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "🤖 AGRI (IA)"])

    # Datos clave para cálculos
    real_f = df[df['Origen']=='Real'].iloc[-1]
    proy_f = df[df['Fecha'] == pd.to_datetime(mes_proy)].iloc[0]

    # --- 1. DASHBOARD ---
    with tabs[0]:
        st.subheader(f"Dashboard: {prod}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Precio Hoy", f"₡{real_f[prod]:,.0f}")
        c2.metric("🔮 Precio Proyectado", f"₡{proy_f[prod]:,.0f}")
        c3.metric("📈 Variación", f"{((proy_f[prod]/real_f[prod])-1)*100:+.1f}%")
        c4.metric("📊 Registros", len(df[df['Origen']=='Real']))
        
        st.markdown(f"### 🚨 Alerta de Mercado")
        if proy_f[prod] < real_f[prod]:
            st.error(f"📉 Se detecta tendencia a la baja para {prod} en {mes_proy}. ¡Cuidado con la venta!")
        else:
            st.success(f"📈 Tendencia alcista detectada para {prod} en {mes_proy}. Escenario favorable.")

    # --- 2. COMPARATIVA ---
    with tabs[1]:
        st.subheader("Comparativa Mensual Directa")
        fig_comp = px.bar(x=['Precio Hoy', f'Precio {mes_proy}'], y=[real_f[prod], proy_f[prod]], 
                         color=['Hoy', 'Futuro'], text_auto='.2s', title=f"Diferencia de precios para {prod}")
        st.plotly_chart(fig_comp, use_container_width=True)

    # --- 3. HISTÓRICO Y PREDICCIÓN ---
    with tabs[2]:
        st.subheader("Línea de Tiempo: Real + Proyectado")
        df_p = df[df['Fecha'] <= pd.to_datetime(mes_proy)]
        fig_line = px.line(df_p, x="Fecha", y=prod, color="Origen", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    # --- 4. PATRONES ---
    with tabs[3]:
        st.subheader("Mapa de Estacionalidad Histórica")
        df_h = df[df['Origen']=='Real'].copy()
        df_h['Mes'] = df_h['Fecha'].dt.month
        heat = df_h.groupby('Mes').mean(numeric_only=True)[[prod]]
        st.plotly_chart(px.imshow(heat.T, color_continuous_scale='RdYlGn', text_auto=True), use_container_width=True)
        
        m_sel = pd.to_datetime(mes_proy).month
        if m_sel in [4, 5, 6]: st.success(f"✅ Mes {m_sel}: Época de altos precios históricamente.")
        else: st.warning(f"⚠️ Mes {m_sel}: Época de precios bajos o promedio.")

    # --- 5. CALCULADORA ---
    with tabs[4]:
        st.subheader("Simulador de Rentabilidad")
        col_a, col_b = st.columns(2)
        hectareas = col_a.number_input("Hectáreas", 0.1, 100.0, 1.0)
        costos_fijos = col_b.number_input("Costos Totales (Insumos, Mano de obra, etc) ₡", value=500000)
        
        p_venta = st.slider("Simular Precio de Venta (₡)", 1000, 30000, int(real_f[prod]))
        
        ingreso = hectareas * 600 * p_venta
        utilidad = ingreso - costos_fijos
        st.divider()
        st.metric("UTILIDAD NETA ESTIMADA", f"₡{utilidad:,.2f}", f"{(utilidad/costos_fijos)*100:.1f}% ROI")

    # --- 6. AGRI (IA) ---
    with tabs[5]:
        st.markdown("<div id='agri-seccion'></div>", unsafe_allow_html=True)
        st.subheader("🤖 Agri - Asistente Inteligente")
        msg = st.chat_input("Pregunte a Agri...")
        if msg:
            res = client.chat.completions.create(
                messages=[{"role":"system","content":"Eres Agri, experto agrónomo de Cartago."}, {"role":"user","content":msg}],
                model="llama-3.3-70b-versatile"
            )
            st.chat_message("assistant").write(res.choices[0].message.content)

else:
    st.error("❌ No se pudo cargar el archivo Excel. Verifique el nombre en GitHub.")
