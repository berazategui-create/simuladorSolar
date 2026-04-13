import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Simulador Solar Finca La Caramela - PRO",
    layout="wide"
)

st.title("Simulador de Ahorro con Energía Solar - Finca La Caramela PRO")
st.markdown(
    """
Simulación con **consumos mensuales reales** y comparación de configuraciones técnicas.

Este simulador permite evaluar:

- comportamiento mensual real del consumo,
- operación distribuida vs concentrada,
- autoconsumo, excedente y compra a red,
- clipping estimado del inversor,
- y comparación entre configuraciones de paneles e inversor.
"""
)

# ---------------------------------------------------
# DATOS BASE
# ---------------------------------------------------
meses = [
    "Mar 25", "Abr 25", "May 25", "Jun 25", "Jul 25", "Ago 25",
    "Sep 25", "Oct 25", "Nov 25", "Dic 25", "Ene 26", "Feb 26"
]

# Consumos históricos reales La Caramela
consumo_real = [652, 450, 469, 603, 571, 661, 807, 849, 1023, 534, 748, 690]

# Días reales por mes
dias_mes = [31, 30, 31, 30, 31, 31, 30, 31, 30, 31, 31, 28]

# Base de generación para un sistema de 5 kWp DC (estimación mensual)
gen_base_5kw = [560, 450, 360, 280, 250, 400, 510, 600, 660, 690, 675, 620]

# Horas solares equivalentes diarias usadas para límite mensual AC simplificado
horas_sol_eq_dia = [5.2, 4.7, 3.8, 3.0, 2.7, 3.7, 4.3, 4.9, 5.2, 5.4, 5.3, 5.0]

potencia_panel = 0.585  # kWp

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    configuracion = st.selectbox(
        "Configuración a evaluar",
        [
            "12 paneles + inversor 5 kW",
            "16 paneles + inversor 5 kW",
            "16 paneles + inversor 8 kW",
            "Personalizado"
        ]
    )

    if configuracion == "12 paneles + inversor 5 kW":
        num_paneles = 12
        potencia_inversor_ac = 5.0
    elif configuracion == "16 paneles + inversor 5 kW":
        num_paneles = 16
        potencia_inversor_ac = 5.0
    elif configuracion == "16 paneles + inversor 8 kW":
        num_paneles = 16
        potencia_inversor_ac = 8.0
    else:
        num_paneles = st.number_input(
            "Número de paneles",
            min_value=1,
            max_value=40,
            value=12,
            step=1
        )
        potencia_inversor_ac = st.slider(
            "Potencia del inversor AC (kW)",
            min_value=1.0,
            max_value=15.0,
            value=5.0,
            step=0.5
        )

    potencia_dc = num_paneles * potencia_panel

    st.markdown(f"**Potencia DC instalada:** {potencia_dc:.2f} kWp")
    st.markdown(f"**Potencia inversor AC:** {potencia_inversor_ac:.2f} kW")
    st.markdown("---")

    dias_operacion = st.slider(
        "Días de operación por mes",
        min_value=1,
        max_value=30,
        value=15,
        step=1,
        help="Cantidad de días de producción efectiva por mes."
    )

    modo_consumo = st.radio(
        "Modelo de consumo",
        options=["Distribuido en todo el mes", "Concentrado en días operativos", "Comparar ambos"],
        index=2
    )

    modo_inyeccion = st.radio(
        "Modo de excedente",
        options=["Con inyección habilitada", "Sin inyección (limitado)"],
        index=0
    )

    tarifa = st.number_input(
        "Tarifa variable ($/kWh)",
        min_value=50.0,
        max_value=1000.0,
        value=226.09,
        step=10.0
    )

    impuestos_pct = st.slider(
        "Impuestos y tasas (%)",
        min_value=0,
        max_value=80,
        value=38,
        step=1
    )

    compensacion_pct = st.slider(
        "Reconocimiento excedente (%)",
        min_value=0,
        max_value=100,
        value=40,
        step=5
    )

    factor_perdidas = st.slider(
        "Pérdidas del sistema (%)",
        min_value=0,
        max_value=30,
        value=15,
        step=1
    ) / 100

    st.markdown("---")
    st.caption("El clipping se estima de forma simplificada a nivel mensual.")

