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

#### 🆕 Módulo de Divisas (FX)

##### Descripción
Permite convertir todos los NAVs, valoraciones de cartera y flujos de caja a la **moneda base de la cartera**. Soporta carteras en EUR, USD, GBP, etc., calculando conversiones consistentes a partir de un pivot EUR usando datos oficiales del BCE.

##### Funcionalidades
- Descarga y parsing automático del histórico de tipos de cambio del BCE.
- Archivo único de referencia (`euro_forex.json`) con todos los rates históricos en base EUR.
- Conversión en cualquier fecha entre pares de divisas usando EUR como pivot.
- Actualización automática o bajo demanda.
- Fallback en frontend para recarga manual en caso de corrupción de datos.

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

cPortfolio_Tracker/
│
├── main.py                  # Punto de entrada de la app Streamlit
├── requirements.txt         # Dependencias del proyecto
│
├── data/
│   ├── benchmark/           # Datos de benchmarks por cartera
│   ├── nav_historico/       # Históricos NAV por ISIN
│   ├── outputs/             # Salidas exportadas (PDF/Excel u otros)
│   ├── transacciones/       # CSVs de transacciones por cartera
│   ├── activos_cache.json   # Cache de ISINs/nombres
│   ├── cache_nav_ft.json    # Cache de NAVs desde FT
│   ├── cache_nav_investing.json
│   ├── cache_nav_morningstar.json
│   ├── cache_nav_real.json
│   └── carteras.json        # Definición de carteras
│
└── utils/
    ├── __pycache__/         # Archivos compilados Python
    │
    ├── benchmark.py         # Carga y manejo de benchmarks
    ├── config.py            # Paths y constantes globales
    ├── data_loader.py       # Carga/guardado genérico de datos locales
    ├── evolucion.py         # (opcional) lógica para evolución de carteras
    ├── flujos.py            # Procesamiento de flujos netos
    ├── formatting.py        # Formateadores y helpers UI
    ├── ft_fetcher.py        # Scraping de NAVs de FT.com
    ├── ganancias.py         # Cálculo de ganancias/pérdidas por activo
    ├── general.py           # Estado general de cartera y NAVs
    ├── historial_nav.py     # Validación y fusión de históricos NAV
    ├── investing_fetcher.py # Scraping de Investing.com
    ├── merge_nav_data.py    # Algoritmo de merge y validación cruzada de NAVs
    ├── morningstar_fetcher.py # Scraping de Morningstar.es
    ├── nav_cache.py         # Manejador de caché de NAVs
    ├── nav_fetcher.py       # Orquestador para buscar NAVs
    ├── rentabilidad_backend.py # Cálculo de rentabilidades TWR y ponderadas
    ├── rentabilidad_frontend.py # Interfaz Streamlit para el módulo de rentabilidades
    └── transacciones.py     # CRUD de transacciones con validación
    ├── fx_loader.py             # Carga y consulta de rates históricos
    └── fx_updater.py           # Descarga y parsing desde el BCE

## 📝 Guía rápida de instalación y ejecución

### 1️⃣ Requisitos previos

* **Python 3.10 o superior** instalado en tu máquina.
* (Opcional pero recomendado) Tener **Git** instalado para clonar el repositorio.

---

### 2️⃣ Descargar el proyecto

**Opcion A: Clonar con Git**

```bash
git clone https://github.com/soyhommer/Portfolio_Tracker.git
cd Portfolio_Tracker
```

**Opcion B: Descargar ZIP**

* Haz clic en **Code > Download ZIP** en GitHub.
* Descomprime el archivo en tu ordenador.
* Abre la carpeta descomprimida en tu terminal o editor.

---

### 3️⃣ Crear un entorno virtual

**En Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

**En macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

✅ Verás el prompt del terminal con el entorno virtual activado.

---

### 4️⃣ Instalar las dependencias

Asegúrate de estar en la carpeta raíz del proyecto (donde está `requirements.txt`):

```bash
pip install -r requirements.txt
```

✅ Esto descargará e instalará todos los paquetes necesarios.

---

### 5️⃣ Ejecutar la aplicación

Para iniciar la app localmente en tu navegador:

```bash
streamlit run main.py
```

✅ Esto abrirá automáticamente la interfaz en tu navegador predeterminado.

---

### 6️⃣ Salir del entorno virtual

Cuando termines de trabajar, puedes desactivar el entorno con:

```bash
deactivate
```

---

### ⚡️ Notas adicionales

* Para **actualizar dependencias** en el futuro:

```bash
pip install --upgrade -r requirements.txt
```

* Si quieres trabajar en otro ordenador, repite estos mismos pasos.

---

🌟 ¡Y listo! Con estos pasos tendrás el proyecto funcionando localmente para gestionar y analizar tus carteras de inversión de forma sencilla.

---

## ✅ Novedades y Funcionalidades Implementadas

