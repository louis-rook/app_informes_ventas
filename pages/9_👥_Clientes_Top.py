"""
pages/9_👥_Clientes_Top.py
Análisis de clientes y concentración de cartera:
  • Top 20 clientes por ventas
  • Pareto 80/20 con alerta de concentración
  • Por Clase de Cliente
  • Clientes nuevos vs recurrentes (si hay período anterior)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Clientes Top", page_icon="👥", layout="wide")

df_all = cargar_data()
if df_all.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

def get_col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

CLI_COL   = get_col(df_all, "Nombre_Cliente",  "Razon social cliente factura")
CLASE_COL = get_col(df_all, "Clase_Cliente",   "CLASES DE CLIENTES")
CANAL_COL = get_col(df_all, "Canal",           "CANAL DE VENTAS")
ZONA_COL  = get_col(df_all, "Zona",            "ZONAS")
VEND_COL  = get_col(df_all, "Nombre_Vendedor", "Nombre vendedor")
ITEM_COL  = get_col(df_all, "Nombre_Item",     "Desc. item")

if not CLI_COL:
    st.error("❌ Columna de cliente no encontrada.")
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

    if CLASE_COL:
        clases = ["Todas"] + sorted(df_all[CLASE_COL].dropna().unique().tolist())
        clase_sel = st.selectbox("Clase de Cliente", clases)
    else:
        clase_sel = "Todas"

    top_n = st.slider("Top N clientes", 10, 50, 20)
    umbral_conc = st.slider("Umbral concentración (%)", 50, 95, 80,
                             help="Alerta si N clientes superan este % de las ventas")

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if canal_sel != "Todos" and CANAL_COL:
    df = df[df[CANAL_COL] == canal_sel]
if clase_sel != "Todas" and CLASE_COL:
    df = df[df[CLASE_COL] == clase_sel]

st.title("👥 Clientes y Concentración de Cartera")
st.caption(f"Canal: **{canal_sel}**  •  Clase: **{clase_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── KPIs globales ──────────────────────────────────────────────────────────
n_cli  = df[CLI_COL].nunique()
venta  = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
rent   = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0

# Concentración: ¿cuántos clientes hacen el X%?
cli_rank = (
    df.groupby(CLI_COL)["Valor_Neto"].sum()
    .sort_values(ascending=False).reset_index()
)
cli_rank.columns = ["Cliente", "Ventas"]
cli_rank["%_Acum"] = cli_rank["Ventas"].cumsum() / cli_rank["Ventas"].sum() * 100
n_top_umbral = (cli_rank["%_Acum"] <= umbral_conc).sum() + 1
pct_clientes = n_top_umbral / n_cli * 100 if n_cli else 0

# Cliente #1
top1_nombre = cli_rank.iloc[0]["Cliente"] if len(cli_rank) else "—"
top1_pct = cli_rank.iloc[0]["Ventas"] / venta * 100 if venta and len(cli_rank) else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("👥 Clientes activos", f"{n_cli:,}",
          help="Clientes con al menos una venta en el período")
k2.metric("💰 Ventas Netas",     formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k3.metric("📈 Margen global",    f"{rent/venta*100:.1f}%" if venta else "—",
          help="(Ventas - Costo) / Ventas × 100")
k4.metric(f"🎯 {n_top_umbral} clientes = {umbral_conc}% ventas",
          f"{pct_clientes:.1f}% del total",
          delta=f"Riesgo {'ALTO' if pct_clientes < 10 else 'MODERADO'}",
          delta_color="inverse",
          help="Indicador de concentración de cartera de clientes")
k5.metric("🥇 Top cliente",
          f"{str(top1_nombre)[:25]}...",
          delta=f"{top1_pct:.1f}% de ventas",
          delta_color="off",
          help="Cliente con mayor valor de ventas en el período")

# Alerta de concentración
if pct_clientes < 5:
    st.error(f"⚠️ **Alta concentración:** solo {n_top_umbral} clientes ({pct_clientes:.1f}% del total) "
             f"representan el {umbral_conc}% de las ventas.")
elif pct_clientes < 15:
    st.warning(f"🟡 **Concentración moderada:** {n_top_umbral} clientes ({pct_clientes:.1f}%) "
               f"= {umbral_conc}% de las ventas.")
else:
    st.success(f"✅ **Cartera diversificada:** {n_top_umbral} clientes ({pct_clientes:.1f}%) "
               f"= {umbral_conc}% de las ventas.")

st.divider()

tab1, tab2, tab3 = st.tabs(["🏆 Top Clientes", "📊 Pareto 80/20", "🏷️ Por Clase de Cliente"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 – TOP CLIENTES
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    agg_c = {
        "Ventas":     ("Valor_Neto",         "sum"),
        "Margen":     ("Valor_Rentabilidad", "sum"),
        "Unidades":   ("Cantidad",           "sum"),
        "Transacciones": (CLI_COL,           "count"),
    }
    if ITEM_COL: agg_c["Items_distintos"] = (ITEM_COL, "nunique")
    if CLASE_COL and clase_sel == "Todas":
        agg_c["Clase"] = (CLASE_COL, "first")
    if CANAL_COL and canal_sel == "Todos":
        agg_c["Canal"] = (CANAL_COL, "first")
    if VEND_COL:
        agg_c["Vendedor"] = (VEND_COL, "first")

    top_cli = df.groupby(CLI_COL).agg(**agg_c).reset_index()
    total_vn = top_cli["Ventas"].sum()
    top_cli["%_Mg"]   = top_cli["Margen"] / top_cli["Ventas"].replace(0, 1)
    top_cli["%_Part"]  = top_cli["Ventas"] / total_vn if total_vn else 0
    top_cli = top_cli.nlargest(top_n, "Ventas")

    col_g, col_t = st.columns([2, 1])
    with col_g:
        st.subheader(f"💰 Top {top_n} clientes por Ventas Netas")
        fig_cli = px.bar(
            top_cli.sort_values("Ventas"), x="Ventas", y=CLI_COL,
            orientation="h", color="%_Mg",
            color_continuous_scale="RdYlGn", text_auto=".3s",
            labels={"Ventas": "$", CLI_COL: "", "%_Mg": "% Margen"},
        )
        fig_cli.update_layout(
            plot_bgcolor="white", height=max(450, top_n * 30),
            coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"),
        )
        st.plotly_chart(fig_cli, use_container_width=True)

    with col_t:
        st.subheader("📋 Detalle")
        fmt_c = {"Ventas": "{:,.0f}", "Unidades": "{:,.0f}",
                 "%_Mg": "{:.2%}", "%_Part": "{:.2%}",
                 "Transacciones": "{:,.0f}"}

        def semaforo(val):
            if not isinstance(val, (int, float)): return ""
            pct = val * 100 if val <= 1 else val
            if pct >= 35: return "color:#16a34a;font-weight:bold"
            if pct >= 20: return "color:#ca8a04"
            return "color:#dc2626"

        cols_show = [CLI_COL, "Ventas", "%_Mg", "%_Part", "Transacciones"]
        if ITEM_COL: cols_show.append("Items_distintos")

        st.dataframe(
            top_cli[cols_show]
            .rename(columns={
                CLI_COL: "Cliente", "Ventas": "Ventas ($)",
                "%_Mg": "% Margen", "%_Part": "% Part.",
                "Items_distintos": "# Productos",
            })
            .style.format({
                "Ventas ($)": "{:,.0f}", "% Margen": "{:.2%}",
                "% Part.": "{:.2%}", "Transacciones": "{:,.0f}",
            })
            .map(semaforo, subset=["% Margen"]),
            column_config={
                "% Margen":      st.column_config.NumberColumn("% Margen",      help="(Ventas - Costo) / Ventas × 100"),
                "% Part.":       st.column_config.NumberColumn("% Part.",       help="Participación porcentual sobre el total del período"),
                "Transacciones": st.column_config.NumberColumn("Transacciones", help="Número de documentos de venta generados"),
                "# Productos":   st.column_config.NumberColumn("# Productos",   help="Número de referencias de producto distintas"),
            },
            use_container_width=True, hide_index=True, height=500
        )

    # Detalle de un cliente seleccionado
    st.divider()
    st.subheader("🔍 Zoom en un cliente")
    cli_zoom = st.selectbox("Selecciona cliente", top_cli[CLI_COL].tolist(), key="zoom")
    df_z = df[df[CLI_COL] == cli_zoom]
    if not df_z.empty and ITEM_COL:
        top_items_z = (
            df_z.groupby(ITEM_COL)
            .agg(Ventas=("Valor_Neto","sum"), Unidades=("Cantidad","sum"))
            .reset_index().nlargest(10,"Ventas")
        )
        fig_z = px.pie(
            top_items_z, values="Ventas", names=ITEM_COL,
            title=f"Composición de compras — {cli_zoom}",
        )
        fig_z.update_layout(height=320)
        st.plotly_chart(fig_z, use_container_width=True)

    st.download_button(
        "📥 Descargar Top Clientes CSV",
        data=top_cli.rename(columns={CLI_COL: "Cliente"})
                    .to_csv(index=False, encoding="utf-8-sig"),
        file_name="top_clientes.csv", mime="text/csv"
    )

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 – PARETO
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("📊 Análisis de Pareto — Concentración de ventas")

    cli_rank_full = (
        df.groupby(CLI_COL)["Valor_Neto"].sum()
        .sort_values(ascending=False).reset_index()
    )
    cli_rank_full.columns = ["Cliente", "Ventas"]
    cli_rank_full["%_Acum"] = cli_rank_full["Ventas"].cumsum() / cli_rank_full["Ventas"].sum() * 100
    cli_rank_full["N_Cliente"] = range(1, len(cli_rank_full) + 1)

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(
        x=cli_rank_full["N_Cliente"],
        y=cli_rank_full["Ventas"],
        name="Ventas por cliente",
        marker_color="#3b82f6",
        opacity=0.7,
        yaxis="y",
    ))
    fig_pareto.add_trace(go.Scatter(
        x=cli_rank_full["N_Cliente"],
        y=cli_rank_full["%_Acum"],
        name="% Acumulado",
        line=dict(color="#ef4444", width=2),
        yaxis="y2",
    ))
    fig_pareto.add_hline(y=80, line_dash="dot", line_color="#f59e0b",
                          annotation_text="80%", yref="y2")

    fig_pareto.update_layout(
        plot_bgcolor="white", height=480,
        xaxis=dict(title="N° de clientes (ordenados por ventas)"),
        yaxis=dict(title="Ventas ($)", showgrid=False),
        yaxis2=dict(title="% Acumulado", overlaying="y", side="right",
                    range=[0, 105], ticksuffix="%"),
        legend=dict(orientation="h", y=-0.2),
        barmode="overlay",
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    # Tabla resumen de concentración
    st.subheader("📋 Resumen de concentración")
    niveles = [10, 20, 30, 50, 80]
    rows_conc = []
    total_vn_p = cli_rank_full["Ventas"].sum()
    for pct_obj in niveles:
        n_cli_pct = int((cli_rank_full["%_Acum"] <= pct_obj).sum()) + 1
        rows_conc.append({
            "% Ventas": f"{pct_obj}%",
            "N° Clientes": n_cli_pct,
            "% del total clientes": f"{n_cli_pct / len(cli_rank_full) * 100:.1f}%",
        })
    st.dataframe(pd.DataFrame(rows_conc), use_container_width=False, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 – POR CLASE DE CLIENTE
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if not CLASE_COL:
        st.info("Columna de clase de cliente no encontrada.")
    else:
        agg_clase = df.groupby(CLASE_COL).agg(
            Ventas=("Valor_Neto", "sum"),
            Margen=("Valor_Rentabilidad", "sum"),
            Unidades=("Cantidad", "sum"),
            Clientes=(CLI_COL, "nunique"),
        ).reset_index()
        total_vn_c = agg_clase["Ventas"].sum()
        agg_clase["%_Mg"]   = agg_clase["Margen"] / agg_clase["Ventas"].replace(0, 1)
        agg_clase["%_Part"] = agg_clase["Ventas"] / total_vn_c if total_vn_c else 0
        agg_clase = agg_clase.sort_values("Ventas", ascending=False)

        col_p, col_b = st.columns(2)
        with col_p:
            st.subheader("🥧 Participación por clase")
            fig_pie = px.pie(
                agg_clase, values="Ventas", names=CLASE_COL,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_pie.update_layout(height=380)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            st.subheader("📊 Margen por clase")
            fig_mg = px.bar(
                agg_clase.sort_values("%_Mg"), x="%_Mg", y=CLASE_COL,
                orientation="h", text_auto=".1%",
                color="%_Mg", color_continuous_scale="RdYlGn",
                labels={"%_Mg": "% Margen", CLASE_COL: ""},
            )
            fig_mg.update_layout(plot_bgcolor="white", coloraxis_showscale=False, height=380)
            st.plotly_chart(fig_mg, use_container_width=True)

        st.subheader("📋 Tabla por clase de cliente")
        st.dataframe(
            agg_clase.rename(columns={
                CLASE_COL: "Clase", "Ventas": "Ventas ($)", "Margen": "Margen ($)",
                "Clientes": "N° Clientes", "%_Mg": "% Margen", "%_Part": "% Part.",
            }).style.format({
                "Ventas ($)": "{:,.0f}", "Margen ($)": "{:,.0f}",
                "Unidades": "{:,.0f}", "N° Clientes": "{:,.0f}",
                "% Margen": "{:.2%}", "% Part.": "{:.2%}",
            }),
            column_config={
                "% Margen":    st.column_config.NumberColumn("% Margen",    help="(Ventas - Costo) / Ventas × 100"),
                "% Part.":     st.column_config.NumberColumn("% Part.",     help="Participación porcentual sobre el total del período"),
                "N° Clientes": st.column_config.NumberColumn("N° Clientes", help="Número de clientes distintos atendidos"),
            },
            use_container_width=True, hide_index=True
        )
