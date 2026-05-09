"""
pages/8_📦_Productos.py
Análisis de productos:
  • Top 20 por valor neto
  • Treemap por Grupo → Sub-grupo → Producto
  • Análisis de precio unitario
  • Volumen en litros por producto
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Productos", page_icon="📦", layout="wide")

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

ITEM_COL   = get_col(df_all, "Nombre_Item",  "Desc. item")
FAM_COL    = get_col(df_all, "Familia",      "GRUPOS")
SUBG_COL   = get_col(df_all, "SubGrupo",     "SUB-GRUPO")
CANAL_COL  = get_col(df_all, "Canal",        "CANAL DE VENTAS")
ZONA_COL   = get_col(df_all, "Zona",         "ZONAS")
LITROS_COL = get_col(df_all, "Litros",       "Vol?men en LTR ")
PRECIO_COL = get_col(df_all, "Precio_Unit",  "Precio unit.")
REF_COL    = get_col(df_all, "Referencia")
DSCTO_COL  = get_col(df_all, "Descuento_Pct","Dscto. promedio %")

def semaforo(val):
    if not isinstance(val, (int, float)): return ""
    pct = val * 100 if val <= 1 else val
    if pct >= 35: return "color:#16a34a;font-weight:bold"
    if pct >= 20: return "color:#ca8a04"
    return "color:#dc2626"

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

    if SUBG_COL:
        subgrupos = ["Todos"] + sorted(df_all[SUBG_COL].dropna().unique().tolist())
        subg_sel = st.selectbox("Sub-Grupo", subgrupos)
    else:
        subg_sel = "Todos"

    top_n = st.slider("Top N productos", 10, 50, 20)

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if canal_sel != "Todos" and CANAL_COL:
    df = df[df[CANAL_COL] == canal_sel]
if subg_sel != "Todos" and SUBG_COL:
    df = df[df[SUBG_COL] == subg_sel]

st.title("📦 Análisis de Productos")
st.caption(f"Canal: **{canal_sel}**  •  Sub-grupo: **{subg_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
venta   = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
rent    = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
n_items = df[ITEM_COL].nunique()         if ITEM_COL else 0
litros  = df[LITROS_COL].sum()           if LITROS_COL else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Netas",  formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k2.metric("📈 Margen",        f"{rent/venta*100:.1f}%" if venta else "—",
          help="(Ventas - Costo) / Ventas × 100")
k3.metric("🏷️ Ítems únicos", f"{n_items:,}",
          help="Número de referencias de producto distintas")
k4.metric("🥛 Litros totales", f"{litros:,.0f}" if litros else "—",
          help="Volumen total vendido en litros")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    ["🏆 Top Productos", "🗂️ Por Grupo / Sub-grupo", "💲 Precios", "📅 Tendencia"]
)

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 – TOP PRODUCTOS
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    if not ITEM_COL:
        st.warning("Columna de ítem no encontrada.")
    else:
        agg_c = {
            "Ventas": ("Valor_Neto",         "sum"),
            "Margen": ("Valor_Rentabilidad", "sum"),
            "Unidades": ("Cantidad",         "sum"),
        }
        if LITROS_COL: agg_c["Litros"] = (LITROS_COL, "sum")

        top = df.groupby(ITEM_COL).agg(**agg_c).reset_index().nlargest(top_n, "Ventas")
        total_vn = top["Ventas"].sum()
        top["%_Margen"] = top["Margen"] / top["Ventas"].replace(0, 1)
        top["%_Part"]   = top["Ventas"] / total_vn if total_vn else 0

        # ── Gráfica ──────────────────────────────────────────────────────────
        st.subheader(f"💰 Top {top_n} por Ventas Netas")
        st.caption("Barras horizontales con los productos de mayor venta. El color de cada barra indica su % de margen: 🟢 verde = alto · 🟡 amarillo = medio · 🔴 rojo = bajo. Ajusta el 'Top N' en el panel lateral.")
        fig_top = px.bar(
            top.sort_values("Ventas"), x="Ventas", y=ITEM_COL,
            orientation="h", color="%_Margen",
            color_continuous_scale="RdYlGn", text_auto=".3s",
            labels={"Ventas": "Ventas ($)", ITEM_COL: "", "%_Margen": "% Margen"},
        )
        fig_top.update_layout(
            plot_bgcolor="white", height=max(500, top_n * 32),
            coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"),
            margin=dict(l=10, r=10, t=20, b=20),
        )
        st.plotly_chart(fig_top, use_container_width=True)

        # ── Tabla ─────────────────────────────────────────────────────────────
        st.subheader("📋 Detalle")
        st.caption("Tabla de los mismos productos con sus métricas. **Ventas ($)** = Ventas Netas · **% Margen** = (Ventas − Costo) / Ventas · **% Part.** = participación sobre el total · **Margen ($)** = ganancia en pesos.")
        cols_det = [ITEM_COL, "Ventas", "Margen", "%_Margen", "%_Part", "Unidades"]
        if LITROS_COL and "Litros" in top.columns:
            cols_det.append("Litros")
        top_det = top[cols_det].rename(columns={
            ITEM_COL:   "Producto",
            "Ventas":   "Ventas ($)",
            "Margen":   "Margen ($)",
            "%_Margen": "% Margen",
            "%_Part":   "% Part.",
        })
        fmt_det = {
            "Ventas ($)": "{:,.0f}",
            "Margen ($)": "{:,.0f}",
            "Unidades":   "{:,.0f}",
            "% Margen":   "{:.2%}",
            "% Part.":    "{:.2%}",
        }
        if LITROS_COL and "Litros" in top.columns:
            fmt_det["Litros"] = "{:,.1f}"
        st.dataframe(
            top_det.style.format(fmt_det).map(semaforo, subset=["% Margen"]),
            column_config={
                "% Margen":   st.column_config.NumberColumn("% Margen",   help="(Ventas − Costo) / Ventas × 100"),
                "% Part.":    st.column_config.NumberColumn("% Part.",     help="Participación sobre el total del período"),
                "Margen ($)": st.column_config.NumberColumn("Margen ($)",  help="Rentabilidad en pesos = Ventas − Costo"),
            },
            use_container_width=True, hide_index=True,
        )

        # Pareto acumulado
        st.subheader("📊 Regla 80/20 — concentración de ventas")
        st.caption(
            "**Principio de Pareto:** en la mayoría de negocios, un pequeño grupo de productos "
            "genera la mayor parte de las ventas. "
            "La curva muestra cuánto % acumulado de ventas aportan los primeros N productos "
            "(ordenados de mayor a menor). "
            "La zona azul son los productos que generan el **80% de las ventas** — son los más críticos."
        )

        top_pareto = (
            df.groupby(ITEM_COL)["Valor_Neto"].sum()
            .sort_values(ascending=False).reset_index()
        )
        top_pareto.columns = ["Producto", "Ventas"]
        top_pareto["%_Acum"] = top_pareto["Ventas"].cumsum() / top_pareto["Ventas"].sum() * 100
        top_pareto["N"] = range(1, len(top_pareto) + 1)

        n80 = int((top_pareto["%_Acum"] <= 80).sum()) + 1
        total_items = len(top_pareto)
        plot_pareto = top_pareto.head(min(100, total_items)).copy()

        import plotly.graph_objects as go_p
        fig_pareto = go_p.Figure()

        # Área sombreada: los productos del 80%
        mask80 = plot_pareto["N"] <= n80
        fig_pareto.add_trace(go_p.Scatter(
            x=plot_pareto.loc[mask80, "N"],
            y=plot_pareto.loc[mask80, "%_Acum"],
            fill="tozeroy", mode="none",
            fillcolor="rgba(59,130,246,0.15)",
            name=f"Top {n80} productos (80% ventas)",
            showlegend=True,
        ))
        # Línea completa
        fig_pareto.add_trace(go_p.Scatter(
            x=plot_pareto["N"], y=plot_pareto["%_Acum"],
            mode="lines", line=dict(color="#1d4ed8", width=2),
            name="% Ventas acumuladas",
        ))
        # Líneas de referencia
        fig_pareto.add_hline(y=80, line_dash="dot", line_color="#ef4444",
                             annotation_text="80% de ventas",
                             annotation_position="bottom right",
                             annotation_font=dict(size=10, color="#ef4444"))
        fig_pareto.add_vline(x=n80, line_dash="dot", line_color="#3b82f6",
                             annotation_text=f"{n80} productos",
                             annotation_position="top right",
                             annotation_font=dict(size=10, color="#1d4ed8"))
        fig_pareto.update_layout(
            plot_bgcolor="white", height=380,
            xaxis=dict(title="Productos (ordenados de mayor a menor venta)"),
            yaxis=dict(title="% Ventas acumuladas", ticksuffix="%", range=[0, 105]),
            legend=dict(orientation="h", y=-0.2),
            margin=dict(t=20, b=60),
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

        c1, c2 = st.columns(2)
        c1.metric("📌 Productos clave (generan 80% ventas)",
                  f"{n80} de {total_items}",
                  help="Número de productos que acumulan el 80% de las ventas totales")
        c2.metric("📉 Concentracion",
                  f"{n80/total_items*100:.1f}% del catálogo",
                  help="Qué porcentaje del catálogo total representa ese grupo clave")

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 – TREEMAP GRUPO / SUB-GRUPO
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    treemap_cols = [c for c in [FAM_COL, SUBG_COL, ITEM_COL] if c]
    if len(treemap_cols) < 2:
        st.info("Se necesitan columnas de Familia/Grupo y Sub-grupo.")
    else:
        agg_tree = df.groupby(treemap_cols).agg(
            Ventas=("Valor_Neto", "sum"),
            Margen=("Valor_Rentabilidad", "sum"),
            Unidades=("Cantidad", "sum"),
        ).reset_index()
        agg_tree["%_Mg"] = agg_tree["Margen"] / agg_tree["Ventas"].replace(0, 1)
        agg_tree = agg_tree[agg_tree["Ventas"] > 0]

        # Limpiar strings del GRUPOS
        for col in treemap_cols:
            agg_tree[col] = agg_tree[col].astype(str).str.strip()

        st.subheader("🗂️ Treemap de ventas por grupo")
        st.caption("Mapa de área donde el tamaño de cada bloque representa las ventas. Los bloques más grandes son los grupos/productos que más venden. El color indica el % de margen (verde = alto, rojo = bajo). Haz clic en un grupo para ver su detalle.")
        fig_tree = px.treemap(
            agg_tree,
            path=[px.Constant("Todos")] + treemap_cols,
            values="Ventas",
            color="%_Mg",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0.3,
            hover_data={"Ventas": ":,.0f", "Unidades": ":,.0f", "%_Mg": ":.2%"},
            labels={"%_Mg": "% Margen"},
        )
        fig_tree.update_layout(height=600,
                                coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"))
        fig_tree.update_traces(textinfo="label+value+percent root")
        st.plotly_chart(fig_tree, use_container_width=True)

        # Tabla por grupo
        if FAM_COL:
            st.subheader("📋 Resumen por Grupo")
            st.caption("Ventas totales por familia de producto con rentabilidad. **N° Ítems** = referencias distintas dentro de ese grupo · **% Margen** indica la rentabilidad promedio de la categoría.")
            resumen_g = df.groupby(FAM_COL).agg(
                Ventas=("Valor_Neto", "sum"),
                Margen=("Valor_Rentabilidad", "sum"),
                Unidades=("Cantidad", "sum"),
                Items=(ITEM_COL, "nunique") if ITEM_COL else ("Cantidad", "count"),
            ).reset_index()
            total_vn_g = resumen_g["Ventas"].sum()
            resumen_g["%_Mg"] = resumen_g["Margen"] / resumen_g["Ventas"].replace(0, 1)
            resumen_g["%_Part"] = resumen_g["Ventas"] / total_vn_g if total_vn_g else 0
            resumen_g[FAM_COL] = resumen_g[FAM_COL].astype(str).str.strip()
            resumen_g = resumen_g.sort_values("Ventas", ascending=False)

            st.dataframe(
                resumen_g.rename(columns={
                    FAM_COL: "Grupo", "Ventas": "Ventas ($)",
                    "Margen": "Margen ($)", "Items": "N° Ítems",
                    "%_Mg": "% Margen", "%_Part": "% Part.",
                }).style.format({
                    "Ventas ($)": "{:,.0f}", "Margen ($)": "{:,.0f}",
                    "Unidades": "{:,.0f}", "N° Ítems": "{:,.0f}",
                    "% Margen": "{:.2%}", "% Part.": "{:.2%}",
                }).map(semaforo, subset=["% Margen"]),
                column_config={
                    "% Margen":  st.column_config.NumberColumn("% Margen",  help="(Ventas - Costo) / Ventas × 100"),
                    "% Part.":   st.column_config.NumberColumn("% Part.",   help="Participación porcentual sobre el total del período"),
                    "N° Ítems":  st.column_config.NumberColumn("N° Ítems",  help="Número de referencias de producto distintas"),
                },
                use_container_width=True, hide_index=True
            )

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 – PRECIOS
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if not PRECIO_COL or not ITEM_COL:
        st.info("Se requieren columnas de precio unitario e ítem.")
    else:
        st.subheader("💲 Precio unitario por producto")
        st.caption("Cada punto es un producto. **Eje X** = precio promedio de venta · **Eje Y** = variación entre el precio más alto y más bajo registrado (Max − Min). Una variación alta puede indicar descuentos inconsistentes entre clientes o fechas. El tamaño del punto representa el volumen de ventas.")
        precio_data = (
            df.groupby(ITEM_COL)
            .agg(
                Precio_Prom=(PRECIO_COL, "mean"),
                Precio_Min=(PRECIO_COL, "min"),
                Precio_Max=(PRECIO_COL, "max"),
                Unidades=("Cantidad", "sum"),
                Ventas=("Valor_Neto", "sum"),
            )
            .reset_index()
            .nlargest(top_n, "Ventas")
        )
        precio_data["Rango_Precio"] = precio_data["Precio_Max"] - precio_data["Precio_Min"]

        st.caption(
            "Cada punto es un producto. "
            "**Eje X:** precio promedio de venta. "
            "**Eje Y:** variación entre el precio máximo y mínimo registrado — "
            "alta variación puede indicar descuentos inconsistentes. "
            "El tamaño del punto representa las ventas totales. "
            "Pasa el cursor para ver el nombre del producto."
        )
        precio_data["_nombre_corto"] = precio_data[ITEM_COL].str[:30]
        fig_precio = px.scatter(
            precio_data, x="Precio_Prom", y="Rango_Precio",
            size="Ventas", hover_name=ITEM_COL,
            color="Unidades", color_continuous_scale="Blues",
            hover_data={"Precio_Prom": ":,.0f", "Rango_Precio": ":,.0f",
                        "Ventas": ":,.0f", "_nombre_corto": False},
            labels={
                "Precio_Prom":  "Precio Promedio ($)",
                "Rango_Precio": "Variacion precio (Max-Min $)",
            },
        )
        fig_precio.update_layout(plot_bgcolor="white", height=450,
                                  coloraxis_colorbar=dict(title="Unidades"))
        st.plotly_chart(fig_precio, use_container_width=True)

        st.subheader("📋 Tabla de precios")
        st.dataframe(
            precio_data.rename(columns={
                ITEM_COL: "Producto",
                "Precio_Prom": "Precio Prom ($)",
                "Precio_Min":  "Precio Mín ($)",
                "Precio_Max":  "Precio Máx ($)",
                "Rango_Precio": "Variación ($)",
                "Unidades": "Unidades",
            }).style.format({
                "Precio Prom ($)": "{:,.0f}", "Precio Mín ($)": "{:,.0f}",
                "Precio Máx ($)": "{:,.0f}", "Variación ($)": "{:,.0f}",
                "Unidades": "{:,.0f}",
            }),
            use_container_width=True, hide_index=True
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 4 – TENDENCIA TEMPORAL
# ─────────────────────────────────────────────────────────────────────────
with tab4:
    if "Fecha" not in df.columns or not ITEM_COL:
        st.info("Se requieren columnas Fecha e Ítem.")
    else:
        st.subheader("📅 Evolución de ventas por producto")
        st.caption("Evolución diaria de ventas de los 8 productos con mayor facturación. Cada línea es un producto. Permite identificar estacionalidades, picos de demanda y caídas.")
        # Solo top 8 por ventas para que la gráfica sea legible
        top8 = df.groupby(ITEM_COL)["Valor_Neto"].sum().nlargest(8).index.tolist()
        df_t8 = df[df[ITEM_COL].isin(top8)].copy()

        serie_p = (
            df_t8.groupby([ITEM_COL, df_t8["Fecha"].dt.date])["Valor_Neto"]
            .sum().reset_index()
        )
        serie_p.columns = ["Producto", "Fecha", "Ventas"]

        fig_evo = px.line(
            serie_p, x="Fecha", y="Ventas", color="Producto",
            markers=True,
            labels={"Ventas": "Ventas ($)", "Fecha": ""},
            title="Top 8 productos — ventas diarias",
        )
        fig_evo.update_layout(plot_bgcolor="white", height=450,
                               legend=dict(orientation="h", y=-0.3))
        st.plotly_chart(fig_evo, use_container_width=True)

        if LITROS_COL and df[LITROS_COL].sum() > 0:
            st.subheader("🥛 Volumen en litros — Top 8 productos")
            serie_l = (
                df_t8.groupby([ITEM_COL, df_t8["Fecha"].dt.date])[LITROS_COL]
                .sum().reset_index()
            )
            serie_l.columns = ["Producto", "Fecha", "Litros"]
            fig_lit = px.area(
                serie_l, x="Fecha", y="Litros", color="Producto",
                labels={"Litros": "Litros"},
            )
            fig_lit.update_layout(plot_bgcolor="white", height=380,
                                   legend=dict(orientation="h", y=-0.3))
            st.plotly_chart(fig_lit, use_container_width=True)
