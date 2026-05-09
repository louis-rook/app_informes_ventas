"""
pages/2_🏪_Por_Cliente.py
Vista jerárquica: C.O. → Vendedor → Cliente → Ítem
+ Detalle individual por cliente
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones
from utils.params import MOTIVOS_OBSEQUIO

st.set_page_config(page_title="Por Cliente", page_icon="🏪", layout="wide")

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

# ── Helpers numéricos ──────────────────────────────────────────────────────
def fmt_num(v):
    if pd.isna(v) or v == 0: return "—"
    if abs(v) >= 1_000_000_000: return f"${v/1e9:.2f}mm"
    if abs(v) >= 1_000_000:     return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"

def fmt_cant(v):
    if pd.isna(v) or v == 0: return "—"
    return f"{v:,.0f}"

def semaforo_color(pct):
    if pct >= 35: return "#22c55e"
    if pct >= 20: return "#f59e0b"
    return "#ef4444"

def metricas(grp):
    cant_  = grp["Cantidad"].sum()           if "Cantidad"           in grp.columns else 0
    neto_  = grp["Valor_Neto"].sum()         if "Valor_Neto"         in grp.columns else 0
    costo_ = grp["Costo_Total"].sum()        if "Costo_Total"        in grp.columns else 0
    rent_  = grp["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in grp.columns else 0
    mg_    = rent_ / neto_ * 100             if neto_ else 0
    return cant_, neto_, costo_, rent_, mg_

# ── Sidebar filtros ────────────────────────────────────────────────────────
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

    CANAL_COL = "Canal" if "Canal" in df_all.columns else "Clase_Cliente"
    if CANAL_COL in df_all.columns:
        canales = ["Todas"] + sorted(df_all[CANAL_COL].dropna().unique().tolist())
        canal_sel = st.selectbox("Tipo_Cliente", canales)
    else:
        canal_sel = "Todas"

    CO_COL = "Desc_CO" if "Desc_CO" in df_all.columns else None
    if CO_COL:
        cos = ["Todos"] + sorted(df_all[CO_COL].dropna().unique().tolist())
        co_sel = st.selectbox("C.O.", cos)
    else:
        co_sel = "Todos"

    if "Nombre_Vendedor" in df_all.columns:
        vendedores = ["Todos"] + sorted(df_all["Nombre_Vendedor"].dropna().unique().tolist())
        vend_sel = st.selectbox("Vendedor", vendedores)
    else:
        vend_sel = "Todos"

    st.divider()
    busqueda = st.text_input("🔍 Buscar cliente (Tab Detalle)",
                             placeholder="Nombre o NIT...")

# ── Filtrado ───────────────────────────────────────────────────────────────
df = df_all.copy()
if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]
if tipo_motivo != "Todos":
    df = df[df["Tipo_Motivo"] == tipo_motivo]
if canal_sel != "Todas" and CANAL_COL in df.columns:
    df = df[df[CANAL_COL] == canal_sel]
if co_sel != "Todos" and CO_COL and CO_COL in df.columns:
    df = df[df[CO_COL] == co_sel]
if vend_sel != "Todos" and "Nombre_Vendedor" in df.columns:
    df = df[df["Nombre_Vendedor"] == vend_sel]

# ── Título y KPIs globales ─────────────────────────────────────────────────
st.title("🏪 Análisis por Cliente")
st.caption("Vista jerárquica: selecciona un **Centro de Operación → Vendedor → Cliente** para ver el detalle de compras. Cada nivel muestra ventas, costo, rentabilidad y unidades acumuladas.")
st.caption(f"Motivo: **{tipo_motivo}**  •  Canal: **{canal_sel}**  •  C.O.: **{co_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

venta = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
costo = df["Costo_Total"].sum()        if "Costo_Total"        in df.columns else 0
rent  = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
cant  = df["Cantidad"].sum()           if "Cantidad"           in df.columns else 0
n_cli = df["Nombre_Cliente"].nunique() if "Nombre_Cliente"     in df.columns else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Ventas Netas", formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k2.metric("🏭 Costo Total",  formatear_millones(costo),
          help="Costo promedio total de los ítems vendidos")
k3.metric("📈 Rentabilidad", formatear_millones(rent),
          delta=f"{rent/venta*100:.1f}%" if venta else None,
          help="Ventas Netas menos Costo Total")
k4.metric("📦 Cantidad",     f"{cant:,.0f}",
          help="Número total de unidades vendidas")
k5.metric("👥 Clientes",     f"{n_cli:,}",
          help="Clientes con al menos una venta en el período")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["📊 Vista Jerárquica", "🔍 Detalle por Cliente"])

# ──────────────────────────────────────────────────────────────────────────
# TAB 1 — VISTA JERÁRQUICA
# ──────────────────────────────────────────────────────────────────────────
with tab1:
    st.caption("**C.O.** (azul oscuro) → **Vendedor** (azul claro) → **Cliente** (blanco) → Ítem (detalle)")

    co_col   = CO_COL if CO_COL and CO_COL in df.columns else None
    vend_col = "Nombre_Vendedor" if "Nombre_Vendedor" in df.columns else None
    cli_col  = "Nombre_Cliente"  if "Nombre_Cliente"  in df.columns else None
    ref_col  = "Referencia"      if "Referencia"      in df.columns else None
    item_col = "Nombre_Item"     if "Nombre_Item"     in df.columns else None

    if not cli_col:
        st.warning("Columna Nombre_Cliente no encontrada.")
    else:
        mostrar_items = (co_sel != "Todos") or (vend_sel != "Todos") or (len(df) < 3000)
        if not mostrar_items:
            st.info("💡 Para ver el detalle por ítem, filtra por un **C.O.** o **Vendedor** específico.")

        def tr(label, cant, neto, costo, rent, mg, nivel=0, es_total=False):
            pad = nivel * 18 + 8
            c_mg = semaforo_color(mg)
            if es_total:
                bg, fg, fw = "#0f172a", "white", "bold"
            elif nivel == 0:
                bg, fg, fw = "#1d4ed8", "white", "bold"
            elif nivel == 1:
                bg, fg, fw = "#bfdbfe", "#1e3a8a", "bold"
            elif nivel == 2:
                bg, fg, fw = "#f0f9ff", "#1e293b", "600"
            else:
                bg, fg, fw = "#ffffff", "#374151", "normal"

            pre = "↳ " if nivel >= 2 else ("  " if nivel == 1 else "")
            td = "padding:3px 8px;border-bottom:1px solid #e2e8f0;"
            return (
                f'<tr style="background:{bg};color:{fg};font-weight:{fw};">'
                f'<td style="{td}padding-left:{pad}px">{pre}{label}</td>'
                f'<td style="{td}text-align:right">{fmt_cant(cant)}</td>'
                f'<td style="{td}text-align:right">{fmt_num(neto)}</td>'
                f'<td style="{td}text-align:right">{fmt_num(costo)}</td>'
                f'<td style="{td}text-align:right">{fmt_num(rent)}</td>'
                f'<td style="{td}text-align:right;color:{c_mg};font-weight:bold">{mg:.2f}%</td>'
                f'</tr>'
            )

        rows = []
        grupos_co = [(None, df)] if not co_col else sorted(
            df.groupby(co_col), key=lambda x: str(x[0]))

        for co_name, df_co in grupos_co:
            c, n, cs, r, mg = metricas(df_co)
            rows.append(tr(str(co_name) if co_name else "Sin C.O.", c, n, cs, r, mg, nivel=0))

            grupos_vend = [(None, df_co)] if not vend_col else sorted(
                df_co.groupby(vend_col), key=lambda x: str(x[0]))

            for vend_name, df_vend in grupos_vend:
                if vend_col:
                    c, n, cs, r, mg = metricas(df_vend)
                    rows.append(tr(str(vend_name), c, n, cs, r, mg, nivel=1))

                for cli_name, df_cli in sorted(df_vend.groupby(cli_col),
                                               key=lambda x: -df_vend[df_vend[cli_col]==x[0]]["Valor_Neto"].sum()):
                    c, n, cs, r, mg = metricas(df_cli)
                    rows.append(tr(str(cli_name), c, n, cs, r, mg, nivel=2))

                    if mostrar_items:
                        item_gcols = [col for col in [ref_col, item_col] if col]
                        if item_gcols:
                            for keys, df_item in df_cli.groupby(item_gcols):
                                if not isinstance(keys, tuple): keys = (keys,)
                                lbl = "  ".join(str(k) for k in keys)
                                c, n, cs, r, mg = metricas(df_item)
                                rows.append(tr(lbl, c, n, cs, r, mg, nivel=3))

        c, n, cs, r, mg = metricas(df)
        rows.append(tr("TOTAL GENERAL", c, n, cs, r, mg, nivel=0, es_total=True))

        html = f"""
        <style>
          .jt{{width:100%;border-collapse:collapse;font-size:0.82rem;font-family:sans-serif;}}
          .jt th{{background:#0f172a;color:white;padding:7px 10px;text-align:left;
                  position:sticky;top:0;z-index:2;white-space:nowrap;}}
          .jt th.r{{text-align:right;}}
          .jt tr:hover td{{filter:brightness(0.92);cursor:default;}}
        </style>
        <div style="max-height:640px;overflow-y:auto;border:1px solid #cbd5e1;border-radius:8px;">
        <table class="jt">
          <thead><tr>
            <th>C.O. / Vendedor / Cliente / Ítem</th>
            <th class="r">Cantidad</th>
            <th class="r">Neto Calc</th>
            <th class="r">Costo</th>
            <th class="r">Rentab</th>
            <th class="r">Margen %</th>
          </tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table></div>"""

        st.markdown(html, unsafe_allow_html=True)

        st.divider()
        export_cols = [c for c in [co_col, vend_col, cli_col, ref_col, item_col,
                                   "Motivo","Cantidad","Valor_Neto","Costo_Total",
                                   "Valor_Rentabilidad","Margen_Pct"]
                       if c and c in df.columns]
        st.download_button("📥 Descargar CSV jerárquico",
                           data=df[export_cols].to_csv(index=False, encoding="utf-8-sig"),
                           file_name="clientes_jerarquico.csv", mime="text/csv")

# ──────────────────────────────────────────────────────────────────────────
# TAB 2 — DETALLE INDIVIDUAL POR CLIENTE
# ──────────────────────────────────────────────────────────────────────────
with tab2:
    if "Nombre_Cliente" not in df.columns:
        st.warning("Columna Nombre_Cliente no encontrada.")
        st.stop()

    opciones = sorted(df["Nombre_Cliente"].dropna().unique())
    if busqueda:
        opciones = [c for c in opciones if busqueda.upper() in c.upper()]
    if not opciones:
        st.info("No se encontraron clientes con ese criterio.")
        st.stop()

    cliente_sel = st.selectbox("Selecciona el cliente", opciones)
    dff = df[df["Nombre_Cliente"] == cliente_sel].copy()

    if dff.empty:
        st.info("Sin datos para este cliente con los filtros activos.")
        st.stop()

    co_v    = dff[CO_COL].iloc[0]             if CO_COL and CO_COL in dff.columns else "—"
    canal_v = dff[CANAL_COL].iloc[0]          if CANAL_COL in dff.columns else "—"
    vend_v  = dff["Nombre_Vendedor"].iloc[0]  if "Nombre_Vendedor" in dff.columns else "—"
    zona_v  = dff["Zona"].iloc[0]             if "Zona" in dff.columns else "—"

    ia, ib, ic, id_ = st.columns(4)
    ia.info(f"**C.O.:** {co_v}")
    ib.info(f"**Canal:** {canal_v}")
    ic.info(f"**Vendedor:** {vend_v}")
    id_.info(f"**Zona:** {zona_v}")

    v_c  = dff["Valor_Neto"].sum()         if "Valor_Neto"         in dff.columns else 0
    c_c  = dff["Costo_Total"].sum()        if "Costo_Total"        in dff.columns else 0
    r_c  = dff["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in dff.columns else 0
    q_c  = dff["Cantidad"].sum()           if "Cantidad"           in dff.columns else 0
    lt_c = dff["Litros"].sum()             if "Litros"             in dff.columns else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💰 Ventas",   formatear_millones(v_c),
              help="Suma del valor neto facturado en el período (sin IVA)")
    k2.metric("🏭 Costo",    formatear_millones(c_c),
              help="Costo promedio total de los ítems vendidos")
    k3.metric("📈 Rentab.",  formatear_millones(r_c),
              delta=f"{r_c/v_c*100:.1f}%" if v_c else None,
              help="Ventas Netas menos Costo Total")
    k4.metric("📦 Cantidad", f"{q_c:,.0f}",
              help="Número total de unidades vendidas")
    k5.metric("🥛 Litros",   f"{lt_c:,.1f}",
              help="Volumen total vendido en litros")

    st.divider()
    st.subheader("📋 Detalle por ítem")
    st.caption("Lista de todos los productos comprados por este cliente en el período, ordenados por valor neto. **Margen_%** = (Ventas − Costo) / Ventas. **Precio Unit.** = precio promedio de venta del ítem en el período.")
    gcols = [c for c in ["Familia", "Referencia", "Nombre_Item"] if c in dff.columns]
    if gcols:
        agg = dff.groupby(gcols).agg(
            Cantidad  =("Cantidad",           "sum"),
            Neto_Calc =("Valor_Neto",         "sum"),
            Costo     =("Costo_Total",        "sum"),
            Rentab    =("Valor_Rentabilidad", "sum"),
        ).reset_index()
        agg["Margen_%"] = agg["Rentab"] / agg["Neto_Calc"].where(agg["Neto_Calc"] != 0, 1) * 100
        agg["Precio_U"] = agg["Neto_Calc"] / agg["Cantidad"].where(agg["Cantidad"] != 0, 1)
        agg = agg.sort_values("Neto_Calc", ascending=False)
        agg = agg.rename(columns={"Rentab": "Rentab. ($)", "Precio_U": "Precio Unit."})

        def color_mg(val):
            if not isinstance(val, (int, float)): return ""
            if val >= 35: return "color:#22c55e;font-weight:bold"
            if val >= 20: return "color:#f59e0b"
            return "color:#ef4444"

        st.dataframe(
            agg.style.format({
                "Cantidad":     "{:,.0f}",
                "Neto_Calc":    "${:,.0f}",
                "Costo":        "${:,.0f}",
                "Rentab. ($)":  "${:,.0f}",
                "Margen_%":     "{:.2f}%",
                "Precio Unit.": "${:,.0f}",
            }).map(color_mg, subset=["Margen_%"]),
            column_config={
                "Neto_Calc":    st.column_config.NumberColumn("Neto_Calc",    help="Valor neto calculado internamente"),
                "Rentab. ($)":  st.column_config.NumberColumn("Rentab. ($)",  help="Ventas Netas menos Costo Total en pesos"),
                "Precio Unit.": st.column_config.NumberColumn("Precio Unit.", help="Precio unitario promedio en el período"),
            },
            use_container_width=True, hide_index=True
        )

    if "Fecha" in dff.columns and dff["Fecha"].notna().any():
        st.divider()
        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
            st.subheader("📅 Evolución de ventas")
            st.caption("Área sombreada con las ventas diarias del cliente en el período. Permite identificar picos de compra, estacionalidades o brechas sin pedidos.")
            serie = dff.groupby(dff["Fecha"].dt.date)["Valor_Neto"].sum().reset_index()
            serie.columns = ["Fecha", "Ventas"]
            fig = px.area(serie, x="Fecha", y="Ventas",
                          color_discrete_sequence=["#3b82f6"])
            fig.update_layout(plot_bgcolor="white", height=280, margin=dict(t=10,b=20))
            st.plotly_chart(fig, use_container_width=True)
        with col_ev2:
            if "Familia" in dff.columns:
                st.subheader("🧪 Por Familia")
                st.caption("Distribución de las compras del cliente por familia de producto. Las familias más grandes en el gráfico representan las categorías más compradas en el período.")
                pf = dff.groupby("Familia")["Valor_Neto"].sum().reset_index()
                pf = pf[pf["Valor_Neto"] > 0]
                fig2 = px.pie(pf, values="Valor_Neto", names="Familia",
                              color_discrete_sequence=px.colors.qualitative.Set3)
                fig2.update_layout(height=280, margin=dict(t=10,b=20))
                st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.download_button("📥 Descargar detalle",
                       data=dff.to_csv(index=False, encoding="utf-8-sig"),
                       file_name=f"cliente_{cliente_sel.replace(' ','_')[:40]}.csv",
                       mime="text/csv")