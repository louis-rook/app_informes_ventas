"""
pages/2_🏪_Por_Cliente.py
Reporte: Análisis detallado por gran cliente.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Por Cliente", page_icon="🏪", layout="wide")

df = cargar_data()
if df.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

# ── Sidebar filtros ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filtros")

    busqueda = st.text_input("🔍 Buscar cliente", placeholder="Ej: ARA, EXITO, CENCOSUD...")
    if "Nombre_Cliente" in df.columns:
        opciones = sorted(df["Nombre_Cliente"].dropna().unique())
        if busqueda:
            opciones = [c for c in opciones if busqueda.upper() in c.upper()]
        cliente_sel = st.selectbox("Cliente", opciones if opciones else ["(sin resultados)"])
    else:
        st.warning("Columna de cliente no encontrada.")
        st.stop()

    if "Fecha" in df.columns and df["Fecha"].notna().any():
        fmin = df["Fecha"].min().date()
        fmax = df["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", value=(fmin, fmax),
                              min_value=fmin, max_value=fmax)
    else:
        rango = None

    if "Familia" in df.columns:
        familias = ["Todas"] + sorted(df["Familia"].dropna().unique().tolist())
        familia_sel = st.selectbox("Familia", familias)
    else:
        familia_sel = "Todas"

    if "Motivo" in df.columns:
        motivos = ["Todos"] + sorted(df["Motivo"].dropna().unique().tolist())
        motivo_sel = st.selectbox("Motivo", motivos)
    else:
        motivo_sel = "Todos"

# ── Filtrado ───────────────────────────────────────────────────────────────
dff = df[df["Nombre_Cliente"] == cliente_sel].copy()
if rango and len(rango) == 2 and "Fecha" in dff.columns:
    dff = dff[(dff["Fecha"].dt.date >= rango[0]) & (dff["Fecha"].dt.date <= rango[1])]
if familia_sel != "Todas" and "Familia" in dff.columns:
    dff = dff[dff["Familia"] == familia_sel]
if motivo_sel != "Todos" and "Motivo" in dff.columns:
    dff = dff[dff["Motivo"] == motivo_sel]

# ── Título ─────────────────────────────────────────────────────────────────
st.title("🏪 Análisis por Gran Cliente")
st.subheader(f"{cliente_sel}")

if dff.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

canal  = dff["Canal"].iloc[0]  if "Canal"  in dff.columns else "—"
zona   = dff["Zona"].iloc[0]   if "Zona"   in dff.columns else "—"
clase  = dff["Clase_Cliente"].iloc[0] if "Clase_Cliente" in dff.columns else "—"
ia, ib, ic = st.columns(3)
ia.info(f"**Canal:** {canal}")
ib.info(f"**Zona:** {zona}")
ic.info(f"**Clase:** {clase}")

# ── KPIs ───────────────────────────────────────────────────────────────────
venta  = dff["Valor_Neto"].sum()         if "Valor_Neto"         in dff.columns else 0
costo  = dff["Costo_Total"].sum()        if "Costo_Total"        in dff.columns else 0
rent   = dff["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in dff.columns else 0
cant   = dff["Cantidad"].sum()           if "Cantidad"           in dff.columns else 0
litros = dff["Litros"].sum()             if "Litros"             in dff.columns else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Ventas Netas",  formatear_millones(venta))
k2.metric("🏭 Costo",         formatear_millones(costo))
k3.metric("📈 Rentabilidad",  formatear_millones(rent),
          delta=f"{rent/venta*100:.1f}%" if venta else None)
k4.metric("📦 Unidades",      f"{cant:,.0f}")
k5.metric("🥛 Litros",        f"{litros:,.1f}")
st.divider()

# ── Tabla por ítem ─────────────────────────────────────────────────────────
st.subheader("📋 Detalle por ítem")
gcols = [c for c in ["Familia", "Referencia", "Nombre_Item"] if c in dff.columns]

if gcols:
    agg = dff.groupby(gcols).agg(
        Cantidad      =("Cantidad",           "sum"),
        Valor_Neto    =("Valor_Neto",         "sum"),
        Costo_Total   =("Costo_Total",        "sum"),
        Rentabilidad  =("Valor_Rentabilidad", "sum"),
        Litros        =("Litros",             "sum"),
    ).reset_index()
    agg["Costo_Unit"]  = agg["Costo_Total"]  / agg["Cantidad"].replace(0, 1)
    agg["Precio_Unit"] = agg["Valor_Neto"]   / agg["Cantidad"].replace(0, 1)
    agg["%Rent"]       = agg["Rentabilidad"] / agg["Valor_Neto"].replace(0, 1)
    agg = agg.sort_values("Valor_Neto", ascending=False)

    def color_rent(val):
        if isinstance(val, float):
            if val >= 0.35: return "color:#16a34a;font-weight:bold"
            if val >= 0.20: return "color:#ca8a04"
            return "color:#dc2626"
        return ""

    fmt = {"Cantidad":"{:,.0f}","Valor_Neto":"{:,.0f}","Costo_Total":"{:,.0f}",
           "Rentabilidad":"{:,.0f}","Litros":"{:,.1f}",
           "Costo_Unit":"{:,.0f}","Precio_Unit":"{:,.0f}","%Rent":"{:.2%}"}
    styled = agg.style.format(fmt).map(color_rent, subset=["%Rent"]) \
                      .background_gradient(subset=["Valor_Neto"], cmap="Blues")
    st.dataframe(styled, use_container_width=True, hide_index=True)

# ── Gráficas ───────────────────────────────────────────────────────────────
st.divider()
g1, g2 = st.columns(2)

with g1:
    st.subheader("Top ítems por Ventas")
    top = agg.nlargest(15, "Valor_Neto")
    ic = "Nombre_Item" if "Nombre_Item" in top.columns else gcols[-1]
    fig = px.bar(top, x="Valor_Neto", y=ic, orientation="h",
                 color="Valor_Neto", color_continuous_scale="Blues",
                 text_auto=".3s", labels={"Valor_Neto": "Ventas ($)", ic: ""})
    fig.update_layout(showlegend=False, coloraxis_showscale=False,
                      plot_bgcolor="white", height=420)
    st.plotly_chart(fig, use_container_width=True)

with g2:
    if "Familia" in agg.columns:
        st.subheader("Ventas por Familia")
        pf = agg.groupby("Familia")["Valor_Neto"].sum().reset_index()
        fig2 = px.pie(pf, values="Valor_Neto", names="Familia",
                      color_discrete_sequence=px.colors.qualitative.Set3)
        fig2.update_layout(height=420)
        st.plotly_chart(fig2, use_container_width=True)

# ── Evolución ──────────────────────────────────────────────────────────────
if "Fecha" in dff.columns and dff["Fecha"].notna().any():
    st.divider()
    st.subheader("📅 Evolución de ventas")
    serie = dff.groupby(dff["Fecha"].dt.date)["Valor_Neto"].sum().reset_index()
    serie.columns = ["Fecha", "Ventas"]
    fig3 = px.line(serie, x="Fecha", y="Ventas", markers=True,
                   labels={"Ventas": "Ventas Netas ($)"},
                   color_discrete_sequence=["#3b82f6"])
    fig3.update_traces(fill="tozeroy", fillcolor="rgba(59,130,246,0.1)")
    fig3.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

# ── Exportar ───────────────────────────────────────────────────────────────
st.divider()
nombre = f"cliente_{cliente_sel.replace(' ','_')[:40]}.csv"
st.download_button("📥 Descargar detalle completo",
                   data=dff.to_csv(index=False, encoding="utf-8-sig"),
                   file_name=nombre, mime="text/csv")