# ---------------------------------------------------
# FUNCIONES
# ---------------------------------------------------
def calcular_generacion_y_clipping(potencia_dc_kwp, potencia_inv_ac_kw, perdidas):
    generacion_dc = [g * (potencia_dc_kwp / 5.0) * (1 - perdidas) for g in gen_base_5kw]
    limite_mensual_ac = [potencia_inv_ac_kw * h * d for h, d in zip(horas_sol_eq_dia, dias_mes)]
    generacion_ac = [min(gdc, lim) for gdc, lim in zip(generacion_dc, limite_mensual_ac)]
    clipping = [max(0, gdc - gac) for gdc, gac in zip(generacion_dc, generacion_ac)]
    return generacion_dc, generacion_ac, clipping, limite_mensual_ac


def simular_distribuido(consumos_mensuales, generaciones_mensuales, dias_mes_list, inyeccion_habilitada):
    autoconsumo = []
    excedente = []
    compra_red = []
    desperdicio = []
    factura_sin = []
    factura_con = []
    ahorro = []
    cobertura = []

    for consumo_mes, gen_mes, dias in zip(consumos_mensuales, generaciones_mensuales, dias_mes_list):
        consumo_diario = consumo_mes / dias if dias > 0 else 0
        gen_diaria = gen_mes / dias if dias > 0 else 0

        autoc = min(consumo_diario, gen_diaria) * dias
        exced_bruto = max(0, gen_diaria - consumo_diario) * dias
        red = max(0, consumo_diario - gen_diaria) * dias

        if inyeccion_habilitada:
            exced = exced_bruto
            desp = 0
        else:
            exced = 0
            desp = exced_bruto

        subtotal_sin = consumo_mes * tarifa
        credito_excedente = exced * tarifa * (compensacion_pct / 100)
        subtotal_con = (red * tarifa) - credito_excedente

        fact_sin = subtotal_sin * (1 + impuestos_pct / 100)
        fact_con = subtotal_con * (1 + impuestos_pct / 100)
        ah = fact_sin - fact_con

        autoconsumo.append(autoc)
        excedente.append(exced)
        compra_red.append(red)
        desperdicio.append(desp)
        factura_sin.append(fact_sin)
        factura_con.append(fact_con)
        ahorro.append(ah)
        cobertura.append((autoc / consumo_mes * 100) if consumo_mes > 0 else 0)

    return {
        "autoconsumo": autoconsumo,
        "excedente": excedente,
        "compra_red": compra_red,
        "desperdicio": desperdicio,
        "factura_sin": factura_sin,
        "factura_con": factura_con,
        "ahorro": ahorro,
        "cobertura_pct": cobertura
    }


def simular_concentrado(consumos_mensuales, generaciones_mensuales, dias_mes_list, dias_op, inyeccion_habilitada):
    autoconsumo = []
    excedente = []
    compra_red = []
    desperdicio = []
    factura_sin = []
    factura_con = []
    ahorro = []
    cobertura = []
    consumo_diario_operativo = []
    generacion_diaria = []

    for consumo_mes, gen_mes, dias in zip(consumos_mensuales, generaciones_mensuales, dias_mes_list):
        dias_op_aj = min(dias_op, dias)
        dias_no_op = dias - dias_op_aj

        gen_dia = gen_mes / dias if dias > 0 else 0
        cons_dia_op = consumo_mes / dias_op_aj if dias_op_aj > 0 else 0

        autoc_op = min(cons_dia_op, gen_dia) * dias_op_aj
        red_op = max(0, cons_dia_op - gen_dia) * dias_op_aj
        exced_op = max(0, gen_dia - cons_dia_op) * dias_op_aj

        autoc_noop = 0
        red_noop = 0
        exced_noop = gen_dia * dias_no_op

        exced_bruto = exced_op + exced_noop

        if inyeccion_habilitada:
            exced = exced_bruto
            desp = 0
        else:
            exced = 0
            desp = exced_bruto

        autoc = autoc_op + autoc_noop
        red = red_op + red_noop

        subtotal_sin = consumo_mes * tarifa
        credito_excedente = exced * tarifa * (compensacion_pct / 100)
        subtotal_con = (red * tarifa) - credito_excedente

        fact_sin = subtotal_sin * (1 + impuestos_pct / 100)
        fact_con = subtotal_con * (1 + impuestos_pct / 100)
        ah = fact_sin - fact_con

        autoconsumo.append(autoc)
        excedente.append(exced)
        compra_red.append(red)
        desperdicio.append(desp)
        factura_sin.append(fact_sin)
        factura_con.append(fact_con)
        ahorro.append(ah)
        cobertura.append((autoc / consumo_mes * 100) if consumo_mes > 0 else 0)
        consumo_diario_operativo.append(cons_dia_op)
        generacion_diaria.append(gen_dia)

    return {
        "autoconsumo": autoconsumo,
        "excedente": excedente,
        "compra_red": compra_red,
        "desperdicio": desperdicio,
        "factura_sin": factura_sin,
        "factura_con": factura_con,
        "ahorro": ahorro,
        "cobertura_pct": cobertura,
        "consumo_diario_operativo": consumo_diario_operativo,
        "generacion_diaria": generacion_diaria
    }

