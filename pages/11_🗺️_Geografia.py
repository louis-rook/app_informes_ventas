"""
pages/11_🗺️_Geografia.py
Cobertura geográfica:
  • Ventas y margen por Zona
  • Desempeño por Ruta de ventas
  • Top ciudades (cuando hay datos)
  • Mapa de calor zona × canal
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones

st.set_page_config(page_title="Geografía", page_icon="🗺️", layout="wide")

df_all = cargar_data()
if df_all.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

def get_col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

ZONA_COL   = get_col(df_all, "Zona",            "ZONAS")
RUTA_COL   = get_col(df_all, "Ruta",            "RUTAS DE VENTAS")
CIUDAD_COL = get_col(df_all, "Ciudad",          "Desc. ciudad")
CANAL_COL  = get_col(df_all, "Canal",           "CANAL DE VENTAS")
CLI_COL    = get_col(df_all, "Nombre_Cliente",  "Razon social cliente factura")
ITEM_COL   = get_col(df_all, "Nombre_Item",     "Desc. item")
VEND_COL   = get_col(df_all, "Nombre_Vendedor", "Nombre vendedor")

if not ZONA_COL:
    st.error("❌ Columna de zona no encontrada.")
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

    zonas = ["Todas"] + sorted(df_all[ZONA_COL].dropna().unique().tolist())
    zona_sel = st.selectbox("Zona", zonas)

    if CANAL_COL:
        canales = ["Todos"] + sorted(df_all[CANAL_COL].dropna().unique().tolist())
        canal_sel = st.selectbox("Canal", canales)
    else:
        canal_sel = "Todos"

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if zona_sel != "Todas":
    df = df[df[ZONA_COL] == zona_sel]
if canal_sel != "Todos" and CANAL_COL:
    df = df[df[CANAL_COL] == canal_sel]

st.title("🗺️ Cobertura Geográfica")
st.caption(f"Zona: **{zona_sel}**  •  Canal: **{canal_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────
venta    = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
rent     = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
n_zonas  = df[ZONA_COL].nunique()
n_rutas  = df[RUTA_COL].nunique()  if RUTA_COL  else 0
n_cities = df[CIUDAD_COL].dropna().nunique() if CIUDAD_COL else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Ventas Netas",  formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k2.metric("📈 Margen global", f"{rent/venta*100:.1f}%" if venta else "—",
          help="(Ventas - Costo) / Ventas × 100")
k3.metric("🗺️ Zonas",         f"{n_zonas:,}",
          help="Número de zonas geográficas con ventas en el período")
k4.metric("🚛 Rutas",          f"{n_rutas:,}",
          help="Número de rutas de ventas activas en el período")
k5.metric("🏙️ Ciudades",       f"{n_cities:,}" if n_cities else "N/D",
          help="Número de ciudades con ventas registradas en el período")

st.divider()

tab1, tab2, tab3 = st.tabs(["🗺️ Por Zona", "🚛 Por Ruta", "🏙️ Por Ciudad"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 – POR ZONA
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    agg_z = df.groupby(ZONA_COL).agg(
        Ventas=("Valor_Neto", "sum"),
        Costo=("Costo_Total", "sum"),
        Rentabilidad=("Valor_Rentabilidad", "sum"),
        Unidades=("Cantidad", "sum"),
        Clientes=(CLI_COL, "nunique") if CLI_COL else ("Cantidad", "count"),
    ).reset_index()
    total_vn = agg_z["Ventas"].sum()
    agg_z["%_Mg"]   = agg_z["Rentabilidad"] / agg_z["Ventas"].replace(0, 1)
    agg_z["%_Part"] = agg_z["Ventas"] / total_vn if total_vn else 0
    agg_z[ZONA_COL] = agg_z[ZONA_COL].astype(str).str.strip()
    agg_z = agg_z.sort_values("Ventas", ascending=False)

    col_g, col_pie = st.columns([3, 2])

    with col_g:
        st.subheader("💰 Ventas por Zona")
        fig_z = px.bar(
            agg_z, x=ZONA_COL, y="Ventas",
            color="%_Mg", color_continuous_scale="RdYlGn",
            text_auto=".3s",
            labels={"Ventas": "$", ZONA_COL: "", "%_Mg": "% Margen"},
        )
        fig_z.update_layout(
            plot_bgcolor="white", height=380,
            coloraxis_colorbar=dict(tickformat=".0%", title="% Mg"),
        )
        st.plotly_chart(fig_z, use_container_width=True)

    with col_pie:
        st.subheader("🥧 Participación por Zona")
        fig_pie_z = px.pie(
            agg_z, values="Ventas", names=ZONA_COL,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pie_z.update_layout(height=380)
        st.plotly_chart(fig_pie_z, use_container_width=True)

    # Tabla
    st.subheader("📋 Detalle por Zona")
    st.dataframe(
        agg_z.rename(columns={
            ZONA_COL: "Zona", "Ventas": "Ventas ($)", "Costo": "Costo ($)",
            "Rentabilidad": "Rentabilidad ($)", "Clientes": "Clientes",
            "%_Mg": "% Margen", "%_Part": "% Part.",
        }).style.format({
            "Ventas ($)": "{:,.0f}", "Costo ($)": "{:,.0f}",
            "Rentabilidad ($)": "{:,.0f}", "Unidades": "{:,.0f}",
            "Clientes": "{:,.0f}", "% Margen": "{:.2%}", "% Part.": "{:.2%}",
        }),
        column_config={
            "% Margen":        st.column_config.NumberColumn("% Margen",        help="(Ventas - Costo) / Ventas × 100"),
            "% Part.":         st.column_config.NumberColumn("% Part.",         help="Participación porcentual sobre el total del período"),
            "Rentabilidad ($)": st.column_config.NumberColumn("Rentabilidad ($)", help="Ventas Netas menos Costo Total en pesos"),
        },
        use_container_width=True, hide_index=True
    )

    # Mapa de calor zona × canal
    if CANAL_COL:
        st.subheader("🔥 Mapa de calor — Ventas Zona × Canal")
        pivot_zc = df.groupby([ZONA_COL, CANAL_COL])["Valor_Neto"].sum().reset_index()
        pivot_zc[ZONA_COL]  = pivot_zc[ZONA_COL].astype(str).str.strip()
        pivot_zc[CANAL_COL] = pivot_zc[CANAL_COL].astype(str).str.strip()
        pivot_wide = pivot_zc.pivot_table(
            index=ZONA_COL, columns=CANAL_COL,
            values="Valor_Neto", aggfunc="sum"
        ).fillna(0)

        fig_heat = px.imshow(
            pivot_wide / 1_000_000,  # en millones
            color_continuous_scale="Blues", aspect="auto", text_auto=".1f",
            labels=dict(x="Canal", y="Zona", color="Millones ($)"),
        )
        fig_heat.update_layout(
            height=max(300, len(pivot_wide) * 55),
            margin=dict(l=10, r=10, t=30, b=60),
            coloraxis_colorbar=dict(title="Millones ($)"),
            xaxis=dict(tickangle=-30),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("Valores en millones de pesos")

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 – POR RUTA
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    if not RUTA_COL:
        st.info("Columna de ruta no encontrada.")
    else:
        agg_r = df.groupby(RUTA_COL).agg(
            Ventas=("Valor_Neto", "sum"),
            Costo=("Costo_Total", "sum"),
            Rentabilidad=("Valor_Rentabilidad", "sum"),
            Unidades=("Cantidad", "sum"),
            Clientes=(CLI_COL, "nunique") if CLI_COL else ("Cantidad", "count"),
        ).reset_index()
        total_vn_r = agg_r["Ventas"].sum()
        agg_r["%_Mg"]   = agg_r["Rentabilidad"] / agg_r["Ventas"].replace(0, 1)
        agg_r["%_Part"] = agg_r["Ventas"] / total_vn_r if total_vn_r else 0
        agg_r[RUTA_COL] = agg_r[RUTA_COL].astype(str).str.strip()
        agg_r = agg_r.sort_values("Ventas", ascending=False)

        st.subheader("🚛 Desempeño por Ruta")
        fig_ruta = px.bar(
            agg_r.sort_values("Ventas"), x="Ventas", y=RUTA_COL,
            orientation="h", color="%_Mg",
            color_continuous_scale="RdYlGn", text_auto=".3s",
            labels={"Ventas": "$", RUTA_COL: "", "%_Mg": "% Margen"},
        )
        fig_ruta.update_layout(
            plot_bgcolor="white", height=max(400, len(agg_r) * 38),
            coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"),
        )
        st.plotly_chart(fig_ruta, use_container_width=True)

        st.subheader("📋 Tabla por Ruta")
        st.dataframe(
            agg_r.rename(columns={
                RUTA_COL: "Ruta", "Ventas": "Ventas ($)",
                "Rentabilidad": "Rentabilidad ($)", "Clientes": "Clientes",
                "%_Mg": "% Margen", "%_Part": "% Part.",
            }).style.format({
                "Ventas ($)": "{:,.0f}", "Rentabilidad ($)": "{:,.0f}",
                "Unidades": "{:,.0f}", "Clientes": "{:,.0f}",
                "% Margen": "{:.2%}", "% Part.": "{:.2%}",
            }),
            column_config={
                "% Margen": st.column_config.NumberColumn("% Margen", help="(Ventas - Costo) / Ventas × 100"),
                "% Part.":  st.column_config.NumberColumn("% Part.",  help="Participación porcentual sobre el total del período"),
            },
            use_container_width=True, hide_index=True
        )

        # Detalle de ruta seleccionada
        st.divider()
        st.subheader("🔍 Zoom en una ruta")
        ruta_sel = st.selectbox("Selecciona ruta", agg_r[RUTA_COL].tolist())
        df_r = df[df[RUTA_COL].astype(str).str.strip() == ruta_sel]

        if not df_r.empty:
            r1, r2, r3 = st.columns(3)
            r1.metric("💰 Ventas",   formatear_millones(df_r["Valor_Neto"].sum()),
                      help="Suma del valor neto facturado en el período (sin IVA)")
            r2.metric("👥 Clientes", str(df_r[CLI_COL].nunique()) if CLI_COL else "—",
                      help="Número de clientes distintos atendidos en esta ruta")
            r3.metric("📈 Margen",
                      f"{df_r['Valor_Rentabilidad'].sum()/df_r['Valor_Neto'].sum()*100:.1f}%"
                      if df_r["Valor_Neto"].sum() else "—",
                      help="(Ventas - Costo) / Ventas × 100")

            if ITEM_COL:
                top_r = (
                    df_r.groupby(ITEM_COL)["Valor_Neto"].sum()
                    .nlargest(10).reset_index()
                )
                top_r.columns = ["Producto", "Ventas ($)"]
                col_ra, col_rb = st.columns(2)
                with col_ra:
                    fig_rp = px.bar(
                        top_r.sort_values("Ventas ($)"), x="Ventas ($)", y="Producto",
                        orientation="h", text_auto=".3s", color="Ventas ($)",
                        color_continuous_scale=[[0,"#bfdbfe"],[1,"#1d4ed8"]],
                        title=f"Top 10 productos — {ruta_sel}",
                    )
                    fig_rp.update_layout(plot_bgcolor="white",
                                         coloraxis_showscale=False, height=350)
                    st.plotly_chart(fig_rp, use_container_width=True)
                with col_rb:
                    fig_rp2 = px.pie(
                        top_r, values="Ventas ($)", names="Producto",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                    )
                    fig_rp2.update_layout(height=350)
                    st.plotly_chart(fig_rp2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 – POR CIUDAD
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if not CIUDAD_COL:
        st.info("Columna de ciudad no encontrada.")
    else:
        df_c = df.dropna(subset=[CIUDAD_COL]).copy()
        df_c[CIUDAD_COL] = df_c[CIUDAD_COL].astype(str).str.strip()
        total_con_ciudad = len(df_c)
        total_sin_ciudad = len(df) - total_con_ciudad

        if total_sin_ciudad > 0:
            st.caption(
                f"⚠️ {total_sin_ciudad:,} registros ({total_sin_ciudad/len(df)*100:.1f}%) "
                f"no tienen ciudad asignada y se excluyen de esta vista."
            )

        if df_c.empty:
            st.info("No hay datos de ciudad disponibles.")
        else:
            top_n_c = st.slider("Top N ciudades", 10, 30, 20, key="top_c")
            agg_c = df_c.groupby(CIUDAD_COL).agg(
                Ventas=("Valor_Neto", "sum"),
                Rentabilidad=("Valor_Rentabilidad", "sum"),
                Unidades=("Cantidad", "sum"),
                Clientes=(CLI_COL, "nunique") if CLI_COL else ("Cantidad","count"),
            ).reset_index()
            total_vn_c = agg_c["Ventas"].sum()
            agg_c["%_Mg"]   = agg_c["Rentabilidad"] / agg_c["Ventas"].replace(0, 1)
            agg_c["%_Part"] = agg_c["Ventas"] / total_vn_c if total_vn_c else 0
            top_c = agg_c.nlargest(top_n_c, "Ventas")

            st.subheader(f"🏙️ Top {top_n_c} ciudades por Ventas")
            fig_city = px.bar(
                top_c.sort_values("Ventas"), x="Ventas", y=CIUDAD_COL,
                orientation="h", color="%_Mg",
                color_continuous_scale="RdYlGn", text_auto=".3s",
                labels={"Ventas": "$", CIUDAD_COL: "", "%_Mg": "% Margen"},
            )
            fig_city.update_layout(
                plot_bgcolor="white", height=max(400, top_n_c * 30),
                coloraxis_colorbar=dict(tickformat=".0%", title="% Margen"),
            )
            st.plotly_chart(fig_city, use_container_width=True)

            # Zona × Ciudad (si hay zona)
            if ZONA_COL and zona_sel == "Todas":
                st.subheader("🗺️ Distribución de ciudades por zona")
                zona_city = (
                    df_c.groupby([ZONA_COL, CIUDAD_COL])["Valor_Neto"].sum()
                    .reset_index().nlargest(40, "Valor_Neto")
                )
                zona_city[ZONA_COL]   = zona_city[ZONA_COL].astype(str).str.strip()
                zona_city[CIUDAD_COL] = zona_city[CIUDAD_COL].astype(str).str.strip()
                fig_tree_geo = px.treemap(
                    zona_city,
                    path=[ZONA_COL, CIUDAD_COL],
                    values="Valor_Neto",
                    color="Valor_Neto",
                    color_continuous_scale="Blues",
                    labels={"Valor_Neto": "Ventas ($)"},
                )
                fig_tree_geo.update_layout(height=450)
                st.plotly_chart(fig_tree_geo, use_container_width=True)

            st.download_button(
                "📥 Descargar ciudades CSV",
                data=agg_c.rename(columns={CIUDAD_COL:"Ciudad"})
                           .to_csv(index=False, encoding="utf-8-sig"),
                file_name="ciudades_ventas.csv", mime="text/csv"
            )
