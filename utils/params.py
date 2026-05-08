"""
utils/params.py
---------------
Parametrización manual centralizada de la app.
Contiene mapeos de clientes, ítems, vendedores y clasificaciones
que se unifican con la data importada del sistema.
"""

# ─────────────────────────────────────────────────────────────────────────────
# NOMBRES DE LISTAS DE PRECIOS (código → nombre completo)
# Usado en el filtro LP del módulo Lista de Precios
# ─────────────────────────────────────────────────────────────────────────────
LP_NOMBRES = {
    "PDT":  "LISTA DE PRECIOS DISTRIBUIDORES DISTRITO",
    "PDN":  "LISTA DE PRECIOS DISTRIBUIDORES NACIONALES",
    "PDL":  "LISTA DE PRECIOS DISTRIBUIDORES LOCALES",
    "TAT":  "LISTA DE PRECIOS TAT",
    "PAE":  "LISTA DE PRECIOS PAE",
    "GRD":  "LISTA DE PRECIOS GRANDES DISTRIBUIDORES",
    "INS":  "LISTA DE PRECIOS INSTITUCIONALES",
    "PDV":  "LISTA DE PRECIOS PUNTO DE VENTA",
    "EXP":  "LISTA DE PRECIOS EXPORTACION",
    "ESP":  "LISTA DE PRECIOS ESPECIAL",
    # Agrega más según los códigos que aparezcan en tu data
}

# ─────────────────────────────────────────────────────────────────────────────
# Usado para el filtro "ITEM" en el módulo de Lista de Precios.
# Valores: ENTERA | DESLACTOSADA | SEMIDESCREMADA | N.R.
# ─────────────────────────────────────────────────────────────────────────────
TIPO_LECHE = {
    # Leches ENTERA
    "04010301": "ENTERA",   # LECHE ENTERA UHT X 200 C.C.
    "04010303": "ENTERA",   # LECHE ENTERA UHT X 900 C.C
    "04010306": "ENTERA",   # MEGALITRO 1.1 LTS ENTERA
    "04010307": "ENTERA",   # SIXPACK LECHE ENTERA UHT X 400 C.C.
    "04010309": "ENTERA",   # SIXPACK LECHE ENTERA UHT X 900 C.C.
    "04010311": "ENTERA",   # SIXPACK LECHE ENTERA MEGALITRO 1.1 LTS
    "04010312": "ENTERA",   # LECHE ENTERA UHT X 400 C.C.
    "04010315": "ENTERA",   # FC LECHE ENTERA UHT X 900 C.C
    # Leches DESLACTOSADA
    "04010112": "DESLACTOSADA",   # LECHE UHT DESLACTOSADA X 900 CC
    "04010114": "DESLACTOSADA",   # MEGALITRO 1.1 LTS DESLACTOSADA
    "04010115": "DESLACTOSADA",   # SIXPACK LECHE UHT DESLACT X900 C.C
    "04010117": "DESLACTOSADA",   # SIXPACK LECHE DESLACT MEGALITRO 1.1 LTS
    "04010122": "DESLACTOSADA",   # SIXPACK LECHE DESLACT. UTH X 400 C.C.
    "04010127": "DESLACTOSADA",   # LECHE UHT DESLACTOSADA X 400 CC
    "04010128": "DESLACTOSADA",   # FC LECHE UHT DESLACTOSADA X 400 CC
    "04010129": "DESLACTOSADA",   # FC LECHE UHT DESLACTOSADA X 900 CC
    "04010135": "DESLACTOSADA",   # FC MEGALITRO 1.1 LTS DESLACTOSADA
    # Leches SEMIDESCREMADA
    "04010120": "SEMIDESCREMADA", # LECHE UHT SEMIDESCREMADA X 900 CC.
    "04010121": "SEMIDESCREMADA", # FC LECHE UHT SEMIDESCREMADA X 900 CC
    "04010123": "SEMIDESCREMADA", # LECHE UHT SEMIDESCREMADA X 400 ML
    "04010125": "SEMIDESCREMADA", # SIXPACK LECHE UHT SEMIDESCREM X900 C.
    "04010136": "SEMIDESCREMADA", # LECHE SEMIDESCREMADA UHT DE LA CUESTA SL
    # Avenas
    "04010501": "N.R",    # AVENA NATURAL UHT X 200 ML
    "04010503": "N.R",    # SIXPACK AVENA NATURAL UHT X 200 ML
    "04010516": "N.R",    # EXC. AVENA NATURAL UHT X 200 ML
    "04010520": "N.R",    # AVENA NATURAL UHT X 200 ML (alt)
    "04010521": "N.R",    # SIXPACK AVENA NATURAL UHT X 200 ML (alt)
}

