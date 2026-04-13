import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Simulador Solar Finca La Caramela",
    layout="wide"
)

st.title("Simulador de Ahorro con Energía Solar - Finca La Caramela")
st.markdown(
    """
Simulación con **consumos mensuales reales** y una lógica de operación más representativa:

- **Escenario distribuido:** el consumo mensual se reparte en todos los días del mes.
- **Escenario concentrado:** el consumo mensual se concentra en los días operativos.
- Posibilidad de evaluar:
  - **con inyección habilitada**
  - **sin inyección** (limitación de exportación)
"""
)

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
with st.sidebar:
    st.header("Configuración del sistema")

    potencia_panel = 0.585  # kWp por panel
    num_paneles = st.number_input(
        "Número de paneles",
        min_value=1,
        max_value=36,
        value=12,
        step=1,
        help="Cantidad de paneles solares de 585 Wp."
    )

    potencia_calculada = num_paneles * potencia_panel

    potencia = st.slider(
        "Potencia instalada (kWp DC)",
        min_value=0.5,
        max_value=20.0,
        value=float(round(potencia_calculada, 2)),
        step=0.1,
        help="Potencia pico total del sistema del lado DC."
    )

    # Sincronización simple
    if abs(potencia - potencia_calculada) > 0.05:
        num_paneles = int(round(potencia / potencia_panel))
        potencia = num_paneles * potencia_panel

    st.markdown(f"**Equivale a ≈ {num_paneles} paneles de 585 Wp**")
    st.markdown("---")

    tarifa = st.number_input(
        "Tarifa variable ($/kWh)",
        min_value=50.0,
        max_value=1000.0,
        value=226.09,
        step=10.0,
        help="Cargo variable por kWh consumido."
    )

    impuestos_pct = st.slider(
        "Impuestos y tasas (%)",
        min_value=0,
        max_value=80,
        value=38,
        step=1,
        help="Porcentaje aplicado sobre el subtotal de energía."
    )

    compensacion_pct = st.slider(
        "Reconocimiento por excedente (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
        help="Porcentaje del valor de tarifa reconocido por la energía inyectada."
    )

    st.markdown("---")

    dias_operacion = st.slider(
        "Días de operación por mes",
        min_value=1,
        max_value=30,
        value=15,
        step=1,
        help="Días efectivos de producción en el mes."
    )

    modo_inyeccion = st.radio(
        "Modo de excedente",
        options=["Con inyección habilitada", "Sin inyección (limitado)"],
        index=0,
        help="Con inyección: el excedente se reconoce. Sin inyección: el sistema limita exportación."
    )

    st.markdown("---")
    st.caption("Modelo basado en consumos históricos reales y operación concentrada en días productivos.")

# ---------------------------------------------------
# Datos reales de consumo
# ---------------------------------------------------
meses = [
    "Mar 25", "Abr 25", "May 25", "Jun 25", "Jul 25", "Ago 25",
    "Sep 25", "Oct 25", "Nov 25", "Dic 25", "Ene 26", "Feb 26"
]

consumo_real = [652, 450, 469, 603, 571, 661, 807, 849, 1023, 534, 748, 690]

# Días del mes para cada período
dias_mes = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28]

# Generación base mensual para sistema de 5 kWp DC (kWh/mes)
# Curva estacional aproximada para Buenos Aires / Ranchos
gen_base_5kw = [560, 450, 360, 280, 250, 400, 510, 600, 660, 690, 675, 620]

# ---------------------------------------------------
# Ajuste de generación por potencia y pérdidas
# ---------------------------------------------------
factor_perdidas = 0.85
generacion_dc = [g * (potencia / 5.0) * factor_perdidas for g in gen_base_5kw]

# Clipping simplificado por inversor AC 5 kW
potencia_inversor_ac = 5.0
horas_sol_eq_dia = [5.2, 4.7, 3.8, 3.0, 2.7, 3.7, 4.3, 4.9, 5.2, 5.4, 5.3, 5.0]
limite_mensual_ac = [potencia_inversor_ac * h * d for h, d in zip(horas_sol_eq_dia, dias_mes)]

