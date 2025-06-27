# AGENTS.md

## 📈 Proyecto: Gestor de Carteras Financieras

Aplicación local desarrollada en Python y Streamlit para el seguimiento y análisis de carteras personales. Inspirada en el gestor gratuito de Morningstar.

Permite cargar transacciones, calcular estado actual, analizar ganancias y pérdidas, consultar NAV en tiempo real desde varias fuentes, y visualizar resultados con tablas y gráficos interactivos.

---

## ⚙️ Tecnologías principales

- Python 3.10+
- Streamlit
- Pandas
- Requests, BeautifulSoup, lxml
- CSV como persistencia local
- Scraping de Morningstar, FT, Investing para NAV

---

## 📚 Arquitectura actual

- **Frontend**: Streamlit, todo en un solo flujo monolítico.
- **Backend**:
  - utils/ con módulos funcionales (nav_fetcher, ganancias, general, transacciones, etc.)
  - scraping por fuente
  - almacenamiento en CSV + caches en JSON
- Sin separación clara de lógica de negocio y visualización.

---

## 🛠️ Convenciones de código

- Estilo PEP8
- Funciones puras siempre que sea posible
- Tipado opcional (mypy-friendly)
- Logging preferido sobre prints (a mejorar)
- Modularidad por fuente de datos y funcionalidad
- Persistencia en CSV/JSON

---

## 🧭 Próximas tareas recomendadas

### ✅ General

- Refactorizar para separar **cálculos (lógica de negocio)** de **presentación (Streamlit)**.
- Crear estructura de **módulos backend** que se puedan importar y testear sin Streamlit.
- Mantener compatibilidad con la arquitectura actual durante la transición.

---

### ✅ Backend

- Extraer lógica de cálculo de rentabilidades, ganancias/pérdidas en funciones puras independientes.
- Generar **estructura de históricos**:
  - Carpetas o tablas separadas para NAV histórico por fuente.
  - Sistema de control de versiones / fechas para caches.
- Implementar validación de datos al cargar CSV.
- Unificar y documentar estrategia de caché (real, investing, morningstar, FT).

---

### ✅ Frontend (Streamlit)

- Simplificar main.py para que solo maneje navegación y UI.
- Crear componentes o vistas modulares para cada sección.
- Usar callbacks / botones para refresco de NAV y caches.
- Mejorar feedback al usuario (loaders, mensajes de error amigables).

---

### ✅ Pruebas y calidad

- Implementar tests unitarios para lógica de negocio.
- Separar funciones de scraping para permitir mocks en tests.
- Añadir linters y formateadores automáticos (black, flake8).

---

## ✅ Tareas prioritarias

1. Refactorizar cálculo de estado actual y ganancias/pérdidas fuera de Streamlit.
2. Diseñar estructura de almacenamiento de históricos de NAV con fecha y fuente.
3. Definir y documentar contratos entre frontend y backend.
4. Mejorar gestión de caché (invalidación, expiración, multi-fuente).
5. Modularizar vistas de Streamlit por funcionalidad.
6. Añadir logging estructurado.

---

## 🗂️ Estructura sugerida para futuro

/Portfolio_Tracker/
│
├── AGENTS.md
├── README.md
├── requirements.txt
├── main.py
├── app/ # Código Streamlit (frontend)
│ ├── pages/
│ └── components/
├── backend/ # Lógica de negocio
│ ├── calculators/
│ ├── data_sources/
│ └── models/
├── data/ # Persistencia local
│ ├── transacciones/
│ └── cache_nav_*.json
└── tests/ # Tests unitarios y funcionales

yaml
Copiar
Editar

---

## ✅ Notas para el Agente

- Priorizar la claridad y la modularidad del código.
- Mantener compatibilidad con CSV y estructura de datos local.
- Usar tipado y docstrings.
- Sugerir mejoras para scraping multi-fuente y fusión de resultados.