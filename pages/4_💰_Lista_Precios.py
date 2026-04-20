"""
pages/4_💰_Lista_Precios.py
Análisis por Lista de Precios — replica hoja ANALISIS X LISTA PRECIOS
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.loader import cargar_data, formatear_millones
from utils.params import TIPO_LECHE, IBUA_ITEMS, ICUI_VALOR

st.set_page_config(page_title="Lista de Precios", page_icon="💰", layout="wide")

df = cargar_data()
if df.empty:
    st.warning("⚠️ No hay datos cargados. Ve a la página principal y sube tu archivo.")
    st.stop()

# ── Enriquecer con tipo de leche ───────────────────────────────────────────
if "Referencia" in df.columns:
    ref = df["Referencia"].astype(str).str.strip()
    df["Tipo_Leche"] = ref.map(TIPO_LECHE).fillna("N.R")

# ── Sidebar filtros ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filtros")

    # Filtro LP — usa Desc_Lista_Precios de la data (viene del loader)
    if "Lista_Precios" in df.columns:
        # Construir mapa código → descripción desde la propia data
        if "Desc_Lista_Precios" in df.columns:
            mapa_lp = (
                df[["Lista_Precios", "Desc_Lista_Precios"]]
                .dropna(subset=["Lista_Precios"])
                .drop_duplicates()
                .set_index("Lista_Precios")["Desc_Lista_Precios"]
                .to_dict()
            )
        else:
            mapa_lp = {}

        lps_codigos = sorted(df["Lista_Precios"].dropna().unique().tolist())
        lp_etiquetas = {}
        for cod in lps_codigos:
            desc = mapa_lp.get(cod, "")
            desc = str(desc).strip() if desc else ""
            lp_etiquetas[cod] = f"{cod} — {desc}" if desc and desc != cod else str(cod)

        lp_etiqueta_inv = {v: k for k, v in lp_etiquetas.items()}

        lp_sel_etiq = st.multiselect(
            "LP — Lista de Precios",
            options=list(lp_etiquetas.values()),
            default=list(lp_etiquetas.values())[:1] if lp_etiquetas else [],
            help="Selecciona una o más listas de precios"
        )
        lp_sel = [lp_etiqueta_inv[e] for e in lp_sel_etiq]
    else:
        lp_sel = []
        st.warning("Columna Lista_Precios no encontrada.")

    # Filtro CODIGO (Familia)
    if "Familia" in df.columns:
        familias = ["Todas"] + sorted(df["Familia"].dropna().unique().tolist())
        familia_sel = st.selectbox("CODIGO — Familia", familias)
    else:
        familia_sel = "Todas"

    # Filtro ITEM (Tipo de leche)
    tipos_disponibles = ["N.R", "ENTERA", "DESLACTOSADA", "SEMIDESCREMADA"]
    tipo_sel = st.selectbox("ITEM — Tipo de leche", ["Todos"] + tipos_disponibles)

    st.divider()

    # Filtro de fecha (opcional)
    if "Fecha" in df.columns and df["Fecha"].notna().any():
        fmin = df["Fecha"].min().date()
        fmax = df["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", value=(fmin, fmax),
                              min_value=fmin, max_value=fmax)
    else:
        rango = None

    # Mostrar solo ítems con impuesto saludable
    solo_con_impuesto = st.checkbox("Solo ítems con IMP_SALUDABLE > 0", value=False)

# ── Título ─────────────────────────────────────────────────────────────────
st.title("💰 Análisis por Lista de Precios")

lp_label = ", ".join(lp_sel) if lp_sel else "Todas"
st.caption(f"LP: **{lp_label}**  •  Familia: **{familia_sel}**  •  Tipo: **{tipo_sel}**")

# ── Aplicar filtros ────────────────────────────────────────────────────────
dff = df.copy()

if lp_sel and "Lista_Precios" in dff.columns:
    dff = dff[dff["Lista_Precios"].isin(lp_sel)]

if familia_sel != "Todas" and "Familia" in dff.columns:
    dff = dff[dff["Familia"] == familia_sel]

if tipo_sel != "Todos" and "Tipo_Leche" in dff.columns:
    dff = dff[dff["Tipo_Leche"] == tipo_sel]

if rango and len(rango) == 2 and "Fecha" in dff.columns:
    dff = dff[(dff["Fecha"].dt.date >= rango[0]) & (dff["Fecha"].dt.date <= rango[1])]

if dff.empty:
    st.info("No hay datos para los filtros seleccionados.")
    st.stop()

# ── Construcción de tabla (replica hoja Excel) ─────────────────────────────
# Columnas requeridas: ID_LIPRE1, FAMILIA, ID_REFERENCIA, DESCRIPCION2,
#                      FECHA_VIG, Precio, IMP_SALUDABLE

gcols = []
if "Lista_Precios" in dff.columns: gcols.append("Lista_Precios")
if "Familia"       in dff.columns: gcols.append("Familia")
if "Referencia"    in dff.columns: gcols.append("Referencia")
if "Nombre_Item"   in dff.columns: gcols.append("Nombre_Item")

if not gcols:
    st.error("No se encontraron columnas suficientes para construir la tabla.")
    st.stop()

# Agregar: precio más reciente, impuesto saludable promedio por unidad
def _precio_reciente(grp):
    """Retorna el precio unitario del registro más reciente."""
    if "Fecha" in grp.columns and grp["Fecha"].notna().any():
        idx = grp["Fecha"].idxmax()
        return grp.loc[idx, "Precio_Unit"] if "Precio_Unit" in grp.columns else 0
    return grp["Precio_Unit"].median() if "Precio_Unit" in grp.columns else 0

def _fecha_vig(grp):
    """Retorna la fecha de vigencia (máxima fecha de transacción)."""
    if "Fecha" in grp.columns and grp["Fecha"].notna().any():
        return grp["Fecha"].max()
    return pd.NaT

def _imp_saludable(grp):
    """IMP_SALUDABLE = (Ibua + Icui) / Cantidad total."""
    cant = grp["Cantidad"].sum() if "Cantidad" in grp.columns else 1
    ibua = grp["Ibua"].sum() if "Ibua" in grp.columns else 0
    icui = grp["Icui"].sum() if "Icui" in grp.columns else 0
    total_imp = ibua + icui
    return round(total_imp / cant, 2) if cant else 0

agg_rows = []
for keys, grp in dff.groupby(gcols):
    if not isinstance(keys, tuple):
        keys = (keys,)
    row = dict(zip(gcols, keys))
    row["FECHA_VIG"]      = _fecha_vig(grp)
    row["Precio"]         = _precio_reciente(grp)
    row["IMP_SALUDABLE"]  = _imp_saludable(grp)
    row["Cantidad_Total"] = grp["Cantidad"].sum() if "Cantidad" in grp.columns else 0
    row["Valor_Neto"]     = grp["Valor_Neto"].sum() if "Valor_Neto" in grp.columns else 0
    agg_rows.append(row)

tabla = pd.DataFrame(agg_rows)

if tabla.empty:
    st.info("No hay registros para mostrar.")
    st.stop()

# Filtrar solo con impuesto saludable > 0 si aplica
if solo_con_impuesto:
    tabla = tabla[tabla["IMP_SALUDABLE"] > 0]

# Renombrar para presentación
rename_map = {
    "Lista_Precios": "ID_LIPRE1",
    "Familia":       "FAMILIA",
    "Referencia":    "ID_REFERENCIA",
    "Nombre_Item":   "DESCRIPCION2",
}
tabla_display = tabla.rename(columns=rename_map)

# Formatear FECHA_VIG como YYYYMMDD (igual al Excel)
if "FECHA_VIG" in tabla_display.columns:
    tabla_display["FECHA_VIG"] = pd.to_datetime(
        tabla_display["FECHA_VIG"], errors="coerce"
    ).dt.strftime("%Y%m%d").fillna("—")

# Ordenar: ID_LIPRE1 > FAMILIA > ID_REFERENCIA
sort_cols = [c for c in ["ID_LIPRE1", "FAMILIA", "ID_REFERENCIA"] if c in tabla_display.columns]
if sort_cols:
    tabla_display = tabla_display.sort_values(sort_cols)

# ── KPIs superiores ────────────────────────────────────────────────────────
total_items  = len(tabla_display)
precio_prom  = tabla["Precio"].mean() if "Precio" in tabla.columns else 0
imp_total    = tabla[tabla["IMP_SALUDABLE"] > 0].shape[0]
venta_total  = tabla["Valor_Neto"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("📦 Ítems en lista",          f"{total_items:,}")
k2.metric("💲 Precio promedio",         f"${precio_prom:,.0f}")
k3.metric("🧪 Ítems con imp. saludable", f"{imp_total:,}")
k4.metric("💰 Venta total período",     formatear_millones(venta_total))

st.divider()

# ── Tabla principal ────────────────────────────────────────────────────────
st.subheader("📋 Información de Listas de Precios")
st.caption("Precio = último precio unitario registrado  •  IMP_SALUDABLE = (IBUA + ICUI) por unidad")

# Columnas a mostrar
cols_show = [c for c in [
    "ID_LIPRE1", "FAMILIA", "ID_REFERENCIA", "DESCRIPCION2",
    "FECHA_VIG", "Precio", "IMP_SALUDABLE"
] if c in tabla_display.columns]

fmt = {}
if "Precio"        in cols_show: fmt["Precio"]        = "${:,.2f}"
if "IMP_SALUDABLE" in cols_show: fmt["IMP_SALUDABLE"] = "${:,.2f}"

def color_imp(val):
    if isinstance(val, (int, float)) and val > 0:
        return "color:#dc2626; font-weight:bold"
    return "color:#64748b"

def color_familia(row):
    """Alterna fondo suave por familia para facilitar lectura."""
    return [""] * len(row)

styled = (
    tabla_display[cols_show]
    .style
    .format(fmt)
    .map(color_imp, subset=["IMP_SALUDABLE"] if "IMP_SALUDABLE" in cols_show else [])
    .set_properties(**{"font-size": "0.85rem"})
)

st.dataframe(styled, use_container_width=True, hide_index=True, height=520)

# ── Resumen por Familia ────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Resumen por Familia")

if "FAMILIA" in tabla_display.columns:
    resumen_fam = (
        tabla_display.groupby("FAMILIA")
        .agg(
            Items        =("ID_REFERENCIA", "count") if "ID_REFERENCIA" in tabla_display.columns else ("FAMILIA","count"),
            Precio_Prom  =("Precio", "mean"),
            Con_Impuesto =("IMP_SALUDABLE", lambda x: (x > 0).sum()),
            Imp_Prom     =("IMP_SALUDABLE", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
        )
        .reset_index()
        .sort_values("Items", ascending=False)
    )

    resumen_fam.columns = ["Familia", "N° Ítems", "Precio Prom ($)", "Con Imp. Saludable", "Imp. Saludable Prom ($)"]

    st.dataframe(
        resumen_fam.style.format({
            "N° Ítems": "{:,.0f}",
            "Precio Prom ($)": "${:,.0f}",
            "Con Imp. Saludable": "{:,.0f}",
            "Imp. Saludable Prom ($)": "${:,.2f}",
        }).map(
            lambda v: "font-weight:bold; color:#1d4ed8" if isinstance(v,(int,float)) and v>0 else "",
            subset=["N° Ítems"]
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── Exportar ───────────────────────────────────────────────────────────────
st.divider()
csv_out = tabla_display[cols_show].to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    "📥 Descargar tabla como CSV",
    data=csv_out,
    file_name="lista_precios.csv",
    mime="text/csv"
)