generacion = [min(gdc, lim) for gdc, lim in zip(generacion_dc, limite_mensual_ac)]

# ---------------------------------------------------
# Función de simulación por escenario
# ---------------------------------------------------
def simular_escenario(consumos_mensuales, generaciones_mensuales, dias_mes_list, dias_op, inyeccion_habilitada):
    autoconsumo_mes = []
    excedente_mes = []
    compra_red_mes = []
    desperdicio_mes = []
    factura_sin_mes = []
    factura_con_mes = []
    ahorro_mes = []

    for consumo_mes, gen_mes, dias in zip(consumos_mensuales, generaciones_mensuales, dias_mes_list):
        dias_op_ajustados = min(dias_op, dias)
        dias_no_op = dias - dias_op_ajustados

        # Caso distribuido
        consumo_diario = consumo_mes / dias if dias > 0 else 0
        gen_diaria = gen_mes / dias if dias > 0 else 0

        autoconsumo_distribuido = min(consumo_diario, gen_diaria) * dias
        excedente_distribuido = max(0, gen_diaria - consumo_diario) * dias if inyeccion_habilitada else 0
        desperdicio_distribuido = max(0, gen_diaria - consumo_diario) * dias if not inyeccion_habilitada else 0
        compra_red_distribuido = max(0, consumo_diario - gen_diaria) * dias

        subtotal_sin = consumo_mes * tarifa
        credito_excedente = excedente_distribuido * tarifa * (compensacion_pct / 100)
        subtotal_con = (compra_red_distribuido * tarifa) - credito_excedente

        factura_sin = subtotal_sin * (1 + impuestos_pct / 100)
        factura_con = subtotal_con * (1 + impuestos_pct / 100)
        ahorro = factura_sin - factura_con

        autoconsumo_mes.append(autoconsumo_distribuido)
        excedente_mes.append(excedente_distribuido)
        compra_red_mes.append(compra_red_distribuido)
        desperdicio_mes.append(desperdicio_distribuido)
        factura_sin_mes.append(factura_sin)
        factura_con_mes.append(factura_con)
        ahorro_mes.append(ahorro)

    return {
        "autoconsumo": autoconsumo_mes,
        "excedente": excedente_mes,
        "compra_red": compra_red_mes,
        "desperdicio": desperdicio_mes,
        "factura_sin": factura_sin_mes,
        "factura_con": factura_con_mes,
        "ahorro": ahorro_mes,
    }


def simular_concentrado(consumos_mensuales, generaciones_mensuales, dias_mes_list, dias_op, inyeccion_habilitada):
    autoconsumo_mes = []
    excedente_mes = []
    compra_red_mes = []
    desperdicio_mes = []
    factura_sin_mes = []
    factura_con_mes = []
    ahorro_mes = []
    consumo_diario_operativo_mes = []
    generacion_diaria_mes = []

    for consumo_mes, gen_mes, dias in zip(consumos_mensuales, generaciones_mensuales, dias_mes_list):
        dias_op_ajustados = min(dias_op, dias)
        dias_no_op = dias - dias_op_ajustados

        gen_diaria = gen_mes / dias if dias > 0 else 0
        consumo_diario_operativo = consumo_mes / dias_op_ajustados if dias_op_ajustados > 0 else 0

        # Días operativos
        autoconsumo_operativo = min(consumo_diario_operativo, gen_diaria) * dias_op_ajustados
        compra_red_operativo = max(0, consumo_diario_operativo - gen_diaria) * dias_op_ajustados
        excedente_operativo = max(0, gen_diaria - consumo_diario_operativo) * dias_op_ajustados

        # Días no operativos
        autoconsumo_no_operativo = 0
        compra_red_no_operativo = 0
        excedente_no_operativo = gen_diaria * dias_no_op

        excedente_total_bruto = excedente_operativo + excedente_no_operativo

        if inyeccion_habilitada:
            excedente_total = excedente_total_bruto
            desperdicio_total = 0
        else:
            excedente_total = 0
            desperdicio_total = excedente_total_bruto

        autoconsumo_total = autoconsumo_operativo + autoconsumo_no_operativo
        compra_red_total = compra_red_operativo + compra_red_no_operativo

        subtotal_sin = consumo_mes * tarifa
        credito_excedente = excedente_total * tarifa * (compensacion_pct / 100)
        subtotal_con = (compra_red_total * tarifa) - credito_excedente

        factura_sin = subtotal_sin * (1 + impuestos_pct / 100)
        factura_con = subtotal_con * (1 + impuestos_pct / 100)
        ahorro = factura_sin - factura_con

        autoconsumo_mes.append(autoconsumo_total)
        excedente_mes.append(excedente_total)
        compra_red_mes.append(compra_red_total)
        desperdicio_mes.append(desperdicio_total)
        factura_sin_mes.append(factura_sin)
        factura_con_mes.append(factura_con)
        ahorro_mes.append(ahorro)
        consumo_diario_operativo_mes.append(consumo_diario_operativo)
        generacion_diaria_mes.append(gen_diaria)

    return {
        "autoconsumo": autoconsumo_mes,
        "excedente": excedente_mes,
        "compra_red": compra_red_mes,
        "desperdicio": desperdicio_mes,
        "factura_sin": factura_sin_mes,
        "factura_con": factura_con_mes,
        "ahorro": ahorro_mes,
        "consumo_diario_operativo": consumo_diario_operativo_mes,
        "generacion_diaria": generacion_diaria_mes,
    }

