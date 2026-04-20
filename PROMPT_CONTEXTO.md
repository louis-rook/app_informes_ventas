# 🧠 PROMPT DE CONTEXTO — APP VENTAS (para nuevo chat)

Pega este texto completo al inicio de un nuevo chat con Claude para retomar el trabajo.

---

## Aplicación
App de **reportes de ventas** en **Python + Streamlit**. Sector lácteo. Carga CSV/Excel del ERP.

## Estructura
```
app_ventas/
├── app.py
├── pages/
│   ├── 1_📈_Consolidados.py      ← Tabs: Por Canal | Por C.O.+Motivo | Por Familia
│   ├── 2_🏪_Por_Cliente.py
│   ├── 3_🔍_Consulta.py
│   └── 4_💰_Lista_Precios.py
├── utils/
│   ├── loader.py                 ← Carga robusta + normalización
│   └── params.py                 ← Parametrización del negocio
└── data/data.csv
```

## loader.py
- Detecta formato NUEVO (`"Razon social cliente factura"`) o ANTIGUO (`"Nombre Cliente"`)
- `_leer_csv_robusto()`: `on_bad_lines='skip'`, `engine='python'`, detecta `;`/`,`, utf-8→latin-1→cp1252
- `_normalizar()`: convierte a numérico ANTES de calcular (fix crítico `str-str`)
- Columnas internas: `Fecha, CO, Desc_CO, Cliente, Nombre_Cliente, Lista_Precios, Canal, Clase_Cliente, Motivo, Vendedor, Nombre_Vendedor, Zona, Familia, Referencia, Nombre_Item, Cantidad, Litros, Precio_Unit, Valor_Neto, Costo_Total, Valor_Rentabilidad, Margen_Pct, Ibua, Icui, IVA, Ruta, Subgrupo, Grupos`

## params.py
| Elemento | Descripción |
|---|---|
| `LP_NOMBRES` | `{código_LP: "Descripción completa"}` — para el filtro de Lista de Precios |
| `TIPO_LECHE` | `{referencia: tipo}` → ENTERA/DESLACTOSADA/SEMIDESCREMADA/N.R |
| `IBUA_ITEMS` | Set referencias con IBUA |
| `ICUI_VALOR` | `{ref: valor_unit}` ICUI por unidad |
| `CLIENTES_INSTITUCIONALES/PAE/TIENDA_DESCUENTO` | NIT→nombre |
| `VENDEDORES` | Código→nombre |
| `MOTIVOS_VENTA` / `MOTIVOS_OBSEQUIO` | Sets de texto para clasificar `Tipo_Motivo` |
| `enriquecer_df(df)` | Agrega: Tipo_Leche, Tiene_IBUA, Tiene_ICUI, Clase_Doc |

## Módulos completados

### 1_📈_Consolidados.py ✅ REDISEÑADO
- Filtro sidebar: Fechas, **TIPO_MOTIVO (VENTA/OBSEQUIO/Todos)**, Zona
- `Tipo_Motivo` se calcula comparando `Motivo` contra sets en params.py
- **Tab "Por Canal"**: tabla con %Rent semáforo, gráficas barras, fila TOTAL azul
- **Tab "Por C.O. y Motivo"**: replica tabla dinámica del informe Excel
  - `Desc_CO` como nivel padre (fila azul claro, bold)
  - Motivos como hijos indentados con ↳
  - Columnas: Cantidad | Valor Neto | Valor Costo
  - Fila "Total general" al final en azul oscuro
  - HTML personalizado con scroll vertical (max 600px)
- **Tab "Por Familia"**: tabla + pie chart + barra horizontal

### 4_💰_Lista_Precios.py ✅
- Filtros: LP (muestra descripción si existe en LP_NOMBRES, si no solo el código), Familia, Tipo_Leche
- Tabla: ID_LIPRE1 | FAMILIA | ID_REFERENCIA | DESCRIPCION2 | FECHA_VIG | Precio | IMP_SALUDABLE
- IMP_SALUDABLE = (Ibua+Icui)/Cantidad, rojo si >0

### 2_🏪_Por_Cliente.py y 3_🔍_Consulta.py
- Funcionan correctamente, pendientes de ajustar al informe real

## Errores resueltos
| Error | Solución |
|---|---|
| `ParserError: Expected N fields, saw N+1` | `on_bad_lines='skip'` + `engine='python'` |
| `TypeError: str - str` en rentabilidad | `pd.to_numeric()` antes de operar |
| `ImportError: background_gradient requires matplotlib` | Reemplazado por `.map()` simple |
| LP filter muestra "ACR — ACR" | Solo agrega descripción si existe en `LP_NOMBRES` |

## Estado
✅ app.py (carga robusta)
✅ Módulo 1: Consolidados (3 tabs: Canal / C.O.+Motivo / Familia)
✅ Módulo 4: Lista de Precios
✅ params.py completo
🔄 Próximo: siguiente módulo del informe (pasar captura)

## Para retomar
> "Continúo con app_ventas en Streamlit. Adjunto archivos actuales. Siguiente módulo: [nombre]. Captura de referencia adjunta."

**Subir:** `app.py`, `utils/loader.py`, `utils/params.py`, `pages/*.py`