# ---------------------------------------------------
# CÁLCULOS BASE
# ---------------------------------------------------
inyeccion_habilitada = modo_inyeccion == "Con inyección habilitada"

generacion_dc, generacion_ac, clipping_mensual, limite_mensual_ac = calcular_generacion_y_clipping(
    potencia_dc, potencia_inversor_ac, factor_perdidas
)

ratio_dc_ac = potencia_dc / potencia_inversor_ac if potencia_inversor_ac > 0 else 0

resultado_distribuido = simular_distribuido(
    consumo_real,
    generacion_ac,
    dias_mes,
    inyeccion_habilitada
)

resultado_concentrado = simular_concentrado(
    consumo_real,
    generacion_ac,
    dias_mes,
    dias_operacion,
    inyeccion_habilitada
)

# ---------------------------------------------------
# KPIs
# ---------------------------------------------------
st.subheader("Indicadores clave")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Potencia DC", f"{potencia_dc:.2f} kWp")
k2.metric("Potencia AC inversor", f"{potencia_inversor_ac:.2f} kW")
k3.metric("Ratio DC/AC", f"{ratio_dc_ac:.2f}")
k4.metric("Generación AC anual", f"{sum(generacion_ac):,.0f} kWh")
k5.metric("Clipping anual", f"{sum(clipping_mensual):,.0f} kWh")

if ratio_dc_ac <= 1.35:
    st.success("Sobredimensionamiento DC/AC bajo a moderado.")
elif ratio_dc_ac <= 1.55:
    st.warning("Sobredimensionamiento DC/AC alto pero todavía razonable.")
elif ratio_dc_ac <= 1.75:
    st.warning("Sobredimensionamiento DC/AC agresivo. Revisar clipping y criterio de diseño.")
else:
    st.error("Sobredimensionamiento DC/AC muy alto. Conviene revisar inversor o configuración.")

# ---------------------------------------------------
# MÉTRICAS ENERGÉTICAS
# ---------------------------------------------------
st.subheader("Resumen energético anual")

if modo_consumo == "Distribuido en todo el mes":
    resultado_principal = resultado_distribuido
    nombre_escenario = "Distribuido"
elif modo_consumo == "Concentrado en días operativos":
    resultado_principal = resultado_concentrado
    nombre_escenario = "Concentrado"
else:
    resultado_principal = resultado_concentrado
    nombre_escenario = "Concentrado"

autoconsumo_pct = (
    sum(resultado_principal["autoconsumo"]) / sum(generacion_ac) * 100
    if sum(generacion_ac) > 0 else 0
)