# ---------------------------------------------------
# Simulación de ambos escenarios
# ---------------------------------------------------
inyeccion_habilitada = modo_inyeccion == "Con inyección habilitada"

resultado_distribuido = simular_escenario(
    consumo_real,
    generacion,
    dias_mes,
    dias_operacion,
    inyeccion_habilitada
)

resultado_concentrado = simular_concentrado(
    consumo_real,
    generacion,
    dias_mes,
    dias_operacion,
    inyeccion_habilitada
)

# ---------------------------------------------------
# Métricas principales
# ---------------------------------------------------
st.subheader("Métricas principales")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Consumo anual real",
    f"{sum(consumo_real):,.0f} kWh"
)

col2.metric(
    "Generación anual estimada",
    f"{sum(generacion):,.0f} kWh"
)

col3.metric(
    "Ahorro anual - Distribuido",
    f"${sum(resultado_distribuido['ahorro']):,.0f}"
)

col4.metric(
    "Ahorro anual - Concentrado",
    f"${sum(resultado_concentrado['ahorro']):,.0f}"
)

# ---------------------------------------------------
# Métricas comparativas
# ---------------------------------------------------
st.subheader("Comparación energética anual")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Autoconsumo anual - Distribuido",
    f"{sum(resultado_distribuido['autoconsumo']):,.0f} kWh"
)

c2.metric(
    "Autoconsumo anual - Concentrado",
    f"{sum(resultado_concentrado['autoconsumo']):,.0f} kWh"
)

c3.metric(
    "Excedente anual - Distribuido",
    f"{sum(resultado_distribuido['excedente']):,.0f} kWh"
)

c4.metric(
    "Excedente anual - Concentrado",
    f"{sum(resultado_concentrado['excedente']):,.0f} kWh"
)

# ---------------------------------------------------
# Gráfico 1: Consumo real vs generación
# ---------------------------------------------------
st.subheader("Evolución mensual del consumo y la generación")

