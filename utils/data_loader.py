import os
import json
import shutil
import streamlit as st
import pandas as pd

DATA_DIR = "data"
CARTERAS_FILE = os.path.join(DATA_DIR, "carteras.json")
TRANSACCIONES_DIR = os.path.join(DATA_DIR, "transacciones")

def cargar_carteras():
    if not os.path.exists(CARTERAS_FILE):
        return []
    with open(CARTERAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_carteras(carteras):
    with open(CARTERAS_FILE, "w", encoding="utf-8") as f:
        json.dump(carteras, f, indent=2)

def seleccionar_cartera(carteras):
    if not carteras:
        return None
    return st.sidebar.selectbox("Selecciona una cartera", carteras)

# def crear_cartera_si_necesario():
    # with st.sidebar.expander("➕ Crear nueva cartera"):
        # nombre = st.text_input("Nombre de la cartera")
        # moneda = st.selectbox("Moneda base", ["EUR", "USD", "GBP"])
        # benchmark = st.text_input("Benchmark (nombre o índice)")
        # if st.button("Crear cartera"):
            # if not nombre:
                # st.warning("El nombre no puede estar vacío.")
                # return
            # carteras = cargar_carteras()
            # if nombre in carteras:
                # st.warning("Ya existe una cartera con ese nombre.")
                # return
            # carteras.append(nombre)
            # guardar_carteras(carteras)
            # os.makedirs(TRANSACCIONES_DIR, exist_ok=True)
            # df_vacio = pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])
            # df_vacio.to_csv(os.path.join(TRANSACCIONES_DIR, f"{nombre}.csv"), index=False)
            # st.success(f"Cartera '{nombre}' creada correctamente. Recarga para seleccionarla.")
            # st.experimental_rerun()
          

def crear_cartera_si_necesario():
    with st.sidebar.expander("➕ Crear nueva cartera"):
        nombre = st.text_input("Nombre de la cartera")
        moneda = st.selectbox("Moneda base", ["EUR", "USD", "GBP"])
        benchmark = st.text_input("Benchmark (nombre o índice)")
        if st.button("Crear cartera"):
            if not nombre:
                st.warning("El nombre no puede estar vacío.")
                return
            carteras = cargar_carteras()
            if nombre in carteras:
                st.warning("Ya existe una cartera con ese nombre.")
                return
            carteras.append(nombre)
            guardar_carteras(carteras)
            os.makedirs(TRANSACCIONES_DIR, exist_ok=True)
            df_vacio = pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])
            df_vacio.to_csv(os.path.join(TRANSACCIONES_DIR, f"{nombre}.csv"), index=False)
            st.success(f"Cartera '{nombre}' creada correctamente. Recarga para seleccionarla.")

    # 📝 Renombrar cartera
    carteras = cargar_carteras()
    if carteras:
        with st.sidebar.expander("✏️ Renombrar cartera"):
            cartera_a_renombrar = st.selectbox("Selecciona cartera a renombrar", carteras)
            nuevo_nombre = st.text_input("Nuevo nombre:", key="renombrar")
            if st.button("Guardar nuevo nombre"):
                if nuevo_nombre.strip() and nuevo_nombre != cartera_a_renombrar:
                    carteras = cargar_carteras()
                    if nuevo_nombre in carteras:
                        st.error("Ya existe una cartera con ese nombre.")
                    else:
                        exito = renombrar_cartera(cartera_a_renombrar, nuevo_nombre)
                        if exito:
                            st.success(f"Cartera renombrada a: {nuevo_nombre}")
                            st.rerun()
                        else:
                            st.error("Error al renombrar la cartera.")
                else:
                    st.warning("Introduce un nombre distinto y no vacío.")

    # 🗑️ Eliminar cartera
    if carteras:
        with st.sidebar.expander("🗑️ Eliminar cartera existente"):
            cartera_a_borrar = st.selectbox("Selecciona cartera a eliminar", carteras, key="borrar")
            confirmar = st.checkbox("Confirmo que deseo eliminar esta cartera permanentemente")
            if st.button("Eliminar cartera"):
                if confirmar:
                    exito = eliminar_cartera(cartera_a_borrar)
                    if exito:
                        st.success(f"Cartera '{cartera_a_borrar}' eliminada correctamente.")
                        st.rerun()
                    else:
                        st.error("No se pudo eliminar la cartera.")
                else:
                    st.warning("Debes marcar la casilla de confirmación antes de eliminar.")

def renombrar_cartera(nombre_antiguo, nombre_nuevo):
    try:
        # Leer carteras
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            carteras = json.load(f)

        # Reemplazar el nombre
        if nombre_antiguo not in carteras:
            return False
        carteras[nombre_nuevo] = carteras.pop(nombre_antiguo)

        # Guardar
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(carteras, f, indent=2, ensure_ascii=False)

        # Renombrar archivo de transacciones si existe
        archivo_antiguo = os.path.join(TRANSACCIONES_DIR, f"{nombre_antiguo}.csv")
        archivo_nuevo = os.path.join(TRANSACCIONES_DIR, f"{nombre_nuevo}.csv")
        if os.path.exists(archivo_antiguo):
            shutil.move(archivo_antiguo, archivo_nuevo)

        return True
    except Exception as e:
        print(f"⚠️ Error al renombrar cartera: {e}")
        return False
        
def eliminar_cartera(nombre):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            carteras = json.load(f)

        if nombre in carteras:
            del carteras[nombre]
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(carteras, f, indent=2, ensure_ascii=False)

        archivo_csv = os.path.join(TRANSACCIONES_DIR, f"{nombre}.csv")
        if os.path.exists(archivo_csv):
            os.remove(archivo_csv)

        return True
    except Exception as e:
        print(f"⚠️ Error eliminando cartera '{nombre}': {e}")
        return False