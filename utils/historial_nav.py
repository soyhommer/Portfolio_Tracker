import os
import pandas as pd
from pathlib import Path
import streamlit as st

# Ruta del directorio compartido de históricos
NAV_HISTORICO_DIR = Path("data/nav_historico")
NAV_HISTORICO_DIR.mkdir(parents=True, exist_ok=True)


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


def mostrar_gestor_historicos_nav():
    """
    Componente de Streamlit para cargar históricos.
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
    
    # 1️⃣ Selección o entrada de ISIN
    isins_disponibles = listar_isins_disponibles()
    col1, col2 = st.columns(2)

    with col1:
        isin_existente = st.selectbox("📌 ISIN ya cargado:", options=[""] + isins_disponibles)

    with col2:
        isin_nuevo = st.text_input("🆕 O escribe un nuevo ISIN:", value="")

    isin_final = isin_nuevo.strip() or isin_existente.strip()

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
            st.experimental_rerun()
