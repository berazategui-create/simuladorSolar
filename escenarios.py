import streamlit as st
import plotly.graph_objects as go

# Parámetros iniciales
consumo_mensual = st.number_input("Consumo mensual de la fábrica (kWh)", value=3000)
generacion_diaria = st.number_input("Generación solar diaria promedio (kWh)", value=150)

dias_mes = 30
dias_operativos = 15

# Escenario 1: consumo distribuido en 30 días
consumo_diario_promedio = consumo_mensual / dias_mes
consumo_promedio = [consumo_diario_promedio] * dias_mes
generacion_promedio = [generacion_diaria] * dias_mes
balance_promedio = [g - c for g, c in zip(generacion_promedio, consumo_promedio)]

# Escenario 2: consumo concentrado en 15 días
consumo_diario_operativo = consumo_mensual / dias_operativos
consumo_concentrado = [consumo_diario_operativo if d < dias_operativos else 0 for d in range(dias_mes)]
generacion_concentrado = [generacion_diaria] * dias_mes
balance_concentrado = [g - c for g, c in zip(generacion_concentrado, consumo_concentrado)]

# Mostrar resultados
st.subheader("Escenario 1: Consumo promedio (30 días)")
st.write(f"Consumo diario promedio: {consumo_diario_promedio:.2f} kWh")

st.subheader("Escenario 2: Consumo concentrado (15 días)")
st.write(f"Consumo diario operativo: {consumo_diario_operativo:.2f} kWh")
st.write("Los días restantes la fábrica no consume y toda la generación se inyecta.")

# Gráfico comparativo
fig = go.Figure()

fig.add_trace(go.Scatter(y=consumo_promedio, name="Consumo promedio (30 días)", line=dict(color="red")))
fig.add_trace(go.Scatter(y=consumo_concentrado, name="Consumo concentrado (15 días)", line=dict(color="orange")))
fig.add_trace(go.Scatter(y=generacion_promedio, name="Generación solar", line=dict(color="green")))
fig.add_trace(go.Scatter(y=balance_promedio, name="Balance promedio", line=dict(color="blue", dash="dot")))
fig.add_trace(go.Scatter(y=balance_concentrado, name="Balance concentrado", line=dict(color="purple", dash="dot")))

fig.update_layout(title="Comparación de escenarios de consumo",
                  xaxis_title="Días del mes",
                  yaxis_title="kWh")

st.plotly_chart(fig)
