import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")
LLAVE_PAIC = "AQ.Ab8RN6KbGWiFXRO2zRRDzP6jz2dvgrd3MzPUnjAwPLx5TzfZ1A"

st.markdown("""
    <style>
    .rentable { color: #2E7D32; background-color: #E8F5E9; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #2E7D32; }
    .ajustado { color: #FBC02D; background-color: #FFFDE7; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #FBC02D; }
    .perdida { color: #D32F2F; background-color: #FFEBEE; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #D32F2F; }
    .stMetric { background-color: #F9FBE7; padding: 15px; border-radius: 10px; border: 1px solid #DCEDC8; }
    </style>
    """, unsafe_allow_html=True)

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
        for i, fecha in enumerate(fechas_proy):
            mes = fecha.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            ajuste = 1 + (i * 0.002)
            proy.append({
                'Fecha': fecha,
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * ajuste,
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * ajuste,
                'Fresa (Kg)': prom['Fresa (Kg)'] * ajuste,
                'Origen': 'Proyección PAIC'
            })
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(proy)], ignore_index=True)
    except Exception as e:
        return str(e)

df_total = motor_datos()

# --- 3. ESTRUCTURA ---
if isinstance(df_total, str):
    st.error(f"Error en datos: {df_total}")
else:
    t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs(["🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN", "🧮 CALCULADORA PRO", "🤖 IA"])

    with t_inicio:
        st.header("🎯 Comparativa: Mes Actual vs Próximo Mes")
        # Obtenemos el último dato real y el primero proyectado
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        prods = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']
        cols = [c1, c2, c3]
        
        for p, col in zip(prods, cols):
            # Cálculo de la diferencia porcentual para la comparativa
            variacion = ((prox[p] / real[p]) - 1) * 100
            col.metric(
                label=f"Actual: {p}", 
                value=f"₡{real[p]:,.0f}", 
                delta=f"Próx. Mes: {prox[p]:,.0f} ({variacion:+.1f}%)",
                delta_color="normal"
            )
        
        st.info("💡 El indicador 'delta' (en verde o rojo) muestra la tendencia de precio esperada para el siguiente ciclo mensual.")

    with t_hist:
        st.header("📚 Registro Histórico de Precios")
        fig_h = px.line(df_total[df_total['Origen'] == 'Histórico Real'], x='Fecha', y=prods, title="Historial CENADA")
        st.plotly_chart(fig_h, use_container_width=True)

    with t_pred:
        st.header("🔮 Horizonte de Precios 2026-2027")
        p_sel = st.selectbox("Seleccione producto para ver predicción:", prods)
        fig_p = px.line(df_total, x='Fecha', y=p_sel, color='Origen', title=f"Tendencia Proyectada: {p_sel}")
        st.plotly_chart(fig_p, use_container_width=True)

    with t_calc:
        st.header("🧮 Calculadora de Rentabilidad Pro")
        with st.expander("🌱 Definición de Producción", expanded=True):
            col_a, col_b = st.columns(2)
            area = col_a.number_input("Hectáreas sembradas:", value=1.0)
            rend = col_b.number_input("Rendimiento (Unidades/Ha):", value=600.0)
        
        with st.expander("💰 Ingresos Estimados"):
            col_c, col_d = st.columns(2)
            precio_v = col_c.number_input("Precio de Venta ₡ (por unidad):", value=int(real['Papa Blanca (quintal)']))
            merma = col_d.slider("% Merma o Desperdicio:", 0, 50, 5)

        with st.expander("🧾 Estructura de Costos"):
            c1, c2, c3 = st.columns(3)
            insumos = c1.number_input("Insumos (Semilla, Abono) ₡:", value=400000)
            jornales = c2.number_input("Mano de Obra (Jornales) ₡:", value=300000)
            logistica = c3.number_input("Logística y Transporte ₡:", value=150000)
            otros = st.number_input("Otros Gastos (Riego, Alquiler) ₡:", value=50000)

        # --- CÁLCULOS FINANCIEROS ---
        prod_neta = (area * rend) * (1 - merma/100)
        ingreso_bruto = prod_neta * precio_v
        costos_totales = insumos + jornales + logistica + otros
        ganancia_neta = ingreso_bruto - costos_totales
        margen = (ganancia_neta / ingreso_bruto * 100) if ingreso_bruto > 0 else 0

        st.markdown("---")
        st.subheader("📊 Resumen de Resultados")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Ingreso Bruto", f"₡{ingreso_bruto:,.0f}")
        r2.metric("Costos Totales", f"₡{costos_totales:,.0f}")
        r3.metric("Ganancia Neta", f"₡{ganancia_neta:,.0f}")
        r4.metric("Margen Real", f"{margen:.1f}%")

        if ganancia_neta > 200000:
            st.markdown("<div class='rentable'><h3>🟢 ESTADO: RENTABLE</h3><p>El proyecto genera utilidades sólidas.</p></div>", unsafe_allow_html=True)
        elif ganancia_neta > 0:
            st.markdown("<div class='ajustado'><h3>🟡 ESTADO: AJUSTADO</h3><p>Cuidado: El margen de ganancia es mínimo.</p></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='perdida'><h3>🔴 ESTADO: PÉRDIDA</h3><p>Atención: Los costos superan los ingresos.</p></div>", unsafe_allow_html=True)

    with t_ia:
        st.header("🤖 Consultor PAIC (IA)")
        pregunta = st.text_area("Haga una consulta sobre sus resultados financieros:")
        if st.button("ANALIZAR ESCENARIO"):
            try:
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Agricultor Cartago. Ganancia: {ganancia_neta}. Margen: {margen}%. Pregunta: {pregunta}")
                st.info(res.text)
            except Exception as e:
                st.error(f"Error IA: {e}")
