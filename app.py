"""
app.py — Página principal y cargador de archivos
Ejecutar con: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from utils.loader import cargar_data, DATA_FOLDER

st.set_page_config(
    page_title="Reportes de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; }
  .stMetric label { font-size: 0.85rem !important; color: #64748b; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Reportes de Ventas")
    st.divider()
    st.subheader("📂 Cargar datos")
    st.caption("Sube el archivo que exportas de tu sistema")

    archivo = st.file_uploader(
        "Archivo de ventas",
        type=["csv", "xlsx", "xlsm"],
        help="El sistema puede exportar CSV o Excel. Ambos funcionan."
    )

    if archivo:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        ext = archivo.name.split(".")[-1].lower()

        if ext == "csv":
            destino = os.path.join(DATA_FOLDER, "data.csv")
            with open(destino, "wb") as f:
                f.write(archivo.getbuffer())
            st.success(f"✅ CSV cargado correctamente")
        else:
            # Excel: leer la hoja Sheet1 o DATA y guardar como CSV
            try:
                try:
                    df_raw = pd.read_excel(archivo, sheet_name="Sheet1", engine="openpyxl")
                except Exception:
                    df_raw = pd.read_excel(archivo, sheet_name="DATA", engine="openpyxl")

                destino = os.path.join(DATA_FOLDER, "data.csv")
                df_raw.to_csv(destino, index=False, encoding="utf-8")
                st.success(f"✅ Excel cargado: {len(df_raw):,} filas")
            except Exception as e:
                st.error(f"Error al leer el Excel: {e}")

        cargar_data.clear()

    st.divider()
    st.caption("Navega con el menú de arriba ☝️")

# ── Portada ────────────────────────────────────────────────────────────────
st.title("📊 Sistema de Reportes de Ventas")

df = cargar_data()

if df.empty:
    st.info("""
    ### 👈 Para comenzar:
    1. En el panel izquierdo haz clic en **"Browse files"**
    2. Sube tu archivo de ventas (`.csv` o `.xlsx`)
    3. La app lo procesa automáticamente
    4. Navega a los reportes con el menú de la izquierda
    """)
    st.stop()

# ── KPIs portada ──────────────────────────────────────────────────────────
fecha_info = ""
if "Fecha" in df.columns and df["Fecha"].notna().any():
    fmin = df["Fecha"].min().strftime("%d/%m/%Y")
    fmax = df["Fecha"].max().strftime("%d/%m/%Y")
    fecha_info = f"Período: **{fmin}** al **{fmax}**"

st.markdown(f"### Resumen del archivo cargado  •  {fecha_info}")

venta = df["Valor_Neto"].sum()         if "Valor_Neto"         in df.columns else 0
costo = df["Costo_Total"].sum()        if "Costo_Total"        in df.columns else 0
rent  = df["Valor_Rentabilidad"].sum() if "Valor_Rentabilidad" in df.columns else 0
filas = len(df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Ventas Netas",   f"${venta/1e6:,.1f}M" if venta >= 1e6 else f"${venta:,.0f}")
k2.metric("🏭 Costo Total",    f"${costo/1e6:,.1f}M" if costo >= 1e6 else f"${costo:,.0f}")
k3.metric("📈 Rentabilidad",   f"${rent/1e6:,.1f}M"  if rent  >= 1e6 else f"${rent:,.0f}",
          delta=f"{rent/venta*100:.1f}%" if venta else None)
k4.metric("📋 Transacciones",  f"{filas:,}")

st.divider()

# Mini resumen por canal
if "Canal" in df.columns:
    st.markdown("#### Vista rápida por canal")
    resumen = (
        df.groupby("Canal")
        .agg(Ventas=("Valor_Neto","sum"), Unidades=("Cantidad","sum"),
             Rentabilidad=("Valor_Rentabilidad","sum"))
        .reset_index()
    )
    resumen["%Rent"] = resumen["Rentabilidad"] / resumen["Ventas"].replace(0,1)
    resumen = resumen.sort_values("Ventas", ascending=False)
    st.dataframe(
        resumen.style.format({
            "Ventas":"{:,.0f}","Unidades":"{:,.0f}",
            "Rentabilidad":"{:,.0f}","%Rent":"{:.2%}"
        }),
        use_container_width=True, hide_index=True
    )
