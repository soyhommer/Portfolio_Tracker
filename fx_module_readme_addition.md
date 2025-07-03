## 🆕 Módulo de Divisas (FX)

### Descripción
Permite convertir todos los NAVs, valoraciones de cartera y flujos de caja a la **moneda base de la cartera**. Soporta carteras en EUR, USD, GBP, etc., calculando conversiones consistentes a partir de un pivot EUR usando datos oficiales del BCE.

### Funcionalidades
- Descarga y parsing automático del histórico de tipos de cambio del BCE.
- Archivo único de referencia (`euro_forex.json`) con todos los rates históricos en base EUR.
- Conversión en cualquier fecha entre pares de divisas usando EUR como pivot.
- Actualización automática o bajo demanda.
- Fallback en frontend para recarga manual en caso de corrupción de datos.

### Arquitectura de Archivos (actualizada)

Portfolio_Tracker/
│
├── main.py
├── requirements.txt
│
├── data/
│   ├── benchmark/
│   ├── nav_historico/
│   ├── outputs/
│   ├── transacciones/
│   ├── fx_rates/
│   │   └── euro_forex.json     # Tipos de cambio históricos en base EUR
│   ├── activos_cache.json
│   ├── cache_nav_ft.json
│   ├── cache_nav_investing.json
│   ├── cache_nav_morningstar.json
│   ├── cache_nav_real.json
│   └── carteras.json
│
└── utils/
    ├── benchmark.py
    ├── config.py
    ├── data_loader.py
    ├── evolucion.py
    ├── flujos.py
    ├── formatting.py
    ├── ft_fetcher.py
    ├── ganancias.py
    ├── general.py
    ├── historial_nav.py
    ├── investing_fetcher.py
    ├── merge_nav_data.py
    ├── morningstar_fetcher.py
    ├── nav_cache.py
    ├── nav_fetcher.py
    ├── rentabilidad_backend.py
    ├── rentabilidad_frontend.py
    ├── transacciones.py
    ├── fx_loader.py             # Carga y consulta de rates históricos
    └── fx_updater.py           # Descarga y parsing desde el BCE

### Actualizaciones en Frontend y Backend
- Comprobación automática al iniciar la app: verifica si hay datos actualizados, descarga si faltan.
- Conversión de todos los valores a la moneda base en el cálculo de rentabilidades y flujos.
- Botón opcional en Streamlit para refrescar manualmente los rates.

### Dependencias sugeridas
- pandas, requests para descarga y parsing.
- Cron (opcional) para actualización diaria en servidor.

