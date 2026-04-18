"""
utils/loader.py
---------------
Carga y normaliza los datos del informe de ventas.

Detecta automáticamente si el archivo viene en formato NUEVO (sistema actual)
o formato ANTIGUO (Excel anterior), y lo convierte a nombres internos estándar.

NOMBRES INTERNOS que usa toda la app:
  Fecha, CO, Desc_CO, Cliente, Nombre_Cliente, Lista_Precios,
  Categoria, Canal, Clase_Cliente, Tipo_Doc, Nro_Doc,
  Item, Referencia, Nombre_Item, Tipo_Inventario, UM,
  Motivo, Vendedor, Nombre_Vendedor, Ciudad, Zona,
  Cantidad, Familia, Litros, Precio_Unit,
  Valor_Descuentos, Dscto1, Dscto2, Dscto3, Dscto_Pct,
  Valor_Impuestos, Ibua, Icui, IVA,
  Valor_Neto, Valor_Bruto, Valor_Subtotal,
  Costo_Total, Margen_Pct, Valor_Rentabilidad,
  Ruta, Subgrupo, Zona, Grupos
"""

import pandas as pd
import streamlit as st
import os

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")

def _ruta(nombre):
    return os.path.join(DATA_FOLDER, nombre)

# Formato NUEVO (sistema actual)
MAPA_NUEVO = {
    "Fecha":                         "Fecha",
    "C.O.":                          "CO",
    "Desc. C.O.":                    "Desc_CO",
    "Cliente factura":               "Cliente",
    "Razon social cliente factura":  "Nombre_Cliente",
    "Sucursal factura":              "Sucursal",
    "Lista de precios":              "Lista_Precios",
    "CATEGORIA":                     "Categoria",
    "CLASES DE CLIENTES":            "Clase_Cliente",
    "Tipo docto.":                   "Tipo_Doc",
    "Nro documento":                 "Nro_Doc",
    "Item":                          "Item",
    "Referencia":                    "Referencia",
    "Desc. item":                    "Nombre_Item",
    "Desc. tipo inventario":         "Tipo_Inventario",
    "U.M. inv.":                     "UM",
    "Desc. motivo":                  "Motivo",
    "Vendedor":                      "Vendedor",
    "Nombre vendedor":               "Nombre_Vendedor",
    "Desc. ciudad":                  "Ciudad",
    "Cantidad":                      "Cantidad",
    "Desc. U.N.":                    "Familia",
    "Vol?men en LTR ":               "Litros",
    "Precio unit.":                  "Precio_Unit",
    "Valor descuentos":              "Valor_Descuentos",
    "Descuento 1":                   "Dscto1",
    "Descuento 2":                   "Dscto2",
    "Descuento 3":                   "Dscto3",
    "Dscto. promedio %":             "Dscto_Pct",
    "Valor impuestos":               "Valor_Impuestos",
    "Vlr. imp. IBUA":                "Ibua",
    "Vlr. imp. ICUI":                "Icui",
    "Vlr. imp. IVA":                 "IVA",
    "Valor neto":                    "Valor_Neto",
    "Valor bruto":                   "Valor_Bruto",
    "Valor subtotal":                "Valor_Subtotal",
    "Costo promedio total":          "Costo_Total",
    "Margen promedio":               "Margen_Pct",
    "CANAL DE VENTAS":               "Canal",
    "RUTAS DE VENTAS":               "Ruta",
    "SUB-GRUPO":                     "Subgrupo",
    "ZONAS":                         "Zona",
    "GRUPOS":                        "Grupos",
}

# Formato ANTIGUO (Excel base)
MAPA_ANTIGUO = {
    "FECHA":                         "Fecha",
    "Centro de Operacion":           "CO",
    "Nombre Centro de Operacion":    "Desc_CO",
    "CLIENTE":                       "Cliente",
    "Nombre Cliente":                "Nombre_Cliente",
    "Lista de Precio Cliente":       "Lista_Precios",
    "CATEGORIA":                     "Categoria",
    "Tipo_Cliente":                  "Canal",
    "Nombre Clase Cliente":          "Clase_Cliente",
    "Tipo de Documento":             "Tipo_Doc",
    "Documento Ventas":              "Nro_Doc",
    "ITEM":                          "Item",
    "Referencia Item":               "Referencia",
    "Nombre Item":                   "Nombre_Item",
    "Unidad Inventario 1 Item":      "UM",
    "Nombre Motivo":                 "Motivo",
    "VENDEDOR":                      "Vendedor",
    "Nombre Vendedor":               "Nombre_Vendedor",
    "Nombre Departamento":           "Zona",
    "Cantidad 1":                    "Cantidad",
    "Familia":                       "Familia",
    "Litros":                        "Litros",
    "Precio Uni":                    "Precio_Unit",
    "Valor Descuentos":              "Valor_Descuentos",
    "DSCT1%":                        "Dscto1",
    "DSCT2%":                        "Dscto2",
    "DSCT3%":                        "Dscto3",
    "Valor Impuestos":               "Valor_Impuestos",
    "Vlr ibua":                      "Ibua",
    "Vlr Icui":                      "Icui",
    "Valor Neto":                    "Valor_Neto",
    "Valor Bruto":                   "Valor_Bruto",
    "Valor Costo":                   "Costo_Total",
    "Valor Rentabilidad":            "Valor_Rentabilidad",
    "Neto Calculado":                "Neto_Calculado",
    "Neto esp Calculado":            "Neto_Esp_Calculado",
    "Vlr Costo Transporte":          "Costo_Transporte",
}

