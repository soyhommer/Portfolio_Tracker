# 📜 Especificaciones Funcionales - Módulo de Históricos NAV

## 🎯 Objetivo

Desarrollar un sistema en la app Streamlit que permita:

* Gestionar históricos de precios para **Fondos UCITS**, **ETFs**, **Acciones**.
* Usar **un formato estándar Investing.com** para soportar todos los activos.
* Almacenar históricos **una sola vez**, evitando duplicados entre usuarios.
* Permitir **importación incremental** y gestión de intervalos.
* Mostrar **intervalos cargados** al usuario para control de cobertura.

---

## ✅ 1️⃣ Estructura de almacenamiento

```
/data/
  /nav_historico/
    ES0116567035.csv
    US1234567890.csv
    ETF5678901234.csv
```

✔️ Carpeta **común a todos los usuarios**.
✔️ Evita duplicación innecesaria.
✔️ Cada archivo CSV está indexado por **ISIN**.

---

## ✅ 2️⃣ Formato estándar del CSV

**Encabezado Investing.com:**

```
Date,"Price","Open","High","Low","Change %"
```

✔️ Para **fondos**, Price, Open, High, Low suelen ser iguales.
✔️ Para **ETFs/Acciones**, los campos pueden diferir y son importantes.
✔️ Se mantiene **siempre** esta estructura para todos los activos.

✅ Ejemplo:

| Date       | Price  | Open   | High   | Low    | Change % |
| ---------- | ------ | ------ | ------ | ------ | -------- |
| 2022-01-03 | 101.23 | 101.23 | 101.23 | 101.23 | 0.00%    |
| 2022-01-04 | 102.50 | 101.80 | 103.20 | 101.20 | 1.25%    |

---

## ✅ 3️⃣ Funcionalidades del sistema

### ✔️ Carga manual incremental

* El usuario puede subir históricos por tramos.
* Puede complementar periodos faltantes sin sobrescribir datos previos.

### ✔️ Almacenamiento único por ISIN

* Evita duplicar datos para varios usuarios o carteras.
* Centraliza el histórico por ISIN.

### ✔️ Fusión de datos

* Nuevos CSVs se fusionan al histórico existente.
* Sin duplicados en fechas.

### ✔️ Detección de intervalos continuos

* El sistema analiza gaps de fechas.
* Registra intervalos continuos para cada ISIN.

✅ Ejemplo de intervalos detectados:

| ISIN          | Fecha Inicio | Fecha Fin  | Registros |
| ------------- | ------------ | ---------- | --------- |
| ES0116...7035 | 2022-01-01   | 2022-12-31 | 365       |
| ES0116...7035 | 2024-01-01   | 2024-06-30 | 181       |

---

## ✅ 4️⃣ Frontend (Streamlit) - Especificación del formulario

### 🟣 Campos principales:

* **Selector de ISIN existente**

  * Desplegable con ISINs ya cargados.
* **Campo para ISIN nuevo**

  * Input manual para nuevos fondos.

### 🟣 Subida del archivo CSV

* **FileUploader** limitado a .csv.
* Mensaje de ayuda indicando formato esperado Investing.com.

### 🟣 Vista previa del CSV cargado

* Tabla completa con columnas:

  * Date
  * Price
  * Open
  * High
  * Low
  * Change %

### 🟣 Intervalos ya cargados para el ISIN

* Tabla generada automáticamente mostrando:

  * Intervalo inicio
  * Intervalo fin
  * Número de registros

### 🟣 Botón para guardar

* Llama a la lógica backend para fusionar y guardar.
* Feedback de éxito con ISIN y nuevos intervalos.

---

## ✅ 5️⃣ Backend (historial\_nav.py) - Funciones necesarias

### 🟠 leer\_csv\_investing(file)

* Lee CSV subido.
* Limpia y normaliza fechas.
* Mantiene todas las columnas estándar.

### 🟠 guardar\_historico\_isin(df, isin)

* Fusiona con histórico existente (si lo hay).
* Elimina duplicados de fechas.
* Guarda CSV en `/data/nav_historico/{ISIN}.csv`.

### 🟠 cargar\_historico\_isin(isin)

* Lee histórico existente desde disco.

### 🟠 detectar\_intervalos\_continuos(df)

* Analiza fechas ordenadas.
* Devuelve lista de intervalos continuos.

### 🟠 listar\_isins\_disponibles()

* Devuelve lista de ISINs con históricos cargados.

---

## ✅ 6️⃣ Responsabilidades claras

| Parte    | Responsabilidad                                         |
| -------- | ------------------------------------------------------- |
| MAIN     | Añadir sección al menú y llamar a la función de UI      |
| FRONTEND | Formulario en Streamlit, vista previa, tabla intervalos |
| BACKEND  | Lectura CSV, fusión, guardado, detección intervalos     |

---

## ✅ 7️⃣ Resultado esperado en la app

* Usuarios pueden **ver y gestionar** sus históricos por ISIN.
* Importar nuevos tramos **sin sobrescribir**.
* Visualizar **intervalos cubiertos** para cada ISIN.
* Preparado para **fondos, ETFs y acciones** con el mismo formato.

---

## ✅ 8️⃣ Ventajas de este diseño

✔️ Evita duplicados entre usuarios.
✔️ Estructura estándar Investing.com.
✔️ Soporta incremental y gaps.
✔️ Preparado para multiusuario en el futuro.
✔️ Sencillo de mantener y extender.
