import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="PAIC - Cartago 2026", layout="wide", page_icon="🌱")
LLAVE_PAIC = "AQ.Ab8RN6KbGWiFXRO2zRRDzP6jz2dvgrd3MzPUnjAwPLx5TzfZ1A"

# Estilo para semáforos y métricas
st.markdown("""
    <style>
    .rentable { color: #2E7D32; font-weight: bold; }
    .ajustado { color: #FBC02D; font-weight: bold; }
    .perdida { color: #D32F2F; font-weight: bold; }
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
        
        lista_proy = []
        for i, fecha in enumerate(fechas_proy):
            mes = fecha.month
            prom = df[df['Fecha'].dt.month == mes].mean(numeric_only=True)
            # Factor de tendencia estacional
            ajuste = 1 + (i * 0.002)
            lista_proy.append({
                'Fecha': fecha,
                'Papa Blanca (quintal)': prom['Papa Blanca (quintal)'] * ajuste,
                'Cebolla Amarilla (Kg)': prom['Cebolla Amarilla (Kg)'] * ajuste,
                'Fresa (Kg)': prom['Fresa (Kg)'] * ajuste,
                'Origen': 'Proyección PAIC'
            })
        
        df['Origen'] = 'Histórico Real'
        return pd.concat([df, pd.DataFrame(lista_proy)], ignore_index=True)
    except Exception as e:
        return str(e)

df_total = motor_datos()

# --- 3. ESTRUCTURA DE PESTAÑAS ---
if isinstance(df_total, str):
    st.error(f"Error en datos: {df_total}")
else:
    t_inicio, t_hist, t_pred, t_calc, t_ia = st.tabs([
        "🏠 INICIO", "📚 HISTÓRICO", "🔮 PREDICCIÓN 2027", "🧮 CALCULADORA PRO", "🤖 CONSULTOR IA"
    ])

    # --- PESTAÑA 1: INICIO (RESUMEN EJECUTIVO) ---
    with t_inicio:
        st.header("🎯 Resumen de Mercado y Comparativa")
        real = df_total[df_total['Origen'] == 'Histórico Real'].iloc[-1]
        prox = df_total[df_total['Origen'] == 'Proyección PAIC'].iloc[0]
        
        c1, c2, c3 = st.columns(3)
        productos = ['Papa Blanca (quintal)', 'Cebolla Amarilla (Kg)', 'Fresa (Kg)']
        col_list = [c1, c2, c3]
        
        for p, col in zip(productos, col_list):
            diff = ((prox[p] / real[p]) - 1) * 100
            col.metric(p, f"₡{real[p]:,.0f}", f"Próx. Mes: {diff:+.1f}%")
        
        st.subheader("📈 Tendencia General")
        fig_ini = px.area(df_total[df_total['Origen'] == 'Histórico Real'].tail(12), 
                         x='Fecha', y='Papa Blanca (quintal)', title="Variación últimos 12 meses")
        st.plotly_chart(fig_ini, use_container_width=True)

    # --- PESTAÑA 2: HISTÓRICO (SEPARADA) ---
    with t_hist:
        st.header("📚 Registro Histórico de Precios")
        fig_hist = px.line(df_total[df_total['Origen'] == 'Histórico Real'], 
                          x='Fecha', y=productos, title="Historial Completo")
        st.plotly_chart(fig_hist, use_container_width=True)
        st.dataframe(df_total[df_total['Origen'] == 'Histórico Real'].tail(20))

    # --- PESTAÑA 3: PREDICCIÓN ---
    with t_pred:
        st.header("🔮 Horizonte 2026-2027")
        prod_sel = st.selectbox("Producto a proyectar:", productos)
        fig_proy = px.line(df_total, x='Fecha', y=prod_sel, color='Origen',
                          title=f"Proyección de Mercado: {prod_sel}")
        st.plotly_chart(fig_proy, use_container_width=True)

    # --- PESTAÑA 4: CALCULADORA PRO (EL CEREBRO) ---
    with t_calc:
        st.header("🧮 Calculadora de Rentabilidad Avanzada")
        
        with st.expander("🌱 1. Definición del Cultivo", expanded=True):
            col_a, col_b, col_c = st.columns(3)
            cultivo = col_a.selectbox("Tipo de Cultivo:", ["Papa", "Cebolla", "Fresa"])
            area = col_b.number_input("Área sembrada (Hectáreas):", value=1.0)
            rendimiento = col_c.number_input("Rendimiento esperado (Unid/Ha):", value=600)
        
        with st.expander("💰 2. Ingresos y Ventas"):
            col_d, col_e = st.columns(2)
            precio_v = col_d.number_input("Precio de venta (₡ por Unidad):", value=int(real['Papa Blanca (quintal)']))
            merma_per = col_e.slider("% Pérdida por merma/rechazo:", 0, 50, 5)
            canal = st.multiselect("Canales de Venta:", ["Feria", "CENADA", "Intermediario", "Supermercado"], ["CENADA"])

        with st.expander("🧾 3. Estructura de Costos"):
            c_ins, c_mano, c_log = st.columns(3)
            insumos = c_ins.number_input("Insumos (Semilla, Abono, Agro) ₡:", value=400000)
            jornales = c_mano.number_input("Mano de Obra (Jornales) ₡:", value=300000)
            logistica = c_log.number_input("Logística (Transporte, Empaque) ₡:", value=150000)
            otros = st.number_input("Otros (Agua, Electricidad, Alquiler) ₡:", value=50000)

        # CÁLCULOS FINANCIEROS
        prod_total = (area * rendimiento) * (1 - merma_per/100)
        ingreso_estimado = prod_total * precio_v
        costos_totales = insumos + jornales + logistica + otros
        ganancia_neta = ingreso_estimado - costos_totales
        margen = (ganancia_neta / ingreso_estimado * 100) if ingreso_estimado > 0 else 0
        punto_eq = costos_totales / (precio_v if precio_v > 0 else 1)

        # RESULTADOS RESUMIDOS
        st.markdown("---")
        st.subheader("📊 Resultados de la Simulación")
        res1, res2, res3, res4 = st.columns(4)
        res1.metric("Ingreso Bruto", f"₡{ingreso_total:,.0f}")
        res2.metric("Costos Totales", f"₡{costos_totales:,.0f}")
        res3.metric("Ganancia Neta", f"₡{ganancia_neta:,.0f}")
        res4.metric("Margen (%)", f"{margen:.1f}%")

        # SEMÁFORO
        if ganancia_neta > 200000:
            st.markdown("<h2 class='rentable'>🟢 ESTADO: RENTABLE</h2>", unsafe_allow_html=True)
        elif ganancia_neta > 0:
            st.markdown("<h2 class='ajustado'>🟡 ESTADO: AJUSTADO</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2 class='perdida'>🔴 ESTADO: PÉRDIDA</h2>", unsafe_allow_html=True)

    # --- PESTAÑA 5: CONSULTOR IA ---
    with t_ia:
        st.header("🤖 Consultor PAIC")
        pregunta = st.text_area("Consulta técnica sobre estos resultados:")
        if st.button("GENERAR ANÁLISIS"):
            try:
                genai.configure(api_key=LLAVE_PAIC)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Agricultor Cartago. Cultivo: {cultivo}. Ganancia: {ganancia_neta}. Margen: {margen}%. Pregunta: {pregunta}"
                with st.spinner('IA analizando...'):
                    res = model.generate_content(prompt)
                    st.info(res.text)
            except Exception as e:
                st.error(f"Error IA: {e}")
