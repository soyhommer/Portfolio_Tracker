import json
import os
import pandas as pd
from pathlib import Path
import streamlit as st
from utils.investing_fetcher import buscar_nav_investing

# Ruta del directorio compartido de históricos
NAV_HISTORICO_DIR = Path("data/nav_historico")
NAV_HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_NOMBRE_PATH = NAV_HISTORICO_DIR / "cache_nombre_activo.json"
TRANSACCIONES_DIR = Path("data/transacciones")
TRANSACCIONES_DIR.mkdir(parents=True, exist_ok=True)

def leer_csv_investing(file) -> pd.DataFrame:
    """
    Lee un archivo CSV descargado desde Investing.com.
    - Mantiene todas las columnas estándar (Date, Price, Open, High, Low, Change %)
    - Convierte Date a formato YYYY-MM-DD
    - Convierte precios a float
    """
    df = pd.read_csv(file)

    # Asegurar encabezados correctos
    expected_columns = ["Date", "Price", "Open", "High", "Low", "Change %"]
    df.columns = [col.strip() for col in df.columns]

    if not all(col in df.columns for col in expected_columns):
        raise ValueError("El CSV no tiene las columnas esperadas de Investing.com")

    # Normalizar fecha
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["Date"])

    # Limpiar precios
    for col in ["Price", "Open", "High", "Low"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "")
            .str.replace("%", "")
            .astype(float)
        )

    # Change %: opcional limpiar
    df["Change %"] = df["Change %"].astype(str).str.strip()

    # Ordenar por fecha
    df = df.sort_values("Date").reset_index(drop=True)

    return df


def cargar_historico_isin(isin: str) -> pd.DataFrame:
    """
    Carga el histórico guardado para un ISIN desde /data/nav_historico/{ISIN}.csv
    - Devuelve un DataFrame con el formato estándar
    - Si no existe, devuelve DataFrame vacío
    """
    path = NAV_HISTORICO_DIR / f"{isin}.csv"

    columnas_estandar = ["Date", "Price", "Open", "High", "Low", "Change %"]

    if path.exists():
        df = pd.read_csv(path)
        df.columns = [col.strip() for col in df.columns]
        return df[columnas_estandar]
    else:
        return pd.DataFrame(columns=columnas_estandar)


