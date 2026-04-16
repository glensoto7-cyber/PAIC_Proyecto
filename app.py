import streamlit as st
import pandas as pd
from groq import Groq
import plotly.express as px
import calendar
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILOS AVANZADOS ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")

# CSS para el Botón Flotante Real y Diseño Pro
st.markdown("""
    <style>
    /* Branding */
    .branding-banner { background-color: #1B5E20; padding: 15px; color: white; text-align: center; border-radius: 10px; margin-bottom: 20px; font-size: 1.8rem; font-weight: bold; }
    
    /* Botón Flotante AGRI corregido */
    #agri-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        background-color: #2E7D32;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        z-index: 999999;
        border: 3px solid white;
        text-decoration: none;
    }
    #agri-btn:hover { background-color: #1B5E20; transform: scale(1.1); transition: 0.3s; }

    /* Estilo del Calendario */
    .cal-box { border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center; background-color: white; }
    .cal-header { background-color: #1B5E20; color: white; font-weight: bold; padding: 5px; border-radius: 5px; }
    </style>
    
    <a id="agri-btn" href="#asistente-agri">🤖</a>
    """, unsafe_allow_html=True)

# --- IA ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.sidebar.error("⚠️ Error de API Key.")

# --- 2. MOTOR DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("Precios historicos 15 ABRIL.xlsx", engine='openpyxl')
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha')
        ultima_f = df['Fecha'].max()
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

df_full = cargar_datos()

