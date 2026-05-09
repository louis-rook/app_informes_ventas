"""
pages/5_🥛_Volumenes.py
Análisis de volúmenes de producción:
  • Sueros → Litros por canal y por día
  • Leches → Litros por canal, tipo de leche y por día
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data
from utils.params import (TIPO_LECHE, MOTIVOS_OBSEQUIO,
                          FAMILIAS_SUERO, FAMILIAS_LECHE, FAMILIA_MAQUILA,
                          CANALES_DYV, CANALES_PAE, CANALES_SMK_TD,
                          ML_POR_REFERENCIA_SUERO)

st.set_page_config(page_title="Volúmenes", page_icon="🥛", layout="wide")

df_all = cargar_data()
if df_all.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

# ── Clasificar Tipo_Motivo ─────────────────────────────────────────────────
def clasificar_motivo(m):
    m_up = str(m).strip().upper()
    if any(k.upper() in m_up for k in MOTIVOS_OBSEQUIO):
        return "OBSEQUIO"
    return "VENTA"

if "Motivo" in df_all.columns:
    df_all["Tipo_Motivo"] = df_all["Motivo"].apply(clasificar_motivo)
else:
    df_all["Tipo_Motivo"] = "VENTA"

# Enriquecer con Tipo_Leche
if "Referencia" in df_all.columns:
    df_all["Tipo_Leche"] = df_all["Referencia"].astype(str).str.strip().map(TIPO_LECHE).fillna("N.R")

# ── Helpers ────────────────────────────────────────────────────────────────
CANAL_COL = "Canal" if "Canal" in df_all.columns else "Clase_Cliente"

def dias_periodo(df):
    if "Fecha" not in df.columns or df["Fecha"].isna().all():
        return 1
    return max(1, (df["Fecha"].max() - df["Fecha"].min()).days + 1)

def fmt_lit(v):
    if pd.isna(v): return "—"
    if abs(v) >= 1_000_000: return f"{v/1_000_000:,.2f}M"
    return f"{v:,.1f}"

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filtros")

    if "Fecha" in df_all.columns and df_all["Fecha"].notna().any():
        fmin = df_all["Fecha"].min().date()
        fmax = df_all["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", value=(fmin, fmax),
                              min_value=fmin, max_value=fmax)
    else:
        rango = None

    tipo_motivo = st.selectbox("TIPO_MOTIVO", ["VENTA", "Todos", "OBSEQUIO"])

    if CANAL_COL in df_all.columns:
        canales = ["Todos"] + sorted(df_all[CANAL_COL].dropna().unique().tolist())
        canal_sel = st.selectbox("Canal de Ventas", canales)
    else:
        canal_sel = "Todos"

# ── Filtrar ────────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if tipo_motivo != "Todos":
    df = df[df["Tipo_Motivo"] == tipo_motivo]
if canal_sel != "Todos" and CANAL_COL in df.columns:
    df = df[df[CANAL_COL] == canal_sel]

DIAS = dias_periodo(df)

# ── Título ─────────────────────────────────────────────────────────────────
st.title("🥛 Volúmenes de Producción")
st.caption(f"Motivo: **{tipo_motivo}**  •  Canal de Ventas: **{canal_sel}**  •  Días del período: **{DIAS}**")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════
tab_sueros, tab_leches = st.tabs(["🧴 Sueros (Litros)", "🥛 Leches (Litros)"])

# ══════════════════════════════════════════════════════════════════════════
# TAB SUEROS
# ══════════════════════════════════════════════════════════════════════════
with tab_sueros:

    df_s = df[df["Familia"].isin(FAMILIAS_SUERO)] if "Familia" in df.columns else pd.DataFrame()

    # El sistema no registra litros para sueros: se calculan desde Cantidad × ml/unidad
    if not df_s.empty and "Referencia" in df_s.columns:
        df_s = df_s.copy()
        ref = df_s["Referencia"].astype(str).str.strip()
        um  = df_s["UM"].astype(str).str.strip() if "UM" in df_s.columns else pd.Series("UND", index=df_s.index)
        ml_unit = ref.map(ML_POR_REFERENCIA_SUERO).fillna(0)
        df_s["Litros"] = (
            (df_s["Cantidad"] * ml_unit / 1000).where(um != "KG", 0) +
            df_s["Cantidad"].where(um == "KG", 0)
        )

    if df_s.empty:
        st.info("No hay datos de Sueros para los filtros actuales.")
    else:
        # KPIs sueros
        lit_total_s = df_s["Litros"].sum() if "Litros" in df_s.columns else 0
        cant_total  = df_s["Cantidad"].sum() if "Cantidad" in df_s.columns else 0
        lit_dia_s   = lit_total_s / DIAS

        k1, k2, k3 = st.columns(3)
        k1.metric("📦 Unidades totales",  f"{cant_total:,.0f}",
                  help="Número total de unidades vendidas")
        k2.metric("🧴 Litros totales",    f"{lit_total_s:,.1f} L",
                  help="Volumen total de sueros en litros del período")
        k3.metric("📅 Litros por día",    f"{lit_dia_s:,.1f} L/día",
                  help="Promedio de litros vendidos por día del período")

        st.divider()
        st.caption("Analiza el volumen despachado de **sueros** en litros. Los litros se calculan a partir de las unidades vendidas multiplicadas por el volumen por unidad de cada referencia (no viene directamente del ERP).")

        for familia in FAMILIAS_SUERO:
            df_fam = df_s[df_s["Familia"] == familia] if "Familia" in df_s.columns else df_s
            if df_fam.empty:
                continue

            lit_fam = df_fam["Litros"].sum() if "Litros" in df_fam.columns else 0
            st.subheader(f"🧴 {familia}  —  {lit_fam:,.1f} L")

            # ── Tabla por canal ──────────────────────────────────────────
            st.markdown("**Por Canal de Ventas**")
            if CANAL_COL in df_fam.columns:
                agg = df_fam.groupby(CANAL_COL).agg(
                    Cantidad =("Cantidad", "sum"),
                    Litros   =("Litros",   "sum"),
                ).reset_index()
                agg["%_Part"]  = agg["Litros"] / lit_fam * 100 if lit_fam else 0
                agg["L_x_Dia"] = agg["Litros"] / DIAS
                agg = agg.sort_values("Litros", ascending=False)

                tabla_s_disp = agg[[CANAL_COL,"Cantidad","Litros","%_Part","L_x_Dia"]].rename(columns={
                    CANAL_COL: "Canal de Ventas",
                    "Litros":  "Litros (L)",
                    "%_Part":  "% Part.",
                    "L_x_Dia": "L/Día",
                })
                st.dataframe(
                    tabla_s_disp.style
                        .format({"Cantidad": "{:,.0f}", "Litros (L)": "{:,.1f}", "L/Día": "{:,.1f}"}),
                    column_config={
                        "Canal de Ventas": st.column_config.TextColumn("Canal de Ventas"),
                        "Cantidad":   st.column_config.NumberColumn("Cantidad"),
                        "Litros (L)": st.column_config.NumberColumn("Litros (L)"),
                        "% Part.":    st.column_config.ProgressColumn("% Part.",
                                        min_value=0, max_value=100, format="%.1f%%",
                                        help="Participación porcentual del canal sobre el total de litros"),
                        "L/Día":      st.column_config.NumberColumn("L/Día",
                                        help="Litros promedio despachados por día del período"),
                    },
                    use_container_width=True, hide_index=True,
                )

            # ── Gráfica evolución por canal ──────────────────────────────
            if "Fecha" in df_fam.columns and CANAL_COL in df_fam.columns:
                agrupar_semana = DIAS > 14
                if agrupar_semana:
                    df_fam2 = df_fam.copy()
                    df_fam2["_periodo"] = df_fam2["Fecha"].dt.to_period("W").dt.start_time.dt.strftime("%d-%b")
                    label_eje = "Semana (inicio)"
                else:
                    df_fam2 = df_fam.copy()
                    df_fam2["_periodo"] = df_fam2["Fecha"].dt.strftime("%d-%b")
                    label_eje = "Día"

                serie_c = df_fam2.groupby([CANAL_COL, "_periodo"])["Litros"].sum().reset_index()
                serie_c.columns = ["Canal de Ventas", label_eje, "Litros (L)"]

                n_canales_s = serie_c["Canal de Ventas"].nunique()
                caption_txt = "Por semana (período > 14 días)" if agrupar_semana else "Por día"
                st.markdown(f"**Litros por Canal de Ventas — {caption_txt}**")

                if n_canales_s == 1:
                    fig_heat = px.bar(
                        serie_c, x=label_eje, y="Litros (L)",
                        color="Litros (L)",
                        color_continuous_scale=[[0,"#93c5fd"],[1,"#1d4ed8"]],
                        text_auto=".0f",
                    )
                    fig_heat.update_layout(coloraxis_showscale=False,
                                           plot_bgcolor="white", height=300,
                                           xaxis=dict(tickangle=-45))
                else:
                    fig_heat = px.line(
                        serie_c, x=label_eje, y="Litros (L)",
                        color="Canal de Ventas",
                        markers=True,
                    )
                    fig_heat.update_layout(plot_bgcolor="white", height=350,
                                           xaxis=dict(tickangle=-45),
                                           legend=dict(orientation="h", y=-0.3))
                st.plotly_chart(fig_heat, use_container_width=True)

            st.divider()

# ══════════════════════════════════════════════════════════════════════════
# TAB LECHES
# ══════════════════════════════════════════════════════════════════════════
with tab_leches:

    df_l = df[df["Familia"].isin(FAMILIAS_LECHE)] if "Familia" in df.columns else pd.DataFrame()

    if df_l.empty:
        st.info("No hay datos de Leches para los filtros actuales.")
    else:
        lit_total  = df_l["Litros"].sum()   if "Litros"   in df_l.columns else 0
        cant_total = df_l["Cantidad"].sum() if "Cantidad" in df_l.columns else 0
        lit_dia    = lit_total / DIAS

        k1, k2, k3 = st.columns(3)
        k1.metric("📦 Unidades totales", f"{cant_total:,.0f}",
                  help="Número total de unidades vendidas")
        k2.metric("🥛 Litros totales",   f"{lit_total:,.1f} L",
                  help="Volumen total vendido en litros")
        k3.metric("📅 Litros por día",   f"{lit_dia:,.1f} L/día",
                  help="Promedio de litros vendidos por día del período")

        st.divider()

        # ── Sección 1: Resumen por canal ──────────────────────────────────
        col_canal, col_tipo = st.columns([1, 1])

        with col_canal:
            st.subheader("📋 Por Canal de Ventas")
            st.caption("Distribución de los litros de leche vendidos por cada canal. **L/Día** = promedio de litros despachados por día hábil del período.")
            if CANAL_COL in df_l.columns:
                agg_l = df_l.groupby(CANAL_COL).agg(
                    Cantidad =("Cantidad", "sum"),
                    Litros   =("Litros",   "sum"),
                ).reset_index()
                agg_l["%_Part"]  = agg_l["Litros"] / lit_total * 100 if lit_total else 0
                agg_l["L_x_Dia"] = agg_l["Litros"] / DIAS
                agg_l = agg_l.sort_values("Litros", ascending=False)

                tabla_l = agg_l.rename(columns={
                    CANAL_COL: "Canal de Ventas",
                    "Litros":  "Litros (L)",
                    "%_Part":  "% Part.",
                    "L_x_Dia": "L/Día",
                })
                st.dataframe(
                    tabla_l.style
                        .format({"Cantidad": "{:,.0f}", "Litros (L)": "{:,.1f}", "L/Día": "{:,.1f}"}),
                    column_config={
                        "Canal de Ventas": st.column_config.TextColumn("Canal de Ventas"),
                        "Cantidad":  st.column_config.NumberColumn("Cantidad"),
                        "Litros (L)":st.column_config.NumberColumn("Litros (L)"),
                        "% Part.":   st.column_config.ProgressColumn("% Part.",
                                        min_value=0, max_value=100, format="%.1f%%",
                                        help="Participación porcentual del canal sobre el total de litros"),
                        "L/Día":     st.column_config.NumberColumn("L/Día",
                                        help="Litros promedio despachados por día del período"),
                    },
                    use_container_width=True, hide_index=True,
                )

                # Gráfica de barras horizontal
                fig_canal = px.bar(
                    agg_l.sort_values("Litros"), x="Litros", y=CANAL_COL,
                    orientation="h", text_auto=".3s",
                    color="Litros",
                    color_continuous_scale=[[0,"#93c5fd"],[1,"#1d4ed8"]],
                    labels={"Litros": "Litros (L)", CANAL_COL: ""},
                )
                fig_canal.update_layout(coloraxis_showscale=False,
                                        plot_bgcolor="white", height=260,
                                        margin=dict(t=10, b=10))
                st.plotly_chart(fig_canal, use_container_width=True)

        with col_tipo:
            st.subheader("🔬 Por Tipo de Leche")
            st.caption("Desglose por tipo de leche: Entera, Deslactosada, Semidescremada. La clasificación se hace por referencia de producto. **N.R** = sin clasificar (referencia no mapeada).")
            df_solo_leche = df_l[df_l["Familia"] == "LECHE"] if "Familia" in df_l.columns else df_l

            if "Tipo_Leche" in df_solo_leche.columns:
                agg_t = df_solo_leche.groupby("Tipo_Leche").agg(
                    Cantidad =("Cantidad", "sum"),
                    Litros   =("Litros",   "sum"),
                ).reset_index()
                lit_solo = agg_t["Litros"].sum()
                agg_t["%_Part"]  = agg_t["Litros"] / lit_solo * 100 if lit_solo else 0
                agg_t["L_x_Dia"] = agg_t["Litros"] / DIAS
                agg_t = agg_t.sort_values("Litros", ascending=False)

                tabla_t = agg_t.rename(columns={
                    "Tipo_Leche": "Tipo",
                    "Litros":     "Litros (L)",
                    "%_Part":     "% Part.",
                    "L_x_Dia":    "L/Día",
                })
                st.dataframe(
                    tabla_t.style
                        .format({"Cantidad": "{:,.0f}", "Litros (L)": "{:,.1f}", "L/Día": "{:,.1f}"}),
                    column_config={
                        "Tipo":      st.column_config.TextColumn("Tipo de Leche"),
                        "Cantidad":  st.column_config.NumberColumn("Cantidad"),
                        "Litros (L)":st.column_config.NumberColumn("Litros (L)"),
                        "% Part.":   st.column_config.ProgressColumn("% Part.",
                                        min_value=0, max_value=100, format="%.1f%%",
                                        help="Participación porcentual del tipo sobre el total de litros de leche"),
                        "L/Día":     st.column_config.NumberColumn("L/Día",
                                        help="Litros promedio por día del período"),
                    },
                    use_container_width=True, hide_index=True,
                )

                # Gráfica de torta (excluye N.R)
                datos_pie = agg_t[agg_t["Tipo_Leche"] != "N.R"].copy()
                if not datos_pie.empty:
                    fig_pie = px.pie(
                        datos_pie, values="Litros", names="Tipo_Leche",
                        color_discrete_map={
                            "ENTERA":         "#3b82f6",
                            "DESLACTOSADA":   "#22c55e",
                            "SEMIDESCREMADA": "#f59e0b",
                        }
                    )
                    fig_pie.update_layout(height=260, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.caption("ℹ️ Sin clasificación por tipo disponible (referencias no mapeadas)")

        # ── Sección 2: Calendario diario ──────────────────────────────────
        st.divider()
        st.subheader("📅 Litros por Canal de Ventas y Día")
        st.caption("Solo familia LECHE (excluye Producción para Terceros)")

        if "Fecha" in df_solo_leche.columns and CANAL_COL in df_solo_leche.columns:
            agrupar_semana_l = DIAS > 14
            if agrupar_semana_l:
                df_sl2 = df_solo_leche.copy()
                df_sl2["_periodo"] = df_sl2["Fecha"].dt.to_period("W").dt.start_time.dt.strftime("%d-%b")
                label_l = "Semana"
                st.caption("Agrupado por semana (período > 14 días)")
            else:
                df_sl2 = df_solo_leche.copy()
                df_sl2["_periodo"] = df_sl2["Fecha"].dt.strftime("%d-%b")
                label_l = "Día"

            serie_l = df_sl2.groupby([CANAL_COL, "_periodo"])["Litros"].sum().reset_index()
            serie_l.columns = ["Canal de Ventas", label_l, "Litros (L)"]

            fig_heat_l = px.line(
                serie_l, x=label_l, y="Litros (L)",
                color="Canal de Ventas",
                markers=True,
            )
            fig_heat_l.update_layout(
                plot_bgcolor="white",
                height=max(300, 350),
                xaxis=dict(tickangle=-45),
                legend=dict(orientation="h", y=-0.3),
                margin=dict(t=10, b=80),
            )
            st.plotly_chart(fig_heat_l, use_container_width=True)

        # ── Sección 3: D y V / PAE ────────────────────────────────────────
        st.divider()
        st.subheader("📊 Resumen especial")
        st.caption("**D y V** = Distribuidores y Vendedores (locales + nacionales + otros). **PAE** = Programa de Alimentación Escolar. **SMK + TD** = Supermercados y Tiendas de Descuento. El delta en cada métrica muestra el promedio diario.")

        # D y V = Distribuidores y Vendedores (locales + nacionales + otros)
        if CANAL_COL in df_solo_leche.columns:
            lit_dyv    = df_solo_leche[df_solo_leche[CANAL_COL].isin(CANALES_DYV)]["Litros"].sum() \
                         if "Litros" in df_solo_leche.columns else 0
            lit_pae    = df_solo_leche[df_solo_leche[CANAL_COL].isin(CANALES_PAE)]["Litros"].sum() \
                         if "Litros" in df_solo_leche.columns else 0
            lit_smk_td = df_solo_leche[df_solo_leche[CANAL_COL].isin(CANALES_SMK_TD)]["Litros"].sum() \
                         if "Litros" in df_solo_leche.columns else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🚛 D y V",           f"{lit_dyv:,.1f} L",
                      delta=f"{lit_dyv/DIAS:,.1f} L/día",
                      help="Litros vendidos a Distribuidores y Vendedores (locales + nacionales)")
            c2.metric("🏫 PAE",             f"{lit_pae:,.1f} L",
                      delta=f"{lit_pae/DIAS:,.1f} L/día",
                      help="Litros vendidos al canal PAE (Programa de Alimentación Escolar)")
            c3.metric("🛒 SMK + TD",        f"{lit_smk_td:,.1f} L",
                      delta=f"{lit_smk_td/DIAS:,.1f} L/día",
                      help="Litros vendidos a Supermercados y Tiendas de Descuento")
            c4.metric("🥛 Total Leches",    f"{lit_total:,.1f} L",
                      delta=f"{lit_dia:,.1f} L/día",
                      help="Volumen total vendido en litros")

        # ── Sección 4: Maquila Leche ──────────────────────────────────────
        df_maq_leche = df_l[df_l["Familia"] == FAMILIA_MAQUILA] if "Familia" in df_l.columns else pd.DataFrame()
        if not df_maq_leche.empty:
            st.divider()
            st.subheader("🏭 Producción para Terceros (Maquila)")
            lit_maq = df_maq_leche["Litros"].sum() if "Litros" in df_maq_leche.columns else 0

            m1, m2 = st.columns(2)
            m1.metric("🥛 Litros Maquila", f"{lit_maq:,.1f} L",
                      help="Volumen total de producción para terceros en litros")
            m2.metric("📅 L/Día Maquila",  f"{lit_maq/DIAS:,.1f} L/día",
                      help="Promedio de litros de maquila por día del período")

            if "Fecha" in df_maq_leche.columns and CANAL_COL in df_maq_leche.columns:
                agrupar_maq = DIAS > 14
                df_maq2 = df_maq_leche.copy()
                df_maq2["_periodo"] = (
                    df_maq2["Fecha"].dt.to_period("W").dt.start_time.dt.strftime("%d-%b")
                    if agrupar_maq else
                    df_maq2["Fecha"].dt.strftime("%d-%b")
                )
                label_maq = "Semana" if agrupar_maq else "Día"
                serie_maq = df_maq2.groupby("_periodo")["Litros"].sum().reset_index()
                serie_maq.columns = [label_maq, "Litros (L)"]

                fig_maq = px.bar(
                    serie_maq, x=label_maq, y="Litros (L)",
                    text_auto=".0f",
                    color="Litros (L)",
                    color_continuous_scale=[[0,"#86efac"],[1,"#15803d"]],
                )
                fig_maq.update_layout(
                    coloraxis_showscale=False, plot_bgcolor="white",
                    height=250, margin=dict(t=10, b=60),
                    xaxis=dict(tickangle=-45),
                )
                st.plotly_chart(fig_maq, use_container_width=True)
