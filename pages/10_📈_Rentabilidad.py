"""
pages/10_📈_Rentabilidad.py
Análisis de rentabilidad y márgenes:
  • Margen por canal, zona, producto y vendedor
  • Impacto de descuentos en la rentabilidad
  • Desglose de impuestos (IVA, IBUA, ICUI)
  • Waterfall: de Valor Bruto a Valor Neto
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Rentabilidad", page_icon="📈", layout="wide")

df_all = cargar_data()
if df_all.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

def get_col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

CANAL_COL   = get_col(df_all, "Canal",           "CANAL DE VENTAS")
ZONA_COL    = get_col(df_all, "Zona",            "ZONAS")
ITEM_COL    = get_col(df_all, "Nombre_Item",     "Desc. item")
FAM_COL     = get_col(df_all, "Familia",         "GRUPOS")
VEND_COL    = get_col(df_all, "Nombre_Vendedor", "Nombre vendedor")
DSCTO_COL   = get_col(df_all, "Descuento_Pct",  "Dscto. promedio %")
VAL_DSCTO   = get_col(df_all, "Valor_Descuentos","Valor descuentos")
IVA_COL     = get_col(df_all, "Iva",            "Vlr. imp. IVA")
IBUA_COL    = get_col(df_all, "Ibua",           "Vlr. imp. IBUA")
ICUI_COL    = get_col(df_all, "Icui",           "Vlr. imp. ICUI")
VB_COL      = get_col(df_all, "Valor_Bruto",    "Valor bruto")
MARG_PCT    = get_col(df_all, "Margen_Pct",     "Margen promedio")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filtros")
    if "Fecha" in df_all.columns and df_all["Fecha"].notna().any():
        fmin, fmax = df_all["Fecha"].min().date(), df_all["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", value=(fmin, fmax),
                              min_value=fmin, max_value=fmax)
    else:
        rango = None

    if CANAL_COL:
        canales = ["Todos"] + sorted(df_all[CANAL_COL].dropna().unique().tolist())
        canal_sel = st.selectbox("Canal", canales)
    else:
        canal_sel = "Todos"

    if ZONA_COL:
        zonas = ["Todas"] + sorted(df_all[ZONA_COL].dropna().unique().tolist())
        zona_sel = st.selectbox("Zona", zonas)
    else:
        zona_sel = "Todas"

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if canal_sel != "Todos" and CANAL_COL:
    df = df[df[CANAL_COL] == canal_sel]
if zona_sel != "Todas" and ZONA_COL:
    df = df[df[ZONA_COL] == zona_sel]

st.title("📈 Rentabilidad y Márgenes")
st.caption(f"Canal: **{canal_sel}**  •  Zona: **{zona_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
venta   = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
costo   = df["Costo_Total"].sum()        if "Costo_Total"        in df.columns else 0
rent    = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
vbruto  = df[VB_COL].sum()              if VB_COL else 0
dscto   = df[VAL_DSCTO].sum()           if VAL_DSCTO else 0
iva     = df[IVA_COL].sum()             if IVA_COL else 0
ibua    = df[IBUA_COL].sum()            if IBUA_COL else 0
icui    = df[ICUI_COL].sum()            if ICUI_COL else 0
imptos  = iva + ibua + icui

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Netas",  formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k2.metric("🏭 Costo Total",   formatear_millones(costo),
          help="Costo promedio total de los ítems vendidos")
k3.metric("📈 Rentabilidad",  formatear_millones(rent),
          delta=f"{rent/venta*100:.1f}%" if venta else None,
          help="Ventas Netas menos Costo Total")
k4.metric("💸 Descuentos otorgados", formatear_millones(dscto),
          delta=f"{dscto/vbruto*100:.1f}% sobre bruto" if vbruto else None,
          delta_color="inverse",
          help="Valor total de descuentos aplicados en el período")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Margen por Dimensión",
    "💸 Impacto Descuentos",
    "🧾 Impuestos",
    "📉 Cascada de Valor",
])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 – MARGEN POR DIMENSIÓN
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    dims = {}
    if CANAL_COL: dims["Canal"] = CANAL_COL
    if ZONA_COL:  dims["Zona"]  = ZONA_COL
    if FAM_COL:   dims["Grupo de producto"] = FAM_COL
    if VEND_COL:  dims["Vendedor"] = VEND_COL

    if not dims:
        st.info("No se encontraron columnas de dimensión.")
    else:
        dim_label = st.selectbox("Ver margen por", list(dims.keys()))
        dim_col   = dims[dim_label]

        agg = df.groupby(dim_col).agg(
            Ventas=("Valor_Neto", "sum"),
            Costo=("Costo_Total", "sum"),
            Rentabilidad=("Valor_Rentabilidad", "sum"),
        ).reset_index()
        total_vn = agg["Ventas"].sum()
        agg["%_Mg"]   = agg["Rentabilidad"] / agg["Ventas"].replace(0, 1)
        agg["%_Part"] = agg["Ventas"] / total_vn if total_vn else 0
        agg[dim_col]  = agg[dim_col].astype(str).str.strip()
        agg = agg.sort_values("%_Mg", ascending=False)

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader(f"% Margen por {dim_label}")
            colores = [
                "#ef4444" if v < 0.20 else "#f59e0b" if v < 0.35 else "#22c55e"
                for v in agg["%_Mg"]
            ]
            fig_mg = go.Figure(go.Bar(
                y=agg[dim_col], x=agg["%_Mg"] * 100,
                orientation="h",
                marker_color=colores,
                text=[f"{v*100:.1f}%" for v in agg["%_Mg"]],
                textposition="outside", cliponaxis=False,
            ))
            fig_mg.add_vline(x=20, line_dash="dot", line_color="#ef4444",
                              annotation_text="20%", annotation_position="top right")
            fig_mg.add_vline(x=35, line_dash="dot", line_color="#22c55e",
                              annotation_text="35%", annotation_position="top right")
            fig_mg.update_layout(
                plot_bgcolor="white", height=max(350, len(agg) * 48),
                xaxis=dict(ticksuffix="%", title="% Margen"),
                yaxis=dict(title=""),
            )
            st.plotly_chart(fig_mg, use_container_width=True)

        with col_b:
            st.subheader(f"Ventas y Rentabilidad por {dim_label}")
            fig_combo = go.Figure()
            fig_combo.add_trace(go.Bar(
                y=agg[dim_col], x=agg["Ventas"],
                name="Ventas ($)", orientation="h",
                marker_color="#93c5fd", opacity=0.85,
            ))
            fig_combo.add_trace(go.Bar(
                y=agg[dim_col], x=agg["Rentabilidad"],
                name="Rentabilidad ($)", orientation="h",
                marker_color="#22c55e", opacity=0.85,
            ))
            fig_combo.update_layout(
                barmode="group", plot_bgcolor="white",
                height=max(350, len(agg) * 48),
                xaxis=dict(title="$"),
                yaxis=dict(title=""),
                legend=dict(orientation="h", y=-0.15),
            )
            st.plotly_chart(fig_combo, use_container_width=True)

        # Tabla
        st.dataframe(
            agg.rename(columns={
                dim_col: dim_label, "Ventas": "Ventas ($)", "Costo": "Costo ($)",
                "Rentabilidad": "Rentabilidad ($)", "%_Mg": "% Margen", "%_Part": "% Part.",
            }).style.format({
                "Ventas ($)": "{:,.0f}", "Costo ($)": "{:,.0f}",
                "Rentabilidad ($)": "{:,.0f}", "% Margen": "{:.2%}", "% Part.": "{:.2%}",
            }),
            column_config={
                "% Margen":        st.column_config.NumberColumn("% Margen",        help="(Ventas - Costo) / Ventas × 100"),
                "% Part.":         st.column_config.NumberColumn("% Part.",         help="Participación porcentual sobre el total del período"),
                "Rentabilidad ($)": st.column_config.NumberColumn("Rentabilidad ($)", help="Ventas Netas menos Costo Total en pesos"),
            },
            use_container_width=True, hide_index=True
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 – IMPACTO DESCUENTOS
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    if not DSCTO_COL and not VAL_DSCTO:
        st.info("Columnas de descuento no encontradas.")
    else:
        st.subheader("💸 Análisis de Descuentos")

        c1, c2, c3 = st.columns(3)
        if vbruto:
            c1.metric("💵 Valor bruto",     formatear_millones(vbruto),
                      help="Valor total antes de descuentos e impuestos")
            c2.metric("💸 Descuentos",      formatear_millones(dscto),
                      delta=f"-{dscto/vbruto*100:.1f}%", delta_color="inverse",
                      help="Valor total de descuentos aplicados en el período")
            c3.metric("💰 Valor neto",      formatear_millones(venta),
                      help="Suma del valor neto facturado en el período (sin IVA)")

        if DSCTO_COL and CANAL_COL:
            st.subheader(f"% Descuento promedio por {canal_sel if canal_sel != 'Todos' else 'Canal'}")
            dscto_canal = df.groupby(CANAL_COL).agg(
                Ventas=("Valor_Neto", "sum"),
                Dscto_Prom=(DSCTO_COL, "mean"),
                Margen=("Valor_Rentabilidad", "sum"),
            ).reset_index()
            dscto_canal["%_Mg"] = dscto_canal["Margen"] / dscto_canal["Ventas"].replace(0, 1)
            dscto_canal[CANAL_COL] = dscto_canal[CANAL_COL].astype(str).str.strip()

            fig_dscto = px.scatter(
                dscto_canal, x="Dscto_Prom", y="%_Mg",
                size="Ventas", color=CANAL_COL, text=CANAL_COL,
                labels={
                    "Dscto_Prom": "Descuento Promedio (%)",
                    "%_Mg": "% Margen",
                    CANAL_COL: "Canal",
                },
                title="A mayor descuento, ¿menor margen?",
            )
            fig_dscto.update_traces(textposition="top center")
            fig_dscto.update_layout(
                plot_bgcolor="white", height=420,
                yaxis=dict(tickformat=".0%"),
            )
            st.plotly_chart(fig_dscto, use_container_width=True)

        # Top ítems con mayor descuento
        if DSCTO_COL and ITEM_COL:
            st.subheader("🏷️ Productos con mayor descuento promedio")
            top_dscto = (
                df.groupby(ITEM_COL)
                .agg(
                    Dscto_Prom=(DSCTO_COL, "mean"),
                    Ventas=("Valor_Neto", "sum"),
                    Margen=("Valor_Rentabilidad", "sum"),
                )
                .reset_index()
                .nlargest(20, "Dscto_Prom")
            )
            top_dscto["%_Mg"] = top_dscto["Margen"] / top_dscto["Ventas"].replace(0, 1)
            fig_td = px.bar(
                top_dscto.sort_values("Dscto_Prom"),
                x="Dscto_Prom", y=ITEM_COL, orientation="h",
                color="%_Mg", color_continuous_scale="RdYlGn",
                text_auto=".1f",
                labels={"Dscto_Prom": "% Descuento Promedio", ITEM_COL: "",
                        "%_Mg": "% Margen"},
            )
            fig_td.update_layout(
                plot_bgcolor="white", height=500,
                coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"),
            )
            st.plotly_chart(fig_td, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 – IMPUESTOS
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if not any([IVA_COL, IBUA_COL, ICUI_COL]):
        st.info("Columnas de impuestos no encontradas.")
    else:
        st.subheader("🧾 Desglose de impuestos sobre ventas")

        imptos_data = {}
        if IVA_COL  and iva:  imptos_data["IVA"]  = iva
        if IBUA_COL and ibua: imptos_data["IBUA"] = ibua
        if ICUI_COL and icui: imptos_data["ICUI"] = icui

        if imptos_data:
            ci1, ci2, ci3, ci4 = st.columns(4)
            ci1.metric("🧾 IVA total",  formatear_millones(iva)  if IVA_COL  else "N/A",
                       delta=f"{iva/venta*100:.2f}% de ventas" if venta and IVA_COL else None,
                       help="Impuesto al Valor Agregado cobrado en el período")
            ci2.metric("🍬 IBUA total", formatear_millones(ibua) if IBUA_COL else "N/A",
                       delta=f"{ibua/venta*100:.2f}% de ventas" if venta and IBUA_COL else None,
                       help="Impuesto a las Bebidas Ultraprocesadas Azucaradas (por ml)")
            ci3.metric("🥤 ICUI total", formatear_millones(icui) if ICUI_COL else "N/A",
                       delta=f"{icui/venta*100:.2f}% de ventas" if venta and ICUI_COL else None,
                       help="Impuesto al Consumo de productos Ultraprocesados (por unidad)")
            ci4.metric("🏛️ Total impuestos", formatear_millones(imptos),
                       delta=f"{imptos/venta*100:.2f}% de ventas" if venta else None,
                       delta_color="inverse",
                       help="Suma de IVA + IBUA + ICUI en el período")
            st.caption("**IBUA**: Impuesto a Bebidas Ultraprocesadas Azucaradas (aplica por ml al consumidor)  |  **ICUI**: Impuesto al Consumo de productos Ultraprocesados (valor fijo por unidad)")

            # Pie de impuestos
            df_imp = pd.DataFrame({
                "Impuesto": list(imptos_data.keys()),
                "Valor": list(imptos_data.values()),
            })
            col_pie, col_bar = st.columns(2)
            with col_pie:
                fig_i = px.pie(df_imp, values="Valor", names="Impuesto",
                               color_discrete_sequence=["#3b82f6","#f59e0b","#ef4444"],
                               title="Composición de impuestos")
                fig_i.update_layout(height=350)
                st.plotly_chart(fig_i, use_container_width=True)

            # IBUA / ICUI por canal (impuesto saludable)
            with col_bar:
                if (IBUA_COL or ICUI_COL) and CANAL_COL:
                    agg_imp = df.groupby(CANAL_COL).agg(
                        IVA=(IVA_COL, "sum") if IVA_COL else ("Cantidad","sum"),
                        IBUA=(IBUA_COL, "sum") if IBUA_COL else ("Cantidad","sum"),
                    ).reset_index()
                    agg_imp[CANAL_COL] = agg_imp[CANAL_COL].astype(str).str.strip()
                    fig_imp_canal = px.bar(
                        agg_imp, y=CANAL_COL, x=["IVA","IBUA"] if IBUA_COL else ["IVA"],
                        orientation="h", barmode="stack",
                        title="Impuestos por canal",
                        labels={CANAL_COL: ""},
                    )
                    fig_imp_canal.update_layout(plot_bgcolor="white", height=350)
                    st.plotly_chart(fig_imp_canal, use_container_width=True)

        # IBUA por producto (top 15 afectados)
        if IBUA_COL and ITEM_COL:
            st.subheader("🍬 Top productos con mayor IBUA (impuesto saludable)")
            top_ibua = (
                df.groupby(ITEM_COL)
                .agg(
                    IBUA=(IBUA_COL, "sum"),
                    Ventas=("Valor_Neto", "sum"),
                    Unidades=("Cantidad", "sum"),
                )
                .reset_index()
                .nlargest(15, "IBUA")
            )
            top_ibua["IBUA_por_unidad"] = top_ibua["IBUA"] / top_ibua["Unidades"].replace(0, 1)
            fig_ibua = px.bar(
                top_ibua.sort_values("IBUA"), x="IBUA", y=ITEM_COL,
                orientation="h", text_auto=".3s", color="IBUA_por_unidad",
                color_continuous_scale="Reds",
                labels={"IBUA": "IBUA ($)", ITEM_COL: "", "IBUA_por_unidad": "IBUA/und"},
            )
            fig_ibua.update_layout(plot_bgcolor="white", height=450)
            st.plotly_chart(fig_ibua, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 4 – CASCADA DE VALOR (WATERFALL)
# ─────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("📉 Cascada: de Valor Bruto a Rentabilidad")

    pasos = []
    valores = []
    tipos = []

    if vbruto:
        pasos.append("Valor Bruto");   valores.append(vbruto);    tipos.append("absolute")
    if dscto:
        pasos.append("Descuentos");    valores.append(-dscto);    tipos.append("relative")
    if imptos:
        pasos.append("Impuestos");     valores.append(-imptos);   tipos.append("relative")
    if venta:
        pasos.append("Valor Neto");    valores.append(None);      tipos.append("total")
    if costo:
        pasos.append("Costo Total");   valores.append(-costo);    tipos.append("relative")
    if rent:
        pasos.append("Rentabilidad");  valores.append(None);      tipos.append("total")

    if len(pasos) < 3:
        st.info("Columnas insuficientes para construir la cascada. "
                "Se necesitan Valor_Bruto, Valor descuentos y/o Costo_Total.")
    else:
        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=tipos,
            x=pasos,
            y=valores,
            connector=dict(line=dict(color="#94a3b8", width=1, dash="dot")),
            increasing=dict(marker_color="#22c55e"),
            decreasing=dict(marker_color="#ef4444"),
            totals=dict(marker_color="#3b82f6"),
            text=[formatear_millones(abs(v)) if v else "" for v in valores],
            textposition="outside",
        ))
        fig_wf.update_layout(
            plot_bgcolor="white", height=480,
            title="Cascada de valor — período seleccionado",
            yaxis=dict(title="$"),
        )
        st.plotly_chart(fig_wf, use_container_width=True)

        # Tabla resumen
        rows_wf = []
        if vbruto: rows_wf.append(("Valor Bruto",     vbruto,          "—"))
        if dscto:  rows_wf.append(("(-) Descuentos",  -dscto,  f"-{dscto/vbruto*100:.1f}%" if vbruto else "—"))
        if imptos: rows_wf.append(("(-) Impuestos",   -imptos, f"-{imptos/vbruto*100:.1f}%" if vbruto else "—"))
        if venta:  rows_wf.append(("= Valor Neto",    venta,   f"{venta/vbruto*100:.1f}%" if vbruto else "—"))
        if costo:  rows_wf.append(("(-) Costo Total", -costo,  f"-{costo/venta*100:.1f}%" if venta else "—"))
        if rent:   rows_wf.append(("= Rentabilidad",  rent,    f"{rent/venta*100:.1f}%" if venta else "—"))

        df_wf = pd.DataFrame(rows_wf, columns=["Concepto", "Valor ($)", "% sobre anterior"])
        st.dataframe(
            df_wf.style.format({"Valor ($)": "{:,.0f}"}),
            use_container_width=False, hide_index=True
        )