# ─────────────────────────────────────────────────────────────────────────────
# ÍTEMS SUJETOS A IBUA (Impuesto Bebidas Ultraprocesadas Azucaradas)
# Son las leches con azúcar añadida (aplica IBUA por ML)
# ─────────────────────────────────────────────────────────────────────────────
IBUA_ITEMS = {
    "04010309",  # SIXPACK LECHE ENTERA UHT X 900 C.C.
    "04010115",  # SIXPACK LECHE UHT DESLACT X900 C.C
    "04010112",  # LECHE UHT DESLACTOSADA X 900 CC
    "04010114",  # MEGALITRO 1.1 LTS DESLACTOSADA
    "04010303",  # LECHE ENTERA UHT X 900 C.C
    "04010117",  # SIXPACK LECHE DESLACT MEGALITRO 1.1 LTS
    "04010306",  # MEGALITRO 1.1 LTS ENTERA
    "04010127",  # LECHE UHT DESLACTOSADA X 400 CC
    "04010311",  # SIXPACK LECHE ENTERA MEGALITRO 1.1 LTS
    "04010312",  # LECHE ENTERA UHT X 400 C.C.
    "04010301",  # LECHE ENTERA UHT X 200 C.C.
    "04010307",  # SIXPACK LECHE ENTERA UHT X 400 C.C.
    "04010122",  # SIXPACK LECHE DESLACT. UTH X 400 C.C.
    "04010125",  # SIXPACK LECHE UHT SEMIDESCREM X900 C.
    "04010120",  # LECHE UHT SEMIDESCREMADA X 900 CC.
    "04010128",  # FC LECHE UHT DESLACTOSADA X 400 CC
    "04010135",  # FC MEGALITRO 1.1 LTS DESLACTOSADA
    "04010315",  # FC LECHE ENTERA UHT X 900 C.C
    "04010129",  # FC LECHE UHT DESLACTOSADA X 900 CC
    "04010121",  # FC LECHE UHT SEMIDESCREMADA X 900 CC
}

# ─────────────────────────────────────────────────────────────────────────────
# ÍTEMS SUJETOS A ICUI (Impuesto a las Bebidas Ultraprocesadas)
# Valor = pesos por unidad vendida
# ─────────────────────────────────────────────────────────────────────────────
ICUI_VALOR = {
    "04050170": 130,    # TANLLERIN NARANJA BOLSA X 200 CC.
    "04010501": 130,    # AVENA NATURAL UHT X 200 ML
    "04030201": 123.5,  # KLASSGURT FRESA BOLSA X 200 GRS
    "04010503": 780,    # SIXPACK AVENA NATURAL UHT X 200 ML
    "04030221": 741,    # SIXPACK KLASS BOL x200 (6 FRESA)
    "04010516": 130,    # EXC. AVENA NATURAL UHT X 200 ML
    "04040383": 0,      # AFOGATTO KLARENS INC (20% IVA)
    "04040351": 0,      # HELADO CLASICO CONO IVA (20% IVA)
    "04040350": 0,      # HELADO CLASICO VASO IVA (20% IVA)
    "04040319": 0,      # HELADO COMBI VAI-ARE CONO 100 GR INC (20%)
    "04040320": 0,      # HELADO COMBI VAI-ARE VASO 100GR INC (20%)
    "04040317": 0,      # HELADO DE AREQUIPE CONO 100GR INC (20%)
    "04040316": 0,      # HELADO DE AREQUIPE VASO 100GR INC (20%)
    "04040315": 0,      # HELADO DE VAINILLA CONO 100GR INC (20%)
    "04040314": 0,      # HELADO DE VAINILLA VASO 100 GR INC (20%)
    "04040347": 0,      # HELADO ESPECIAL CHELIKLARENAS INC (20%)
    "04040349": 0,      # HELADO SUNDAE (IVA) (20%)
}

