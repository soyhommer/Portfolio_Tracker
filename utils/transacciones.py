import os
import re
import pandas as pd
import streamlit as st
from utils.nav_fetcher import get_nav_real as get_nav
from utils.nav_fetcher import cargar_cache_nav
from utils.nav_cache import actualizar_cache_isin
from utils.config import TRANSACCIONES_DIR, NAV_HISTORICO_DIR

# DATA_DIR = "data"
# TRANSACCIONES_DIR = os.path.join(DATA_DIR, "transacciones")

def obtener_ruta_transacciones(cartera):
    return os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")

def cargar_transacciones(cartera):
    path = obtener_ruta_transacciones(cartera)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

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
def extraer_isin(nombre):
    cache = cargar_cache_nav()
    datos = cache.get(nombre)
    if datos and datos.get("isin") and datos.get("nav") is not None:
        return datos["isin"]
    return "—"

def mostrar_tabla_transacciones(cartera):
    st.markdown(f"### Transacciones de la cartera: {cartera}")

    df = cargar_transacciones(cartera)

    from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
    df = limpiar_isin(df)
    validar_isin_vs_nombre(df)

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
        df["ISIN"] = df["Posición"].apply(extraer_isin)
    else:
        df["ISIN"] = df["ISIN"].where(df["ISIN"].apply(es_isin_valido))
        df["ISIN"] = df["ISIN"].fillna(df["Posición"].apply(extraer_isin))

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
        guardar_transacciones(cartera, df_guardar)

        for _, row in df_guardar.iterrows():
            nombre = row["Posición"]
            isin = row.get("ISIN")
            if isinstance(nombre, str) and isinstance(isin, str) and isin.strip() and isin != "—":
                actualizar_cache_isin(nombre, isin)

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


def formulario_nueva_transaccion(cartera):
    st.markdown("---")
    st.subheader("Añadir nueva transacción")

    df = cargar_transacciones(cartera)

    with st.form(key="form_transaccion"):
        col1, col2, col3 = st.columns(3)

        with col1:
            identificador = st.text_input(
                "ISIN / Ticker / Código",
                help="Código identificativo del activo (ISIN, Ticker u otro). Se guardará en la columna ISIN."
            )
            tipo = st.selectbox("Tipo", ["Compra", "Venta", "Venta total"])

        with col2:
            nombre = st.text_input(
                "Nombre del activo",
                help="Nombre del fondo, acción, PP, ETF, etc. Se guardará en la columna Posición. Si se deja vacío se intentará autocompletar desde históricos o consultar online."
            )
            participaciones = st.number_input("Participaciones", min_value=0.0001, format="%.4f")
            fecha = st.date_input("Fecha")

        with col3:
            moneda = st.selectbox("Moneda", ["EUR", "USD", "GBP", "CHF", "JPY"])
            precio = st.number_input(
                "Precio unitario",
                min_value=0.0,
                value=0.0,
                format="%.4f",
                help="Si se deja en 0 se intentará completar automáticamente con el histórico NAV."
            )
            gasto = st.number_input("Gasto (opcional)", min_value=0.0, format="%.2f", value=0.0)

        submitted = st.form_submit_button("Añadir transacción")

        if submitted:
            if not identificador.strip():
                st.error("❌ El campo ISIN / Ticker / Código es obligatorio.")
                return

            # Autocompletar NOMBRE si está vacío
            if not nombre.strip():
                datos_nav = get_nav(identificador)
                if datos_nav and "nombre" in datos_nav:
                    nombre = datos_nav["nombre"]
                    st.success(f"✔️ Nombre del activo autocompletado: {nombre}")
                else:
                    st.warning("⚠️ No se pudo autocompletar el nombre del activo. Por favor complétalo manualmente si puedes.")

            # Autocompletar PRECIO si está en 0
            if precio == 0.0:
                precio_nav = buscar_nav_para_transaccion(identificador, fecha, NAV_HISTORICO_DIR)

                if precio_nav is not None:
                    precio = precio_nav
                    st.success(f"✔️ Precio unitario autocompletado desde histórico NAV: {precio:.4f}")
                else:
                    # Intento alternativo: buscar precio anterior más cercano (<=7 días antes)
                    precio_cercano = buscar_precio_historico_cercano(
                        isin=identificador,
                        fecha_transaccion=fecha,
                        nav_historico_dir=NAV_HISTORICO_DIR,
                        dias_max=7
                    )
                    if precio_cercano is not None:
                        precio = precio_cercano
                        st.success(
                            f"✔️ Precio unitario autocompletado con histórico más cercano (≤7 días antes): {precio:.4f}"
                        )
                    else:
                        st.warning("⚠️ No se encontró NAV en históricos para este activo ni para fechas cercanas. Precio dejado en 0.")

            # Construir registro alineado con el esquema EXISTENTE del CSV
            nueva = {
                "Posición": nombre,
                "ISIN": identificador,
                "Tipo": tipo,
                "Participaciones": participaciones,
                "Fecha": fecha,
                "Moneda": moneda,
                "Precio": precio,
                "Gasto": gasto
            }

            # Añadir al dataframe
            df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)

            # Limpieza y validación de ISIN
            from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
            df = limpiar_isin(df)
            validar_isin_vs_nombre(df)

            # Guardar
            guardar_transacciones(cartera, df)

            st.success("✅ Transacción añadida correctamente.")
            st.rerun()

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
            
            guardar_transacciones(cartera, df)
            st.success(f"Se han importado {len(df_excel)} transacciones correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")