# 📈 Módulo de Rentabilidad - Especificación funcional

## 🎯 Objetivo
Calcular y mostrar la rentabilidad histórica de la cartera, integrando datos de:

- Transacciones (compra/venta, participaciones, precios)
- Históricos NAV (valores liquidativos por fecha)
- Benchmark de la cartera

---

## ⚙️ Funcionalidades clave

### ✅ Gráfica de rentabilidad a 12 meses
- **Series temporales (mensual):**
  - ✅ Línea continua de rentabilidad acumulada TWR
    - *Tooltip:* explicación de TWR (Time-Weighted Return)
  - ✅ Línea continua de rentabilidad acumulada MWR
    - *Tooltip:* explicación de MWR (Money-Weighted Return)
  - ✅ Línea continua del benchmark

- **Tabla asociada (12 meses):**
  - ✅ Medias mensuales de las 3 series

---

### ✅ Gráfica de rentabilidad anual (hasta 12 años)
- **Series temporales (anual):**
  - ✅ Línea continua de rentabilidad acumulada TWR
  - ✅ Línea continua de rentabilidad acumulada MWR
  - ✅ Línea del benchmark

- **Tabla asociada (12 años):**
  - ✅ Medias anuales de las 3 series

---

### ✅ Tabla de rentabilidades acumuladas
- Horizontes de tiempo:
  - 1 semana
  - 1 mes
  - 3 meses
  - 6 meses
  - YTD (Year-To-Date)
  - 3 años (anualizado)
  - 5 años (anualizado)
  - 10 años (anualizado)
  - Desde compra (anualizado)

---

### ✅ Tabla con activos actuales en cartera
- Misma estructura de rentabilidades acumuladas:
  - 1 semana
  - 1 mes
  - 3 meses
  - 6 meses
  - YTD
  - 3 años (anualizado)
  - 5 años (anualizado)
  - 10 años (anualizado)
  - Desde compra (anualizado)

---

## 🔗 Datos necesarios
- **Transacciones**
  - Fecha, tipo, participaciones, precio, gasto, moneda
- **Históricos NAV**
  - ISIN, fecha, price
- **Benchmark**
  - Evolución mensual/anual del índice de referencia

---

## 🧩 Integración requerida
- Usar módulo `transacciones.py` para cargar y procesar movimientos
- Usar módulo `historial_nav.py` para obtener precios históricos NAV
- Usar benchmarks definidos en configuración
- Consolidar NAV con transacciones para calcular valor de cartera en el tiempo
- Calcular TWR y MWR sobre series temporales

---

## 📌 Tooltips sugeridos
- **TWR (Time-Weighted Return):** Mide la rentabilidad eliminando el efecto de los flujos de efectivo, adecuado para comparar con benchmarks.
- **MWR (Money-Weighted Return):** Incluye el efecto de los flujos de efectivo reales, refleja la rentabilidad efectiva del inversor.

---

## 🛠️ Pendiente de implementación
- Cálculo de series temporales TWR y MWR (mensual, anual)
- Cálculo de benchmark histórico
- Tablas de medias mensuales/anuales
- Tablas de acumulados por periodo
- Tablas de acumulados por activo

---

## ✅ Resultado esperado
- Visualización intuitiva en Streamlit
- Gráficas interactivas con líneas y tooltips explicativos
- Tablas claras con resultados por periodo
- Integración fluida con otras pestañas del gestor
