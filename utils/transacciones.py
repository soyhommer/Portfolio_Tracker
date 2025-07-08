import os
import re
import logging
import pandas as pd
import streamlit as st
from utils.nav_fetcher import get_nav_real as get_nav
from utils.nav_fetcher import cargar_cache_nav
from utils.nav_fetcher import actualizar_cache_isin
from utils.config import TRANSACCIONES_DIR, NAV_HISTORICO_DIR

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")
logger = logging.getLogger(__name__)

# DATA_DIR = "data"
# TRANSACCIONES_DIR = os.path.join(DATA_DIR, "transacciones")

def obtener_ruta_transacciones(cartera):
    return os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")

def cargar_transacciones(cartera):
    path = obtener_ruta_transacciones(cartera)
    columnas_correctas = ["Posición", "ISIN", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"]

    if os.path.exists(path):
        df = pd.read_csv(path)
        # Quitar columnas no esperadas
        df = df[[col for col in df.columns if col in columnas_correctas]]

        # Asegurar todas las columnas correctas
        for col in columnas_correctas:
            if col not in df.columns:
                if col in ["Posición", "ISIN", "Tipo", "Moneda"]:
                    df[col] = ""
                else:
                    df[col] = 0.0

        # Reordenar
        df = df[columnas_correctas]
        return df

    else:
        return pd.DataFrame(columns=columnas_correctas)


def guardar_transacciones(cartera, df):
    path = obtener_ruta_transacciones(cartera)
    df.to_csv(path, index=False)


# @st.cache_data
# def extraer_isin(nombre):
    # datos = get_nav(nombre)
    # if datos and datos.get("isin") and datos.get("nav") is not None:
        # return datos["isin"]
    # return "—"

@st.cache_data
def extraer_isin(nombre, cartera):
    cache = cargar_cache_nav(cartera)
    datos = cache.get(nombre)
    if datos and datos.get("isin") and datos.get("nav") is not None:
        return datos["isin"]
    return "—"

def validar_stock_no_negativo(df_transacciones: pd.DataFrame) -> list:
    df_transacciones = df_transacciones.copy()
    df_transacciones = df_transacciones.sort_values(["ISIN", "Fecha"])

    problemas = []

    for isin, group in df_transacciones.groupby("ISIN"):
        saldo_participaciones = 0.0

        for _, row in group.iterrows():
            tipo = str(row["Tipo"]).lower()
            participaciones = row["Participaciones"]

            if pd.isna(participaciones):
                participaciones = 0

            if tipo.startswith("compra"):
                saldo_participaciones += participaciones
            elif tipo.startswith("venta"):
                saldo_participaciones -= participaciones

            if saldo_participaciones < -1e-4:
                problemas.append(isin)
                break  # ya no hace falta seguir revisando este ISIN

    return problemas

def mostrar_tabla_transacciones(cartera):
    
    st.markdown(f"### Transacciones de la cartera: {cartera}")

    # Cargar datos del CSV
    df = cargar_transacciones(cartera)

    # Filtrar columnas válidas
    columnas_correctas = [
        "Seleccionar", "Posición", "ISIN", "Tipo", 
        "Participaciones", "Fecha", "Moneda", "Precio", "Gasto", "Valor operación"
    ]
    df = df[[col for col in df.columns if col in columnas_correctas]]

    # Añadir columnas faltantes
    for col in columnas_correctas:
        if col not in df.columns:
            if col == "Seleccionar":
                df[col] = False
            elif col in ["Posición", "ISIN", "Tipo", "Moneda", "Fecha"]:
                df[col] = ""
            else:
                df[col] = 0.0

    # Reordenar
    df = df[columnas_correctas]
                                                                 
    df["Valor operación"] = df["Participaciones"] * df["Precio"] + df["Gasto"]
    df["Valor operación"] = df["Valor operación"].round(2)

    # Reordenar columnas para colocar 'Valor operación' después de 'Gasto'
    cols = df.columns.tolist()
    if "Gasto" in cols and "Valor operación" in cols:
        gasto_idx = cols.index("Gasto")
        cols.insert(gasto_idx + 1, cols.pop(cols.index("Valor operación")))
        df = df[cols]

    # Validación defensiva de columna clave
    if "Posición" not in df.columns:
        st.error("❌ No se encuentra la columna 'Posición' en el archivo de transacciones.")
        return df

    if df.empty:
        st.warning("⚠️ La cartera no tiene transacciones registradas.")
        return df

    # Asegurar tipo fecha
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.date

    # Limpieza preventiva de caracteres invisibles en ISIN
    if "ISIN" in df.columns:
        df["ISIN"] = df["ISIN"].astype(str).apply(
            lambda x: x.strip().replace("\u200b", "").replace("\u00a0", "") if isinstance(x, str) else x
        ).replace("—", None)

    def es_isin_valido(x):
        return isinstance(x, str) and x.strip() != "" and x != "—"

    if "ISIN" not in df.columns:
        df["ISIN"] = df["Posición"].apply(lambda nombre: extraer_isin(nombre, cartera))
    else:
        df["ISIN"] = df["ISIN"].where(df["ISIN"].apply(es_isin_valido))
        df["ISIN"] = df["ISIN"].fillna(df["Posición"].apply(lambda nombre: extraer_isin(nombre, cartera)))

    # Colocar ISIN justo después de "Posición"
    cols = df.columns.tolist()
    if "ISIN" in cols and "Posición" in cols:
        cols.insert(cols.index("Posición") + 1, cols.pop(cols.index("ISIN")))
        df = df[cols]

    # Añadir columna de selección si no existe
    if "Seleccionar" not in df.columns:
        df.insert(0, "Seleccionar", False)

    st.markdown("**✔️ Edita directamente las transacciones. Usa el icono 🗑️ para borrar filas individualmente y la casilla 'Seleccionar' para eliminar en lote. El menú de columna permite ordenar asc/desc:**")

    df_editado = st.data_editor(
        df,
        use_container_width=True,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("Seleccionar"),
            "Fecha": st.column_config.DateColumn(
                label="Fecha",
                format="YYYY-MM-DD",
                required=True
            ),
            "Moneda": st.column_config.SelectboxColumn(
                label="Moneda",
                options=["EUR", "USD", "GBP", "CHF", "JPY"],
                required=True
            ),
            "Tipo": st.column_config.SelectboxColumn(
                label="Tipo",
                options=["Compra", "Venta", "Venta total"],
                required=True
            ),
        },
    )

    # Botón para borrar filas seleccionadas
    if st.button("🗑️ Eliminar transacciones seleccionadas"):
        seleccionadas = df_editado[df_editado["Seleccionar"]]
        if seleccionadas.empty:
            st.warning("⚠️ No se han marcado transacciones para eliminar.")
        else:
            df_filtrado = df_editado[df_editado["Seleccionar"] == False].drop(columns=["Seleccionar"])
            guardar_transacciones(cartera, df_filtrado)
            st.success(f"✅ Se eliminaron {len(seleccionadas)} transacciones.")
            st.rerun()

    # Botón para guardar todas las ediciones
    if st.button("💾 Guardar cambios en transacciones"):
    
        df_guardar = df_editado.drop(columns=["Seleccionar"])

        if not validar_stock_no_negativo(df_guardar):
            st.error("❌ Error: hay ventas que exceden el stock disponible. Corrige antes de guardar.")
            return
        
        guardar_transacciones(cartera, df_guardar)

        for _, row in df_guardar.iterrows():
            nombre = row["Posición"]
            isin = row.get("ISIN")
            if isinstance(nombre, str) and isinstance(isin, str) and isin.strip() and isin != "—":
                actualizar_cache_isin(nombre, isin, cartera)


        st.success("✅ Cambios guardados correctamente.")
        st.rerun()

    return df

