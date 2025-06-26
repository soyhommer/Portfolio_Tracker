# 馃搱 Cartera Inversor Personal (CIP) - MVP Streamlit

## 馃攳 Descripci贸n

Aplicaci贸n local para el seguimiento y edici贸n de carteras de inversi贸n personales, centrada en fondos UCITS, planes de pensiones espa帽oles (DGS) y acciones internacionales. Inspirada en la cartera gratuita de Morningstar, implementada r谩pidamente usando **Streamlit** y **Python**.

---

## 鈿欙笍 Funcionalidades incluidas (versi贸n MVP)

### 1. Gesti贸n de Carteras

* Crear nuevas carteras: nombre, moneda base, benchmark.
* Editar nombre o eliminar cartera existente.
* Men煤 desplegable superior para seleccionar cartera activa.

### 2. Seguimiento

#### General

* Tabla con activos actuales: nombre, 煤ltimo NAV, participaciones, valor, peso, fecha.
* Integraci贸n de NAVs en tiempo real desde m煤ltiples fuentes (ver secci贸n fuentes).

#### Rentabilidad

* Rentabilidad mensual (total, personal, 铆ndice) con gr谩fica de 11 meses + actual.
* Rentabilidad anual (total, personal, 铆ndice) con gr谩fica de 10 a帽os + YTD.
* Tabla resumen con rentabilidades por periodo: 1s, 1m, 3m, 6m, YTD, 1a, 3a, 5a, 10a, desde compra.
* Tabla de fondos en cartera con %A帽o, %3a, volatilidad, etc.

#### Ganancias / P茅rdidas

* Tabla con historial de activos desde inicio: participaciones, desembolsos, reembolsos, valor mercado, ganancia/p茅rdida absoluta y %.

#### Flujos

* Tabla trimestral con compras netas, ventas netas, gastos, flujo neto.

### 3. Edici贸n de Transacciones

* Tabla editable de transacciones (CRUD).
* Formulario para a帽adir nuevas transacciones: activo, tipo, fecha, moneda, precio, gasto, etc.
* Importaci贸n desde Excel.
* Ordenaci贸n por cualquier columna.

### 4. Persistencia

* Todas las carteras, transacciones y activos se guardan localmente (formato CSV).
* Sistema de cach茅 para NAVs (por nombre o ISIN) por fuente.

---

## 馃敆 Fuentes de Datos

| Fuente                       | Tipo de activos soportados                  | M茅todo       | Prioridad | Calidad     |
| ---------------------------- | ------------------------------------------- | ------------ | --------- | ----------- |
| **Morningstar.es**           | Fondos UCITS, PPS espa帽oles                 | Scraping     | 馃 Alta    | Muy alta    |
| **FT.com (Financial Times)**| Fondos UCITS internacionales                | Scraping     | 馃 Media   | Alta        |
| **Investing.com**            | Fondos UCITS, gr谩ficos                      | Scraping     | 馃 Baja    | Media       |
| **FundAPI.io**               | Fondos UCITS europeos (ISIN, VL, categor铆a) | API          | Secundaria| Alta        |
| **CNMV**                     | Fondos y PPS registrados en Espa帽a          | Scraping     | Backup    | Alta        |
| **Yahoo Finance (yfinance)** | Acciones, ETFs, algunos fondos              | Python       | Opcional  | Inconsistente|

* El sistema selecciona autom谩ticamente el mejor dato entre las fuentes seg煤n calidad y disponibilidad.
* Las tasas de cambio hist贸ricas se consultan mediante API (ECB, Open Exchange Rates) y se almacenan en cada transacci贸n.

---

## 馃搮 Tecnolog铆as utilizadas

### Backend / L贸gica:

* Python 3.10+
* Pandas, Numpy
* Requests, BeautifulSoup4, Unidecode
* M贸dulos de scraping personalizados
* CSV para persistencia local

### Frontend / Interfaz:

* Streamlit
* streamlit-aggrid (para tablas interactivas)
* Matplotlib o Plotly para gr谩ficas

---

## 馃洜锔?Arquitectura de archivos

```
cartera_streamlit/
|
鈹溾攢鈹€ data/
鈹?  鈹溾攢鈹€ transacciones/            # CSV por cartera
鈹?  鈹斺攢鈹€ cache_nav_*.json          # Cache por fuente
|
鈹溾攢鈹€ main.py                       # Punto de entrada Streamlit
鈹溾攢鈹€ utils/
鈹?  鈹溾攢鈹€ data_loader.py            # Lectura/escritura de carteras
鈹?  鈹溾攢鈹€ nav_fetcher.py            # Funci贸n unificada get_nav_real
鈹?  鈹溾攢鈹€ investing_fetcher.py      # Scraper de Investing.com
鈹?  鈹溾攢鈹€ morningstar_fetcher.py    # Scraper de Morningstar.es
鈹?  鈹溾攢鈹€ ft_fetcher.py             # Scraper de FT.com
鈹?  鈹溾攢鈹€ merge_nav_data.py         # L贸gica de fusi贸n de NAVs
鈹?  鈹溾攢鈹€ ganancias.py              # C谩lculo de ganancia/p茅rdida
鈹?  鈹溾攢鈹€ general.py                # Estado actual de la cartera
鈹?  鈹斺攢鈹€ rentabilidad.py           # Rentabilidad por periodo
```

---

## 馃殌 Roadmap futuro

* [ ] M贸dulo de dividendos
* [ ] M贸dulo de splits
* [ ] M贸dulo de transacciones recurrentes
* [ ] C谩lculo fiscal con compensaci贸n de plusval铆as/minusval铆as
* [ ] Login de usuario y encriptado local
* [ ] Paso a entorno cloud (Streamlit Sharing, Docker, etc.)
* [ ] Soporte multimoneda con hist贸rico
* [ ] Control de calidad de fuentes y auditor铆a de cambios de NAV
