"""
pages/3_🔍_Consulta.py
Consulta libre por cliente o por ítem.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Consulta", page_icon="🔍", layout="wide")

df = cargar_data()
if df.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

st.title("🔍 Consulta Libre")
st.caption("Busca y analiza el historial de un **cliente específico** o de un **producto específico**. Usa el panel izquierdo para filtrar por nombre, rango de fechas y otros criterios.")
modo = st.radio("¿Qué quieres consultar?", ["Por Cliente", "Por Ítem"], horizontal=True)
st.divider()

# ─────────────────────────────────────────────────────────────────
# POR CLIENTE
# ─────────────────────────────────────────────────────────────────
if modo == "Por Cliente":
    col_l, col_r = st.columns([1, 3])

    with col_l:
        st.subheader("Filtros")
        busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o NIT...")
        opciones = sorted(df["Nombre_Cliente"].dropna().unique()) if "Nombre_Cliente" in df.columns else []
        if busqueda:
            opciones = [c for c in opciones if busqueda.upper() in c.upper()]
        cliente_sel = st.selectbox("Cliente", opciones if opciones else ["(sin resultados)"])

        if "Fecha" in df.columns and df["Fecha"].notna().any():
            fmin = df["Fecha"].min().date()
            fmax = df["Fecha"].max().date()
            rango = st.date_input("Rango de fechas", value=(fmin, fmax),
                                  min_value=fmin, max_value=fmax)
        else:
            rango = None

        if "Motivo" in df.columns:
            motivos = ["Todos"] + sorted(df["Motivo"].dropna().unique().tolist())
            motivo_sel = st.selectbox("Motivo", motivos)
        else:
            motivo_sel = "Todos"

    dff = df[df["Nombre_Cliente"] == cliente_sel].copy() if "Nombre_Cliente" in df.columns else df.copy()
    if rango and len(rango) == 2 and "Fecha" in dff.columns:
        dff = dff[(dff["Fecha"].dt.date >= rango[0]) & (dff["Fecha"].dt.date <= rango[1])]
    if motivo_sel != "Todos" and "Motivo" in dff.columns:
        dff = dff[dff["Motivo"] == motivo_sel]

    with col_r:
        if dff.empty:
            st.info("No hay datos para este cliente.")
            st.stop()

        canal   = dff["Canal"].iloc[0]         if "Canal"         in dff.columns else "—"
        zona    = dff["Zona"].iloc[0]          if "Zona"          in dff.columns else "—"
        vendedor = dff["Nombre_Vendedor"].iloc[0] if "Nombre_Vendedor" in dff.columns else "—"
        ia, ib, ic = st.columns(3)
        ia.info(f"**Canal:** {canal}")
        ib.info(f"**Zona:** {zona}")
        ic.info(f"**Vendedor:** {vendedor}")

        venta = dff["Valor_Neto"].sum()         if "Valor_Neto"         in dff.columns else 0
        costo = dff["Costo_Total"].sum()        if "Costo_Total"        in dff.columns else 0
        rent  = dff["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in dff.columns else 0
        cant  = dff["Cantidad"].sum()           if "Cantidad"           in dff.columns else 0
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Ventas",   formatear_millones(venta))
        k2.metric("🏭 Costo",    formatear_millones(costo))
        k3.metric("📈 Rent.",    formatear_millones(rent),
                  delta=f"{rent/venta*100:.1f}%" if venta else None)
        k4.metric("📦 Unidades", f"{cant:,.0f}")

        st.markdown("#### Ítems comprados")
        st.caption("Lista de todos los productos comprados por este cliente en el período, ordenados por valor. **%Rent** = (Ventas − Costo) / Ventas.")
        gcols = [c for c in ["Familia", "Referencia", "Nombre_Item"] if c in dff.columns]
        if gcols:
            tbl = dff.groupby(gcols).agg(
                Cantidad      =("Cantidad",           "sum"),
                Valor_Neto    =("Valor_Neto",         "sum"),
                Costo_Total   =("Costo_Total",        "sum"),
                Rentabilidad  =("Valor_Rentabilidad", "sum"),
            ).reset_index()
            tbl["%Rent"] = tbl["Rentabilidad"] / tbl["Valor_Neto"].replace(0, 1)
            tbl = tbl.sort_values("Valor_Neto", ascending=False)
            st.dataframe(tbl.style.format({
                "Cantidad":"{:,.0f}","Valor_Neto":"{:,.0f}",
                "Costo_Total":"{:,.0f}","Rentabilidad":"{:,.0f}","%Rent":"{:.2%}"
            }),
            column_config={
                "%Rent": st.column_config.NumberColumn("%Rent", help="(Ventas - Costo) / Ventas × 100"),
            },
            use_container_width=True, hide_index=True)

        if "Fecha" in dff.columns and dff["Fecha"].notna().any():
            serie = dff.groupby(dff["Fecha"].dt.date)["Valor_Neto"].sum().reset_index()
            serie.columns = ["Fecha", "Ventas"]
            n_fechas = len(serie)

            if n_fechas == 1:
                # Un solo día: mostrar desglose por canal o por ítem
                st.markdown("#### 📋 Compras del día")
                if "Canal" in dff.columns:
                    pc = dff.groupby("Canal")["Valor_Neto"].sum().reset_index()
                    pc.columns = ["Canal de Ventas", "Ventas ($)"]
                    pc = pc.sort_values("Ventas ($)", ascending=True)
                    fig = px.bar(pc, x="Ventas ($)", y="Canal de Ventas", orientation="h",
                                 text_auto=".3s",
                                 color="Ventas ($)",
                                 color_continuous_scale=[[0,"#93c5fd"],[1,"#1d4ed8"]],
                                 labels={"Ventas ($)": "Ventas Netas ($)", "Canal de Ventas": ""},
                                 title=f"Ventas del {serie['Fecha'].iloc[0]} por canal")
                    fig.update_layout(coloraxis_showscale=False, plot_bgcolor="white", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Una sola fecha registrada: {serie['Fecha'].iloc[0]}  •  Ventas: ${serie['Ventas'].iloc[0]:,.0f}")
            else:
                # Múltiples fechas: línea con puntos + línea de tendencia
                st.markdown("#### 📈 Evolución de ventas")
                st.caption("Línea azul = ventas reales por fecha  •  Línea naranja punteada = Tendencia MM3 (promedio móvil de 3 períodos: suaviza los altos y bajos para mostrar la dirección general de las ventas)")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=serie["Fecha"], y=serie["Ventas"],
                    name="Ventas ($)",
                    mode="lines+markers",
                    line=dict(color="#3b82f6", width=2),
                    marker=dict(size=8, color="#3b82f6"),
                ))
                if n_fechas >= 4:
                    mm = serie["Ventas"].rolling(3, center=True).mean()
                    fig.add_trace(go.Scatter(
                        x=serie["Fecha"], y=mm,
                        name="Tendencia (MM3)",
                        mode="lines",
                        line=dict(color="#f59e0b", width=2, dash="dot"),
                    ))
                fig.update_layout(
                    plot_bgcolor="white", height=350,
                    yaxis=dict(title="Ventas Netas ($)", showgrid=True, gridcolor="#e2e8f0"),
                    legend=dict(orientation="h", y=-0.2),
                    margin=dict(t=20, b=60),
                )
                st.plotly_chart(fig, use_container_width=True)

        st.download_button("📥 Descargar detalle completo",
                           data=dff.to_csv(index=False, encoding="utf-8-sig"),
                           file_name=f"cliente_{cliente_sel.replace(' ','_')[:40]}.csv",
                           mime="text/csv")

# ─────────────────────────────────────────────────────────────────
# POR ÍTEM
# ─────────────────────────────────────────────────────────────────
else:
    col_l, col_r = st.columns([1, 3])

    with col_l:
        st.subheader("Filtros")
        busqueda_i = st.text_input("🔍 Buscar ítem", placeholder="Nombre o referencia...")
        opciones_i = sorted(df["Nombre_Item"].dropna().unique()) if "Nombre_Item" in df.columns else []
        if busqueda_i:
            opciones_i = [i for i in opciones_i if busqueda_i.upper() in i.upper()]
        item_sel = st.selectbox("Ítem", opciones_i if opciones_i else ["(sin resultados)"])

        if "Fecha" in df.columns and df["Fecha"].notna().any():
            fmin = df["Fecha"].min().date()
            fmax = df["Fecha"].max().date()
            rango_i = st.date_input("Rango de fechas", value=(fmin, fmax),
                                    min_value=fmin, max_value=fmax, key="fi")
        else:
            rango_i = None

        if "Canal" in df.columns:
            canales = ["Todos"] + sorted(df["Canal"].dropna().unique().tolist())
            canal_sel = st.selectbox("Canal", canales)
        else:
            canal_sel = "Todos"

    dfi = df[df["Nombre_Item"] == item_sel].copy() if "Nombre_Item" in df.columns else df.copy()
    if rango_i and len(rango_i) == 2 and "Fecha" in dfi.columns:
        dfi = dfi[(dfi["Fecha"].dt.date >= rango_i[0]) & (dfi["Fecha"].dt.date <= rango_i[1])]
    if canal_sel != "Todos" and "Canal" in dfi.columns:
        dfi = dfi[dfi["Canal"] == canal_sel]

    with col_r:
        if dfi.empty:
            st.info("No hay datos para este ítem.")
            st.stop()

        ref = dfi["Referencia"].iloc[0] if "Referencia" in dfi.columns else "—"
        fam = dfi["Familia"].iloc[0]    if "Familia"    in dfi.columns else "—"
        ia, ib = st.columns(2)
        ia.info(f"**Referencia:** {ref}")
        ib.info(f"**Familia:** {fam}")

        venta = dfi["Valor_Neto"].sum()         if "Valor_Neto"         in dfi.columns else 0
        costo = dfi["Costo_Total"].sum()        if "Costo_Total"        in dfi.columns else 0
        rent  = dfi["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in dfi.columns else 0
        cant  = dfi["Cantidad"].sum()           if "Cantidad"           in dfi.columns else 0
        lts   = dfi["Litros"].sum()             if "Litros"             in dfi.columns else 0
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("💰 Ventas",   formatear_millones(venta))
        k2.metric("🏭 Costo",    formatear_millones(costo))
        k3.metric("📈 Rent.",    formatear_millones(rent),
                  delta=f"{rent/venta*100:.1f}%" if venta else None)
        k4.metric("📦 Unidades", f"{cant:,.0f}")
        k5.metric("🥛 Litros",   f"{lts:,.1f}")

        if "Canal" in dfi.columns:
            st.markdown("#### Ventas por canal")
            pc = dfi.groupby("Canal").agg(
                Cantidad    =("Cantidad",           "sum"),
                Valor_Neto  =("Valor_Neto",         "sum"),
                Costo_Total =("Costo_Total",        "sum"),
                Rent        =("Valor_Rentabilidad", "sum"),
            ).reset_index()
            pc["%Rent"] = pc["Rent"] / pc["Valor_Neto"].replace(0, 1)
            g1, g2 = st.columns(2)
            with g1:
                fig = px.bar(pc, x="Canal", y="Valor_Neto", color="Canal",
                             text_auto=".3s", title="Ventas por canal",
                             labels={"Valor_Neto": "Ventas ($)"})
                fig.update_layout(showlegend=False, plot_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                fig2 = px.bar(pc, x="Canal", y="%Rent", color="%Rent",
                              color_continuous_scale="RdYlGn", text_auto=".1%",
                              title="% Rentabilidad por canal",
                              labels={"%Rent": "% Rent."})
                fig2.update_layout(coloraxis_showscale=False, plot_bgcolor="white",
                                   yaxis=dict(tickformat=".0%"))
                st.plotly_chart(fig2, use_container_width=True)

        if "Nombre_Cliente" in dfi.columns:
            st.markdown("#### Top clientes compradores")
            st.caption("Los 20 clientes que más compraron este producto en el período, ordenados por valor de compra.")
            top_c = dfi.groupby("Nombre_Cliente")["Valor_Neto"].sum().nlargest(20).reset_index()
            top_c.columns = ["Cliente", "Ventas Netas ($)"]
            top_c["Ventas Netas ($)"] = top_c["Ventas Netas ($)"].map(lambda x: f"${x:,.0f}")
            st.dataframe(top_c, use_container_width=True, hide_index=True)

        if "Fecha" in dfi.columns and dfi["Fecha"].notna().any():
            serie = dfi.groupby(dfi["Fecha"].dt.date)["Cantidad"].sum().reset_index()
            serie.columns = ["Fecha", "Unidades"]
            fig3 = px.line(serie, x="Fecha", y="Unidades", markers=True,
                           title="Evolución de unidades vendidas",
                           color_discrete_sequence=["#8b5cf6"])
            fig3.update_layout(plot_bgcolor="white")
            st.plotly_chart(fig3, use_container_width=True)

        st.download_button("📥 Descargar detalle completo",
                           data=dfi.to_csv(index=False, encoding="utf-8-sig"),
                           file_name=f"item_{item_sel.replace(' ','_')[:50]}.csv",
                           mime="text/csv")
