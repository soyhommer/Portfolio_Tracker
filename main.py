import streamlit as st
import os
import json
from utils.data_loader import cargar_carteras, seleccionar_cartera, crear_cartera_si_necesario, renombrar_cartera
from utils.transacciones import mostrar_tabla_transacciones, formulario_nueva_transaccion, importar_transacciones_excel, cargar_transacciones
from utils.general import mostrar_estado_general, calcular_estado_actual
from utils.ganancias import mostrar_ganancias_perdidas
from utils.flujos import mostrar_flujos
from utils.rentabilidad_frontend import mostrar_rentabilidad
from utils.evolucion import mostrar_evolucion_valor_cartera
from utils.benchmark import comparar_con_benchmark
from utils.config import CACHE_TTL_HORAS
from utils.formatting import mostrar_dataframe_formateado
from utils.historial_nav import mostrar_gestor_historicos_nav

import logging

# ✅ Configurar logging global de forma segura para Streamlit (evita duplicados en rerun)
logger = logging.getLogger()

if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    logging.debug("✅ Logging global configurado en nivel DEBUG")

# Configuración inicial
st.set_page_config(page_title="Gestor de Carteras", layout="wide")

# Cargar configuración
CONFIG_PATH = "config/settings.json"
if not os.path.exists(CONFIG_PATH):
    st.error("No se encontró el archivo de configuración. Asegúrate de tener settings.json en /config.")
    st.stop()

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    settings = json.load(f)

# Título principal
st.title("📈 Gestor de Carteras")

# Sección superior: selección y gestión de cartera
st.sidebar.header("Carteras disponibles")
carteras = cargar_carteras()
cartera_activa = seleccionar_cartera(carteras)

if cartera_activa:
    st.session_state['cartera'] = cartera_activa
else:
    st.warning("No hay carteras disponibles. Crea una para empezar.")

# Formulario siempre disponible
crear_cartera_si_necesario()

# Navegación entre pestañas
menu = st.sidebar.radio("Navegar a:", ["General", "Rentabilidad", "Ganancias y Pérdidas", "Flujos", "Transacciones", "Cargar Históricos NAV"])

if menu == "General":
    st.subheader(f"Resumen general - {cartera_activa}")

    from utils.nav_fetcher import refrescar_navs_si_expirados
    from datetime import datetime, timedelta
    from utils.config import CACHE_TTL_HORAS  # Asegúrate de tener esto definido

    # Estado actual
    df_transacciones = cargar_transacciones(cartera_activa)

    ahora = datetime.now()
    ultima = st.session_state.get("navs_ultima_actualizacion")

    if (
        ultima is None
        or not isinstance(ultima, datetime)
        or (ahora - ultima) > timedelta(hours=CACHE_TTL_HORAS)
    ):
        refrescar_navs_si_expirados(df_transacciones, cartera_activa)
        st.session_state["navs_ultima_actualizacion"] = ahora
        print(f"⏱️ NAVs actualizados automáticamente a las {ahora}")

    # Botón de actualización manual
    if st.button("🔄 Refrescar manualmente NAVs"):
        refrescar_navs_si_expirados(df_transacciones, cartera_activa, forzar=True)
        st.session_state["navs_ultima_actualizacion"] = datetime.now()
        st.success("✅ NAVs actualizados manualmente.")
        st.rerun()

    df_resultado = calcular_estado_actual(df_transacciones, cartera_activa)
    mostrar_dataframe_formateado(df_resultado)
    
    st.markdown("---")
  
            
elif menu == "Rentabilidad":
    st.subheader("Rentabilidad histórica")
    if "cartera" in st.session_state:
        mostrar_rentabilidad(st.session_state["cartera"])
    else:
        st.warning("Selecciona una cartera para ver su rentabilidad.")
        
elif menu == "Ganancias y Pérdidas":
    logger.info("📌 PESTAÑA SELECCIONADA: Ganancias / Pérdidas")
    st.subheader("Histórico de resultados")
    if "cartera" in st.session_state:
        logger.debug(f"✅ Cartera activa en sesión: {st.session_state['cartera']}")
        mostrar_ganancias_perdidas(st.session_state["cartera"])
    else:
        logger.warning("⚠️ No hay cartera en session_state")
        st.warning("Selecciona una cartera para visualizar los resultados.")
        
elif menu == "Flujos":
    st.subheader("Flujos trimestrales")
    if "cartera" in st.session_state:
        mostrar_flujos(st.session_state["cartera"])
    else:
        st.warning("Selecciona una cartera para visualizar los flujos.")
        
elif menu == "Transacciones":
    st.subheader("Historial de transacciones")
    if "cartera" in st.session_state:
        mostrar_tabla_transacciones(st.session_state["cartera"])
        formulario_nueva_transaccion(st.session_state["cartera"])
        importar_transacciones_excel(st.session_state["cartera"])
    else:
        st.warning("Selecciona una cartera para trabajar con transacciones.")

elif menu == "Cargar Históricos NAV":
    st.subheader("Cargar Históricos NAV")
    mostrar_gestor_historicos_nav(cartera_activa)