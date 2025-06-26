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
* Integración de NAVs en tiempo real desde múltiples fuentes (ver sección fuentes).

#### Rentabilidad

* Rentabilidad mensual (total, personal, índice) con gráfica de 11 meses + actual.
* Rentabilidad anual (total, personal, índice) con gráfica de 10 años + YTD.
* Tabla resumen con rentabilidades por periodo: 1s, 1m, 3m, 6m, YTD, 1a, 3a, 5a, 10a, desde compra.
* Tabla de fondos en cartera con %Año, %3a, volatilidad, etc.

#### Ganancias / Pérdidas

* Tabla con historial de activos desde inicio: participaciones, desembolsos, reembolsos, valor mercado, ganancia/pérdida absoluta y %.

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
| **FT.com (Financial Times)**| Fondos UCITS internacionales                | Scraping     | 🥈 Media   | Alta        |
| **Investing.com**            | Fondos UCITS, gráficos                      | Scraping     | 🥉 Baja    | Media       |
| **FundAPI.io**               | Fondos UCITS europeos (ISIN, VL, categoría) | API          | Secundaria| Alta        |
| **CNMV**                     | Fondos y PPS registrados en España          | Scraping     | Backup    | Alta        |
| **Yahoo Finance (yfinance)** | Acciones, ETFs, algunos fondos              | Python       | Opcional  | Inconsistente|

* El sistema selecciona automáticamente el mejor dato entre las fuentes según calidad y disponibilidad.
* Las tasas de cambio históricas se consultan mediante API (ECB, Open Exchange Rates) y se almacenan en cada transacción.

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

```
cartera_streamlit/
|
├── data/
│   ├── transacciones/            # CSV por cartera
│   └── cache_nav_*.json          # Cache por fuente
|
├── main.py                       # Punto de entrada Streamlit
├── utils/
│   ├── data_loader.py            # Lectura/escritura de carteras
│   ├── nav_fetcher.py            # Función unificada get_nav_real
│   ├── investing_fetcher.py      # Scraper de Investing.com
│   ├── morningstar_fetcher.py    # Scraper de Morningstar.es
│   ├── ft_fetcher.py             # Scraper de FT.com
│   ├── merge_nav_data.py         # Lógica de fusión de NAVs
│   ├── ganancias.py              # Cálculo de ganancia/pérdida
│   ├── general.py                # Estado actual de la cartera
│   └── rentabilidad.py           # Rentabilidad por periodo
```

---


---

## ✅ Novedades recientes 

### 🔁 Gestión Inteligente de NAVs y Cacheo

* Búsqueda por nombre o ISIN con fusión de múltiples fuentes.
* Cacheo local (`cache_nav_real.json`) con control de expiración.
* Scrapers independientes para Morningstar, FT y Investing.
* Algoritmo de validación cruzada (`merge_nav_data`) que prioriza calidad del dato (NAV, fecha, divisa, variación).

### 🧠 Enriquecimiento Automático de Transacciones

* Detección y asignación automática del ISIN por nombre del activo si no está presente.
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

* Consola detallada con trazas de llamadas a `merge_nav_data` (útil para debugging).
* Respuestas distintas si se busca por ISIN vs. nombre.
* Etiqueta fuente NAV (`Morningstar`, `FT`, `Investing`, etc.) visible.

---
## 🚀 Roadmap futuro

* [ ] Módulo de dividendos
* [ ] Módulo de splits
* [ ] Módulo de transacciones recurrentes
* [ ] Cálculo fiscal con compensación de plusvalías/minusvalías
* [ ] Login de usuario y encriptado local
* [ ] Paso a entorno cloud (Streamlit Sharing, Docker, etc.)
* [ ] Soporte multimoneda con histórico
* [ ] Control de calidad de fuentes y auditoría de cambios de NAV
