"""
pages/1_📈_Consolidados.py
Reporte: Ventas consolidadas por canal de cliente.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Consolidados", page_icon="📈", layout="wide")

df = cargar_data()
if df.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

# ── Sidebar filtros ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filtros")

    if "Fecha" in df.columns and df["Fecha"].notna().any():
        fmin = df["Fecha"].min().date()
        fmax = df["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax)
        if len(rango) == 2:
            df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]

    if "Zona" in df.columns:
        zonas = ["Todas"] + sorted(df["Zona"].dropna().unique().tolist())
        zona = st.selectbox("Zona / Departamento", zonas)
        if zona != "Todas":
            df = df[df["Zona"] == zona]

    if "Familia" in df.columns:
        familias = ["Todas"] + sorted(df["Familia"].dropna().unique().tolist())
        familia = st.selectbox("Familia de producto", familias)
        if familia != "Todas":
            df = df[df["Familia"] == familia]

    if "Motivo" in df.columns:
        motivos = ["Todos"] + sorted(df["Motivo"].dropna().unique().tolist())
        motivo = st.selectbox("Motivo", motivos)
        if motivo != "Todos":
            df = df[df["Motivo"] == motivo]

# ── Título ─────────────────────────────────────────────────────────────────
st.title("📈 Consolidados — Ventas por Canal")
st.caption(f"Total de registros filtrados: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── Cálculo ────────────────────────────────────────────────────────────────
CANAL = "Canal" if "Canal" in df.columns else "Clase_Cliente"

agg = df.groupby(CANAL).agg(
    Ventas_Netas    =("Valor_Neto",         "sum"),
    Costo_Sistema   =("Costo_Total",        "sum"),
    Rentabilidad    =("Valor_Rentabilidad", "sum"),
    Unidades        =("Cantidad",           "sum"),
    Litros          =("Litros",             "sum"),
).reset_index()

agg["%Rent"]  = agg["Rentabilidad"] / agg["Ventas_Netas"].replace(0, 1)
agg["%Costo"] = agg["Costo_Sistema"] / agg["Ventas_Netas"].replace(0, 1)

total = pd.DataFrame([{
    CANAL:           "TOTAL",
    "Ventas_Netas":  agg["Ventas_Netas"].sum(),
    "Costo_Sistema": agg["Costo_Sistema"].sum(),
    "Rentabilidad":  agg["Rentabilidad"].sum(),
    "Unidades":      agg["Unidades"].sum(),
    "Litros":        agg["Litros"].sum(),
}])
total["%Rent"]  = total["Rentabilidad"] / total["Ventas_Netas"].replace(0, 1)
total["%Costo"] = total["Costo_Sistema"] / total["Ventas_Netas"].replace(0, 1)

tabla = pd.concat([agg.sort_values("Ventas_Netas", ascending=False), total], ignore_index=True)

# ── KPIs ───────────────────────────────────────────────────────────────────
v = tabla[tabla[CANAL] == "TOTAL"].iloc[0]
k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Netas",  formatear_millones(v["Ventas_Netas"]))
k2.metric("🏭 Costo Total",   formatear_millones(v["Costo_Sistema"]))
k3.metric("📈 Rentabilidad",  formatear_millones(v["Rentabilidad"]),
          delta=f"{v['%Rent']*100:.1f}%")
k4.metric("📦 Unidades",      f"{v['Unidades']:,.0f}")
st.divider()

# ── Tabla ──────────────────────────────────────────────────────────────────
st.subheader("📋 Tabla consolidada por canal")

def color_total(row):
    if row[CANAL] == "TOTAL":
        return ["background-color:#1e3a5f;color:white;font-weight:bold"] * len(row)
    return [""] * len(row)

def color_rent(val):
    if isinstance(val, float):
        if val >= 0.35: return "color:#16a34a;font-weight:bold"
        if val >= 0.20: return "color:#ca8a04"
        return "color:#dc2626"
    return ""

display = tabla.rename(columns={
    CANAL:           "Canal",
    "Ventas_Netas":  "Ventas Netas ($)",
    "Costo_Sistema": "Costo Sistema ($)",
    "Rentabilidad":  "Rentabilidad ($)",
    "Unidades":      "Unidades",
    "Litros":        "Litros",
    "%Rent":         "% Rent.",
    "%Costo":        "% Costo",
})
fmt = {
    "Ventas Netas ($)":  "{:,.0f}",
    "Costo Sistema ($)": "{:,.0f}",
    "Rentabilidad ($)":  "{:,.0f}",
    "Unidades":          "{:,.0f}",
    "Litros":            "{:,.1f}",
    "% Rent.":           "{:.2%}",
    "% Costo":           "{:.2%}",
}
styled = display.style.format(fmt).apply(color_total, axis=1).map(color_rent, subset=["% Rent."])
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Gráficas ───────────────────────────────────────────────────────────────
st.divider()
g1, g2 = st.columns(2)

with g1:
    st.subheader("Ventas Netas por Canal")
    datos_g = tabla[tabla[CANAL] != "TOTAL"].sort_values("Ventas_Netas", ascending=True)
    fig = px.bar(datos_g, x="Ventas_Netas", y=CANAL, orientation="h",
                 color="Ventas_Netas", color_continuous_scale="Blues",
                 text_auto=".3s", labels={"Ventas_Netas": "Ventas ($)", CANAL: ""})
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      plot_bgcolor="white", height=380)
    st.plotly_chart(fig, use_container_width=True)

with g2:
    st.subheader("% Rentabilidad por Canal")
    colores = ["#dc2626" if x < 0.2 else "#ca8a04" if x < 0.35 else "#16a34a"
               for x in datos_g["%Rent"]]
    fig2 = go.Figure(go.Bar(
        x=datos_g["%Rent"] * 100, y=datos_g[CANAL], orientation="h",
        marker_color=colores,
        text=[f"{v:.1f}%" for v in datos_g["%Rent"] * 100],
        textposition="outside",
    ))
    fig2.update_layout(xaxis_title="% Rentabilidad", yaxis_title="",
                       plot_bgcolor="white", height=380,
                       xaxis=dict(ticksuffix="%"))
    st.plotly_chart(fig2, use_container_width=True)

# ── Exportar ───────────────────────────────────────────────────────────────
st.divider()
st.download_button("📥 Descargar tabla como CSV",
                   data=display.to_csv(index=False, encoding="utf-8-sig"),
                   file_name="consolidados.csv", mime="text/csv")
