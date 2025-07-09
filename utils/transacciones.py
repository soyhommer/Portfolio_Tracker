import os
import re
import uuid
import pandas as pd
import streamlit as st
from utils.nav_fetcher import get_nav_real as get_nav
from utils.nav_fetcher import cargar_cache_nav
from utils.nav_fetcher import actualizar_cache_isin
from utils.nav_fetcher import limpiar_isin, normalizar_isin, corregir_nombres_por_isin
from utils.config import TRANSACCIONES_DIR, NAV_HISTORICO_DIR
from utils.formatting import parsear_numero_con_miles_y_decimales

import logging
logger = logging.getLogger(__name__)

# DATA_DIR = "data"
# TRANSACCIONES_DIR = os.path.join(DATA_DIR, "transacciones")

def obtener_ruta_transacciones(cartera):
    return os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")

def cargar_transacciones(cartera):
    path = obtener_ruta_transacciones(cartera)
    columnas_correctas = ["ID_UNICO", "Posición", "ISIN", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"]

    if os.path.exists(path):
        df = pd.read_csv(path)

        # Filtrar solo columnas válidas
        df = df[[col for col in df.columns if col in columnas_correctas]]

        # Asegurar todas las columnas existan
        for col in columnas_correctas:
            if col not in df.columns:
                if col in ["Posición", "ISIN", "Tipo", "Moneda"]:
                    df[col] = ""
                else:
                    df[col] = 0.0

        # Asignar ID_UNICO si faltan o están vacíos
        if "ID_UNICO" not in df.columns:
            df["ID_UNICO"] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            df["ID_UNICO"] = df["ID_UNICO"].fillna("").replace("", None)
            df["ID_UNICO"] = df["ID_UNICO"].apply(lambda x: x if x and x.strip() else str(uuid.uuid4()))

        # Reordenar columnas
        df = df[columnas_correctas]

        # Normalizar columna Posición a texto limpio
        if "Posición" in df.columns:
            df["Posición"] = df["Posición"].apply(
                lambda x: str(x).strip().replace("\u200b", "").replace("\u00a0", "") if pd.notna(x) else ""
            )
            df["Posición"] = df["Posición"].replace("nan", "")

        return df

    else:
        # CSV no existe aún
        return pd.DataFrame(columns=columnas_correctas)

def guardar_transacciones(cartera, df):
    path = obtener_ruta_transacciones(cartera)

    print(f"✅ [guardar_transacciones] Guardando CSV en: {path}")
    print(f"✅ [guardar_transacciones] Número de filas: {len(df)}")
    print(f"✅ [guardar_transacciones] Columnas: {list(df.columns)}")
    print(f"✅ [guardar_transacciones] Primeras filas:\n{df.head()}")

    try:
        # Convertir todas las columnas a string seguro
        df = df.copy()
        for col in df.columns:
            df[col] = df[col].astype(str).replace("nan", "").replace("None", "")

        df.to_csv(path, index=False)
        print("✅ [guardar_transacciones] Guardado correctamente.")

    except Exception as e:
        print(f"❌ ERROR al guardar CSV: {e}")
        raise e

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
    """
    Valida que ninguna transacción provoque stock negativo de participaciones,
    incluso tras ediciones en Streamlit (conversión defensiva de tipos).
    """
    problemas = []

    # 🩹 Conversión crítica
    df_transacciones = df_transacciones.copy()
    df_transacciones["Fecha"] = pd.to_datetime(df_transacciones["Fecha"], errors="coerce")
    df_transacciones["Participaciones"] = pd.to_numeric(df_transacciones["Participaciones"], errors="coerce").fillna(0.0)

    # Eliminar fechas inválidas
    df_transacciones = df_transacciones.dropna(subset=["Fecha"])

    # Orden correcto
    df_transacciones = df_transacciones.sort_values(["ISIN", "Fecha"])

    for isin, group in df_transacciones.groupby("ISIN"):
        saldo = 0.0

        for _, row in group.iterrows():
            tipo = str(row["Tipo"]).strip().lower()
            participaciones = row["Participaciones"]

            if tipo.startswith("compra"):
                saldo += participaciones

            elif tipo.startswith("venta total"):
                if saldo <= 1e-4 and participaciones > 0:
                    problemas.append(isin)
                    break
                if abs(saldo - participaciones) > 1e-4:
                    problemas.append(isin)
                    break
                saldo = 0.0

            elif tipo.startswith("venta"):
                saldo -= participaciones
                if saldo < -1e-4:
                    problemas.append(isin)
                    break

    return list(set(problemas))

def mostrar_tabla_transacciones(cartera):
    
    st.markdown(f"### Transacciones de la cartera: {cartera}")

    # Cargar datos del CSV
    df = cargar_transacciones(cartera)

    # Filtrar columnas válidas
    columnas_correctas = [
        "Seleccionar", "Posición", "ISIN", "Tipo", 
        "Participaciones", "Fecha", "Moneda", "Precio", "Gasto", "Valor operación", "ID_UNICO"
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
        COLUMNS_BASE = ["ID_UNICO", "Posición", "ISIN", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"]

        # Eliminar columnas derivadas y asegurar columnas base
        df_guardar = df_editado.drop(columns=["Seleccionar"], errors="ignore")
        if "Valor operación" in df_guardar.columns:
            df_guardar = df_guardar.drop(columns=["Valor operación"])
        
        # Asegurar ID_UNICO
        if "ID_UNICO" not in df_guardar.columns:
            df_guardar["ID_UNICO"] = [str(uuid.uuid4()) for _ in range(len(df_guardar))]
        else:
            df_guardar["ID_UNICO"] = df_guardar["ID_UNICO"].fillna("").replace("", None)
            df_guardar["ID_UNICO"] = df_guardar["ID_UNICO"].apply(lambda x: x if x and x.strip() else str(uuid.uuid4()))

        df_guardar = df_guardar[COLUMNS_BASE]

        # Forzar tipos
        df_guardar["Fecha"] = pd.to_datetime(df_guardar["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_guardar["Participaciones"] = pd.to_numeric(df_guardar["Participaciones"], errors="coerce").fillna(0.0)
        df_guardar["Precio"] = pd.to_numeric(df_guardar["Precio"], errors="coerce").fillna(0.0)
        df_guardar["Gasto"] = pd.to_numeric(df_guardar["Gasto"], errors="coerce").fillna(0.0)

        # Cargar histórico y limpiar columnas
        df_historico = cargar_transacciones(cartera)
        if "ID_UNICO" not in df_historico.columns:
            df_historico["ID_UNICO"] = [str(uuid.uuid4()) for _ in range(len(df_historico))]
        df_historico["Fecha"] = pd.to_datetime(df_historico["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_historico["Participaciones"] = pd.to_numeric(df_historico["Participaciones"], errors="coerce").fillna(0.0)
        df_historico["Precio"] = pd.to_numeric(df_historico["Precio"], errors="coerce").fillna(0.0)
        df_historico["Gasto"] = pd.to_numeric(df_historico["Gasto"], errors="coerce").fillna(0.0)
        df_historico = df_historico[COLUMNS_BASE]

        # ✅ DEBUG antes de merge para comparar
        st.write("📌 df_guardar antes de merge")
        st.dataframe(df_guardar)
        st.write("📌 df_historico antes de merge")
        st.dataframe(df_historico)

        # Merge reemplazando editadas por ID_UNICO
        claves = ["ID_UNICO"]
        df_total = pd.concat([df_historico, df_guardar]).drop_duplicates(subset=claves, keep="last")

        # Recalcular Valor operación
        df_total["Valor operación"] = df_total["Participaciones"] * df_total["Precio"] + df_total["Gasto"]
        df_total["Valor operación"] = df_total["Valor operación"].round(2)

        # Validar stock
        if not validar_stock_no_negativo(df_total):
            st.error("❌ Error: hay ventas que exceden el stock disponible en el histórico completo. Corrige antes de guardar.")
            return

        # Guardar
        guardar_transacciones(cartera, df_total)

        # Actualizar ISIN en caché
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
                datos_nav = get_nav(identificador, cartera)
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
                "ID_UNICO": str(uuid.uuid4()),
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

    # ✅ Inicializar variables de estado si no existen
    if "importado_exitoso" not in st.session_state:
        st.session_state["importado_exitoso"] = False
    
    # ✅ Evitar rerun infinito si ya importó
    if st.session_state["importado_exitoso"]:
        st.success("✅ Archivo ya importado correctamente. Si quieres volver a cargar otro, recarga la página.")
        st.stop()

    # ✅ Usar clave en uploader para poder limpiar después
    archivo = st.file_uploader(
        "Selecciona un archivo Excel",
        type=["xlsx"],        
    )

    st.markdown("""
📌 **Formato requerido del archivo Excel (.xlsx):**
    - **Obligatorio**: ISIN, Tipo, Participaciones, Fecha, Moneda, Precio, Gasto
    - **Opcional**: Posición (Nombre del activo)
    - ISIN es la clave maestra. El sistema usará la caché para asignar el nombre correcto.
    """)

    if archivo is not None:
        try:
            st.write("🟢 PASO 1: Archivo recibido correctamente")

            # ✅ 1. Leer Excel
            df_excel = pd.read_excel(archivo, dtype={"ISIN": str})
            st.write("✅ PASO 2: Excel leído")
            st.dataframe(df_excel)

            # ✅ 2. Definir normalizador seguro
            def normalizar_texto(x):
                if x is None or pd.isna(x):
                    return None
                try:
                    return str(x).strip()
                except Exception as e:
                    st.error(f"❌ Error normalizando texto: {e}")
                    return None

            # ✅ 3. Asegurar columnas esperadas
            for col in ["ISIN", "Tipo", "Moneda", "Posición"]:
                if col not in df_excel.columns:
                    st.warning(f"⚠️ Columna {col} faltaba en Excel: añadida como None")
                    df_excel[col] = None
            st.write("✅ PASO 3: Columnas aseguradas")
            st.dataframe(df_excel)

            # ✅ 4. Aplicar normalizador
            for col in ["ISIN", "Tipo", "Moneda", "Posición"]:
                df_excel[col] = df_excel[col].apply(normalizar_texto)
            st.write("✅ PASO 4: Columnas de texto normalizadas")
            st.dataframe(df_excel)

            # ✅ 5. Limpieza de ISIN
            df_excel = limpiar_isin(df_excel)
            st.write("✅ PASO 5: limpiar_isin aplicado")
            st.dataframe(df_excel)

            # ✅ 6. Corregir nombres con cache
            df_excel = corregir_nombres_por_isin(df_excel, cartera)
            st.write("✅ PASO 6: corregir_nombres_por_isin aplicado")
            st.dataframe(df_excel)

            #Generar identificador unico por transaccion
            if "ID_UNICO" not in df_excel.columns:
                df_excel["ID_UNICO"] = [str(uuid.uuid4()) for _ in range(len(df_excel))]
            else:
                df_excel["ID_UNICO"] = df_excel["ID_UNICO"].fillna("").replace("", None)
                df_excel["ID_UNICO"] = df_excel["ID_UNICO"].apply(lambda x: x if x and x.strip() else str(uuid.uuid4()))

            # ✅ 7. Normalizar números
            for col in ["Participaciones", "Precio", "Gasto"]:
                df_excel[col] = df_excel[col].apply(parsear_numero_con_miles_y_decimales).fillna(0.0)
            st.write("✅ PASO 7: Números normalizados")
            st.dataframe(df_excel)

            # ✅ 8. Verificar columnas obligatorias
            columnas_obligatorias = ["ISIN", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"]
            if not all(col in df_excel.columns for col in columnas_obligatorias):
                st.error("❌ El archivo no contiene todas las columnas obligatorias.")
                return
            st.write("✅ PASO 8: Columnas obligatorias presentes")

            # ✅ 9. Convertir tipos
            df_excel["Participaciones"] = pd.to_numeric(df_excel["Participaciones"], errors="coerce").fillna(0.0)
            df_excel["Precio"] = pd.to_numeric(df_excel["Precio"], errors="coerce").fillna(0.0)
            df_excel["Gasto"] = pd.to_numeric(df_excel["Gasto"], errors="coerce").fillna(0.0)
            df_excel["Fecha"] = pd.to_datetime(df_excel["Fecha"], errors="coerce")
            st.write("✅ PASO 9: Conversión de tipos")
            st.dataframe(df_excel)

            # ✅ 10. Validar fechas
            if df_excel["Fecha"].isnull().any():
                st.error("❌ Hay fechas inválidas en el archivo. Revisa el formato (YYYY-MM-DD).")
                return
            st.write("✅ PASO 10: Fechas validadas")

            # ✅ 11. Redondear
            df_excel["Participaciones"] = df_excel["Participaciones"].round(6)
            df_excel["Precio"] = df_excel["Precio"].round(4)
            df_excel["Gasto"] = df_excel["Gasto"].round(2)
            st.write("✅ PASO 11: Decimales redondeados")
            st.dataframe(df_excel)

            # ✅ 12. Validar ISIN
            if df_excel["ISIN"].isnull().any():
                st.error("❌ Todas las transacciones deben tener ISIN válido. Corrige el Excel y vuelve a cargarlo.")
                return
            st.write("✅ PASO 12: ISINs validados")

            # ✅ 13. Cargar histórico
            df_actual = cargar_transacciones(cartera)
            df_actual["Fecha"] = pd.to_datetime(df_actual["Fecha"], errors="coerce")
            st.write("✅ PASO 13: Histórico cargado (con Fecha convertido a datetime)")
            st.dataframe(df_actual)

            # ✅ 14. Validar fechas VS Venta Total
            try:
                df_hist = df_actual.copy()
                df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"], errors="coerce")
                df_excel["Fecha"] = pd.to_datetime(df_excel["Fecha"], errors="coerce")

                isins_con_error = []

                for isin in df_excel["ISIN"].unique():
                    ventas_totales_hist = df_hist[
                        (df_hist["ISIN"] == isin) &
                        (df_hist["Tipo"].str.lower().str.startswith("venta total"))
                    ]
                    if ventas_totales_hist.empty:
                        continue

                    fecha_ultima_venta_total = ventas_totales_hist["Fecha"].max()

                    nuevas_trans = df_excel[df_excel["ISIN"] == isin]
                    if not nuevas_trans.empty and nuevas_trans["Fecha"].min() <= fecha_ultima_venta_total:
                        isins_con_error.append((isin, fecha_ultima_venta_total.date()))

                if isins_con_error:
                    st.error("❌ No se puede importar: hay transacciones con fecha anterior o igual a la última Venta Total ya registrada.")
                    for isin, fecha in isins_con_error:
                        st.warning(f"- ISIN: {isin} (Venta Total en {fecha})")
                    st.info("✏️ Corrige tu Excel para quitar esas líneas o actualizar sus fechas.")
                    return

                st.write("✅ PASO 14: Fechas vs. Venta Total validadas correctamente")
            except Exception as e:
                st.error(f"❌ Error validando fechas vs. Venta Total: {e}")
                return

            # ✅ 15. Merge con histórico
            st.write(f"✅ Histórico actual tiene {len(df_actual)} filas")
            st.write(f"✅ Excel nuevo tiene {len(df_excel)} filas")

            df_total = pd.concat([df_actual, df_excel], ignore_index=True)
            st.write(f"✅ Tras concat, total de filas = {len(df_total)}")

            COLUMNAS_TODAS = ["ISIN", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto", "Posición"]
            df_total = df_total.drop_duplicates(subset=COLUMNAS_TODAS)
            st.write(f"✅ Tras quitar duplicados exactos (todas columnas), total de filas = {len(df_total)}")

            df_total["Fecha"] = pd.to_datetime(df_total["Fecha"], errors="coerce")
            st.write("✅ Fecha convertida a datetime en todo el DataFrame")

            st.write("✅ PASO 15: Histórico + Nuevas transacciones concatenadas y limpias")
            st.dataframe(df_total)

            st.download_button(
                label="⬇️ Descargar CSV de DF_TOTAL para inspección",
                data=df_total.to_csv(index=False).encode('utf-8'),
                file_name='df_total_para_validacion.csv',
                mime='text/csv'
            )

            # ✅ 16. Validar stock negativo
            problemas = validar_stock_no_negativo(df_total)
            if problemas:
                st.error("❌ La importación NO se ha guardado porque generaría stock negativo en:")
                for isin in problemas:
                    st.warning(f"- {isin}")
                st.info("✏️ Corrige el archivo Excel para resolver estos problemas antes de volver a subirlo.")
                return
            st.write("✅ PASO 16: Validación de stock negativo superada")

            # ✅ 17. Guardar CSV final
            guardar_transacciones(cartera, df_total)
            st.session_state["importado_exitoso"] = True
            st.session_state["uploaded_file"] = None
            st.success(f"✅ Se han importado {len(df_excel)} transacciones correctamente.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error general al procesar el archivo: {e}")

            
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