# ─────────────────────────────────────────────────────────────────────────────
# TASA IVA POR REFERENCIA (para ítems con IVA especial)
# ─────────────────────────────────────────────────────────────────────────────
IVA_TASA = {
    "04040383": 0.20,   # AFOGATTO KLARENS INC
    "04040351": 0.20,   # HELADO CLASICO CONO IVA
    "04040350": 0.20,   # HELADO CLASICO VASO IVA
    "04040319": 0.20,
    "04040320": 0.20,
    "04040317": 0.20,
    "04040316": 0.20,
    "04040315": 0.20,
    "04040314": 0.20,
    "04040347": 0.20,
    "04040349": 0.20,
    "04040353": 0.20,
    "04040356": 0.20,
    "04040357": 0.20,
    "04040349": 0.20,
    "04040384": 0.20,
    "04040382": 0.20,
    "04040380": 0.20,
    "04040336": 0.20,
    "04040337": 0.20,
    "0404030004": 0.20,
    "0404030002": 0.20,
    "0404030003": 0.20,
    "0404030001": 0.20,
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIENTES INSTITUCIONALES
# ─────────────────────────────────────────────────────────────────────────────
CLIENTES_INSTITUCIONALES = {
    "890900608":  "ALMACENES EXITO S A",
    "900155107":  "CENCOSUD COLOMBIA S A",
    "900383385":  "INVERCOMER DEL CARIBE S A S",
    "900059238":  "MAKRO SUPERMAYORISTA SAS",
    "824003724":  "REYES LOPEZ S A S",
    "890107487":  "SUPERTIENDAS Y DROGUERIAS OLIMPICA SA",
    "900319753":  "PRICESMART COLOMBIA SAS",
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIENTES PAE (Programa de Alimentación Escolar)
# ─────────────────────────────────────────────────────────────────────────────
CLIENTES_PAE = {
    "901103445":  "ARCOIRIS INVERSIONES SAS",
    "1100625458": "BENITEZ RODRIGUEZ CAROLINA LUCIA",
    "901598903":  "CONSORCIO NUTRIALIMENTAR 2022",
    "7597980":    "DIAZ SUAREZ RAFAEL EMIRO",
    "901171536":  "EMPRECON SAS ZOMAC",
    "900988847":  "EXALT DISTRIBUCIONES SAS",
    "860008068":  "FEDERACION COLOMBIANA DE GANADEROS",
    "819006346":  "FUNDACION ESPERANZA VERDE DE LOS NINOS EVENI",
    "824002285":  "FUNDACION NINEZ MUJER Y FAMILIA",
    "800145039":  "FUNDACION NINO FELIZ",
    "901031964":  "FUNDACION SAN MARCOS DANIEL",
    "900094547":  "FUNDACION SEMBRANDO FUTURO",
    "901904041":  "UNION TEMPORAL ALIMENTOS 2025",
    "901904660":  "UT PAE SUR DEL CESAR 2025",
    "901932032":  "UNION TEMPORAL MAGDALENA VITAL",
    "901860308":  "UNION TEMPORAL ALIMENTOS MAGDALENA",
    "901675840":  "UNION TEMPORAL NORTECHON PAE 2023",
    "901699469":  "UT POR LA NINEZ DE LA SIERRA NEVADA",
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIENTES TIENDAS DE DESCUENTO (D1, ARA, etc.)
# ─────────────────────────────────────────────────────────────────────────────
CLIENTES_TIENDA_DESCUENTO = {
    "900276962":  "D1 SAS",
    "900480569":  "JERONIMO MARTINS COLOMBIA SAS",
    "901613496":  "PLAN B INVESTMENTS SAS",
}

# ─────────────────────────────────────────────────────────────────────────────
# VENDEDORES (código → nombre)
# ─────────────────────────────────────────────────────────────────────────────
VENDEDORES = {
    "ARBV": "BRITO VEGA ANIBAL RAFAEL",
    "EMES": "ESCORCIA MIRANDA EDWIN SEGUNDO",
    "GVMJ": "DIAZ SALCEDO IVAN ALFONSO",
    "SRDF": "SANCHEZ RINCON DEIMAR FERNANDO",
    "RLFJ": "FUENTES JIMENEZ RAFAEL LAUREANO",
    "PLOD": "PENA LOZANO DAVID",
    "ABFA": "ASOCIACION DE FAMILIAS BENEFICIARIAS",
    "CDMA": "CDMA",
}

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE DOCUMENTO / MOTIVO
# Clasificación: VENTA | OBSEQUIO
# ─────────────────────────────────────────────────────────────────────────────
TIPO_DOC_CLASE = {
    "42AN": "VENTA",    # ANULACION FACTURACION ELECTRONICA
    "4275": "VENTA",    # DEVOLUCION VENTAS PASEADA
    "5072": "VENTA",    # VENTAS PDV
    "4070": "VENTA",    # VENTAS NACIONALES
    "40ME": "OBSEQUIO", # CONSUMO MERIENDA EMPLEADOS
    "5073": "OBSEQUIO", # OBSEQUIOS
    "4278": "VENTA",    # DEVOLUCION VENTAS VENCIDAS
    "4277": "VENTA",    # DEVOLUCION VENTAS FILTRADAS
    "40BF": "OBSEQUIO", # OBSEQUIOS BENEFICENCIA
    "5176": "VENTA",    # NOTA CREDITO PDV
    "4279": "VENTA",    # DEVOLUCION VENTAS MALA CALIDAD
    "40CL": "OBSEQUIO", # CONSUMO LABORATORIO
    "40CR": "OBSEQUIO", # CONSUMO REPRESENTACION
    "40MC": "OBSEQUIO", # CONSUMO MUESTRAS A CLIENTES
    "4276": "VENTA",    # DEVOLUCION VENTAS ACIDAS
    "40GG": "OBSEQUIO", # CONSUMO GERENCIA GENERAL
    "4501": "VENTA",    # MENOR VALOR A COBRAR
    "40FI": "OBSEQUIO", # CONSUMO FESTIVIDADES INTERNAS
    "5074": "OBSEQUIO", # PDV OBSEQUIOS
    "4503": "VENTA",    # DESCUENTO COMERCIALES PAC
    "4504": "VENTA",    # DESCUENTO COMERCIALES POS
    "42DN": "OBSEQUIO", # ANULACION DE OBSEQUIOS Y CONSUMOS
    "40DG": "OBSEQUIO", # DEGUSTACIONES Y PROMOCIONES EN VENTAS
    "5177": "OBSEQUIO", # NOTA CREDITO OBSEQUIOS PDV
}

# ─────────────────────────────────────────────────────────────────────────────
# MOTIVOS QUE SE CONSIDERAN VENTA (para excluir obsequios de análisis)
# ─────────────────────────────────────────────────────────────────────────────
MOTIVOS_VENTA = {"VENTA FACTURA", "VENTAS NACIONALES", "VENTAS PDV",
                 "NOTA CREDITO PDV", "MENOR VALOR A COBRAR",
                 "DEVOLUCION VENTAS PASEADA", "DEVOLUCION VENTAS VENCIDAS",
                 "DEVOLUCION VENTAS FILTRADAS", "DEVOLUCION VENTAS MALA CALIDAD",
                 "DEVOLUCION VENTAS ACIDAS", "DESCUENTO COMERCIALES POS",
                 "DESCUENTO COMERCIALES PAC", "ANULACION FACTURACION ELECTRONICA"}

MOTIVOS_OBSEQUIO = {"OBSEQUIOS", "OBSEQUIOS BENEFICENCIA", "CONSUMO MERIENDA EMPLEADOS",
                    "CONSUMO LABORATORIO", "CONSUMO REPRESENTACION", "CONSUMO MUESTRAS A CLIENTES",
                    "CONSUMO GERENCIA GENERAL", "CONSUMO FESTIVIDADES INTERNAS",
                    "PDV OBSEQUIOS", "NOTA CREDITO OBSEQUIOS PDV",
                    "DEGUSTACIONES Y PROMOCIONES EN VENTAS", "ANULACION DE OBSEQUIOS Y CONSUMOS"}

# ─────────────────────────────────────────────────────────────────────────────
# FAMILIAS DE PRODUCTOS (Desc. U.N. en el sistema)
# Usado en el módulo de Volúmenes
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# CONVERSIÓN SUEROS: ml por unidad vendida (para calcular Litros desde Cantidad)
# El sistema no registra Vol?men en LTR para sueros — se calcula aquí.
# Para ítems en KG (U.M. inv. = KG) se usa 1 KG = 1 L directamente.
# ─────────────────────────────────────────────────────────────────────────────
ML_POR_REFERENCIA_SUERO = {
    "4030404":  200,   # SUERO DOYPACK X 200 GRS
    "4030405":  400,   # SUERO DOYPACK X 400 GRS
    "4030407":   38,   # SUERO SACHET X 38 GR
    "4030458":  200,   # SUERO LATTI BOLSA X 200 GR
    "4030411":  200,   # SUERO PICANTE DOYPACK X 200 GRS
    "4030409": 4000,   # SUERO BOLSA CON VALVULA X 4 KLS
    "4030431":  400,   # SUERO COSTENO KLARENS TRIPACK X 400 GR
    "4030457":  570,   # SUERO SACHET X 38 GR BOLSA X 15 UND (15×38)
    "4030413": 1140,   # SUERO SACHET X 38 GR BOLSA X 30 UND (30×38)
    "4030432":  200,   # SUERO FRESCAMPO BOLSA X 200 GR
}

FAMILIAS_SUERO  = ["SUEROS"]
FAMILIAS_LECHE  = ["LECHE", "PRODUCCION PARA TERCEROS"]
FAMILIA_MAQUILA = "PRODUCCION PARA TERCEROS"

# ─────────────────────────────────────────────────────────────────────────────
# AGRUPACIONES DE CANALES DE VENTAS
# Usado en el módulo de Volúmenes (resumen especial)
# ─────────────────────────────────────────────────────────────────────────────
CANALES_DYV    = ["DISTRIBUIDORES LOCALES", "DISTRIBUIDORES NACIONALES",
                  "OTROS DISTRIBUIDORES", "VENDEDORES"]
CANALES_PAE    = ["PAE"]
CANALES_SMK_TD = ["SUPERMERCADOS", "TIENDAS DE DESCUENTO"]


def enriquecer_df(df):
    """
    Agrega columnas de parametrización al DataFrame:
    - Tipo_Leche: tipo de leche por referencia (ENTERA, DESLACTOSADA, etc.)
    - Tiene_IBUA / Tiene_ICUI: booleanos
    - Clase_Doc: VENTA u OBSEQUIO
    """
    import pandas as pd

    # Normalizar Referencia a string sin espacios para cruzar
    if "Referencia" in df.columns:
        ref = df["Referencia"].astype(str).str.strip()
        df["Tipo_Leche"] = ref.map(TIPO_LECHE).fillna("N.R")
        df["Tiene_IBUA"]  = ref.isin(IBUA_ITEMS)
        df["Tiene_ICUI"]  = ref.isin(ICUI_VALOR)

    if "Motivo" in df.columns:
        df["Clase_Doc"] = df["Motivo"].apply(
            lambda m: "OBSEQUIO" if str(m).strip().upper() in {x.upper() for x in MOTIVOS_OBSEQUIO}
                      else "VENTA"
        )

    return df
