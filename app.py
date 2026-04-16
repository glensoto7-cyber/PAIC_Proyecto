import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO GLOBAL ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# CSS para Identidad Visual y Botones Grandes
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .branding {
        background-color: #1B5E20;
        padding: 15px;
        color: white;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 20px;
        font-weight: bold;
        font-size: 1.8rem;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 15px;
    }
    .papa { border-top: 8px solid #795548; }
    .cebolla { border-top: 8px solid #FBC02D; }
    .fresa { border-top: 8px solid #D32F2F; }
    
    .alert-box {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: bold;
    }
    .alert-danger { background-color: #FFEBEE; color: #B71C1C; border-left: 5px solid #B71C1C; }
    .alert-info { background-color: #E3F2FD; color: #0D47A1; border-left: 5px solid #0D47A1; }
    </style>
    """, unsafe_allow_html=True)

# --- IA Y SEGURIDAD ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ Configure la GROQ_API_KEY en los Secrets de Streamlit.")

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
                'Fecha': f, 
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * (1 + i * 0.002),
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * (1 + i * 0.002),
                'Fresa (Kg)': prom['Fresa (Kg)'] * (1 + i * 0.002),
                'Origen': 'Proyección'
            })
        df['Origen'] = 'Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return f"Error: {e}"

df_total = motor_datos()

# --- 3. INTERFAZ PRINCIPAL ---
if isinstance(df_total, str):
    st.error(df_total)
else:
    # Branding Persistente
    st.markdown("<div class='branding'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTÓRICO", 
        "🔮 PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", 
        "📅 CALENDARIO", "🤖 AGRI (IA)"
    ])

    # Variables de Referencia (CORRECCIÓN DEL KEYERROR)
    real = df_total[df_total['Origen'] == 'Real'].iloc[-1]
    prox = df_total[df_total['Origen'] == 'Proyección'].iloc[0]

    # --- 1. DASHBOARD ---
    with tabs[0]:
        st.subheader("Resumen de Ganancias y Alertas")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Ganancia Neta Est.", "₡1,250,000", "+12%")
        c2.metric("📊 Costos Totales", "₡500,000")
        c3.metric("📈 Ingresos", "₡1,750,000")
        c4.metric("📉 Margen ROI", "35%")

        st.markdown("<div class='alert-box alert-danger'>🚨 TENDENCIA: Los precios de la Cebolla Amarilla bajaron un 4% esta semana.</div>", unsafe_allow_html=True)
        st.markdown("<div class='alert-box alert-info'>💡 PATRÓN: Históricamente, mayo es el mejor mes para vender Fresa en Cartago.</div>", unsafe_allow_html=True)

    # --- 2. COMPARATIVA ---
    with tabs[1]:
        st.subheader("Comparativa Mensual Inteligente")
        col_p, col_c, col_f = st.columns(3)
        
        productos = [
            ("PAPA BLANCA", 'Papa Blanca (quintal)', col_p, "papa"),
            ("CEBOLLA AMARILLA", 'Cebolla Amarilla (Kg)', col_c, "cebolla"),
            ("FRESA", 'Fresa (Kg)', col_f, "fresa")
        ]
        
        for nombre, key, col, css in productos:
            with col:
                diff = ((prox[key]/real[key])-1)*100
                color = "#2E7D32" if diff > 0 else "#D32F2F"
                st.markdown(f"""<div class='metric-card {css}'>
                    <h3>{nombre}</h3>
                    <p>Hoy: <b>₡{real[key]:,.0f}</b></p>
                    <p>Próx. Mes: <b>₡{prox[key]:,.0f}</b></p>
                    <p style='color:{color}; font-weight:bold;'>{diff:+.1f}% {'🔼' if diff>0 else '🔽'}</p>
                </div>""", unsafe_allow_html=True)

    # --- 3. HISTÓRICO ---
    with tabs[2]:
        st.subheader("Exploración de Precios Reales")
        df_h = df_total[df_total['Origen'] == 'Real']
        fig_h = px.line(df_h, x="Fecha", y=['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'], 
                        color_discrete_map={'Papa Blanca (quintal)': '#795548', 'Cebolla Amarilla (Kg)': '#FBC02D', 'Fresa (Kg)': '#D32F2F'})
        st.plotly_chart(fig_h, use_container_width=True)

    # --- 5. PATRONES ---
    with tabs[4]:
        st.subheader("Mapa de Calor de Estacionalidad")
        df_h['Mes'] = df_h['Fecha'].dt.month
        heat = df_h.groupby('Mes').mean(numeric_only=True).iloc[:, :3]
        fig_heat = px.imshow(heat.T, color_continuous_scale='RdYlGn', text_auto=True)
        st.plotly_chart(fig_heat, use_container_width=True)
        
        mes_f = st.selectbox("Analizar Mes:", range(1,13))
        if mes_f in [4, 5, 6]:
            st.success("🟢 BUEN MES PARA VENDER: Precios históricamente altos en la zona.")
        else:
            st.warning("🟡 MES PROMEDIO: Planifique sus costos cuidadosamente.")

    # --- 6. CALCULADORA (FIXED KEYERROR) ---
    with tabs[5]:
        st.subheader("🧮 Calculadora de Rentabilidad Pro")
        col1, col2 = st.columns(2)
        ha = col1.number_input("Hectáreas", value=1.0)
        # CORRECCIÓN: Usamos el nombre de la columna en vez de un índice numérico
        precio_sim = col1.slider("Simular Precio Venta (₡)", 1000, 30000, int(real['Papa Blanca (quintal)']))
        costos_insumo = col2.number_input("Insumos/Maquinaria (₡)", value=300000)
        mano_obra = col2.number_input("Mano de Obra (₡)", value=150000)
        
        utilidad = (ha * 600 * precio_sim) - (costos_insumo + mano_obra)
        st.divider()
        st.metric("GANANCIA NETA ESTIMADA", f"₡{utilidad:,.2f}")

    # --- 8. ASISTENTE AGRI ---
    with tabs[7]:
        st.markdown(f"""<div style='background-color:#E8F5E9; padding:20px; border-radius:15px; border-left:10px solid #2E7D32;'>
            <h4>🤖 Hola, soy Agri</h4>
            <p>Tu asistente experto en la PAIC. Analizo los datos de Cartago para ayudarte.</p>
        </div>""", unsafe_allow_html=True)
        
        duda = st.text_input("Hazle una pregunta a Agri:")
        if st.button("Consultar"):
            res = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres Agri, un experto agrónomo de Cartago. Responde de forma clara y útil."},
                    {"role": "user", "content": f"Precio papa hoy: {real['Papa Blanca (quintal)']}. Pregunta: {duda}"}
                ],
                model="llama-3.3-70b-versatile"
            )
            st.write(res.choices[0].message.content)

# Pie de página constante
st.markdown("---")
st.caption("PAIC - Cartago 2026 | Desarrollado para la comunidad agrícola")
