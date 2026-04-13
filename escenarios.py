import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Simulador Solar - Escenarios de Consumo", layout="wide")
st.title("Simulador de Consumo Solar - Escenario Promedio vs Escenario Concentrado")
st.markdown(
    """
Simulación comparativa para una fábrica con dos formas de consumo:

1. **Escenario promedio:** el consumo mensual se reparte en 30 días iguales.  
2. **Escenario concentrado:** el mismo consumo mensual se concentra en los días operativos y
   en los días sin operación toda la generación solar se inyecta a la red.
"""
)

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    consumo_mensual = st.number_input(
        "Consumo mensual (kWh)",
        min_value=1.0,
        max_value=100000.0,
        value=867.0,
        step=10.0,
        help="Consumo total del mes."
    )

    generacion_diaria = st.number_input(
        "Generación solar diaria promedio (kWh)",
        min_value=0.0,
        max_value=5000.0,
        value=25.0,
        step=1.0,
        help="Energía solar promedio generada por día."
    )

    dias_mes = st.slider(
        "Días del mes",
        min_value=28,
        max_value=31,
        value=30,
        step=1
    )

    dias_operacion = st.slider(
        "Días de operación",
        min_value=1,
        max_value=dias_mes,
        value=15,
        step=1,
        help="Cantidad de días del mes en que la fábrica opera."
    )

    st.markdown("---")
    st.caption("En el escenario concentrado, los días no operativos tienen consumo cero.")

# --------------------------------------------------
# Cálculos base
# --------------------------------------------------
consumo_diario_promedio = consumo_mensual / dias_mes
consumo_diario_operativo = consumo_mensual / dias_operacion if dias_operacion > 0 else 0.0
generacion_mensual = generacion_diaria * dias_mes

# --------------------------------------------------
# Escenario 1: consumo promedio
# --------------------------------------------------
dias = list(range(1, dias_mes + 1))

consumo_promedio_dia = [consumo_diario_promedio] * dias_mes
generacion_dia = [generacion_diaria] * dias_mes

autoconsumo_promedio_dia = [
    min(c, g) for c, g in zip(consumo_promedio_dia, generacion_dia)
]
excedente_promedio_dia = [
    max(0.0, g - c) for c, g in zip(consumo_promedio_dia, generacion_dia)
]
red_promedio_dia = [
    max(0.0, c - g) for c, g in zip(consumo_promedio_dia, generacion_dia)
]
balance_promedio_dia = [
    g - c for c, g in zip(consumo_promedio_dia, generacion_dia)
]

# --------------------------------------------------
# Escenario 2: consumo concentrado
# --------------------------------------------------
consumo_concentrado_dia = []
for i in range(dias_mes):
    if i < dias_operacion:
        consumo_concentrado_dia.append(consumo_diario_operativo)
    else:
        consumo_concentrado_dia.append(0.0)

autoconsumo_concentrado_dia = [
    min(c, g) for c, g in zip(consumo_concentrado_dia, generacion_dia)
]
excedente_concentrado_dia = [
    max(0.0, g - c) for c, g in zip(consumo_concentrado_dia, generacion_dia)
]
red_concentrado_dia = [
    max(0.0, c - g) for c, g in zip(consumo_concentrado_dia, generacion_dia)
]
balance_concentrado_dia = [
    g - c for c, g in zip(consumo_concentrado_dia, generacion_dia)
]

# --------------------------------------------------
# Resumen mensual
# --------------------------------------------------
autoconsumo_promedio_mes = sum(autoconsumo_promedio_dia)
excedente_promedio_mes = sum(excedente_promedio_dia)
red_promedio_mes = sum(red_promedio_dia)
balance_promedio_mes = sum(balance_promedio_dia)

autoconsumo_concentrado_mes = sum(autoconsumo_concentrado_dia)
excedente_concentrado_mes = sum(excedente_concentrado_dia)
red_concentrado_mes = sum(red_concentrado_dia)
balance_concentrado_mes = sum(balance_concentrado_dia)

# --------------------------------------------------
# Métricas principales
# --------------------------------------------------
st.subheader("Métricas principales")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Consumo diario promedio", f"{consumo_diario_promedio:,.2f} kWh/día")
col2.metric("Consumo diario operativo", f"{consumo_diario_operativo:,.2f} kWh/día")
col3.metric("Generación mensual solar", f"{generacion_mensual:,.0f} kWh")
col4.metric("Días de operación", f"{dias_operacion} días")

# --------------------------------------------------
# Resumen comparativo
# --------------------------------------------------
st.subheader("Balance mensual por escenario")

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.markdown("### Escenario promedio")
    a1, a2, a3 = st.columns(3)
    a1.metric("Consumo cubierto", f"{autoconsumo_promedio_mes:,.0f} kWh")
    a2.metric("Excedente inyectado", f"{excedente_promedio_mes:,.0f} kWh")
    a3.metric("Compra a red", f"{red_promedio_mes:,.0f} kWh")
    st.metric("Balance neto mensual", f"{balance_promedio_mes:,.0f} kWh")

with res_col2:
    st.markdown("### Escenario concentrado")
    b1, b2, b3 = st.columns(3)
    b1.metric("Consumo cubierto", f"{autoconsumo_concentrado_mes:,.0f} kWh")
    b2.metric("Excedente inyectado", f"{excedente_concentrado_mes:,.0f} kWh")
    b3.metric("Compra a red", f"{red_concentrado_mes:,.0f} kWh")
    st.metric("Balance neto mensual", f"{balance_concentrado_mes:,.0f} kWh")