def guardar_historico_isin(df_nuevo: pd.DataFrame, isin: str):
    """
    Fusiona un DataFrame nuevo con el histórico existente (si lo hay)
    - Elimina fechas duplicadas
    - Ordena por Date
    - Guarda el resultado en /data/nav_historico/{ISIN}.csv
    """
    path = NAV_HISTORICO_DIR / f"{isin}.csv"

    # Cargar histórico existente
    if path.exists():
        df_existente = pd.read_csv(path)
        df_existente.columns = [col.strip() for col in df_existente.columns]
    else:
        df_existente = pd.DataFrame(columns=df_nuevo.columns)

    # Concatenar y limpiar duplicados por Date
    df_todo = pd.concat([df_existente, df_nuevo], ignore_index=True)
    df_todo = df_todo.drop_duplicates(subset=["Date"]).copy()

    # Normalizar fechas y ordenar
    df_todo["Date"] = pd.to_datetime(df_todo["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df_todo = df_todo.dropna(subset=["Date"])
    df_todo = df_todo.sort_values("Date").reset_index(drop=True)

    # Guardar en disco
    df_todo.to_csv(path, index=False)

    # 🔥 Actualizar cache de nombre
    get_nombre_activo_por_isin(isin)

def detectar_intervalos_continuos(df: pd.DataFrame) -> list:
    """
    Analiza las fechas del histórico y detecta intervalos continuos.
    - Devuelve lista de dicts con start, end, rows
    - Por ejemplo:
      [{"start": "2022-01-01", "end": "2022-12-31", "rows": 365}]
    """
    if df.empty or "Date" not in df.columns:
        return []

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    if df.empty:
        return []

    intervalos = []
    start = df.loc[0, "Date"]
    prev = start
    count = 1

    for i in range(1, len(df)):
        actual = df.loc[i, "Date"]
        diff = (actual - prev).days

        if diff > 1:
            intervalos.append({
                "start": start.strftime("%Y-%m-%d"),
                "end": prev.strftime("%Y-%m-%d"),
                "rows": count
            })
            start = actual
            count = 1
        else:
            count += 1

        prev = actual

    # Añadir último intervalo
    intervalos.append({
        "start": start.strftime("%Y-%m-%d"),
        "end": prev.strftime("%Y-%m-%d"),
        "rows": count
    })

    return intervalos

def listar_isins_disponibles() -> list:
    """
    Escanea /data/nav_historico/
    - Devuelve lista de ISINs disponibles (basado en nombres de archivo .csv)
    """
    if not NAV_HISTORICO_DIR.exists():
        return []

    isins = []
    for file in NAV_HISTORICO_DIR.glob("*.csv"):
        isin = file.stem.strip()
        if isin:
            isins.append(isin)

    return sorted(isins)

def resumen_historicos_cargados():
    """
    Devuelve DataFrame con resumen de ISINs cargados:
    ISIN, nº intervalos, fecha inicio más antigua, fecha fin más reciente
    """
    resumen = []

    isins = listar_isins_disponibles()
    for isin in isins:
        df = cargar_historico_isin(isin)
        intervalos = detectar_intervalos_continuos(df)
        if intervalos:
            fechas_inicio = [i["start"] for i in intervalos]
            fechas_fin = [i["end"] for i in intervalos]
            nombre_activo = get_nombre_activo_por_isin(isin)

            resumen.append({
                "Nombre de activo": nombre_activo,
                "ISIN": isin,
                "Nº intervalos": len(intervalos),
                "Inicio más antiguo": min(fechas_inicio),
                "Fin más reciente": max(fechas_fin)
            })

    return pd.DataFrame(resumen)

def get_nombre_activo_por_isin(isin: str) -> str:
    """
    Devuelve el nombre del activo asociado a un ISIN, usando caché local o scraping si necesario.
    """
    # Cargar cache local
    if CACHE_NOMBRE_PATH.exists():
        with open(CACHE_NOMBRE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    # Verificar si ya está en cache
    if isin in cache:
        return cache[isin]

    # Si no está en cache, scrappear
    datos = buscar_nav_investing(isin)
    if datos and "nombre" in datos:
        nombre = datos["nombre"]
    else:
        nombre = "(nombre desconocido)"

    # Guardar en cache local
    cache[isin] = nombre
    with open(CACHE_NOMBRE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    return nombre

def detectar_faltantes_nav_por_cartera(transacciones_dir, nav_historico_dir):
    """
    Cruza las fechas de las transacciones de todas las carteras
    con los intervalos NAV disponibles.
    
    Devuelve DataFrame con:
    Cartera | ISIN | Nombre de activo | Fechas de transacción sin NAV | Intervalos NAV disponibles
    """
    import pandas as pd

    resultados = []

    # Obtener todos los CSV de transacciones (cada uno es una cartera)
    archivos_carteras = list(transacciones_dir.glob("*.csv"))

    if not archivos_carteras:
        return pd.DataFrame(columns=[
            "Cartera", "ISIN", "Nombre de activo",
            "Fechas transacción sin NAV", "Intervalos NAV disponibles"
        ])

    for archivo in archivos_carteras:
        nombre_cartera = archivo.stem

        try:
            df_trans = pd.read_csv(archivo)
        except Exception as e:
            print(f"Error leyendo {archivo}: {e}")
            continue

        # Validar columnas mínimas necesarias
        if "ISIN" not in df_trans.columns or "Fecha" not in df_trans.columns:
            continue

        # Limpieza mínima
        df_trans["Fecha"] = pd.to_datetime(df_trans["Fecha"], errors='coerce')
        df_trans = df_trans.dropna(subset=["ISIN", "Fecha"])

        # Agrupar transacciones por ISIN
        isins_en_cartera = df_trans["ISIN"].unique()

        for isin in isins_en_cartera:
            fechas_tx = df_trans[df_trans["ISIN"] == isin]["Fecha"].sort_values().unique()

            # Obtener intervalos NAV
            nav_file = nav_historico_dir / f"{isin}.csv"
            if not nav_file.exists():
                intervalos = []
            else:
                try:
                    df_nav = pd.read_csv(nav_file)
                    intervalos = detectar_intervalos_continuos(df_nav)
                except Exception as e:
                    print(f"Error leyendo NAV para {isin}: {e}")
                    intervalos = []

            # Convertir intervalos a rango de fechas
            intervalos_disponibles = [
                (pd.to_datetime(i["start"]), pd.to_datetime(i["end"]))
                for i in intervalos
            ]

            # Verificar cobertura de fechas
            fechas_faltantes = []
            for fecha in fechas_tx:
                covered = any(start <= fecha <= end for (start, end) in intervalos_disponibles)
                if not covered:
                    fechas_faltantes.append(fecha.strftime("%Y-%m-%d"))

            if fechas_faltantes:
                # Obtener nombre de activo (desde caché o scrapping)
                nombre_activo = get_nombre_activo_por_isin(isin)

                resultados.append({
                    "Cartera": nombre_cartera,
                    "ISIN": isin,
                    "Nombre de activo": nombre_activo,
                    "Fechas transacción sin NAV": ", ".join(fechas_faltantes),
                    "Intervalos NAV disponibles": str(intervalos)
                })

    if resultados:
        return pd.DataFrame(resultados)
    else:
        return pd.DataFrame(columns=[
            "Cartera", "ISIN", "Nombre de activo",
            "Fechas transacción sin NAV", "Intervalos NAV disponibles"
        ])

#Funcion para el Frontend
def mostrar_gestor_historicos_nav():
    """
    Componente de Streamlit para cargar históricos.
    - Tabla resumen de ISINs ya cargados
    - Selector de ISIN (existente o nuevo)
    - FileUploader para CSV
    - Vista previa del CSV cargado
    - Tabla de intervalos ya cargados
    - Botón para guardar
    """
    st.header("📥 Gestor de Históricos NAV")
    st.markdown("""
    Esta sección te permite cargar históricos de precios (fondos, ETFs, acciones) 
    descargados desde Investing.com. Puedes añadir nuevos tramos de fechas 
    de forma incremental sin perder datos ya cargados.
    """)

    # 0️⃣ Resumen de ISINs ya cargados en el sistema
    df_resumen = resumen_historicos_cargados()

    st.subheader("📋 ISINs ya cargados en el sistema")
    if not df_resumen.empty:
        st.dataframe(df_resumen, use_container_width=True)
    else:
        st.info("ℹ️ Aún no hay históricos cargados en el sistema.")

    
    st.markdown("---")

    # 1️⃣ Selección o entrada de ISIN
    col1, col2 = st.columns(2)

    isins = df_resumen["ISIN"].tolist() if not df_resumen.empty else []

    with col1:
        isin_existente = st.selectbox("📌 ISIN ya cargado:", options=[""] + isins)

    with col2:
        isin_nuevo = st.text_input("🆕 O escribe un nuevo ISIN:", value="")

    isin_final = (isin_nuevo or isin_existente).strip()

    # 2️⃣ Subida del CSV
    archivo = st.file_uploader(
        "📂 Sube el archivo CSV de Investing.com",
        type=["csv"],
        help="Debe contener columnas: Date, Price, Open, High, Low, Change %"
    )

    # 3️⃣ Vista previa del CSV subido
    if archivo and isin_final:
        try:
            df_subido = leer_csv_investing(archivo)
            st.subheader("👁️ Vista previa del CSV cargado")
            st.dataframe(df_subido)
        except Exception as e:
            st.error(f"❌ Error al procesar el CSV: {e}")

    # 4️⃣ Ver intervalos ya cargados
    if isin_final:
        df_actual = cargar_historico_isin(isin_final)
        if not df_actual.empty:
            st.subheader(f"📊 Intervalos ya cargados para {isin_final}")
            intervalos = detectar_intervalos_continuos(df_actual)
            st.table(intervalos)
        else:
            st.info("ℹ️ No hay datos aún para este ISIN.")

    # 5️⃣ Botón para guardar
    if archivo and isin_final:
        if st.button("💾 Guardar histórico NAV"):
            guardar_historico_isin(df_subido, isin_final)
            st.success(f"✅ Histórico actualizado para ISIN: {isin_final}")
            st.rerun()

    # 6️⃣ Revisión de cobertura NAV
    st.markdown("---")
    st.header("📊 Revisión de Cobertura NAV")

    # Ejecuta la revisión
    faltantes_df = detectar_faltantes_nav_por_cartera(TRANSACCIONES_DIR, NAV_HISTORICO_DIR)

    if not faltantes_df.empty:
        st.warning("⚠️ Hay transacciones en carteras que NO están cubiertas por históricos NAV:")
        st.dataframe(faltantes_df, use_container_width=True)
        st.markdown("""
            ✅ Por favor revisa estas fechas e ISINs y sube los históricos faltantes 
            para poder calcular correctamente las rentabilidades.
        """)
    else:
        st.success("✅ Todas las transacciones de todas las carteras están cubiertas con datos NAV disponibles.")