def buscar_precio_historico_cercano(isin, fecha_transaccion, nav_historico_dir, dias_max=7):
    """
    Busca en histórico NAV el precio más cercano anterior a la fecha_transaccion,
    siempre que esté a 7 días o menos.
    """
    path = nav_historico_dir / f"{isin}.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path)
    if "Date" not in df.columns or "Price" not in df.columns:
        return None

    # Asegurar fechas en datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # ✅ Convertir fecha_transaccion a Timestamp para evitar error de tipo
    fecha_transaccion = pd.Timestamp(fecha_transaccion)

    # Filtrar fechas anteriores o iguales
    df = df[df["Date"] <= fecha_transaccion]

    if df.empty:
        return None

    # Elegir fecha más cercana anterior
    df["diff_days"] = (fecha_transaccion - df["Date"]).dt.days
    df = df[df["diff_days"] >= 0]
    df = df.sort_values("diff_days")

    if df.empty:
        return None

    closest = df.iloc[0]
    if closest["diff_days"] <= dias_max:
        return closest["Price"]
    else:
        return None


def formulario_nueva_transaccion(cartera: str) -> None:
    """
    Formulario de Streamlit para añadir manualmente una nueva transacción a la cartera.
    Valida stock antes de guardar. Autocompleta ventas totales.
    """
    st.markdown("---")
    st.subheader("➕ Añadir nueva transacción")

    # Inicializar feedback
    if "feedback_tipo" not in st.session_state:
        st.session_state["feedback_tipo"] = ""
    if "feedback_mensaje" not in st.session_state:
        st.session_state["feedback_mensaje"] = ""

    df_transacciones = cargar_transacciones(cartera)

    with st.form(key="form_transaccion"):
        col1, col2, col3 = st.columns(3)

        with col1:
            identificador = st.text_input(
                label="ISIN / Ticker / Código",
                value="",
                help="Código identificativo del activo (ISIN, Ticker u otro)."
            )
            tipo = st.selectbox("Tipo", ["Compra", "Venta", "Venta total"])

        with col2:
            nombre = st.text_input(
                label="Nombre del activo",
                value="",
                help="Nombre del fondo, acción, PP, ETF, etc."
            )
            participaciones = st.number_input("Participaciones", min_value=0.0001, format="%.4f")
            fecha = st.date_input("Fecha")

        with col3:
            moneda = st.selectbox("Moneda", ["EUR", "USD", "GBP", "CHF", "JPY"])
            precio = st.number_input(
                label="Precio unitario",
                min_value=0.0,
                value=0.0,
                format="%.4f",
                help="Si se deja en 0 se intentará completar con histórico NAV."
            )
            gasto = st.number_input("Gasto (opcional)", min_value=0.0, format="%.2f", value=0.0)

        submitted = st.form_submit_button("Añadir transacción")

        if submitted:
            
            logger.debug("==== NUEVO SUBMIT DE FORMULARIO ====")
            logger.debug(f"Tipo: {tipo}")
            logger.debug(f"ISIN: {identificador}")
            logger.debug(f"Participaciones input: {participaciones}")
            logger.debug(f"Fecha: {fecha}")


            # Limpiar feedback previo
            st.session_state["feedback_tipo"] = ""
            st.session_state["feedback_mensaje"] = ""

            mensajes_autocompletado = []

            if not identificador.strip():
                st.session_state["feedback_tipo"] = "error"
                st.session_state["feedback_mensaje"] = "❌ El campo ISIN / Ticker / Código es obligatorio."
                return

            # Verificar saldo actual antes de agregar
            saldo_actual = obtener_participaciones_actuales(identificador, fecha, cartera)
            logger.debug(f"Saldo actual para {identificador} en {fecha}: {saldo_actual:.6f}")


            if tipo.lower() == "venta total":
                logger.debug("Modo venta total detectado")
                if saldo_actual <= 0.0:
                    logger.error("Venta total rechazada por saldo <= 0")
                    st.session_state["feedback_tipo"] = "error"
                    st.session_state["feedback_mensaje"] = (
                        "❌ No hay participaciones disponibles para Venta total."
                    )
                    return
                participaciones = saldo_actual
                logger.debug(f"Participaciones asignadas en venta total: {participaciones:.6f}")
                mensajes_autocompletado.append(
                    f"✔️ Venta total: se asignaron {participaciones:.4f} participaciones."
                )

            elif tipo.lower() == "venta":
                logger.debug("Modo venta normal detectado")
                logger.debug(f"Participaciones solicitadas: {participaciones:.6f}, saldo disponible: {saldo_actual:.6f}")
                if participaciones - saldo_actual > 1e-4:
                    st.session_state["feedback_tipo"] = "error"
                    st.session_state["feedback_mensaje"] = (
                        f"❌ No tienes suficientes participaciones para vender.\n"
                        f"Stock disponible a {fecha}: {saldo_actual:.4f}\n"
                        f"Participaciones pedidas: {participaciones:.4f}"
                    )
                    st.rerun()


            # Autocompletar nombre si está vacío
            if not nombre.strip():
                datos_nav = get_nav(identificador)
                if datos_nav and "nombre" in datos_nav:
                    nombre = datos_nav["nombre"]
                    mensajes_autocompletado.append(f"✔️ Nombre autocompletado: {nombre}")
                else:
                    mensajes_autocompletado.append("⚠️ No se pudo autocompletar el nombre del activo.")

            # Autocompletar precio si está en 0
            if precio == 0.0:
                precio_nav = buscar_nav_para_transaccion(identificador, fecha, NAV_HISTORICO_DIR)
                if precio_nav is not None:
                    precio = precio_nav
                    mensajes_autocompletado.append(
                        f"✔️ Precio autocompletado desde histórico NAV: {precio:.4f}"
                    )
                else:
                    precio_cercano = buscar_precio_historico_cercano(
                        isin=identificador,
                        fecha_transaccion=fecha,
                        nav_historico_dir=NAV_HISTORICO_DIR,
                        dias_max=7
                    )
                    if precio_cercano is not None:
                        precio = precio_cercano
                        mensajes_autocompletado.append(
                            f"✔️ Precio autocompletado (≤7 días antes): {precio:.4f}"
                        )
                    else:
                        mensajes_autocompletado.append(
                            "⚠️ No se encontró NAV para este activo. Precio dejado en 0."
                        )

            # ✅ CONSTRUYE SOLO SI PASÓ TODO
            nueva_fila = {
                "Posición": nombre,
                "ISIN": identificador,
                "Tipo": tipo,
                "Participaciones": participaciones,
                "Fecha": fecha,
                "Moneda": moneda,
                "Precio": precio,
                "Gasto": gasto
            }

            logger.debug("Datos finales para nueva fila:")
            logger.debug({
                "Posición": nombre,
                "ISIN": identificador,
                "Tipo": tipo,
                "Participaciones": participaciones,
                "Fecha": fecha,
                "Moneda": moneda,
                "Precio": precio,
                "Gasto": gasto
            })

            # Simula la tabla final tras añadir
            df_simulado = pd.concat([df_transacciones, pd.DataFrame([nueva_fila])], ignore_index=True)
            logger.debug("Validando stock en DataFrame simulado con la nueva fila agregada")

            # Validación defensiva: saldo no negativo
            if tipo.lower() == "compra":
                logger.debug("Validando saldo en DataFrame simulado para compra")
                df_simulado = pd.concat([df_transacciones, pd.DataFrame([nueva_fila])], ignore_index=True)
                problemas = validar_stock_no_negativo(df_simulado)
                if problemas:
                    logger.error(f"Validación de saldo negativa. Problemas encontrados: {problemas}")
                    st.session_state["feedback_tipo"] = "error"
                    st.session_state["feedback_mensaje"] = (
                        "❌ La transacción NO se ha guardado porque crearía participaciones negativas en:\n"
                        + "\n".join(f"- {fondo}" for fondo in problemas)
                        + "\n✏️ Corrige los datos del formulario o añade otras transacciones válidas."
                    )
                    return
            else:
                # Para venta o venta total NO validas después de agregar.
                logger.debug("Saltando validación post-agregado para venta/venta total")

            # Guardar SIEMPRE al final
            guardar_transacciones(cartera, df_simulado)
            logger.debug("Guardando transacciones en CSV")

            mensaje_final = "✅ Transacción añadida correctamente."
            if mensajes_autocompletado:
                mensaje_final += "\n\n" + "\n".join(mensajes_autocompletado)

            st.session_state["feedback_tipo"] = "success"
            st.session_state["feedback_mensaje"] = mensaje_final
            st.rerun()

    # Mostrar feedback fuera del form
    if st.session_state["feedback_mensaje"]:
        if st.session_state["feedback_tipo"] == "error":
            st.error(st.session_state["feedback_mensaje"])
        elif st.session_state["feedback_tipo"] == "success":
            st.success(st.session_state["feedback_mensaje"])
        elif st.session_state["feedback_tipo"] == "warning":
            st.warning(st.session_state["feedback_mensaje"])
        else:
            st.info(st.session_state["feedback_mensaje"])


