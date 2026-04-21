"""
pages/5_🥛_Volumenes.py
Análisis de volúmenes de producción:
  • Sueros → Toneladas por canal y por día
  • Leches → Litros por canal, tipo de leche y por día
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data
from utils.params import TIPO_LECHE, MOTIVOS_OBSEQUIO

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

def fmt_ton(v):
    if pd.isna(v): return "—"
    return f"{v:,.2f}"

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
        canal_sel = st.selectbox("Canal", canales)
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
st.caption(f"Motivo: **{tipo_motivo}**  •  Canal: **{canal_sel}**  •  Días del período: **{DIAS}**")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════
tab_sueros, tab_leches = st.tabs(["🧴 Sueros (Toneladas)", "🥛 Leches (Litros)"])

# ══════════════════════════════════════════════════════════════════════════
# TAB SUEROS
# ══════════════════════════════════════════════════════════════════════════
with tab_sueros:

    FAMILIAS_SUERO = ["Sueros", "Maquila Suero"]
    df_s = df[df["Familia"].isin(FAMILIAS_SUERO)] if "Familia" in df.columns else pd.DataFrame()

    if df_s.empty:
        st.info("No hay datos de Sueros para los filtros actuales.")
    else:
        # KPIs sueros
        ton_total  = df_s["Litros"].sum() / 1000 if "Litros" in df_s.columns else 0
        cant_total = df_s["Cantidad"].sum()       if "Cantidad" in df_s.columns else 0
        ton_dia    = ton_total / DIAS

        k1, k2, k3 = st.columns(3)
        k1.metric("📦 Unidades totales",   f"{cant_total:,.0f}")
        k2.metric("⚖️ Toneladas totales",  f"{ton_total:,.2f} T")
        k3.metric("📅 Toneladas por día",  f"{ton_dia:,.2f} T/día")

        st.divider()

        for familia in FAMILIAS_SUERO:
            df_fam = df_s[df_s["Familia"] == familia] if "Familia" in df_s.columns else df_s
            if df_fam.empty:
                continue

            ton_fam = df_fam["Litros"].sum() / 1000 if "Litros" in df_fam.columns else 0
            st.subheader(f"🧴 {familia}  —  {ton_fam:,.2f} T")

            col_tabla, col_cal = st.columns([1, 2])

            # ── Tabla por canal ──────────────────────────────────────────
            with col_tabla:
                st.markdown("**Por Canal**")
                if CANAL_COL in df_fam.columns:
                    agg = df_fam.groupby(CANAL_COL).agg(
                        Cantidad =("Cantidad", "sum"),
                        Litros   =("Litros",   "sum"),
                    ).reset_index()
                    agg["Toneladas"]  = agg["Litros"] / 1000
                    agg["%_Part"]     = agg["Toneladas"] / ton_fam * 100 if ton_fam else 0
                    agg["T_x_Dia"]    = agg["Toneladas"] / DIAS
                    agg = agg.sort_values("Toneladas", ascending=False)

                    # Fila total
                    tot = pd.DataFrame([{
                        CANAL_COL:   "TOTAL",
                        "Cantidad":  agg["Cantidad"].sum(),
                        "Toneladas": agg["Toneladas"].sum(),
                        "%_Part":    100.0,
                        "T_x_Dia":   agg["Toneladas"].sum() / DIAS,
                    }])
                    tabla_s = pd.concat([agg[[CANAL_COL,"Cantidad","Toneladas","%_Part","T_x_Dia"]],
                                         tot[[CANAL_COL,"Cantidad","Toneladas","%_Part","T_x_Dia"]]],
                                        ignore_index=True)

                    def style_total_s(row):
                        if row[CANAL_COL] == "TOTAL":
                            return ["background:#1e3a5f;color:white;font-weight:bold"] * len(row)
                        return [""] * len(row)

                    st.dataframe(
                        tabla_s.rename(columns={
                            CANAL_COL: "Canal",
                            "Cantidad": "Cantidad",
                            "Toneladas": "Toneladas (T)",
                            "%_Part": "% Part.",
                            "T_x_Dia": "T/Día",
                        }).style
                        .format({
                            "Cantidad":      "{:,.0f}",
                            "Toneladas (T)": "{:,.2f}",
                            "% Part.":       "{:.1f}%",
                            "T/Día":         "{:,.2f}",
                        })
                        .apply(style_total_s, axis=1),
                        use_container_width=True, hide_index=True, height=300
                    )

            # ── Calendario diario ────────────────────────────────────────
            with col_cal:
                st.markdown("**Toneladas por Canal y Día**")
                if "Fecha" in df_fam.columns and CANAL_COL in df_fam.columns:
                    pivot = df_fam.groupby([CANAL_COL, df_fam["Fecha"].dt.strftime("%Y%m%d")])["Litros"] \
                                  .sum().reset_index()
                    pivot.columns = [CANAL_COL, "Fecha", "Litros"]
                    pivot["Toneladas"] = pivot["Litros"] / 1000
                    pivot_wide = pivot.pivot_table(index=CANAL_COL, columns="Fecha",
                                                   values="Toneladas", aggfunc="sum").fillna(0)

                    # Total por día
                    pivot_wide.loc["Total general"] = pivot_wide.sum()

                    # Heatmap
                    fig_heat = px.imshow(
                        pivot_wide,
                        color_continuous_scale="Blues",
                        aspect="auto",
                        text_auto=".2f",
                        labels=dict(x="Fecha", y="Canal", color="Toneladas"),
                    )
                    fig_heat.update_layout(
                        height=max(280, len(pivot_wide) * 45),
                        margin=dict(l=10, r=10, t=10, b=60),
                        coloraxis_showscale=False,
                        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
                        yaxis=dict(tickfont=dict(size=11)),
                    )
                    fig_heat.update_traces(textfont_size=9)
                    st.plotly_chart(fig_heat, use_container_width=True)

            st.divider()

# ══════════════════════════════════════════════════════════════════════════
# TAB LECHES
# ══════════════════════════════════════════════════════════════════════════
with tab_leches:

    FAMILIAS_LECHE = ["Leches", "Maquila Leche"]
    df_l = df[df["Familia"].isin(FAMILIAS_LECHE)] if "Familia" in df.columns else pd.DataFrame()

    if df_l.empty:
        st.info("No hay datos de Leches para los filtros actuales.")
    else:
        lit_total  = df_l["Litros"].sum()   if "Litros"   in df_l.columns else 0
        cant_total = df_l["Cantidad"].sum() if "Cantidad" in df_l.columns else 0
        lit_dia    = lit_total / DIAS

        k1, k2, k3 = st.columns(3)
        k1.metric("📦 Unidades totales", f"{cant_total:,.0f}")
        k2.metric("🥛 Litros totales",   f"{lit_total:,.1f} L")
        k3.metric("📅 Litros por día",   f"{lit_dia:,.1f} L/día")

        st.divider()

        # ── Sección 1: Resumen por canal ──────────────────────────────────
        col_canal, col_tipo = st.columns([1, 1])

        with col_canal:
            st.subheader("📋 Por Canal")
            if CANAL_COL in df_l.columns:
                agg_l = df_l.groupby(CANAL_COL).agg(
                    Cantidad =("Cantidad", "sum"),
                    Litros   =("Litros",   "sum"),
                ).reset_index()
                agg_l["%_Part"]  = agg_l["Litros"] / lit_total * 100 if lit_total else 0
                agg_l["L_x_Dia"] = agg_l["Litros"] / DIAS
                agg_l = agg_l.sort_values("Litros", ascending=False)

                tot_l = pd.DataFrame([{
                    CANAL_COL:  "TOTAL",
                    "Cantidad": agg_l["Cantidad"].sum(),
                    "Litros":   agg_l["Litros"].sum(),
                    "%_Part":   100.0,
                    "L_x_Dia":  agg_l["Litros"].sum() / DIAS,
                }])
                tabla_l = pd.concat([agg_l, tot_l], ignore_index=True)

                def style_total_l(row):
                    if row[CANAL_COL] == "TOTAL":
                        return ["background:#1e3a5f;color:white;font-weight:bold"] * len(row)
                    return [""] * len(row)

                st.dataframe(
                    tabla_l.rename(columns={
                        CANAL_COL: "Canal",
                        "Cantidad": "Cantidad",
                        "Litros": "Litros",
                        "%_Part": "% Part.",
                        "L_x_Dia": "L/Día",
                    }).style
                    .format({
                        "Cantidad": "{:,.0f}",
                        "Litros":   "{:,.1f}",
                        "% Part.":  "{:.1f}%",
                        "L/Día":    "{:,.1f}",
                    })
                    .apply(style_total_l, axis=1),
                    use_container_width=True, hide_index=True
                )

        with col_tipo:
            st.subheader("🔬 Por Tipo de Leche")
            # Solo leches (no maquila) para el desglose por tipo
            df_solo_leche = df_l[df_l["Familia"] == "Leches"] if "Familia" in df_l.columns else df_l

            if "Tipo_Leche" in df_solo_leche.columns:
                agg_t = df_solo_leche.groupby("Tipo_Leche").agg(
                    Cantidad =("Cantidad", "sum"),
                    Litros   =("Litros",   "sum"),
                ).reset_index()
                lit_solo = agg_t["Litros"].sum()
                agg_t["%_Part"]  = agg_t["Litros"] / lit_solo * 100 if lit_solo else 0
                agg_t["L_x_Dia"] = agg_t["Litros"] / DIAS
                agg_t = agg_t.sort_values("Litros", ascending=False)

                tot_t = pd.DataFrame([{
                    "Tipo_Leche": "TOTAL",
                    "Cantidad":   agg_t["Cantidad"].sum(),
                    "Litros":     agg_t["Litros"].sum(),
                    "%_Part":     100.0,
                    "L_x_Dia":    agg_t["Litros"].sum() / DIAS,
                }])
                tabla_t = pd.concat([agg_t, tot_t], ignore_index=True)

                def style_total_t(row):
                    if row["Tipo_Leche"] == "TOTAL":
                        return ["background:#1e3a5f;color:white;font-weight:bold"] * len(row)
                    return [""] * len(row)

                st.dataframe(
                    tabla_t.rename(columns={
                        "Tipo_Leche": "Tipo",
                        "Litros": "Litros",
                        "%_Part": "% Part.",
                        "L_x_Dia": "L/Día",
                    }).style
                    .format({
                        "Cantidad": "{:,.0f}",
                        "Litros":   "{:,.1f}",
                        "% Part.":  "{:.2f}%",
                        "L/Día":    "{:,.1f}",
                    })
                    .apply(style_total_t, axis=1),
                    use_container_width=True, hide_index=True
                )

                # Mini gráfica de torta
                datos_pie = agg_t[agg_t["Tipo_Leche"] != "N.R"].copy()
                if not datos_pie.empty:
                    fig_pie = px.pie(
                        datos_pie, values="Litros", names="Tipo_Leche",
                        color_discrete_map={
                            "ENTERA":        "#3b82f6",
                            "DESLACTOSADA":  "#22c55e",
                            "SEMIDESCREMADA":"#f59e0b",
                        }
                    )
                    fig_pie.update_layout(height=220, margin=dict(t=10, b=10))
                    st.plotly_chart(fig_pie, use_container_width=True)

        # ── Sección 2: Calendario diario ──────────────────────────────────
        st.divider()
        st.subheader("📅 Litros por Canal y Día")
        st.caption("Solo familia Leches (excluye Maquila)")

        if "Fecha" in df_solo_leche.columns and CANAL_COL in df_solo_leche.columns:
            pivot_l = df_solo_leche.groupby(
                [CANAL_COL, df_solo_leche["Fecha"].dt.strftime("%Y%m%d")]
            )["Litros"].sum().reset_index()
            pivot_l.columns = [CANAL_COL, "Fecha", "Litros"]

            pivot_wide_l = pivot_l.pivot_table(
                index=CANAL_COL, columns="Fecha",
                values="Litros", aggfunc="sum"
            ).fillna(0)

            pivot_wide_l.loc["Total general"] = pivot_wide_l.sum()

            # Formatear en miles para legibilidad
            pivot_display = pivot_wide_l / 1000  # mostrar en miles de litros

            fig_heat_l = px.imshow(
                pivot_display,
                color_continuous_scale="Blues",
                aspect="auto",
                text_auto=".1f",
                labels=dict(x="Fecha", y="Canal", color="Miles Litros"),
            )
            fig_heat_l.update_layout(
                height=max(300, len(pivot_wide_l) * 48),
                margin=dict(l=10, r=10, t=10, b=70),
                coloraxis_showscale=False,
                xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
                yaxis=dict(tickfont=dict(size=11)),
            )
            fig_heat_l.update_traces(textfont_size=8)
            st.plotly_chart(fig_heat_l, use_container_width=True)
            st.caption("Valores en miles de litros (kL)")

        # ── Sección 3: D y V / PAE ────────────────────────────────────────
        st.divider()
        st.subheader("📊 Resumen especial")

        # D y V = Distribuidores y Vendedores (locales + nacionales + otros)
        dyv_canales = ["DISTRIBUIDORES LOCALES","DISTRIBUIDORES NACIONALES",
                       "OTROS DISTRIBUIDORES","VENDEDORES"]
        pae_canales = ["PAE"]

        if CANAL_COL in df_solo_leche.columns:
            lit_dyv = df_solo_leche[df_solo_leche[CANAL_COL].isin(dyv_canales)]["Litros"].sum() \
                      if "Litros" in df_solo_leche.columns else 0
            lit_pae = df_solo_leche[df_solo_leche[CANAL_COL].isin(pae_canales)]["Litros"].sum() \
                      if "Litros" in df_solo_leche.columns else 0
            lit_smk_td = df_solo_leche[df_solo_leche[CANAL_COL].isin(
                ["SUPERMERCADOS","TIENDAS DE DESCUENTO"])]["Litros"].sum() \
                if "Litros" in df_solo_leche.columns else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🚛 D y V",           f"{lit_dyv:,.1f} L",
                      delta=f"{lit_dyv/DIAS:,.1f} L/día")
            c2.metric("🏫 PAE",             f"{lit_pae:,.1f} L",
                      delta=f"{lit_pae/DIAS:,.1f} L/día")
            c3.metric("🛒 SMK + TD",        f"{lit_smk_td:,.1f} L",
                      delta=f"{lit_smk_td/DIAS:,.1f} L/día")
            c4.metric("🥛 Total Leches",    f"{lit_total:,.1f} L",
                      delta=f"{lit_dia:,.1f} L/día")

        # ── Sección 4: Maquila Leche ──────────────────────────────────────
        df_maq_leche = df_l[df_l["Familia"] == "Maquila Leche"] if "Familia" in df_l.columns else pd.DataFrame()
        if not df_maq_leche.empty:
            st.divider()
            st.subheader("🏭 Maquila Leche")
            lit_maq = df_maq_leche["Litros"].sum() if "Litros" in df_maq_leche.columns else 0

            m1, m2 = st.columns(2)
            m1.metric("🥛 Litros Maquila", f"{lit_maq:,.1f} L")
            m2.metric("📅 L/Día Maquila",  f"{lit_maq/DIAS:,.1f} L/día")

            if "Fecha" in df_maq_leche.columns and CANAL_COL in df_maq_leche.columns:
                pivot_m = df_maq_leche.groupby(
                    [CANAL_COL, df_maq_leche["Fecha"].dt.strftime("%Y%m%d")]
                )["Litros"].sum().reset_index()
                pivot_m.columns = [CANAL_COL, "Fecha", "Litros"]
                pivot_wide_m = pivot_m.pivot_table(
                    index=CANAL_COL, columns="Fecha",
                    values="Litros", aggfunc="sum"
                ).fillna(0) / 1000

                fig_maq = px.imshow(
                    pivot_wide_m,
                    color_continuous_scale="Greens",
                    aspect="auto", text_auto=".2f",
                )
                fig_maq.update_layout(
                    height=150, margin=dict(l=10, r=10, t=10, b=60),
                    coloraxis_showscale=False,
                    xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
                )
                fig_maq.update_traces(textfont_size=9)
                st.plotly_chart(fig_maq, use_container_width=True)
                st.caption("Valores en miles de litros (kL)")