* **Gestión Inteligente de NAVs y Cacheo**
  - Búsqueda por nombre o ISIN con fusión de múltiples fuentes.
  - Cacheo local con control de expiración.
  - Scrapers independientes para Morningstar, FT y Investing.
  - Algoritmo de validación cruzada (`merge_nav_data`) priorizando la calidad del dato.

* **Enriquecimiento Automático de Transacciones**
  - Detección y asignación automática del ISIN por nombre del activo.
  - Persistencia de ISINs nuevos en caché tras edición o importación.
  - Formulario de nueva transacción con validación y sugerencias.

* **Edición avanzada de Transacciones**
  - Tabla editable con ordenación ascendente/descendente por columnas.
  - Columna de selección (checkbox) para borrado en lote.
  - Icono 🗑️ para borrado individual.
  - Botón para guardar todas las ediciones.
  - Importación masiva desde Excel con validación de columnas.

* **Autocompletado inteligente de NAV**
  - Al agregar transacción con Precio = 0, busca NAV exacto o más cercano (hasta 7 días antes).
  - Notifica al usuario el valor asignado.

* **Validación de Cobertura NAV con Tolerancia**
  - Verificación de cobertura NAV para todas las transacciones.
  - Marca como cubiertas fechas con NAV exacto o ≤7 días anterior.
  - Reporte tabulado en la interfaz de las fechas que requieren históricos adicionales.

* **Gestión Completa de Históricos NAV**
  - Subida incremental de tramos de Investing.com.
  - Validación del formato esperado (decimal europeo `,` soportado).
  - Fusión automática de fechas sin duplicados.
  - Cacheo y sugerencia de nombres de activo por ISIN.

* **Mensajes Aclaratorios en la UI**
  - Nota bajo FileUploader explicando formato Investing.com esperado en INGLÉS.
  - Soporte automático de `,` como decimal y `;` como separador.

* **📈 Mejoras en el Módulo de Rentabilidades (Actualización 2025)**
  - Gráficas con selector de horizonte dinámico (3M, 6M, 1Y, 3Y, 5Y, Desde inicio).
  - Ajuste automático de frecuencia (semanal o mensual) según el horizonte elegido.
  - Series de TWR y Rentabilidad Ponderada rebased desde 0 al inicio del período para mostrar rentabilidad acumulada real.
  - Hover unificado en las gráficas mostrando todas las series al pasar el puntero por la fecha.
  - Leyenda desplazada a la parte inferior para optimizar el ancho útil.
  - KPI generales siempre calculados para toda la vida de la cartera (no afectados por el filtro de horizonte).
  - Tablas de rentabilidad mensual y rolling returns independientes del horizonte seleccionado.

* **Rentabilidad y Ganancias Realistas**
  - Cálculo de NAV actual y comparación con histórico de compra.
  - Ganancia/pérdida total por activo, % sobre desembolso, reembolsos y valoración de mercado.
  - Rentabilidad ponderada por NAV y fecha.

* **Tabla de Rentabilidades Rolling y Mensual**
  - Rolling returns a 7D, 30D, 90D, 180D, YTD, 1 año, 3 años*, 5 años*, 10 años*, Desde Compra*.
  - Indicadores anualizados en columnas marcadas con *.
  - Filtrado para mostrar solo activos con participaciones > 0 en la fecha actual.
  - Tolerancia de ±30 días en búsqueda de precios históricos.
  - Poblado automático de históricos NAV solo desde la primera fecha real disponible sin extrapolación.
  - Ajuste para evitar resultados inflados en carteras con historia corta o flujos variables.
  - Formato robusto en Streamlit, evitando errores con None o NaN, y celdas vacías claras.

* **Validaciones y Manejo de Errores**
  - Validación defensiva del CSV de transacciones.
  - Mensajes informativos en consola y Streamlit ante errores de scraping o parsing.

* **Trazabilidad y Depuración**
  - Consola con trazas de llamadas a `merge_nav_data`.
  - Diferenciación en respuestas si se busca por ISIN o nombre.
  - Etiqueta visible de la fuente NAV utilizada.

---

## 🚀 Roadmap futuro (por prioridades)

- Validación de stock negativo de transacciones via Excel y verificación de "Vental total" con fecha anterior a ultima venta por las 3 vías (edicion formulario/nueva transaccion/excel)
- Cálculo fiscal con FIFO/LIFO y compensación de plusvalías. Ajustar calculo de rentabilidad con RoR, TWT y MWR con el balance FIFO de cada activo.
- Datos Divisas y cambios para expresarlo todo en la moneda base de la cartera.
- Terminar de pasar todas direcciones de archivos de datos en config.py y quitarlas de modulos
- Módulo de dividendos y splits.
- Gestión de transacciones recurrentes.
- Sistema multiusuario con login y base de datos local o en la nube.
- Exportación en PDF/Excel con formato limpio.
- Despliegue en la nube (Streamlit Sharing, Docker, etc.).
- Control de calidad de fuentes y auditoría de cambios de NAV.
- Integración con APIs de brokers o bancos.