def buscar_nav_para_transaccion(isin, fecha, nav_historico_dir):
    """
    Busca en el histórico NAV el valor para un ISIN en la fecha dada.
    Devuelve el Price si se encuentra, o None.
    """
    try:
        path = nav_historico_dir / f"{isin}.csv"
        if not path.exists():
            return None
        df = pd.read_csv(path)
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        match = df[df["Date"] == pd.to_datetime(fecha)]
        if not match.empty:
            return match.iloc[0]["Price"]
    except Exception as e:
        print(f"Error buscando NAV: {e}")
    return None
            
def importar_transacciones_excel(cartera):
    st.markdown("---")
    st.subheader("📥 Importar transacciones desde Excel")
    archivo = st.file_uploader("Selecciona un archivo Excel", type=["xlsx"])    
    if archivo is not None:
        try:
            df_excel = pd.read_excel(archivo)
            columnas_esperadas = ["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"]
            if not all(col in df_excel.columns for col in columnas_esperadas):
                st.error("El archivo no contiene todas las columnas requeridas.")
                return
            df = cargar_transacciones(cartera)
            df = pd.concat([df, df_excel], ignore_index=True)
            
            from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
            df = limpiar_isin(df)
            validar_isin_vs_nombre(df)                     

            #Vigilancia de stock de participaciones
            problemas = validar_stock_no_negativo(df)
            if problemas:
                st.error("❌ La transacción NO se ha guardado porque crearía participaciones negativas en:")
                for fondo in problemas:
                    st.warning(f"- {fondo}")
                st.info("✏️ Corrige los datos del formulario o añade otras transacciones válidas.")
                
                # Desbloquear botón
                if "form_transaccion" in st.session_state:
                    st.session_state["form_transaccion"] = False

                # Limpiar campos si quieres (opcional)
                st.session_state.pop("ISIN / Ticker / Código", None)
                st.session_state.pop("Nombre del activo", None)
                st.session_state.pop("Participaciones", None)
                st.session_state.pop("Precio unitario", None)
                st.session_state.pop("Gasto (opcional)", None)
                return

            guardar_transacciones(cartera, df)
            st.success(f"Se han importado {len(df_excel)} transacciones correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            
def obtener_participaciones_actuales(isin, fecha, cartera):
    """
    Devuelve el número de participaciones actuales para un ISIN en la fecha dada.
    Suma todas las compras y ventas previas en la cartera.
    """
    df = cargar_transacciones(cartera)
    if df.empty or "ISIN" not in df.columns or "Participaciones" not in df.columns or "Tipo" not in df.columns:
        return 0.0

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')
    df = df.dropna(subset=["Fecha"])
    df = df[df["Fecha"] <= pd.to_datetime(fecha)]

    df_isin = df[df["ISIN"] == isin]
    if df_isin.empty:
        return 0.0

    df_isin["Sign"] = df_isin["Tipo"].apply(
        lambda x: 1 if x.lower().startswith("compra") else -1
    )
    df_isin["ParticipacionesAjustadas"] = df_isin["Participaciones"] * df_isin["Sign"]
    total = df_isin["ParticipacionesAjustadas"].sum()

    return max(total, 0.0)