fig1 = go.Figure()
fig1.add_trace(
    go.Scatter(
        x=meses,
        y=consumo_real,
        mode="lines+markers",
        name="Consumo real (kWh)",
        line=dict(color="royalblue", width=4),
        marker=dict(size=9, symbol="circle")
    )
)
fig1.add_trace(
    go.Scatter(
        x=meses,
        y=generacion,
        mode="lines+markers",
        name="Generación solar (kWh)",
        line=dict(color="goldenrod", width=4, dash="dot"),
        marker=dict(size=9, symbol="square")
    )
)
fig1.update_layout(
    xaxis_title="Mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig1, use_container_width=True)

# ---------------------------------------------------
# Gráfico 2: Balance energético mensual - Distribuido
# ---------------------------------------------------
st.subheader("Balance mensual - Escenario distribuido")

fig2 = go.Figure()
fig2.add_trace(
    go.Bar(
        x=meses,
        y=resultado_distribuido["autoconsumo"],
        name="Consumo cubierto por solar",
        marker_color="seagreen"
    )
)
fig2.add_trace(
    go.Bar(
        x=meses,
        y=resultado_distribuido["excedente"],
        name="Excedente inyectado",
        marker_color="orange"
    )
)
fig2.add_trace(
    go.Bar(
        x=meses,
        y=resultado_distribuido["compra_red"],
        name="Compra a red",
        marker_color="royalblue"
    )
)
if not inyeccion_habilitada:
    fig2.add_trace(
        go.Bar(
            x=meses,
            y=resultado_distribuido["desperdicio"],
            name="Generación no aprovechada",
            marker_color="gray"
        )
    )

fig2.update_layout(
    barmode="group",
    xaxis_title="Mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=450,
    hovermode="x unified"
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# Gráfico 3: Balance energético mensual - Concentrado
# ---------------------------------------------------
st.subheader("Balance mensual - Escenario concentrado")

fig3 = go.Figure()
fig3.add_trace(
    go.Bar(
        x=meses,
        y=resultado_concentrado["autoconsumo"],
        name="Consumo cubierto por solar",
        marker_color="seagreen"
    )
)
fig3.add_trace(
    go.Bar(
        x=meses,
        y=resultado_concentrado["excedente"],
        name="Excedente inyectado",
        marker_color="orange"
    )
)
fig3.add_trace(
    go.Bar(
        x=meses,
        y=resultado_concentrado["compra_red"],
        name="Compra a red",
        marker_color="royalblue"
    )
)
if not inyeccion_habilitada:
    fig3.add_trace(
        go.Bar(
            x=meses,
            y=resultado_concentrado["desperdicio"],
            name="Generación no aprovechada",
            marker_color="gray"
        )
    )

fig3.update_layout(
    barmode="group",
    xaxis_title="Mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=450,
    hovermode="x unified"
)
st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------
# Gráfico 4: Comparación de autoconsumo y excedente
# ---------------------------------------------------
st.subheader("Comparación de escenarios")

fig4 = go.Figure()
fig4.add_trace(
    go.Bar(
        x=meses,
        y=resultado_distribuido["autoconsumo"],
        name="Autoconsumo - Distribuido",
        marker_color="mediumseagreen"
    )
)
fig4.add_trace(
    go.Bar(
        x=meses,
        y=resultado_concentrado["autoconsumo"],
        name="Autoconsumo - Concentrado",
        marker_color="darkgreen"
    )
)
fig4.add_trace(
    go.Scatter(
        x=meses,
        y=resultado_distribuido["excedente"],
        mode="lines+markers",
        name="Excedente - Distribuido",
        line=dict(color="darkorange", width=3),
        marker=dict(size=7)
    )
)
fig4.add_trace(
    go.Scatter(
        x=meses,
        y=resultado_concentrado["excedente"],
        mode="lines+markers",
        name="Excedente - Concentrado",
        line=dict(color="firebrick", width=3, dash="dot"),
        marker=dict(size=7)
    )
)
fig4.update_layout(
    xaxis_title="Mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------
# Gráfico 5: Ahorro mensual comparativo
# ---------------------------------------------------
st.subheader("Ahorro mensual estimado")

fig5 = go.Figure()
fig5.add_trace(
    go.Bar(
        x=meses,
        y=resultado_distribuido["ahorro"],
        name="Ahorro - Distribuido",
        marker_color="darkgreen",
        text=[f"${v:,.0f}" for v in resultado_distribuido["ahorro"]],
        textposition="outside"
    )
)
fig5.add_trace(
    go.Bar(
        x=meses,
        y=resultado_concentrado["ahorro"],
        name="Ahorro - Concentrado",
        marker_color="teal",
        text=[f"${v:,.0f}" for v in resultado_concentrado["ahorro"]],
        textposition="outside"
    )
)
fig5.update_layout(
    barmode="group",
    xaxis_title="Mes",
    yaxis_title="Ahorro ($)",
    template="plotly_white",
    height=450,
    hovermode="x unified",
    yaxis=dict(tickformat="$,.0f")
)
st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------
# Tabla resumen principal
# ---------------------------------------------------
st.subheader("Detalle mensual comparativo")

df = pd.DataFrame({
    "Mes": meses,
    "Días del mes": dias_mes,
    "Consumo real (kWh)": consumo_real,
    "Generación solar (kWh)": [round(v, 1) for v in generacion],

    "Autoconsumo Distribuido (kWh)": [round(v, 1) for v in resultado_distribuido["autoconsumo"]],
    "Excedente Distribuido (kWh)": [round(v, 1) for v in resultado_distribuido["excedente"]],
    "Compra red Distribuido (kWh)": [round(v, 1) for v in resultado_distribuido["compra_red"]],
    "Ahorro Distribuido ($)": [round(v, 0) for v in resultado_distribuido["ahorro"]],

    "Consumo diario operativo (kWh/día)": [round(v, 1) for v in resultado_concentrado["consumo_diario_operativo"]],
    "Generación diaria (kWh/día)": [round(v, 1) for v in resultado_concentrado["generacion_diaria"]],
    "Autoconsumo Concentrado (kWh)": [round(v, 1) for v in resultado_concentrado["autoconsumo"]],
    "Excedente Concentrado (kWh)": [round(v, 1) for v in resultado_concentrado["excedente"]],
    "Compra red Concentrado (kWh)": [round(v, 1) for v in resultado_concentrado["compra_red"]],
    "Ahorro Concentrado ($)": [round(v, 0) for v in resultado_concentrado["ahorro"]],
})

if not inyeccion_habilitada:
    df["Generación no aprovechada Distribuido (kWh)"] = [round(v, 1) for v in resultado_distribuido["desperdicio"]]
    df["Generación no aprovechada Concentrado (kWh)"] = [round(v, 1) for v in resultado_concentrado["desperdicio"]]

st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# Resumen anual consolidado
# ---------------------------------------------------
st.subheader("Resumen anual consolidado")

resumen = pd.DataFrame({
    "Escenario": ["Distribuido", "Concentrado"],
    "Consumo anual (kWh)": [sum(consumo_real), sum(consumo_real)],
    "Generación anual (kWh)": [round(sum(generacion), 1), round(sum(generacion), 1)],
    "Autoconsumo anual (kWh)": [
        round(sum(resultado_distribuido["autoconsumo"]), 1),
        round(sum(resultado_concentrado["autoconsumo"]), 1),
    ],
    "Excedente anual (kWh)": [
        round(sum(resultado_distribuido["excedente"]), 1),
        round(sum(resultado_concentrado["excedente"]), 1),
    ],
    "Compra anual a red (kWh)": [
        round(sum(resultado_distribuido["compra_red"]), 1),
        round(sum(resultado_concentrado["compra_red"]), 1),
    ],
    "Ahorro anual ($)": [
        round(sum(resultado_distribuido["ahorro"]), 0),
        round(sum(resultado_concentrado["ahorro"]), 0),
    ],
})

if not inyeccion_habilitada:
    resumen["Generación no aprovechada anual (kWh)"] = [
        round(sum(resultado_distribuido["desperdicio"]), 1),
        round(sum(resultado_concentrado["desperdicio"]), 1),
    ]

st.dataframe(resumen, use_container_width=True)

# ---------------------------------------------------
# Notas
# ---------------------------------------------------
st.info(
    f"""
**Notas del modelo**

- Consumos históricos considerados: **marzo 2025 a febrero 2026**.
- Días de operación configurados: **{dias_operacion} días por mes**.
- En el escenario concentrado, el consumo mensual se reparte solo en los días operativos.
- En los días no operativos:
  - **con inyección habilitada**, la generación se considera excedente inyectado;
  - **sin inyección**, esa energía se considera no aprovechada por limitación.
- La generación solar se ajusta por:
  - potencia instalada,
  - pérdidas del sistema (**15%**),
  - y un límite simplificado del inversor de **5 kW AC**.
- El ahorro económico se calcula con tarifa variable e impuestos configurables.
"""
)
