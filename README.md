# 📈 Cartera Inversor Personal (CIP) - MVP Streamlit

## 🔍 Descripción

Aplicación local para el seguimiento y edición de carteras de inversión personales, centrada en fondos UCITS, planes de pensiones españoles (DGS) y acciones internacionales. Inspirada en la cartera gratuita de Morningstar, implementada rápidamente usando **Streamlit** y **Python**.

---

## ⚙️ Funcionalidades incluidas (versión MVP)

### 1. Gestión de Carteras

* Crear nuevas carteras: nombre, moneda base, benchmark.
* Editar nombre o eliminar cartera existente.
* Menú desplegable superior para seleccionar cartera activa.

### 2. Seguimiento

#### General

* Tabla con activos actuales: nombre, último NAV, participaciones, valor, peso, fecha.
* Integración de NAVs en tiempo real desde múltiples fuentes.

#### Rentabilidad

* Rentabilidad mensual (total, personal, índice) con gráfica de 11 meses + actual.
* Rentabilidad anual (total, personal, índice) con gráfica de 10 años + YTD.
* Tabla resumen con rentabilidades por periodo: 1s, 1m, 3m, 6m, YTD, 1a, 3a, 5a, 10a, desde compra.

#### Ganancias / Pérdidas

* Historial de activos desde inicio: participaciones, desembolsos, reembolsos, valor mercado, ganancia/pérdida absoluta y %.

#### Flujos

* Tabla trimestral con compras netas, ventas netas, gastos, flujo neto.

### 3. Edición de Transacciones

* Tabla editable de transacciones (CRUD).
* Formulario para añadir nuevas transacciones: activo, tipo, fecha, moneda, precio, gasto, etc.
* Importación desde Excel.
* Ordenación por cualquier columna.

### 4. Persistencia

* Todas las carteras, transacciones y activos se guardan localmente (formato CSV).
* Sistema de caché para NAVs (por nombre o ISIN) por fuente.

---

## 🔗 Fuentes de Datos

| Fuente                       | Tipo de activos soportados                  | Método       | Prioridad | Calidad     |
| ---------------------------- | ------------------------------------------- | ------------ | --------- | ----------- |
| **Morningstar.es**           | Fondos UCITS, PPS españoles                 | Scraping     | 🥇 Alta    | Muy alta    |
| **FT.com (Financial Times)** | Fondos UCITS internacionales                | Scraping     | 🥈 Media   | Alta        |
| **Investing.com**            | Fondos UCITS, gráficos                      | Scraping     | 🥉 Baja    | Media       |
| **FundAPI.io**               | Fondos UCITS europeos (ISIN, VL, categoría) | API          | Secundaria| Alta        |
| **CNMV**                     | Fondos y PPS registrados en España          | Scraping     | Backup    | Alta        |
| **Yahoo Finance (yfinance)** | Acciones, ETFs, algunos fondos              | Python       | Opcional  | Inconsistente|

---

## 📅 Tecnologías utilizadas

### Backend / Lógica:

* Python 3.10+
* Pandas, Numpy
* Requests, BeautifulSoup4, Unidecode
* Módulos de scraping personalizados
* CSV para persistencia local

### Frontend / Interfaz:

* Streamlit
* streamlit-aggrid (para tablas interactivas)
* Matplotlib o Plotly para gráficas

---

## 🛠️ Arquitectura de archivos

cartera_streamlit/
|
├── data/
│ ├── transacciones/ # CSV por cartera
│ └── nav_historico/ # CSV por ISIN
|
├── main.py # Punto de entrada Streamlit
├── utils/
│ ├── data_loader.py
│ ├── nav_fetcher.py
│ ├── investing_fetcher.py
│ ├── morningstar_fetcher.py
│ ├── ft_fetcher.py
│ ├── merge_nav_data.py
│ ├── ganancias.py
│ ├── general.py
│ ├── rentabilidad.py
│ └── transacciones.py


---

## ✅ Novedades recientes 

### 🔁 Gestión Inteligente de NAVs y Cacheo

* Búsqueda por nombre o ISIN con fusión de múltiples fuentes.
* Cacheo local con control de expiración.
* Scrapers independientes para Morningstar, FT y Investing.
* Algoritmo de validación cruzada (`merge_nav_data`) priorizando la calidad del dato.

### 🧠 Enriquecimiento Automático de Transacciones

* Detección y asignación automática del ISIN por nombre del activo.
* Persistencia de ISINs nuevos en caché tras edición o importación.
* Formulario de nueva transacción con validación y sugerencias.

### 📊 Rentabilidad y Ganancias Realistas

* Cálculo de NAV actual y comparación con histórico de compra.
* Ganancia/pérdida total por activo, % sobre desembolso, reembolsos y valoración de mercado.
* Rentabilidad ponderada por NAV y fecha.

### 🛡️ Validaciones y Manejo de Errores

* Validación defensiva del CSV de transacciones: columnas requeridas, fechas, estructura.
* Mensajes informativos en consola y Streamlit ante errores de scraping, parsing o estructura.

### 🔍 Trazabilidad y Depuración

* Consola detallada con trazas de llamadas a `merge_nav_data`.
* Respuestas distintas si se busca por ISIN vs. nombre.
* Etiqueta de fuente NAV visible.

---

## 🔥 Funcionalidades adicionales implementadas

### ✅ Edición avanzada de Transacciones
- Tabla editable con ordenación ascendente/descendente por columnas.
- Columna de selección (checkbox) a la izquierda para eliminar múltiples transacciones en lote.
- Icono 🗑️ en cada fila para borrado individual.
- Botón para guardar todas las ediciones en un solo paso.
- Importación masiva desde Excel con validación de columnas.

### ✅ Autocompletado inteligente de NAV
- Al agregar una nueva transacción con Precio = 0:
  - Busca primero el NAV exacto en la fecha.
  - Si no existe, usa el NAV más cercano hasta 7 días antes automáticamente.
  - Notifica al usuario el valor asignado.

### ✅ Validación de Cobertura NAV con tolerancia
- Revisión de cobertura NAV de todas las transacciones de todas las carteras.
- Marca como cubiertas las fechas con NAV exacto o con NAV anterior ≤7 días antes.
- Reporte claro y tabulado en la interfaz de las fechas que requieren históricos adicionales.

### ✅ Gestión completa de históricos NAV
- Subida incremental de tramos de históricos Investing.com.
- Validación de formato esperado con columnas:

- Conversión automática de decimal europeo (`,` a `.`).
- Detección y visualización de intervalos continuos de fechas cubiertas.
- Fusión automática sin duplicados de fechas.
- Cacheo y sugerencia de nombres de activo por ISIN.

### ✅ Mensajes aclaratorios en UI
- Nota bajo FileUploader explicando:
- Formato Investing.com esperado en INGLÉS.
- Decimal `,` soportado automáticamente.
- Separador de columnas `;`.

---

## 🚀 Roadmap futuro

- Datos Divisas y cambios para expresarlo todo en la moneda base de la cartera
- Módulo de dividendos y splits.
- Gestión de transacciones recurrentes.
- Cálculo fiscal con FIFO/LIFO y compensación de plusvalías.
- Sistema multiusuario con login y base de datos local o en la nube.
- Exportación en PDF/Excel con formato limpio.
- Despliegue en la nube (Streamlit Sharing, Docker, etc.).
- Control de calidad de fuentes y auditoría de cambios de NAV.
- Integración con APIs de brokers o bancos.