# --------------------------------------------------
# Gráfico 1: Escenario promedio
# --------------------------------------------------
st.subheader("Gráfico 1 - Escenario promedio")

fig1 = go.Figure()
fig1.add_trace(
    go.Scatter(
        x=dias,
        y=consumo_promedio_dia,
        mode="lines+markers",
        name="Consumo diario",
        line=dict(color="royalblue", width=3),
        marker=dict(size=7)
    )
)
fig1.add_trace(
    go.Scatter(
        x=dias,
        y=generacion_dia,
        mode="lines+markers",
        name="Generación solar",
        line=dict(color="goldenrod", width=3, dash="dot"),
        marker=dict(size=7)
    )
)
fig1.add_trace(
    go.Bar(
        x=dias,
        y=balance_promedio_dia,
        name="Balance diario (gen - consumo)",
        opacity=0.35
    )
)
fig1.update_layout(
    xaxis_title="Día del mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig1, use_container_width=True)

# --------------------------------------------------
# Gráfico 2: Escenario concentrado
# --------------------------------------------------
st.subheader("Gráfico 2 - Escenario concentrado")

fig2 = go.Figure()
fig2.add_trace(
    go.Scatter(
        x=dias,
        y=consumo_concentrado_dia,
        mode="lines+markers",
        name="Consumo diario operativo",
        line=dict(color="firebrick", width=3),
        marker=dict(size=7)
    )
)
fig2.add_trace(
    go.Scatter(
        x=dias,
        y=generacion_dia,
        mode="lines+markers",
        name="Generación solar",
        line=dict(color="goldenrod", width=3, dash="dot"),
        marker=dict(size=7)
    )
)
fig2.add_trace(
    go.Bar(
        x=dias,
        y=balance_concentrado_dia,
        name="Balance diario (gen - consumo)",
        opacity=0.35
    )
)
fig2.update_layout(
    xaxis_title="Día del mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# Gráfico 3: Comparación mensual
# --------------------------------------------------
st.subheader("Gráfico 3 - Comparación mensual de balances")

fig3 = go.Figure()
fig3.add_trace(
    go.Bar(
        x=["Promedio", "Concentrado"],
        y=[autoconsumo_promedio_mes, autoconsumo_concentrado_mes],
        name="Consumo cubierto por solar"
    )
)
fig3.add_trace(
    go.Bar(
        x=["Promedio", "Concentrado"],
        y=[excedente_promedio_mes, excedente_concentrado_mes],
        name="Excedente inyectado"
    )
)
fig3.add_trace(
    go.Bar(
        x=["Promedio", "Concentrado"],
        y=[red_promedio_mes, red_concentrado_mes],
        name="Compra a red"
    )
)
fig3.update_layout(
    barmode="group",
    xaxis_title="Escenario",
    yaxis_title="Energía mensual (kWh)",
    template="plotly_white",
    height=420,
    hovermode="x unified"
)
st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------
# Tabla diaria comparativa
# --------------------------------------------------
st.subheader("Detalle diario comparativo")

df = pd.DataFrame({
    "Día": dias,
    "Consumo promedio (kWh)": [round(x, 2) for x in consumo_promedio_dia],
    "Consumo concentrado (kWh)": [round(x, 2) for x in consumo_concentrado_dia],
    "Generación solar (kWh)": [round(x, 2) for x in generacion_dia],
    "Balance promedio (kWh)": [round(x, 2) for x in balance_promedio_dia],
    "Balance concentrado (kWh)": [round(x, 2) for x in balance_concentrado_dia],
    "Excedente promedio (kWh)": [round(x, 2) for x in excedente_promedio_dia],
    "Excedente concentrado (kWh)": [round(x, 2) for x in excedente_concentrado_dia],
})

st.dataframe(df, use_container_width=True)

# --------------------------------------------------
# Tabla resumen mensual
# --------------------------------------------------
st.subheader("Resumen mensual consolidado")

df_resumen = pd.DataFrame({
    "Escenario": ["Promedio", "Concentrado"],
    "Consumo mensual (kWh)": [round(consumo_mensual, 0), round(consumo_mensual, 0)],
    "Generación mensual (kWh)": [round(generacion_mensual, 0), round(generacion_mensual, 0)],
    "Consumo cubierto por solar (kWh)": [
        round(autoconsumo_promedio_mes, 0),
        round(autoconsumo_concentrado_mes, 0)
    ],
    "Excedente inyectado (kWh)": [
        round(excedente_promedio_mes, 0),
        round(excedente_concentrado_mes, 0)
    ],
    "Compra a red (kWh)": [
        round(red_promedio_mes, 0),
        round(red_concentrado_mes, 0)
    ],
    "Balance neto mensual (kWh)": [
        round(balance_promedio_mes, 0),
        round(balance_concentrado_mes, 0)
    ]
})

st.dataframe(df_resumen, use_container_width=True)

st.info(
    f"""
**Notas:**
- El consumo mensual ingresado es de **{consumo_mensual:,.0f} kWh**.
- La generación solar diaria promedio es de **{generacion_diaria:,.2f} kWh/día**.
- En el escenario promedio, el consumo se reparte en **{dias_mes} días**.
- En el escenario concentrado, el consumo se concentra en **{dias_operacion} días** y
  en los otros **{dias_mes - dias_operacion} días** toda la generación se considera excedente inyectado.
- El balance neto mensual se calcula como **generación - consumo**.
"""
)
