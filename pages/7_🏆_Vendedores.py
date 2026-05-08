"""
pages/7_🏆_Vendedores.py
Desempeño de vendedores:
  • Ranking por ventas netas y margen
  • Clientes atendidos por vendedor
  • Rutas asignadas
  • Evolución temporal
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Vendedores", page_icon="🏆", layout="wide")

df_all = cargar_data()
if df_all.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

# ── Helpers ────────────────────────────────────────────────────────────────
def get_col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

VEND_COL  = get_col(df_all, "Nombre_Vendedor", "Nombre vendedor")
CANAL_COL = get_col(df_all, "Canal", "CANAL DE VENTAS", "Clase_Cliente")
ZONA_COL  = get_col(df_all, "Zona", "ZONAS")
RUTA_COL  = get_col(df_all, "Ruta", "RUTAS DE VENTAS")
CLI_COL   = get_col(df_all, "Nombre_Cliente", "Razon social cliente factura")
CO_COL    = get_col(df_all, "Desc_CO", "Desc. C.O.")
DSCTO_COL = get_col(df_all, "Descuento_Pct", "Dscto. promedio %")

if not VEND_COL:
    st.error("❌ Columna de vendedor no encontrada.")
    st.stop()

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

    if CO_COL:
        cos = ["Todos"] + sorted(df_all[CO_COL].dropna().unique().tolist())
        co_sel = st.selectbox("C.O.", cos)
    else:
        co_sel = "Todos"

    top_n = st.slider("Top N vendedores en ranking", 5, 30, 15)

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if canal_sel != "Todos" and CANAL_COL:
    df = df[df[CANAL_COL] == canal_sel]
if co_sel != "Todos" and CO_COL:
    df = df[df[CO_COL] == co_sel]

st.title("🏆 Desempeño de Vendedores")
st.caption(f"Canal: **{canal_sel}**  •  C.O.: **{co_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── KPIs globales ──────────────────────────────────────────────────────────
n_vend = df[VEND_COL].nunique()
venta  = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
rent   = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
n_cli  = df[CLI_COL].nunique()          if CLI_COL               in df.columns else 0
prom_vend = venta / n_vend if n_vend else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("👥 Vendedores activos", f"{n_vend:,}",
          help="Número de vendedores con al menos una venta en el período")
k2.metric("💰 Ventas Netas",       formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k3.metric("📈 Rentabilidad",       formatear_millones(rent),
          delta=f"{rent/venta*100:.1f}%" if venta else None,
          help="Ventas Netas menos Costo Total")
k4.metric("🏪 Clientes únicos",   f"{n_cli:,}",
          help="Número de clientes distintos atendidos")
k5.metric("📊 Venta promedio/vend", formatear_millones(prom_vend),
          help="Ventas netas promedio por vendedor en el período")

st.divider()

# ── Tabla ranking ──────────────────────────────────────────────────────────
agg_cols = {
    "Ventas_Netas":  ("Valor_Neto",         "sum"),
    "Costo":         ("Costo_Total",        "sum"),
    "Rentabilidad":  ("Valor_Rentabilidad", "sum"),
    "Unidades":      ("Cantidad",           "sum"),
}
if CLI_COL:
    agg_cols["Clientes"] = (CLI_COL, "nunique")
if RUTA_COL:
    agg_cols["Rutas"]    = (RUTA_COL, "nunique")
if DSCTO_COL:
    agg_cols["Dscto_Prom"] = (DSCTO_COL, "mean")

ranking = df.groupby(VEND_COL).agg(**agg_cols).reset_index()
total_vn = ranking["Ventas_Netas"].sum()
ranking["%_Margen"] = ranking["Rentabilidad"] / ranking["Ventas_Netas"].replace(0, 1)
ranking["%_Part"]   = ranking["Ventas_Netas"] / total_vn if total_vn else 0
ranking["Rank"]     = ranking["Ventas_Netas"].rank(ascending=False).astype(int)
ranking = ranking.sort_values("Ventas_Netas", ascending=False)

tab1, tab2, tab3 = st.tabs(["📊 Ranking General", "🔍 Detalle por Vendedor", "📈 Evolución"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 – RANKING
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    top_data = ranking.head(top_n).copy()

    rename = {
        VEND_COL: "Vendedor", "Rank": "#",
        "Ventas_Netas": "Ventas ($)", "Rentabilidad": "Rentabilidad ($)",
        "%_Margen": "% Margen", "%_Part": "% Part.", "Unidades": "Unidades",
    }
    fmt = {
        "Ventas ($)": "{:,.0f}", "Rentabilidad ($)": "{:,.0f}",
        "Unidades": "{:,.0f}", "% Margen": "{:.2%}", "% Part.": "{:.2%}",
    }
    if CLI_COL:
        rename["Clientes"] = "Clientes"
        fmt["Clientes"] = "{:,.0f}"
    if DSCTO_COL:
        rename["Dscto_Prom"] = "% Dscto."
        fmt["% Dscto."] = "{:.1f}%"

    # ── Tabla completa ────────────────────────────────────────────────────
    st.subheader(f"📋 Top {top_n} vendedores")
    st.caption("Color % Margen: 🟢 ≥ 35%  •  🟡 20–35%  •  🔴 < 20%  |  % Part. = participación sobre ventas totales del período")

    cols_show = ["#", VEND_COL, "Ventas_Netas", "Rentabilidad", "%_Margen", "%_Part", "Unidades"]
    if CLI_COL:   cols_show.append("Clientes")
    if DSCTO_COL: cols_show.append("Dscto_Prom")
    cols_show = [c for c in cols_show if c in top_data.columns]

    # ProgressColumn necesita valores en escala 0-100
    top_disp = top_data[cols_show].rename(columns=rename).copy()
    top_disp["% Margen"] = top_disp["% Margen"] * 100
    top_disp["% Part."]  = top_disp["% Part."]  * 100

    col_cfg_v = {
        "Ventas ($)":       st.column_config.NumberColumn("Ventas ($)",       help="Suma del valor neto facturado en el período (sin IVA)"),
        "Rentabilidad ($)": st.column_config.NumberColumn("Rentabilidad ($)", help="Ventas Netas menos Costo Total"),
        "% Margen":         st.column_config.ProgressColumn("% Margen", min_value=0, max_value=100, format="%.1f%%",
                                help="(Ventas - Costo) / Ventas × 100  •  Meta ≥ 35%"),
        "% Part.":          st.column_config.ProgressColumn("% Part.",  min_value=0, max_value=100, format="%.2f%%",
                                help="Participación porcentual sobre el total de ventas del período"),
        "Unidades":         st.column_config.NumberColumn("Unidades", help="Número total de unidades vendidas"),
    }
    if CLI_COL:
        col_cfg_v["Clientes"] = st.column_config.NumberColumn("Clientes", help="Clientes distintos atendidos")
    if DSCTO_COL:
        col_cfg_v["% Dscto."] = st.column_config.NumberColumn("% Dscto.", help="Porcentaje de descuento promedio aplicado")

    st.dataframe(
        top_disp.style.format({
            "Ventas ($)":       "{:,.0f}",
            "Rentabilidad ($)": "{:,.0f}",
            "Unidades":         "{:,.0f}",
        }),
        column_config=col_cfg_v,
        use_container_width=True, hide_index=True,
    )

    # ── Gráfica barras: ventas por vendedor ───────────────────────────────
    st.subheader("💰 Ventas Netas por vendedor")
    st.caption("El color de cada barra refleja su % Margen: verde = rentable, rojo = margen bajo. Pasa el cursor sobre la barra para ver el detalle.")
    fig_rank = px.bar(
        top_data.sort_values("Ventas_Netas"),
        x="Ventas_Netas", y=VEND_COL, orientation="h",
        color="%_Margen", color_continuous_scale="RdYlGn",
        text_auto=".3s",
        labels={"Ventas_Netas": "Ventas ($)", VEND_COL: "", "%_Margen": "% Margen"},
        hover_data={"%_Margen": ":.1%", "Ventas_Netas": ":,.0f"},
    )
    fig_rank.update_layout(
        plot_bgcolor="white", height=max(380, top_n * 36),
        coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"),
        margin=dict(l=10, r=10, t=20, b=20),
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    # ── Gráfica combinada: Ventas (barras) + % Margen (línea) ────────────
    st.subheader("📊 Ventas y % Margen por vendedor")
    st.caption(
        "Barras azules = Ventas Netas  •  Línea naranja = % Margen  •  "
        "🟢 ≥ 35%  🟡 20–35%  🔴 < 20%  •  "
        "Las líneas punteadas marcan los umbrales mínimo (20%) y meta (35%) de margen."
    )

    combo_df = top_data.sort_values("Ventas_Netas", ascending=False).copy()
    colores_mg = [
        "#ef4444" if v < 0.20 else "#f59e0b" if v < 0.35 else "#22c55e"
        for v in combo_df["%_Margen"]
    ]
    nombres = combo_df[VEND_COL].str.split().str[:2].str.join(" ")  # primeras 2 palabras

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(
        x=nombres, y=combo_df["Ventas_Netas"],
        name="Ventas ($)",
        marker_color="#3b82f6",
        text=[f"${v/1e6:.0f}M" if v < 1e9 else f"${v/1e9:.1f}B" for v in combo_df["Ventas_Netas"]],
        textposition="outside",
        yaxis="y1",
        hovertemplate="<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>",
    ))
    fig_combo.add_trace(go.Scatter(
        x=nombres, y=combo_df["%_Margen"] * 100,
        name="% Margen",
        mode="lines+markers+text",
        line=dict(color="#f59e0b", width=2),
        marker=dict(color=colores_mg, size=11, line=dict(color="white", width=1)),
        text=[f"{v*100:.1f}%" for v in combo_df["%_Margen"]],
        textposition="top center",
        textfont=dict(size=10),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>% Margen: %{y:.1f}%<extra></extra>",
    ))
    fig_combo.add_hline(y=20, line_dash="dot", line_color="#ef4444",
                        annotation_text="Mínimo 20%", annotation_position="bottom right",
                        yref="y2", annotation_font=dict(size=9, color="#ef4444"))
    fig_combo.add_hline(y=35, line_dash="dot", line_color="#22c55e",
                        annotation_text="Meta 35%", annotation_position="top right",
                        yref="y2", annotation_font=dict(size=9, color="#22c55e"))
    fig_combo.update_layout(
        plot_bgcolor="white", height=420,
        margin=dict(t=40, b=80, l=10, r=10),
        xaxis=dict(tickangle=-35, tickfont=dict(size=10)),
        yaxis=dict(title="Ventas Netas ($)", showgrid=True, gridcolor="#e2e8f0"),
        yaxis2=dict(title="% Margen", overlaying="y", side="right",
                    ticksuffix="%",
                    range=[0, max(combo_df["%_Margen"] * 100) * 1.5]),
        legend=dict(orientation="h", y=-0.25),
        bargap=0.3,
    )
    st.plotly_chart(fig_combo, use_container_width=True)

    st.download_button(
        "📥 Descargar ranking CSV",
        data=ranking.rename(columns=rename).to_csv(index=False, encoding="utf-8-sig"),
        file_name="ranking_vendedores.csv", mime="text/csv"
    )

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 – DETALLE POR VENDEDOR
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    vendedores_lista = sorted(df[VEND_COL].dropna().unique().tolist())
    vend_sel = st.selectbox("Selecciona vendedor", vendedores_lista)
    df_v = df[df[VEND_COL] == vend_sel].copy()

    if df_v.empty:
        st.info("Sin datos.")
    else:
        v_v = df_v["Valor_Neto"].sum()         if "Valor_Neto"         in df_v.columns else 0
        r_v = df_v["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df_v.columns else 0
        q_v = df_v["Cantidad"].sum()           if "Cantidad"           in df_v.columns else 0
        c_v = df_v[CLI_COL].nunique()          if CLI_COL else 0

        i1, i2, i3, i4 = st.columns(4)
        i1.metric("💰 Ventas",    formatear_millones(v_v),
                  help="Suma del valor neto facturado en el período (sin IVA)")
        i2.metric("📈 Margen",    f"{r_v/v_v*100:.1f}%" if v_v else "—",
                  help="(Ventas - Costo) / Ventas × 100")
        i3.metric("📦 Unidades",  f"{q_v:,.0f}",
                  help="Número total de unidades vendidas")
        i4.metric("🏪 Clientes",  f"{c_v:,}",
                  help="Número de clientes distintos atendidos")

        if RUTA_COL and RUTA_COL in df_v.columns:
            rutas_vend = df_v[RUTA_COL].dropna().unique()
            st.info(f"**Rutas asignadas:** {', '.join(str(r).strip() for r in rutas_vend)}")

        # Top clientes
        if CLI_COL:
            st.markdown("#### Top clientes de este vendedor")
            top_cli = (
                df_v.groupby(CLI_COL)
                .agg(Ventas=("Valor_Neto","sum"), Unidades=("Cantidad","sum"),
                     Margen=("Valor_Rentabilidad","sum"))
                .reset_index().nlargest(15,"Ventas")
            )
            top_cli["%_Mg"] = top_cli["Margen"] / top_cli["Ventas"].replace(0,1)
            st.dataframe(
                top_cli.rename(columns={CLI_COL:"Cliente","Ventas":"Ventas ($)","%_Mg":"% Margen"})
                .style.format({"Ventas ($)":"{:,.0f}","Unidades":"{:,.0f}","% Margen":"{:.2%}"}),
                column_config={
                    "% Margen": st.column_config.NumberColumn("% Margen", help="(Ventas - Costo) / Ventas × 100"),
                },
                use_container_width=True, hide_index=True
            )

        # Top productos
        if "Nombre_Item" in df_v.columns or "Desc. item" in df_v.columns:
            item_c = get_col(df_v, "Nombre_Item", "Desc. item")
            st.markdown("#### Top productos vendidos")
            top_prod = (
                df_v.groupby(item_c)["Valor_Neto"].sum()
                .nlargest(10).reset_index()
            )
            top_prod.columns = ["Producto", "Ventas ($)"]
            fig_prod = px.bar(
                top_prod.sort_values("Ventas ($)"), x="Ventas ($)", y="Producto",
                orientation="h", text_auto=".3s", color="Ventas ($)",
                color_continuous_scale=[[0,"#bfdbfe"],[1,"#1d4ed8"]],
            )
            fig_prod.update_layout(plot_bgcolor="white", coloraxis_showscale=False,
                                   height=350, yaxis=dict(title=""))
            st.plotly_chart(fig_prod, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 – EVOLUCIÓN TEMPORAL
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if "Fecha" not in df.columns:
        st.info("Se requiere columna Fecha.")
    else:
        st.subheader("📈 Ventas diarias — Top vendedores")
        top_vend_names = ranking.head(8)[VEND_COL].tolist()
        df_top = df[df[VEND_COL].isin(top_vend_names)].copy()

        serie_v = (
            df_top.groupby([VEND_COL, df_top["Fecha"].dt.date])["Valor_Neto"]
            .sum().reset_index()
        )
        serie_v.columns = ["Vendedor", "Fecha", "Ventas"]

        fig_evo = px.line(
            serie_v, x="Fecha", y="Ventas", color="Vendedor",
            markers=True, labels={"Ventas": "Ventas ($)"},
        )
        fig_evo.update_layout(plot_bgcolor="white", height=450,
                               legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_evo, use_container_width=True)
