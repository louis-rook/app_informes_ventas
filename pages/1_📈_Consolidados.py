"""
pages/1_📈_Consolidados.py
Consolidado de ventas — 3 vistas:
  • Por Canal de cliente
  • Por C.O. y Motivo  (replica tabla dinámica del informe)
  • Por Familia de producto
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones
from utils.params import MOTIVOS_VENTA, MOTIVOS_OBSEQUIO

def _safe_series(s):
    """Reemplaza 0 en una Series para evitar división por cero."""
    import numpy as np
    s = pd.to_numeric(s, errors="coerce").fillna(0)
    return s.where(s != 0, 1)


st.set_page_config(page_title="Consolidados", page_icon="📈", layout="wide")

df_all = cargar_data()
if df_all.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

# ── Clasificar TIPO_MOTIVO ─────────────────────────────────────────────────
def clasificar_motivo(m):
    m_up = str(m).strip().upper()
    if any(k.upper() in m_up for k in MOTIVOS_OBSEQUIO):
        return "OBSEQUIO"
    return "VENTA"

if "Motivo" in df_all.columns:
    df_all["Tipo_Motivo"] = df_all["Motivo"].apply(clasificar_motivo)
else:
    df_all["Tipo_Motivo"] = "VENTA"

# ── Sidebar filtros globales ───────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filtros")

    # Fechas
    if "Fecha" in df_all.columns and df_all["Fecha"].notna().any():
        fmin = df_all["Fecha"].min().date()
        fmax = df_all["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", value=(fmin, fmax),
                              min_value=fmin, max_value=fmax)
    else:
        rango = None

    # TIPO_MOTIVO
    tipo_motivo = st.selectbox(
        "TIPO_MOTIVO",
        ["Todos", "VENTA", "OBSEQUIO"],
        help="Filtra por tipo de transacción: Venta u Obsequio"
    )

    # Zona (solo para tab Canal)
    if "Zona" in df_all.columns:
        zonas = ["Todas"] + sorted(df_all["Zona"].dropna().unique().tolist())
        zona_sel = st.selectbox("Zona / Departamento", zonas)
    else:
        zona_sel = "Todas"

# ── Aplicar filtros base ───────────────────────────────────────────────────
df = df_all.copy()

if rango and len(rango) == 2 and "Fecha" in df.columns:
    df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]

if tipo_motivo != "Todos":
    df = df[df["Tipo_Motivo"] == tipo_motivo]

if zona_sel != "Todas" and "Zona" in df.columns:
    df = df[df["Zona"] == zona_sel]

# ── Título ─────────────────────────────────────────────────────────────────
st.title("📈 Consolidados de Ventas")
st.caption(f"Tipo motivo: **{tipo_motivo}**  •  Zona: **{zona_sel}**  •  Registros: {len(df):,}")

if df.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── KPIs globales ──────────────────────────────────────────────────────────
venta  = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
costo  = df["Costo_Total"].sum()        if "Costo_Total"        in df.columns else 0
rent   = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
cant   = df["Cantidad"].sum()           if "Cantidad"           in df.columns else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Netas",  formatear_millones(venta),
          help="Suma del valor neto facturado en el período (sin IVA)")
k2.metric("🏭 Costo Total",   formatear_millones(costo),
          help="Costo promedio total de los ítems vendidos")
k3.metric("📈 Rentabilidad",  formatear_millones(rent),
          delta=f"{rent/venta*100:.1f}%" if venta else None,
          help="Ventas Netas menos Costo Total")
k4.metric("📦 Cantidad",      f"{cant:,.0f}",
          help="Número total de unidades vendidas")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📊 Por Canal", "🏭 Por C.O. y Motivo", "🧪 Por Familia"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — POR CANAL
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    CANAL = "Canal" if "Canal" in df.columns else "Clase_Cliente"

    agg = df.groupby(CANAL).agg(
        Ventas_Netas    =("Valor_Neto",         "sum"),
        Costo_Sistema   =("Costo_Total",        "sum"),
        Rentabilidad    =("Valor_Rentabilidad", "sum"),
        Unidades        =("Cantidad",           "sum"),
        Litros          =("Litros",             "sum") if "Litros" in df.columns else ("Cantidad", "sum"),
    ).reset_index()

    agg["%Rent"]  = agg["Rentabilidad"] / _safe_series(agg["Ventas_Netas"])
    agg["%Costo"] = agg["Costo_Sistema"] / _safe_series(agg["Ventas_Netas"])
    _total_vn = agg["Ventas_Netas"].sum()
    agg["%Part"]  = agg["Ventas_Netas"] / (_total_vn if _total_vn != 0 else 1)

    total_row = pd.DataFrame([{
        CANAL:           "TOTAL",
        "Ventas_Netas":  agg["Ventas_Netas"].sum(),
        "Costo_Sistema": agg["Costo_Sistema"].sum(),
        "Rentabilidad":  agg["Rentabilidad"].sum(),
        "Unidades":      agg["Unidades"].sum(),
        "Litros":        agg["Litros"].sum() if "Litros" in agg.columns else 0,
    }])
    total_row["%Rent"]  = total_row["Rentabilidad"] / _safe_series(total_row["Ventas_Netas"])
    total_row["%Costo"] = total_row["Costo_Sistema"] / _safe_series(total_row["Ventas_Netas"])
    total_row["%Part"]  = 1.0

    tabla_c = pd.concat([agg.sort_values("Ventas_Netas", ascending=False), total_row],
                        ignore_index=True)

    def color_total_row(row):
        if row[CANAL] == "TOTAL":
            return ["background-color:#1e3a5f;color:white;font-weight:bold"] * len(row)
        return [""] * len(row)

    def semaforo_rent(val):
        if not isinstance(val, (int, float)): return ""
        if val >= 0.35: return "color:#16a34a;font-weight:bold"
        if val >= 0.20: return "color:#ca8a04"
        return "color:#dc2626"

    display_c = tabla_c.rename(columns={
        CANAL: "Canal", "Ventas_Netas": "Ventas Netas ($)",
        "Costo_Sistema": "Costo ($)", "Rentabilidad": "Rentabilidad ($)",
        "Unidades": "Unidades", "Litros": "Litros",
        "%Rent": "% Rent.", "%Costo": "% Costo", "%Part": "% Part.",
    })

    fmt_c = {
        "Ventas Netas ($)":  "{:,.0f}",
        "Costo ($)":         "{:,.0f}",
        "Rentabilidad ($)":  "{:,.0f}",
        "Unidades":          "{:,.0f}",
        "Litros":            "{:,.1f}",
        "% Rent.":           "{:.2%}",
        "% Costo":           "{:.2%}",
        "% Part.":           "{:.2%}",
    }

    styled_c = (
        display_c.style
        .format(fmt_c)
        .apply(color_total_row, axis=1)
        .map(semaforo_rent, subset=["% Rent."])
    )

    st.subheader("📋 Resumen por Canal")
    st.caption("Tabla de ventas agrupada por Canal de Ventas. Columnas: **Ventas Netas ($)** = valor facturado sin IVA · **Costo ($)** = costo de los productos · **Rentabilidad ($)** = Ventas − Costo · **% Rent.** = Rentabilidad / Ventas (semáforo: 🟢 ≥35% 🟡 20–35% 🔴 <20%) · **% Costo** = Costo / Ventas · **% Part.** = participación de ese canal sobre el total.")
    st.dataframe(styled_c,
                 column_config={
                     "% Rent.":  st.column_config.NumberColumn("% Rent.",  help="Rentabilidad como porcentaje de las ventas netas"),
                     "% Part.":  st.column_config.NumberColumn("% Part.",  help="Participación porcentual sobre el total del período"),
                     "% Costo":  st.column_config.NumberColumn("% Costo",  help="Costo como porcentaje de las ventas netas"),
                 },
                 use_container_width=True, hide_index=True)

    # Gráficas
    g1, g2 = st.columns(2)
    datos_g = tabla_c[tabla_c[CANAL] != "TOTAL"].sort_values("Ventas_Netas", ascending=True)

    n_canales = len(datos_g)
    alto = max(380, n_canales * 52)

    with g1:
        st.subheader("💰 Ventas Netas por Canal")
        st.caption("Barras horizontales ordenadas de mayor a menor. Muestra cuánto vendió en pesos cada canal en el período seleccionado.")

        def _fmt_bar(v):
            if abs(v) >= 1_000_000_000: return f"${v/1e9:.2f}mm"   # miles de millones
            if abs(v) >= 1_000_000:     return f"${v/1e6:.1f}M"
            return f"${v:,.0f}"

        textos_v = [_fmt_bar(v) for v in datos_g["Ventas_Netas"]]

        fig = go.Figure(go.Bar(
            x=datos_g["Ventas_Netas"],
            y=datos_g[CANAL],
            orientation="h",
            marker=dict(
                color=datos_g["Ventas_Netas"],
                colorscale=[[0,"#93c5fd"],[0.5,"#3b82f6"],[1,"#1d4ed8"]],
                showscale=False,
            ),
            text=textos_v,
            textposition="outside",
            textfont=dict(size=13, color="#1e293b"),
            cliponaxis=False,
        ))
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=alto,
            margin=dict(l=10, r=120, t=20, b=40),
            xaxis=dict(
                showgrid=True, gridcolor="#e2e8f0",
                zeroline=True, zerolinecolor="#94a3b8",
                tickfont=dict(size=11),
                title=dict(text="Ventas ($)", font=dict(size=12)),
            ),
            yaxis=dict(
                tickfont=dict(size=12, color="#1e293b"),
                title="",
                automargin=True,
            ),
            bargap=0.35,
        )
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("📊 % Rentabilidad por Canal")
        st.caption("Muestra el margen de ganancia de cada canal. 🔴 Rojo = menos del 20% (crítico) · 🟡 Naranja = 20–35% (aceptable) · 🟢 Verde = más del 35% (meta). Las líneas punteadas marcan los umbrales de referencia.")
        colores = [
            "#ef4444" if x < 0.2 else
            "#f59e0b" if x < 0.35 else
            "#22c55e"
            for x in datos_g["%Rent"]
        ]
        textos_r = [f"{v*100:.1f}%" for v in datos_g["%Rent"]]

        fig2 = go.Figure(go.Bar(
            x=datos_g["%Rent"] * 100,
            y=datos_g[CANAL],
            orientation="h",
            marker_color=colores,
            text=textos_r,
            textposition="outside",
            textfont=dict(size=13, color="#1e293b"),
            cliponaxis=False,
        ))

        # Líneas de referencia semáforo
        fig2.add_vline(x=20, line_dash="dot", line_color="#ef4444",
                       annotation_text="20%", annotation_position="top",
                       annotation_font=dict(size=10, color="#ef4444"))
        fig2.add_vline(x=35, line_dash="dot", line_color="#22c55e",
                       annotation_text="35%", annotation_position="top",
                       annotation_font=dict(size=10, color="#22c55e"))

        fig2.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=alto,
            margin=dict(l=10, r=80, t=30, b=40),
            xaxis=dict(
                showgrid=True, gridcolor="#e2e8f0",
                zeroline=True, zerolinecolor="#94a3b8",
                ticksuffix="%",
                tickfont=dict(size=11),
                title=dict(text="% Rentabilidad", font=dict(size=12)),
            ),
            yaxis=dict(
                tickfont=dict(size=12, color="#1e293b"),
                title="",
                automargin=True,
            ),
            bargap=0.35,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.download_button("📥 Descargar CSV",
                       data=display_c.to_csv(index=False, encoding="utf-8-sig"),
                       file_name="consolidado_canal.csv", mime="text/csv")

# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — POR C.O. Y MOTIVO  (replica tabla dinámica del informe)
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("🏭 Ventas por Centro de Operación y Motivo")
    st.caption("Estructura: C.O. (total) → desglose por Motivo  •  Misma lógica que la tabla dinámica del informe")

    CO_COL = "Desc_CO" if "Desc_CO" in df.columns else ("CO" if "CO" in df.columns else None)

    if CO_COL is None or "Motivo" not in df.columns:
        st.warning("Columnas C.O. o Motivo no encontradas en los datos.")
    else:
        # Agrupar por CO + Motivo
        grp = df.groupby([CO_COL, "Motivo"]).agg(
            Cantidad   =("Cantidad",   "sum"),
            Valor_Neto =("Valor_Neto", "sum"),
            Costo      =("Costo_Total","sum"),
        ).reset_index()

        # Subtotales por CO
        sub = df.groupby(CO_COL).agg(
            Cantidad   =("Cantidad",   "sum"),
            Valor_Neto =("Valor_Neto", "sum"),
            Costo      =("Costo_Total","sum"),
        ).reset_index()
        sub["Motivo"] = "__SUBTOTAL__"

        # Total general
        tot = pd.DataFrame([{
            CO_COL:      "Total general",
            "Motivo":    "__SUBTOTAL__",
            "Cantidad":  df["Cantidad"].sum(),
            "Valor_Neto":df["Valor_Neto"].sum(),
            "Costo":     df["Costo_Total"].sum(),
        }])

        # Construir tabla ordenada: CO subtotal + sus motivos intercalados
        cos = sorted(sub[CO_COL].unique())
        filas = []

        for co in cos:
            # fila CO (subtotal)
            fila_co = sub[sub[CO_COL] == co].copy()
            fila_co["_nivel"] = "co"
            filas.append(fila_co)
            # filas motivo dentro de ese CO
            hijos = grp[grp[CO_COL] == co].sort_values("Motivo")
            hijos["_nivel"] = "motivo"
            filas.append(hijos)

        # Total general al final
        tot["_nivel"] = "total"
        filas.append(tot)

        tabla_co = pd.concat(filas, ignore_index=True)

        # ── Renderizar fila por fila con estilos ──────────────────────────
        def _fmt_num(v, prefix="$"):
            if pd.isna(v): return ""
            if abs(v) >= 1_000_000:
                return f"{prefix}{v/1_000_000:,.1f}M"
            return f"{prefix}{v:,.0f}"

        rows_html = []
        for _, row in tabla_co.iterrows():
            nivel = row["_nivel"]
            co_val = row[CO_COL]
            mot    = row["Motivo"] if row["Motivo"] != "__SUBTOTAL__" else ""
            cant   = row["Cantidad"]
            neto   = row["Valor_Neto"]
            costo  = row["Costo"]

            if nivel == "total":
                style = "background:#1e3a5f;color:white;font-weight:bold"
                label = "Total general"
                indent = ""
            elif nivel == "co":
                style = "background:#dbeafe;font-weight:bold;color:#1e40af"
                label = co_val
                indent = ""
            else:  # motivo
                style = ""
                label = mot
                indent = "padding-left:24px"

            cant_s  = f"{cant:,.1f}"  if not pd.isna(cant)  else "—"
            neto_s  = _fmt_num(neto)
            costo_s = _fmt_num(costo)

            rows_html.append(
                f'<tr style="{style}">'
                f'<td style="padding:4px 8px;{indent}">{label if nivel != "motivo" else "<span style=color:#64748b>↳</span> " + label}</td>'
                f'<td style="padding:4px 12px;text-align:right">{cant_s}</td>'
                f'<td style="padding:4px 12px;text-align:right">{neto_s}</td>'
                f'<td style="padding:4px 12px;text-align:right">{costo_s}</td>'
                f'</tr>'
            )

        html_table = f"""
        <style>
          .co-table {{ width:100%; border-collapse:collapse; font-size:0.84rem; font-family:sans-serif; }}
          .co-table th {{ background:#1e3a5f; color:white; padding:6px 12px; text-align:left; position:sticky; top:0; }}
          .co-table tr:hover td {{ background:#f0f9ff!important; }}
        </style>
        <div style="max-height:600px; overflow-y:auto;">
        <table class="co-table">
          <thead>
            <tr>
              <th>Centro de Operación / Motivo</th>
              <th style="text-align:right">Suma de Cantidad</th>
              <th style="text-align:right">Suma de Valor Neto</th>
              <th style="text-align:right">Suma de Valor Costo</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows_html)}
          </tbody>
        </table>
        </div>
        """

        st.markdown(html_table, unsafe_allow_html=True)

        # Descarga plana
        st.divider()
        export = tabla_co[tabla_co["_nivel"] != "total"][[CO_COL, "Motivo", "Cantidad", "Valor_Neto", "Costo"]].copy()
        export["Motivo"] = export["Motivo"].replace("__SUBTOTAL__", "(Subtotal CO)")
        st.download_button("📥 Descargar CSV",
                           data=export.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="consolidado_co_motivo.csv", mime="text/csv")

# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — POR FAMILIA
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    if "Familia" not in df.columns:
        st.warning("Columna Familia no encontrada.")
    else:
        agg_f = df.groupby("Familia").agg(
            Ventas_Netas  =("Valor_Neto",         "sum"),
            Costo_Sistema =("Costo_Total",        "sum"),
            Rentabilidad  =("Valor_Rentabilidad", "sum"),
            Unidades      =("Cantidad",           "sum"),
        ).reset_index()
        agg_f["%Rent"]  = agg_f["Rentabilidad"]  / _safe_series(agg_f["Ventas_Netas"])
        agg_f["%Costo"] = agg_f["Costo_Sistema"] / _safe_series(agg_f["Ventas_Netas"])
        _total_vn_f = agg_f["Ventas_Netas"].sum()
        agg_f["%Part"]  = agg_f["Ventas_Netas"] / (_total_vn_f if _total_vn_f != 0 else 1)

        tot_f = pd.DataFrame([{
            "Familia": "TOTAL",
            "Ventas_Netas":  agg_f["Ventas_Netas"].sum(),
            "Costo_Sistema": agg_f["Costo_Sistema"].sum(),
            "Rentabilidad":  agg_f["Rentabilidad"].sum(),
            "Unidades":      agg_f["Unidades"].sum(),
        }])
        tot_f["%Rent"]  = tot_f["Rentabilidad"]  / _safe_series(tot_f["Ventas_Netas"])
        tot_f["%Costo"] = tot_f["Costo_Sistema"] / _safe_series(tot_f["Ventas_Netas"])
        tot_f["%Part"]  = 1.0

        tabla_f = pd.concat([agg_f.sort_values("Ventas_Netas", ascending=False), tot_f],
                            ignore_index=True)

        def color_total_f(row):
            if row["Familia"] == "TOTAL":
                return ["background-color:#1e3a5f;color:white;font-weight:bold"] * len(row)
            return [""] * len(row)

        display_f = tabla_f.rename(columns={
            "Familia": "Familia",
            "Ventas_Netas":  "Ventas Netas ($)",
            "Costo_Sistema": "Costo ($)",
            "Rentabilidad":  "Rentabilidad ($)",
            "Unidades":      "Unidades",
            "%Rent":         "% Rent.",
            "%Costo":        "% Costo",
            "%Part":         "% Part.",
        })
        fmt_f = {
            "Ventas Netas ($)": "{:,.0f}",
            "Costo ($)":        "{:,.0f}",
            "Rentabilidad ($)": "{:,.0f}",
            "Unidades":         "{:,.0f}",
            "% Rent.":          "{:.2%}",
            "% Costo":          "{:.2%}",
            "% Part.":          "{:.2%}",
        }
        st.subheader("📋 Resumen por Familia de Producto")
        st.caption("Ventas consolidadas por línea de producto (Familia). Permite identificar qué categorías generan más ventas y cuáles tienen mejor margen.")
        st.dataframe(
            display_f.style.format(fmt_f)
                           .apply(color_total_f, axis=1)
                           .map(semaforo_rent, subset=["% Rent."]),
            column_config={
                "% Rent.":  st.column_config.NumberColumn("% Rent.",  help="Rentabilidad como porcentaje de las ventas netas"),
                "% Part.":  st.column_config.NumberColumn("% Part.",  help="Participación porcentual sobre el total del período"),
                "% Costo":  st.column_config.NumberColumn("% Costo",  help="Costo como porcentaje de las ventas netas"),
            },
            use_container_width=True, hide_index=True
        )

        # Pie chart
        g1f, g2f = st.columns(2)
        datos_pie = tabla_f[tabla_f["Familia"] != "TOTAL"].nlargest(10, "Ventas_Netas")
        with g1f:
            fig_pie = px.pie(datos_pie, values="Ventas_Netas", names="Familia",
                             title="Participación por Familia",
                             color_discrete_sequence=px.colors.qualitative.Set3)
            fig_pie.update_layout(height=400)
            st.caption("Muestra qué porcentaje del total de ventas aporta cada familia de producto. Las familias más grandes en el gráfico son las más relevantes.")
            st.plotly_chart(fig_pie, use_container_width=True)
        with g2f:
            fig_bar_f = px.bar(
                datos_pie.sort_values("Ventas_Netas", ascending=True),
                x="Ventas_Netas", y="Familia", orientation="h",
                color="Ventas_Netas", color_continuous_scale="Blues",
                text_auto=".3s", title="Ventas por Familia",
                labels={"Ventas_Netas": "$", "Familia": ""}
            )
            fig_bar_f.update_layout(showlegend=False, coloraxis_showscale=False,
                                    plot_bgcolor="white", height=400)
            st.caption("Ventas en pesos por familia, ordenadas de mayor a menor. Útil para comparar el tamaño absoluto de cada línea de producto.")
            st.plotly_chart(fig_bar_f, use_container_width=True)

        st.download_button("📥 Descargar CSV",
                           data=display_f.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="consolidado_familia.csv", mime="text/csv")
