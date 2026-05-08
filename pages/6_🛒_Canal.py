"""
pages/6_🛒_Canal.py
Análisis detallado por Canal de Ventas.
  • Resumen por canal: ventas, costo, margen, descuento, participación
  • Tendencia temporal por canal
  • Ranking de productos dentro de cada canal
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Canal de Ventas", page_icon="🛒", layout="wide")

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

CANAL_COL   = get_col(df_all, "Canal", "CANAL DE VENTAS", "Clase_Cliente")
ZONA_COL    = get_col(df_all, "Zona", "ZONAS")
DSCTO_COL   = get_col(df_all, "Descuento_Pct", "Dscto. promedio %")
RUTA_COL    = get_col(df_all, "Ruta", "RUTAS DE VENTAS")
CLASE_COL   = get_col(df_all, "Clase_Cliente", "CLASES DE CLIENTES")
ITEM_COL    = get_col(df_all, "Nombre_Item", "Desc. item")

def safe_pct(num, den):
    return num / den * 100 if den else 0

def semaforo(val):
    if not isinstance(val, (int, float)): return ""
    if val >= 35: return "color:#16a34a;font-weight:bold"
    if val >= 20: return "color:#ca8a04"
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

    if ZONA_COL:
        zonas = ["Todas"] + sorted(df_all[ZONA_COL].dropna().unique().tolist())
        zona_sel = st.selectbox("Zona", zonas)
    else:
        zona_sel = "Todas"

    if CANAL_COL:
        canales = ["Todos"] + sorted(df_all[CANAL_COL].dropna().unique().tolist())
        canal_sel = st.multiselect("Canal (multi-selección)", canales[1:],
                                   default=canales[1:],
                                   help="Deja vacío para ver todos")
    else:
        canal_sel = []

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if zona_sel != "Todas" and ZONA_COL:
    df = df[df[ZONA_COL] == zona_sel]
if canal_sel and CANAL_COL:
    df = df[df[CANAL_COL].isin(canal_sel)]

# ── Título ─────────────────────────────────────────────────────────────────
st.title("📡 Análisis por Canal de Ventas")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

venta = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
costo = df["Costo_Total"].sum()        if "Costo_Total"        in df.columns else 0
rent  = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
cant  = df["Cantidad"].sum()           if "Cantidad"           in df.columns else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Netas",  formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k2.metric("🏭 Costo Total",   formatear_millones(costo),
          help="Costo promedio total de los ítems vendidos")
k3.metric("📈 Rentabilidad",  formatear_millones(rent),
          delta=f"{safe_pct(rent,venta):.1f}%" if venta else None,
          help="Ventas Netas menos Costo Total")
k4.metric("📦 Unidades",      f"{cant:,.0f}",
          help="Número total de unidades vendidas")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📋 Resumen por Canal", "📈 Tendencia Temporal", "🏆 Top Productos por Canal"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 – RESUMEN
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    if not CANAL_COL:
        st.warning("Columna de canal no encontrada.")
    else:
        agg_cols = {
            "Ventas_Netas":  ("Valor_Neto",         "sum"),
            "Costo":         ("Costo_Total",        "sum"),
            "Rentabilidad":  ("Valor_Rentabilidad", "sum"),
            "Unidades":      ("Cantidad",           "sum"),
        }
        if DSCTO_COL:
            agg_cols["Dscto_Prom_Pct"] = (DSCTO_COL, "mean")

        agg = df.groupby(CANAL_COL).agg(**agg_cols).reset_index()
        total_vn = agg["Ventas_Netas"].sum()

        agg["%_Rent"]  = agg["Rentabilidad"] / agg["Ventas_Netas"].replace(0, 1)
        agg["%_Part"]  = agg["Ventas_Netas"] / total_vn if total_vn else 0
        agg = agg.sort_values("Ventas_Netas", ascending=False)

        # Fila total
        tot_row = {
            CANAL_COL: "TOTAL",
            "Ventas_Netas": agg["Ventas_Netas"].sum(),
            "Costo": agg["Costo"].sum(),
            "Rentabilidad": agg["Rentabilidad"].sum(),
            "Unidades": agg["Unidades"].sum(),
            "%_Rent": agg["Rentabilidad"].sum() / agg["Ventas_Netas"].sum() if agg["Ventas_Netas"].sum() else 0,
            "%_Part": 1.0,
        }
        if DSCTO_COL:
            tot_row["Dscto_Prom_Pct"] = agg["Dscto_Prom_Pct"].mean()
        tabla = pd.concat([agg, pd.DataFrame([tot_row])], ignore_index=True)

        rename = {
            CANAL_COL: "Canal",
            "Ventas_Netas": "Ventas ($)",
            "Costo": "Costo ($)",
            "Rentabilidad": "Rentabilidad ($)",
            "Unidades": "Unidades",
            "%_Rent": "% Margen",
            "%_Part": "% Part.",
        }
        fmt = {
            "Ventas ($)": "{:,.0f}", "Costo ($)": "{:,.0f}",
            "Rentabilidad ($)": "{:,.0f}", "Unidades": "{:,.0f}",
            "% Margen": "{:.2%}", "% Part.": "{:.2%}",
        }
        if DSCTO_COL:
            rename["Dscto_Prom_Pct"] = "% Dscto. Prom."
            fmt["% Dscto. Prom."] = "{:.2f}%"

        display = tabla.rename(columns=rename)

        def style_total(row):
            if row["Canal"] == "TOTAL":
                return ["background-color:#1e3a5f;color:white;font-weight:bold"] * len(row)
            return [""] * len(row)

        st.subheader("📋 Tabla por Canal")
        col_cfg = {
            "% Margen":      st.column_config.NumberColumn("% Margen",      help="(Ventas - Costo) / Ventas × 100"),
            "% Part.":       st.column_config.NumberColumn("% Part.",       help="Participación porcentual sobre el total del período"),
        }
        if DSCTO_COL:
            col_cfg["% Dscto. Prom."] = st.column_config.NumberColumn("% Dscto. Prom.", help="Porcentaje de descuento promedio aplicado")
        st.dataframe(
            display.style
                   .format(fmt)
                   .apply(style_total, axis=1)
                   .map(semaforo, subset=["% Margen"]),
            column_config=col_cfg,
            use_container_width=True, hide_index=True
        )

        # Gráficas
        datos_g = tabla[tabla[CANAL_COL] != "TOTAL"].sort_values("Ventas_Netas")
        n_canales = len(datos_g)
        alto = max(350, n_canales * 65)

        if n_canales > 1:
            # ── Vista multi-canal: barras ventas + línea % margen ──────────
            st.subheader("💰 Ventas y % Margen por Canal de Ventas")
            st.caption("Barras = Ventas Netas  •  Línea = % Margen  •  🟢 ≥35%  🟡 20-35%  🔴 <20%")

            colores_bar = [
                "#ef4444" if v < 0.20 else "#f59e0b" if v < 0.35 else "#22c55e"
                for v in datos_g["%_Rent"]
            ]
            fig_combo = go.Figure()
            fig_combo.add_trace(go.Bar(
                x=datos_g[CANAL_COL],
                y=datos_g["Ventas_Netas"],
                name="Ventas Netas ($)",
                marker_color="#3b82f6",
                text=[f"${v/1e6:.1f}M" if v >= 1e6 else f"${v:,.0f}"
                      for v in datos_g["Ventas_Netas"]],
                textposition="outside",
                yaxis="y1",
            ))
            fig_combo.add_trace(go.Scatter(
                x=datos_g[CANAL_COL],
                y=datos_g["%_Rent"] * 100,
                name="% Margen",
                mode="lines+markers+text",
                line=dict(color="#f59e0b", width=2),
                marker=dict(color=colores_bar, size=12, line=dict(color="white", width=1)),
                text=[f"{v*100:.1f}%" for v in datos_g["%_Rent"]],
                textposition="top center",
                textfont=dict(size=11, color="#1e293b"),
                yaxis="y2",
            ))
            fig_combo.add_hline(y=20, line_dash="dot", line_color="#ef4444",
                                annotation_text="Mínimo 20%",
                                annotation_position="bottom right",
                                yref="y2", annotation_font=dict(size=10, color="#ef4444"))
            fig_combo.add_hline(y=35, line_dash="dot", line_color="#22c55e",
                                annotation_text="Meta 35%",
                                annotation_position="top right",
                                yref="y2", annotation_font=dict(size=10, color="#22c55e"))
            fig_combo.update_layout(
                plot_bgcolor="white", height=alto,
                margin=dict(l=10, r=10, t=40, b=60),
                yaxis=dict(title="Ventas Netas ($)", showgrid=True, gridcolor="#e2e8f0"),
                yaxis2=dict(title="% Margen", overlaying="y", side="right",
                            ticksuffix="%", range=[0, max(datos_g["%_Rent"]*100)*1.4]),
                legend=dict(orientation="h", y=-0.15),
                bargap=0.3,
            )
            st.plotly_chart(fig_combo, use_container_width=True)

        else:
            # ── Vista un solo canal: familia + tendencia ───────────────────
            canal_nombre = datos_g[CANAL_COL].iloc[0] if not datos_g.empty else "seleccionado"
            st.info(f"📌 Mostrando detalle del canal **{canal_nombre}**")

            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("🧪 Ventas por Familia de Producto")
                if "Familia" in df.columns:
                    df_c1 = df[df[CANAL_COL] == canal_nombre] if canal_sel else df
                    fam = (df_c1.groupby("Familia")["Valor_Neto"]
                                .sum().reset_index()
                                .sort_values("Valor_Neto", ascending=True)
                                .tail(10))
                    fig_fam = px.bar(
                        fam, x="Valor_Neto", y="Familia", orientation="h",
                        text_auto=".3s",
                        color="Valor_Neto",
                        color_continuous_scale=[[0,"#93c5fd"],[1,"#1d4ed8"]],
                        labels={"Valor_Neto": "Ventas ($)", "Familia": ""},
                    )
                    fig_fam.update_layout(coloraxis_showscale=False,
                                         plot_bgcolor="white", height=350)
                    st.plotly_chart(fig_fam, use_container_width=True)

            with col_b:
                st.subheader("📈 Evolución de Ventas")
                if "Fecha" in df.columns:
                    df_c2 = df[df[CANAL_COL] == canal_nombre] if canal_sel else df
                    serie = (df_c2.groupby(df_c2["Fecha"].dt.date)["Valor_Neto"]
                                  .sum().reset_index())
                    serie.columns = ["Fecha", "Ventas"]
                    fig_line = px.line(
                        serie, x="Fecha", y="Ventas",
                        labels={"Ventas": "Ventas Netas ($)", "Fecha": ""},
                        markers=True,
                    )
                    fig_line.update_layout(plot_bgcolor="white", height=350)
                    st.plotly_chart(fig_line, use_container_width=True)

        # Descuento vs Margen scatter
        if DSCTO_COL and "Dscto_Prom_Pct" in datos_g.columns:
            st.subheader("💸 Descuento promedio vs % Margen")
            fig3 = px.scatter(
                datos_g, x="Dscto_Prom_Pct", y="%_Rent",
                size="Ventas_Netas", color=CANAL_COL, text=CANAL_COL,
                labels={"Dscto_Prom_Pct": "% Descuento Promedio",
                        "%_Rent": "% Margen", CANAL_COL: "Canal"},
                title="Cada burbuja = un canal  •  tamaño = ventas",
            )
            fig3.update_traces(textposition="top center")
            fig3.update_layout(plot_bgcolor="white", yaxis=dict(tickformat=".0%"))
            st.plotly_chart(fig3, use_container_width=True)

        st.download_button(
            "📥 Descargar CSV",
            data=display.to_csv(index=False, encoding="utf-8-sig"),
            file_name="canal_ventas.csv", mime="text/csv"
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 – TENDENCIA TEMPORAL
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    if not CANAL_COL or "Fecha" not in df.columns:
        st.info("Se requieren columnas de Canal y Fecha.")
    else:
        st.subheader("📈 Evolución de ventas por canal")
        granularidad = st.radio("Agrupar por", ["Día", "Semana"], horizontal=True)

        df_t = df.copy()
        if granularidad == "Semana":
            df_t["_periodo"] = df_t["Fecha"].dt.to_period("W").dt.start_time
        else:
            df_t["_periodo"] = df_t["Fecha"].dt.date

        serie = df_t.groupby([CANAL_COL, "_periodo"])["Valor_Neto"].sum().reset_index()
        serie.columns = ["Canal", "Periodo", "Ventas"]

        fig_line = px.line(
            serie, x="Periodo", y="Ventas", color="Canal",
            labels={"Ventas": "Ventas Netas ($)", "Periodo": ""},
            markers=True,
        )
        fig_line.update_layout(plot_bgcolor="white", height=420,
                               legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_line, use_container_width=True)

        # Participación % — barras apiladas al 100% (solo períodos con ventas positivas)
        st.subheader("📊 Participación % por canal de ventas")
        st.caption(
            "Muestra qué porcentaje del total de ventas aportó cada canal en cada período. "
            "Las barras siempre suman 100%. "
            "Se excluyen períodos con devoluciones netas (ventas totales ≤ 0) para evitar distorsiones."
        )
        pivot_t = serie.pivot_table(index="Periodo", columns="Canal",
                                    values="Ventas", aggfunc="sum").fillna(0)
        # Excluir filas donde el total es <= 0 (devoluciones/notas crédito distorsionan %)
        pivot_t = pivot_t[pivot_t.sum(axis=1) > 0]
        # Clampear negativos a 0 antes de calcular participación
        pivot_pos = pivot_t.clip(lower=0)
        pivot_pct = pivot_pos.div(pivot_pos.sum(axis=1), axis=0) * 100
        pivot_pct = pivot_pct.reset_index()
        pivot_melted = pivot_pct.melt(id_vars="Periodo", var_name="Canal de Ventas", value_name="% Participación")

        fig_bar100 = px.bar(
            pivot_melted, x="Periodo", y="% Participación", color="Canal de Ventas",
            barmode="stack",
            labels={"% Participación": "% Participación", "Periodo": ""},
            text_auto=".0f",
        )
        fig_bar100.update_traces(texttemplate="%{y:.0f}%", textposition="inside",
                                 textfont_size=10, insidetextanchor="middle")
        fig_bar100.update_layout(
            plot_bgcolor="white", height=420,
            yaxis=dict(ticksuffix="%", range=[0, 100]),
            legend=dict(orientation="h", y=-0.2),
            uniformtext_minsize=8, uniformtext_mode="hide",
        )
        st.plotly_chart(fig_bar100, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 – TOP PRODUCTOS POR CANAL
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if not CANAL_COL or not ITEM_COL:
        st.info("Se requieren columnas de Canal e Ítem.")
    else:
        st.subheader("🏆 Top productos dentro de cada canal")
        canales_disp = sorted(df[CANAL_COL].dropna().unique().tolist())
        canal_tab3 = st.selectbox("Selecciona el canal a analizar", canales_disp, key="t3")

        df_c = df[df[CANAL_COL] == canal_tab3]
        top_items = (
            df_c.groupby(ITEM_COL)
            .agg(
                Ventas=("Valor_Neto", "sum"),
                Unidades=("Cantidad", "sum"),
                Margen=("Valor_Rentabilidad", "sum"),
            )
            .reset_index()
            .nlargest(20, "Ventas")
        )
        top_items["%_Margen"] = top_items["Margen"] / top_items["Ventas"].replace(0, 1)

        st.caption("Color de las barras = % Margen  •  🟢 alto  🟡 medio  🔴 bajo")
        fig_top = px.bar(
            top_items.sort_values("Ventas"), x="Ventas", y=ITEM_COL,
            orientation="h", color="%_Margen",
            color_continuous_scale="RdYlGn",
            text_auto=".3s",
            labels={"Ventas": "Ventas ($)", ITEM_COL: "", "%_Margen": "% Margen"},
            title=f"Top 20 productos — {canal_tab3}",
        )
        fig_top.update_layout(plot_bgcolor="white", height=560,
                              margin=dict(l=10, r=10, t=40, b=20))
        st.plotly_chart(fig_top, use_container_width=True)

        st.markdown("#### Detalle")
        st.caption("🟢 Margen ≥ 35%  •  🟡 20–35%  •  🔴 < 20%")
        tabla_top = top_items.sort_values("Ventas", ascending=False)[[ITEM_COL, "Ventas", "Unidades", "Margen", "%_Margen"]].rename(columns={
            ITEM_COL:   "Producto",
            "Ventas":   "Ventas ($)",
            "Unidades": "Unidades",
            "Margen":   "Margen ($)",
            "%_Margen": "% Margen",
        })
        def color_margen(row):
            v = row["% Margen"]
            if not isinstance(v, (int, float)): return [""] * len(row)
            color = "#dcfce7" if v >= 0.35 else "#fef9c3" if v >= 0.20 else "#fee2e2"
            return [""] * (len(row) - 1) + [f"background-color:{color}"]

        st.dataframe(
            tabla_top.style
                .apply(color_margen, axis=1)
                .format({
                    "Ventas ($)":  "{:,.0f}",
                    "Unidades":    "{:,.0f}",
                    "Margen ($)":  "{:,.0f}",
                    "% Margen":    "{:.1%}",
                }),
            column_config={
                "% Margen": st.column_config.ProgressColumn(
                    "% Margen", min_value=0, max_value=1, format="%.1f%%",
                    help="(Ventas - Costo) / Ventas × 100"
                ),
                "Ventas ($)":  st.column_config.NumberColumn("Ventas ($)",  help="Ventas netas del producto en el canal"),
                "Margen ($)":  st.column_config.NumberColumn("Margen ($)",  help="Rentabilidad = Ventas - Costo"),
            },
            use_container_width=True, hide_index=True,
        )