if df_full is not None:
    # --- SIDEBAR GLOBAL ---
    st.sidebar.title("🎮 Controles PAIC")
    producto_sel = st.sidebar.selectbox("Producto:", ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)'])
    
    st.markdown("<div class='branding-banner'>🌱 PAIC - Cartago 2026</div>", unsafe_allow_html=True)
    tabs = st.tabs(["🏠 DASHBOARD", "📊 COMPARATIVA", "📉 HISTORIAL/PREDICCIÓN", "🌡️ PATRONES", "🧮 CALCULADORA", "📅 CALENDARIO", "🤖 ASISTENTE"])

    # --- 4. PATRONES (CORREGIDO CON SLIDER MES/AÑO) ---
    with tabs[3]:
        st.subheader("Análisis de Estacionalidad por Fecha")
        
        # Selección de Año y Mes
        col_y, col_m = st.columns(2)
        anio_sel = col_y.select_slider("Seleccione Año:", options=[2026, 2027])
        mes_sel = col_m.select_slider("Seleccione Mes:", options=list(calendar.month_name)[1:])
        
        mes_num = list(calendar.month_name).index(mes_sel)
        fecha_target = datetime(anio_sel, mes_num, 1)
        
        # Filtrar dato específico
        dato_mes = df_full[(df_full['Fecha'].dt.month == mes_num) & (df_full['Fecha'].dt.year == anio_sel)]
        
        if not dato_mes.empty:
            val_p = dato_mes.iloc[0][producto_sel]
            st.metric(f"Precio proyectado para {mes_sel} {anio_sel}", f"₡{val_p:,.0f}")
            
            # Interpretación
            if val_p > df_full[df_full['Origen']=='Histórico Real'][producto_sel].mean():
                st.success(f"🟢 {mes_sel}: Históricamente es un mes de PRECIOS ALTOS. Ideal para vender.")
            else:
                st.warning(f"🟡 {mes_sel}: Mes de PRECIOS BAJOS/PROMEDIO. Controle sus costos.")
        
        # Mapa de Calor Global para contexto
        st.plotly_chart(px.imshow(df_full.groupby(df_full['Fecha'].dt.month).mean(numeric_only=True).iloc[:, :3].T, 
                                 color_continuous_scale='RdYlGn', title="Mapa de Calor Histórico (Promedios Mensuales)"), use_container_width=True)

    # --- 5. CALCULADORA (EXTENDIDA) ---
    with tabs[4]:
        st.subheader("🧮 Calculadora de Costos Completa")
        c1, c2, c3 = st.columns(3)
        with c1:
            ha = st.number_input("Hectáreas", 0.1, 50.0, 1.0)
            insumos = st.number_input("🌿 Fertilizantes/Insumos (₡)", value=250000)
            semilla = st.number_input("🌰 Semilla/Plántulas (₡)", value=100000)
        with c2:
            mano_obra = st.number_input("👷 Jornales/Mano Obra (₡)", value=150000)
            maquinaria = st.number_input("🚜 Alquiler Tractor/Equipos (₡)", value=80000)
            riego = st.number_input("💧 Agua y Electricidad (₡)", value=30000)
        with c3:
            transporte = st.number_input("🚚 Flete/Logística (₡)", value=50000)
            empaque = st.number_input("📦 Sacos/Cajas (₡)", value=20000)
            otros = st.number_input("⚙️ Otros Gastos (₡)", value=10000)

        total_gastos = insumos + semilla + mano_obra + maquinaria + riego + transporte + empaque + otros
        precio_esperado = st.number_input("Precio de Venta Sugerido (₡)", value=int(df_full[df_full['Origen']=='Histórico Real'].iloc[-1][producto_sel]))
        
        ingreso_bruto = ha * 600 * precio_esperado
        utilidad_final = ingreso_bruto - total_gastos
        
        st.divider()
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("COSTO TOTAL PRODUCCIÓN", f"₡{total_gastos:,.2f}")
        col_res2.metric("UTILIDAD NETA ESTIMADA", f"₡{utilidad_final:,.2f}", f"{(utilidad_final/total_gastos)*100:.1f}% ROI")

    # --- 6. CALENDARIO AGRO (NORMAL) ---
    with tabs[5]:
        st.subheader("📅 Planificador Agrícola Mensual")
        c_cal1, c_cal2 = st.columns([1, 3])
        
        mes_cal_sel = c_cal1.selectbox("Ver mes:", list(calendar.month_name)[1:], index=datetime.now().month-1)
        anio_cal_sel = c_cal1.selectbox("Ver año:", [2026, 2027])
        
        mes_idx = list(calendar.month_name).index(mes_cal_sel)
        
        # Generar vista de calendario
        cal = calendar.monthcalendar(anio_cal_sel, mes_idx)
        
        with c_cal2:
            st.markdown(f"### Estimados para {mes_cal_sel} {anio_cal_sel}")
            cols_semana = st.columns(7)
            dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
            for i, d in enumerate(dias): cols_semana[i].markdown(f"<div class='cal-header'>{d}</div>", unsafe_allow_html=True)
            
            # Estimado por semana
            precio_base = df_full[(df_full['Fecha'].dt.month == mes_idx) & (df_full['Fecha'].dt.year == anio_cal_sel)][producto_sel].mean()
            
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day != 0:
                        cols[i].markdown(f"<div class='cal-box'>{day}<br><small>₡{precio_base/1000:,.1f}k</small></div>", unsafe_allow_html=True)

    # --- 7. AGRI (ANCLA PARA EL BOTÓN) ---
    with tabs[6]:
        st.markdown("<div id='asistente-agri'></div>", unsafe_allow_html=True)
        st.subheader("🤖 Agri - Tu Asistente Inteligente")
        p_ia = st.chat_input("¿Tienes dudas sobre el clima, precios o siembra en Cartago?")
        if p_ia:
            res = client.chat.completions.create(
                messages=[{"role":"system","content":"Eres Agri, agrónomo experto de Cartago."}, {"role":"user","content":p_ia}],
                model="llama-3.3-70b-versatile"
            )
            st.chat_message("assistant").write(res.choices[0].message.content)

# Mensaje para el resto de pestañas que no se detallaron pero deben seguir funcionando
with tabs[0]: st.write("Visualice sus indicadores clave en la barra superior.")
with tabs[1]: st.write("Compare precios actuales contra proyecciones futuras.")
with tabs[2]: st.write("Análisis histórico de precios registrados en feria.")
