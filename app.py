import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")
LLAVE_PAIC = "AIzaSyB2Fxb83L448m8-b8DAJw6Da_Js5t_sbCY"

st.markdown("""
    <style>
    .rentable { color: #2E7D32; background-color: #E8F5E9; padding: 10px; border-radius: 5px; text-align: center; }
    .ajustado { color: #FBC02D; background-color: #FFFDE7; padding: 10px; border-radius: 5px; text-align: center; }
    .perdida { color: #D32F2F; background-color: #FFEBEE; padding: 10px; border-radius: 5px; text-align: center; }
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
        st.header("🎯 Comparativa de Mercado")
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
        c1, c2, c3 = st.columns(3)
        prods = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']
        cols = [c1, c2, c3]
        for p, col in zip(prods, cols):
            diff = ((prox[p] / real[p]) - 1) * 100
            col.metric(p, f"₡{real[p]:,.0f}", f"Próx. Mes: {diff:+.1f}%")

    with t_hist:
        st.header("📚 Registro Histórico")
        fig_h = px.line(df_total[df_total['Origen'] == 'Histórico Real'], x='Fecha', y=prods)
        st.plotly_chart(fig_h, use_container_width=True)

    with t_pred:
        st.header("🔮 Horizonte 2027")
        p_sel = st.selectbox("Producto:", prods)
        fig_p = px.line(df_total, x='Fecha', y=p_sel, color='Origen')
        st.plotly_chart(fig_p, use_container_width=True)

    with t_calc:
        st.header("🧮 Calculadora de Rentabilidad")
        with st.expander("🌱 Producción", expanded=True):
            col_a, col_b = st.columns(2)
            area = col_a.number_input("Hectáreas:", value=1.0)
            rend = col_b.number_input("Rendimiento (Unid/Ha):", value=600.0)
        
        with st.expander("💰 Ingresos"):
            col_c, col_d = st.columns(2)
            precio_v = col_c.number_input("Precio Venta ₡:", value=int(real['Papa Blanca (quintal)']))
            merma = col_d.slider("% Merma:", 0, 50, 5)

        with st.expander("🧾 Costos"):
            c1, c2, c3 = st.columns(3)
            insumos = c1.number_input("Insumos ₡:", value=400000)
            jornales = c2.number_input("Mano de Obra ₡:", value=300000)
            logistica = c3.number_input("Logística ₡:", value=150000)
            otros = st.number_input("Otros Gastos ₡:", value=50000)

        # --- CÁLCULOS (CORREGIDOS) ---
        prod_neta = (area * rend) * (1 - merma/100)
        ingreso_bruto = prod_neta * precio_v
        costos_totales = insumos + jornales + logistica + otros
        ganancia_neta = ingreso_bruto - costos_totales
        margen = (ganancia_neta / ingreso_bruto * 100) if ingreso_bruto > 0 else 0

        st.markdown("---")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Ingreso Bruto", f"₡{ingreso_bruto:,.0f}")
        r2.metric("Costos Totales", f"₡{costos_totales:,.0f}")
        r3.metric("Ganancia Neta", f"₡{ganancia_neta:,.0f}")
        r4.metric("Margen", f"{margen:.1f}%")

        if ganancia_neta > 200000:
            st.markdown("<h3 class='rentable'>🟢 RENTABLE</h3>", unsafe_allow_html=True)
        elif ganancia_neta > 0:
            st.markdown("<h3 class='ajustado'>🟡 AJUSTADO</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 class='perdida'>🔴 PÉRDIDA</h3>", unsafe_allow_html=True)

    with t_ia:
        st.header("🤖 Consultor IA")
        pregunta = st.text_area("Consulta técnica:")
        if st.button("ANALIZAR"):
            try:
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Agricultor Cartago. Ganancia: {ganancia_neta}. Pregunta: {pregunta}")
                st.info(res.text)
            except Exception as e:
                st.error(f"Error IA: {e}")