cobertura_pct = (
    sum(resultado_principal["autoconsumo"]) / sum(consumo_real) * 100
    if sum(consumo_real) > 0 else 0
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Autoconsumo anual", f"{sum(resultado_principal['autoconsumo']):,.0f} kWh")
m2.metric("Excedente anual", f"{sum(resultado_principal['excedente']):,.0f} kWh")
m3.metric("Compra anual a red", f"{sum(resultado_principal['compra_red']):,.0f} kWh")
m4.metric("Ahorro anual", f"${sum(resultado_principal['ahorro']):,.0f}")

m5, m6 = st.columns(2)
m5.metric("Autoconsumo del sistema", f"{autoconsumo_pct:.1f}%")
m6.metric("Cobertura del consumo", f"{cobertura_pct:.1f}%")

if not inyeccion_habilitada:
    st.metric(
        "Generación no aprovechada anual",
        f"{sum(resultado_principal['desperdicio']):,.0f} kWh"
    )

# ---------------------------------------------------
# GRÁFICO 1
# ---------------------------------------------------
st.subheader("Consumo mensual real vs generación solar")

fig1 = go.Figure()
fig1.add_trace(
    go.Scatter(
        x=meses,
        y=consumo_real,
        mode="lines+markers",
        name="Consumo real (kWh)",
        line=dict(color="royalblue", width=4),
        marker=dict(size=9)
    )
)
fig1.add_trace(
    go.Scatter(
        x=meses,
        y=generacion_ac,
        mode="lines+markers",
        name="Generación AC aprovechable (kWh)",
        line=dict(color="goldenrod", width=4, dash="dot"),
        marker=dict(size=9)
    )
)
fig1.add_trace(
    go.Scatter(
        x=meses,
        y=generacion_dc,
        mode="lines+markers",
        name="Generación DC estimada (kWh)",
        line=dict(color="gray", width=2, dash="dash"),
        marker=dict(size=6)
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
# GRÁFICO 2 - CLIPPING
# ---------------------------------------------------
st.subheader("Clipping estimado del inversor")

fig_clip = go.Figure()
fig_clip.add_trace(
    go.Bar(
        x=meses,
        y=generacion_dc,
        name="Generación DC estimada",
        marker_color="gold"
    )
)
fig_clip.add_trace(
    go.Bar(
        x=meses,
        y=generacion_ac,
        name="Generación AC aprovechable",
        marker_color="seagreen"
    )
)
fig_clip.add_trace(
    go.Scatter(
        x=meses,
        y=clipping_mensual,
        mode="lines+markers",
        name="Clipping",
        line=dict(color="firebrick", width=3),
        marker=dict(size=8)
    )
)
fig_clip.update_layout(
    barmode="group",
    xaxis_title="Mes",
    yaxis_title="Energía (kWh)",
    template="plotly_white",
    height=450,
    hovermode="x unified"
)
st.plotly_chart(fig_clip, use_container_width=True)

# ---------------------------------------------------
# FUNCIÓN PARA GRAFICAR ESCENARIO
# ---------------------------------------------------
def graficar_balance_escenario(titulo, resultado):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=meses,
            y=resultado["autoconsumo"],
            name="Consumo cubierto por solar",
            marker_color="seagreen"
        )
    )
    fig.add_trace(
        go.Bar(
            x=meses,
            y=resultado["excedente"],
            name="Excedente inyectado",
            marker_color="orange"
        )
    )
    fig.add_trace(
        go.Bar(
            x=meses,
            y=resultado["compra_red"],
            name="Compra a red",
            marker_color="royalblue"
        )
    )
    if not inyeccion_habilitada:
        fig.add_trace(
            go.Bar(
                x=meses,
                y=resultado["desperdicio"],
                name="Generación no aprovechada",
                marker_color="gray"
            )
        )
    fig.update_layout(
        title=titulo,
        barmode="group",
        xaxis_title="Mes",
        yaxis_title="Energía (kWh)",
        template="plotly_white",
        height=450,
        hovermode="x unified"
    )
    return fig

# ---------------------------------------------------
# GRÁFICOS DE ESCENARIOS
# ---------------------------------------------------
if modo_consumo == "Distribuido en todo el mes":
    st.plotly_chart(
        graficar_balance_escenario("Balance mensual - Escenario distribuido", resultado_distribuido),
        use_container_width=True
    )
elif modo_consumo == "Concentrado en días operativos":
    st.plotly_chart(
        graficar_balance_escenario("Balance mensual - Escenario concentrado", resultado_concentrado),
        use_container_width=True
    )
else:
    st.subheader("Comparación de escenarios")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            graficar_balance_escenario("Escenario distribuido", resultado_distribuido),
            use_container_width=True
        )
    with c2:
        st.plotly_chart(
            graficar_balance_escenario("Escenario concentrado", resultado_concentrado),
            use_container_width=True
        )

# ---------------------------------------------------
# GRÁFICO COMPARATIVO
# ---------------------------------------------------
if modo_consumo == "Comparar ambos":
    st.subheader("Autoconsumo y excedente - comparación directa")

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
# AHORRO MENSUAL
# ---------------------------------------------------
st.subheader("Ahorro mensual estimado")

fig5 = go.Figure()

