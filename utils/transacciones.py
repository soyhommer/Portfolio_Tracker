import os
import re
import pandas as pd
import streamlit as st
from utils.nav_fetcher import get_nav_real as get_nav
from utils.nav_fetcher import cargar_cache_nav
from utils.nav_cache import actualizar_cache_isin

DATA_DIR = "data"
TRANSACCIONES_DIR = os.path.join(DATA_DIR, "transacciones")

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

    # Si el DataFrame está vacío, se advierte y retorna
    if df.empty:
        st.warning("La cartera no tiene transacciones registradas.")
        return df

    # Asegurar tipo fecha
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.date

    # Limpieza preventiva de caracteres invisibles en ISIN
    if "ISIN" in df.columns:
        df["ISIN"] = df["ISIN"].astype(str).apply(
            lambda x: x.strip().replace("\u200b", "").replace("\u00a0", "") if isinstance(x, str) else x
        ).replace("—", None)

    # Validación de ISIN
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

    # df_editado = st.data_editor(
        # df,
        # use_container_width=True,
        # num_rows="dynamic",
        # column_config={
            # "Fecha": st.column_config.DateColumn(format="YYYY-MM-DD"),
            # "Moneda": st.column_config.SelectboxColumn(
                # "Moneda", options=["EUR", "USD", "GBP", "CHF", "JPY"]
            # ),
            # "Tipo": st.column_config.SelectboxColumn(
                # "Tipo", options=["Compra", "Venta", "Venta total"]
            # ),
        # },
    # )

    df_editado = st.data_editor(
        df,
        use_container_width=True,
        column_config={
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


    if st.button("💾 Guardar cambios en transacciones"):
        guardar_transacciones(cartera, df_editado)

        for _, row in df_editado.iterrows():
            nombre = row["Posición"]
            isin = row.get("ISIN")
            if isinstance(nombre, str) and isinstance(isin, str) and isin.strip() and isin != "—":
                actualizar_cache_isin(nombre, isin)

        st.success("Cambios guardados correctamente.")
        st.rerun()

    return df

def formulario_nueva_transaccion(cartera):
    st.markdown("---")
    st.subheader("Añadir nueva transacción")

    df = cargar_transacciones(cartera)

    # # ✅ Diagnóstico de ISIN en fondos Seilern
    # def es_isin_valido(x):
        # if not isinstance(x, str):
            # return False
        # x = x.strip().replace("\u200b", "").replace("\u00a0", "")
        # return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", x))

    # diagnostico = []
    # for index, row in df.iterrows():
        # isin = row.get("ISIN")
        # if isin and "Seilern" in row["Posición"]:
            # valido = es_isin_valido(isin)
            # diagnostico.append(f"[{row['Posición']}]: ISIN='{isin}' → válido={valido} → repr: {repr(isin)}")

    # if diagnostico:
        # st.markdown("### 🔍 Diagnóstico ISIN fondos Seilern")
        # st.code("\n".join(diagnostico))

    # ✅ Formulario Streamlit
    with st.form(key="form_transaccion"):
        col1, col2, col3 = st.columns(3)
        with col1:
            posicion = st.text_input("Posición (nombre, ISIN, ticker)")
            tipo = st.selectbox("Tipo", ["Compra", "Venta", "Venta total"])
        with col2:
            participaciones = st.number_input("Participaciones", min_value=0.0001, format="%.4f")
            fecha = st.date_input("Fecha")
        with col3:
            moneda = st.selectbox("Moneda", ["EUR", "USD", "GBP"])
            precio = st.number_input("Precio unitario", min_value=0.0001, format="%.4f")
            gasto = st.number_input("Gasto (opcional)", min_value=0.0, format="%.2f", value=0.0)

        submitted = st.form_submit_button("Añadir transacción")

        if submitted:
            nueva = {
                "Posición": posicion,
                "Tipo": tipo,
                "Participaciones": participaciones,
                "Fecha": fecha,
                "Moneda": moneda,
                "Precio": precio,
                "Gasto": gasto
            }

            df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
            
            from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
            df = limpiar_isin(df)
            validar_isin_vs_nombre(df)
            
            guardar_transacciones(cartera, df)

            st.success("Transacción añadida correctamente.")
            st.rerun()
            
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