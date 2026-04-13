import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Simulador Solar Finca La Caramela", layout="wide")
st.title("☀️ Simulador de Ahorro con Energía Solar - Datos Reales")
st.markdown("""
**Consumos históricos reales** de Finca La Caramela (marzo 2025 - febrero 2026).  
Ajustá la cantidad de paneles y la tarifa para proyectar ahorros.
""")

# --- Sidebar con parámetros interactivos ---
with st.sidebar:
    st.header("⚙️ Configuración del sistema")
    
    # Paneles de 585 Wp
    potencia_panel = 0.585  # kWp por panel
    num_paneles = st.number_input("Número de paneles", min_value=1, max_value=36, value=12, step=1,
                                  help="Cantidad de paneles solares de 585 Wp cada uno.")
    potencia_calculada = num_paneles * potencia_panel
    
    potencia = st.slider("Potencia instalada (kWp)", min_value=0.5, max_value=15.0,
                         value=potencia_calculada, step=0.1,
                         help="Potencia pico total del sistema (DC).")
    
    # Sincronizar
    if abs(potencia - potencia_calculada) > 0.01:
        num_paneles = int(round(potencia / potencia_panel))
    
    st.markdown(f"**Equivale a ≈ {num_paneles} paneles de 585 Wp**")
    st.markdown("---")
    
    tarifa = st.number_input("Tarifa variable ($/kWh)", min_value=100.0, max_value=800.0,
                             value=226.09, step=10.0,
                             help="Cargo por kWh consumido (sin impuestos).")
    impuestos_pct = st.slider("Impuestos y tasas (%)", min_value=0, max_value=60, value=38, step=1,
                              help="Porcentaje sobre subtotal de energía (IVA + Leyes provinciales).")
    
    compensacion_pct = st.slider("Factor de compensación excedente (%)", 
                                 min_value=20, max_value=100, value=40, step=5,
                                 help="Porcentaje del valor de la tarifa que se reconoce por la energía inyectada.")
    
    st.markdown("---")
    st.caption("Generación solar estimada según irradiación promedio en Ranchos, Buenos Aires.")

# --- Datos reales de consumo (mar 2025 - feb 2026) ---
meses = ['Mar 25', 'Abr 25', 'May 25', 'Jun 25', 'Jul 25', 'Ago 25',
         'Sep 25', 'Oct 25', 'Nov 25', 'Dic 25', 'Ene 26', 'Feb 26']
consumo_real = [652, 450, 469, 603, 571, 661, 807, 849, 1023, 534, 748, 690]

# Generación base para 5 kWp (promedio mensual en kWh)
gen_base = [560, 450, 360, 280, 250, 400, 510, 600, 660, 690, 675, 620]

# --- Ajuste con potencia instalada y pérdidas ---
factor_perdidas = 0.85
generacion_dc = [g * potencia / 5.0 * factor_perdidas for g in gen_base]

# --- Clipping del inversor Solax X3 (5 kW AC) ---
potencia_inversor = 5.0  # kW AC
horas_prom_mes = 30 * 4.5  # aprox. 4.5 h equivalentes de sol/día
limite_mensual = potencia_inversor * horas_prom_mes

generacion = [min(g, limite_mensual) for g in generacion_dc]

# --- Cálculos económicos ---
subtotal_sin = [c * tarifa for c in consumo_real]

subtotal_con = []
excedente = []
consumo_red_con_solar = []

for c, g in zip(consumo_real, generacion):
    autoconsumo = min(c, g)
    exced = max(0, g - c)
    costo_red = (c - autoconsumo) * tarifa
    credito_excedente = exced * tarifa * (compensacion_pct/100)
    subtotal_con.append(costo_red - credito_excedente)
    excedente.append(exced)
    consumo_red_con_solar.append(max(0, c - g))

factura_sin = [s * (1 + impuestos_pct/100) for s in subtotal_sin]
factura_con = [s * (1 + impuestos_pct/100) for s in subtotal_con]

ahorro_mensual = [sin - con for sin, con in zip(factura_sin, factura_con)]
ahorro_anual = sum(ahorro_mensual)

# --- Métricas principales ---
col1, col2, col3 = st.columns(3)
col1.metric("💰 Ahorro anual estimado", f"${ahorro_anual:,.0f}")
col2.metric("📆 Consumo anual real", f"{sum(consumo_real):,.0f} kWh")
col3.metric("🌞 Consumo de red con solar", f"{sum(consumo_red_con_solar):,.0f} kWh")

# --- GRÁFICO 1: Curvas de Consumo y Generación Solar ---
st.subheader("📈 Evolución mensual del consumo y la generación solar")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=meses, y=consumo_real, mode='lines+markers',
                          name='Consumo Real (kWh)', line=dict(color='royalblue', width=4),
                          marker=dict(size=10, symbol='circle')))
fig1.add_trace(go.Scatter(x=meses, y=generacion, mode='lines+markers',
                          name='Generación Solar (kWh)', line=dict(color='goldenrod', width=4, dash='dot'),
                          marker=dict(size=10, symbol='square')))
fig1.update_layout(xaxis_title="Mes", yaxis_title="Energía (kWh)", template="plotly_white",
                   height=450, hovermode="x unified",
                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig1, use_container_width=True)

# --- GRÁFICO 2: Barras de ahorro mensual ---
st.subheader("💵 Ahorro mensual estimado con sistema solar")
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=meses, y=ahorro_mensual, marker_color='darkgreen',
                      text=[f"${a:,.0f}" for a in ahorro_mensual], textposition='outside',
                      textfont=dict(size=12, color='black'), name='Ahorro ($)'))
fig2.update_layout(xaxis_title="Mes", yaxis_title="Ahorro ($)", template="plotly_white",
                   height=400, showlegend=False,
                   yaxis=dict(tickformat="$,.0f", gridcolor='lightgray'),
                   plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig2, use_container_width=True)

# --- Tabla detallada ---
st.subheader("📋 Detalle mensual completo")
df = pd.DataFrame({
    'Mes': meses,
    'Consumo real (kWh)': consumo_real,
    'Generación solar (kWh)': [round(g,1) for g in generacion],
    'Consumo de red con solar (kWh)': [round(c,0) for c in consumo_red_con_solar],
    'Excedente inyectado (kWh)': [round(e,0) for e in excedente],
    'Factura sin solar ($)': [round(f,0) for f in factura_sin],
    'Factura con solar ($)': [round(f,0) for f in factura_con],
    'Ahorro ($)': [round(a,0) for a in ahorro_mensual]
})
st.dataframe(df, use_container_width=True)

st.info(f"""
ℹ️ **Notas:**
- Los consumos corresponden al período **marzo 2025 - febrero 2026** (histórico real).
- La generación solar se estimó con datos de irradiación promedio para Ranchos, Buenos Aires.
- Se aplicó un **factor de pérdidas del 15%** y un límite de **5 kW AC** por el inversor Solax X3.
- En meses con excedente, la energía inyectada se compensa al **{compensacion_pct}% del valor de la tarifa** (precio mayorista).
""")