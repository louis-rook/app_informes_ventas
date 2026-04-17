# 📊 App de Reportes de Ventas
### Guía paso a paso para instalación y uso

---

## ✅ Paso 1 — Instalar Python

Si aún no tienes Python instalado:

1. Ve a 👉 https://www.python.org/downloads/
2. Descarga la versión más reciente (3.11 o superior)
3. **MUY IMPORTANTE**: Al instalar, marca la casilla **"Add Python to PATH"**
4. Haz clic en "Install Now"

Para verificar que quedó bien instalado, abre una terminal (CMD o PowerShell en Windows) y escribe:
```
python --version
```
Deberías ver algo como: `Python 3.11.x`

---

## ✅ Paso 2 — Descargar la app

Guarda la carpeta `app_ventas` completa en tu computador.
La estructura debe verse así:

```
app_ventas/
├── app.py                  ← Punto de entrada principal
├── requirements.txt        ← Librerías necesarias
├── utils/
│   └── loader.py           ← Carga de datos
├── pages/
│   ├── 1_📈_Consolidados.py
│   ├── 2_🏪_Por_Cliente.py
│   └── 3_🔍_Consulta.py
└── data/                   ← Aquí van tus archivos CSV (se crea sola)
```

---

## ✅ Paso 3 — Instalar las librerías

1. Abre una terminal (CMD o PowerShell)
2. Navega hasta la carpeta de la app:
   ```
   cd ruta\a\tu\carpeta\app_ventas
   ```
   Ejemplo en Windows:
   ```
   cd C:\Users\TuNombre\Desktop\app_ventas
   ```
3. Instala las librerías:
   ```
   pip install -r requirements.txt
   ```
   Esto puede tardar 1-2 minutos. Es solo la primera vez.

---

## ✅ Paso 4 — Correr la app

Desde la misma terminal, escribe:
```
streamlit run app.py
```

Se abrirá automáticamente tu navegador en `http://localhost:8501` con la app.

> 💡 **Tip:** No cierres la terminal mientras usas la app. Para detenerla, presiona `Ctrl + C`.

---

## ✅ Paso 5 — Cargar tus datos

**Opción A — Subir el Excel directamente (más fácil):**
1. En el panel izquierdo de la app, haz clic en **"Browse files"**
2. Selecciona tu archivo `.xlsm` o `.xlsx`
3. La app extraerá automáticamente la hoja DATA

**Opción B — Exportar como CSV desde Excel (más rápido en el futuro):**
1. Abre tu Excel
2. Ve a la hoja **DATA**
3. Archivo → Guardar como → Tipo: **CSV UTF-8**
4. Guárdalo como `data.csv`
5. Súbelo en la app

---

## 📋 Reportes disponibles

| Reporte | Descripción |
|---|---|
| 📈 **Consolidados** | Ventas/costo/rentabilidad por canal de cliente |
| 🏪 **Por Cliente** | Análisis detallado por gran cliente (ARA, ÉXITO...) |
| 🔍 **Consulta** | Búsqueda libre por cliente o por ítem |

---

## ❓ Preguntas frecuentes

**¿Debo instalar las librerías cada vez?**
No, solo la primera vez. Luego solo corres `streamlit run app.py`.

**¿Qué pasa si cambio los datos del mes?**
Solo sube el nuevo archivo CSV/Excel en el panel izquierdo. La app se actualiza sola.

**¿La app necesita internet?**
Solo para la primera instalación. Después funciona 100% offline.

**¿Cuánto pesa la app?**
Muy poco. Las librerías ocupan ~300MB, pero la app en sí es liviana.

---

## 🆘 Soporte

Si algo no funciona, revisa:
1. Que Python esté en el PATH (`python --version` en la terminal)
2. Que estés en la carpeta correcta cuando corres `streamlit run app.py`
3. Que las librerías estén instaladas (`pip install -r requirements.txt`)