if modo_consumo == "Distribuido en todo el mes":
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
elif modo_consumo == "Concentrado en días operativos":
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
else:
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
# TABLAS
# ---------------------------------------------------
st.subheader("Detalle mensual técnico")

df = pd.DataFrame({
    "Mes": meses,
    "Días mes": dias_mes,
    "Consumo real (kWh)": consumo_real,
    "Generación DC (kWh)": [round(v, 1) for v in generacion_dc],
    "Generación AC (kWh)": [round(v, 1) for v in generacion_ac],
    "Clipping (kWh)": [round(v, 1) for v in clipping_mensual],
    "Autoconsumo Dist. (kWh)": [round(v, 1) for v in resultado_distribuido["autoconsumo"]],
    "Excedente Dist. (kWh)": [round(v, 1) for v in resultado_distribuido["excedente"]],
    "Compra red Dist. (kWh)": [round(v, 1) for v in resultado_distribuido["compra_red"]],
    "Ahorro Dist. ($)": [round(v, 0) for v in resultado_distribuido["ahorro"]],
    "Consumo diario op. (kWh/día)": [round(v, 1) for v in resultado_concentrado["consumo_diario_operativo"]],
    "Gen diaria (kWh/día)": [round(v, 1) for v in resultado_concentrado["generacion_diaria"]],
    "Autoconsumo Conc. (kWh)": [round(v, 1) for v in resultado_concentrado["autoconsumo"]],
    "Excedente Conc. (kWh)": [round(v, 1) for v in resultado_concentrado["excedente"]],
    "Compra red Conc. (kWh)": [round(v, 1) for v in resultado_concentrado["compra_red"]],
    "Ahorro Conc. ($)": [round(v, 0) for v in resultado_concentrado["ahorro"]],
})

if not inyeccion_habilitada:
    df["No aprovechada Dist. (kWh)"] = [round(v, 1) for v in resultado_distribuido["desperdicio"]]
    df["No aprovechada Conc. (kWh)"] = [round(v, 1) for v in resultado_concentrado["desperdicio"]]

st.dataframe(df, use_container_width=True)

st.subheader("Resumen anual")

resumen = pd.DataFrame({
    "Escenario": ["Distribuido", "Concentrado"],
    "Consumo anual (kWh)": [sum(consumo_real), sum(consumo_real)],
    "Generación AC anual (kWh)": [round(sum(generacion_ac), 1), round(sum(generacion_ac), 1)],
    "Autoconsumo anual (kWh)": [
        round(sum(resultado_distribuido["autoconsumo"]), 1),
        round(sum(resultado_concentrado["autoconsumo"]), 1),
    ],
    "Excedente anual (kWh)": [
        round(sum(resultado_distribuido["excedente"]), 1),
        round(sum(resultado_concentrado["excedente"]), 1),
    ],
    "Compra anual red (kWh)": [
        round(sum(resultado_distribuido["compra_red"]), 1),
        round(sum(resultado_concentrado["compra_red"]), 1),
    ],
    "Cobertura consumo (%)": [
        round(sum(resultado_distribuido["autoconsumo"]) / sum(consumo_real) * 100, 1),
        round(sum(resultado_concentrado["autoconsumo"]) / sum(consumo_real) * 100, 1),
    ],
    "Ahorro anual ($)": [
        round(sum(resultado_distribuido["ahorro"]), 0),
        round(sum(resultado_concentrado["ahorro"]), 0),
    ],
})

if not inyeccion_habilitada:
    resumen["No aprovechada anual (kWh)"] = [
        round(sum(resultado_distribuido["desperdicio"]), 1),
        round(sum(resultado_concentrado["desperdicio"]), 1),
    ]

st.dataframe(resumen, use_container_width=True)

# ---------------------------------------------------
# NOTAS
# ---------------------------------------------------
st.info(
    f"""
**Notas del modelo**

- Configuración evaluada: **{configuracion}**
- Potencia DC instalada: **{potencia_dc:.2f} kWp**
- Potencia del inversor AC: **{potencia_inversor_ac:.2f} kW**
- Ratio DC/AC: **{ratio_dc_ac:.2f}**
- Días de operación considerados: **{dias_operacion} días/mes**
- Modo de excedente: **{modo_inyeccion}**
- El clipping se estima a nivel mensual, por lo que sirve para comparación técnica general, no como simulación horaria fina.
- En modo sin inyección, la energía excedente se considera **no aprovechada** por limitación.
"""
)