def _detectar_formato(columnas):
    if "Razon social cliente factura" in columnas:
        return "nuevo"
    if "Nombre Cliente" in columnas or "Nombre Item" in columnas:
        return "antiguo"
    return "desconocido"

def _limpiar_prefijo(serie):
    """Elimina prefijos como '001 - ' de valores tipo '001 - TAT'."""
    return serie.astype(str).str.replace(r"^\d+\s*-\s*", "", regex=True).str.strip()

def _normalizar(df, formato):
    mapa = MAPA_NUEVO if formato == "nuevo" else MAPA_ANTIGUO
    mapa_activo = {k: v for k, v in mapa.items() if k in df.columns}
    df = df.rename(columns=mapa_activo)

    # Convertir columnas numéricas clave ANTES de operar con ellas
    for col in ["Valor_Neto", "Costo_Total", "Valor_Rentabilidad"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False),
                errors="coerce"
            ).fillna(0)

    # Rentabilidad calculada si no viene directa
    if "Valor_Rentabilidad" not in df.columns:
        if "Valor_Neto" in df.columns and "Costo_Total" in df.columns:
            df["Valor_Rentabilidad"] = df["Valor_Neto"] - df["Costo_Total"]

    # Margen % si no viene
    if "Margen_Pct" not in df.columns:
        if "Valor_Rentabilidad" in df.columns and "Valor_Neto" in df.columns:
            df["Margen_Pct"] = (df["Valor_Rentabilidad"] / df["Valor_Neto"].replace(0, 1)) * 100

    # Limpiar prefijos numericos en Canal, Clase_Cliente, Zona
    for col in ["Canal", "Clase_Cliente", "Zona", "Ruta"]:
        if col in df.columns:
            df[col] = _limpiar_prefijo(df[col])

    # Quitar espacios en nombres
    for col in ["Nombre_Cliente", "Nombre_Item", "Nombre_Vendedor"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

def _tipificar(df):
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    num_cols = [
        "Valor_Neto", "Costo_Total", "Valor_Rentabilidad", "Margen_Pct",
        "Cantidad", "Litros", "Precio_Unit", "Valor_Descuentos",
        "Dscto1", "Dscto2", "Dscto3", "Dscto_Pct",
        "Valor_Impuestos", "Ibua", "Icui", "IVA",
        "Valor_Bruto", "Valor_Subtotal",
        "Neto_Calculado", "Neto_Esp_Calculado", "Costo_Transporte",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

@st.cache_data(show_spinner="Cargando datos...")
def cargar_data():
    for nombre in ["data.csv", "data.xlsx"]:
        ruta = _ruta(nombre)
        if not os.path.exists(ruta):
            continue
        if nombre.endswith(".csv"):
            df = _leer_csv_robusto(ruta)
        else:
            df = pd.read_excel(ruta)
        formato = _detectar_formato(df.columns.tolist())
        df = _normalizar(df, formato)
        df = _tipificar(df)
        return df
    return pd.DataFrame()

def _leer_csv_robusto(ruta):
    """
    Lee el CSV tolerando:
    - Filas con campos de más (on_bad_lines='skip')
    - Distintas codificaciones (utf-8, latin-1, cp1252)
    - Separadores ; o ,
    """
    encodings = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            # Intentar detectar separador leyendo primera línea
            with open(ruta, "r", encoding=enc, errors="replace") as f:
                primera = f.readline()
            sep = ";" if primera.count(";") > primera.count(",") else ","

            df = pd.read_csv(
                ruta,
                encoding=enc,
                sep=sep,
                low_memory=False,
                on_bad_lines="skip",   # Omite filas con campos de más
                engine="python",       # Motor más tolerante
            )
            return df
        except Exception:
            continue
    # Último recurso: forzar con engine C y skip
    return pd.read_csv(ruta, encoding="latin-1", on_bad_lines="skip", low_memory=False)

def formatear_millones(valor):
    if abs(valor) >= 1_000_000_000:
        return f"${valor/1_000_000_000:,.2f}B"
    if abs(valor) >= 1_000_000:
        return f"${valor/1_000_000:,.1f}M"
    return f"${valor:,.0f}"

def formatear_pct(valor):
    return f"{valor:.1f}%"