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
    pass


def cargar_historico_isin(isin: str) -> pd.DataFrame:
    """
    Carga el histórico guardado para un ISIN desde /data/nav_historico/{ISIN}.csv
    - Devuelve un DataFrame con el formato estándar
    - Si no existe, devuelve DataFrame vacío
    """
    pass


def guardar_historico_isin(df_nuevo: pd.DataFrame, isin: str):
    """
    Fusiona un DataFrame nuevo con el histórico existente (si lo hay)
    - Elimina fechas duplicadas
    - Ordena por Date
    - Guarda el resultado en /data/nav_historico/{ISIN}.csv
    """
    pass


def detectar_intervalos_continuos(df: pd.DataFrame) -> list:
    """
    Analiza las fechas del histórico y detecta intervalos continuos.
    - Devuelve lista de dicts con start, end, rows
    - Por ejemplo:
      [{"start": "2022-01-01", "end": "2022-12-31", "rows": 365}]
    """
    pass


def listar_isins_disponibles() -> list:
    """
    Escanea /data/nav_historico/
    - Devuelve lista de ISINs disponibles (basado en nombres de archivo .csv)
    """
    pass


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
    st.info("Esta sección permitirá cargar y gestionar históricos de precios para fondos, ETFs y acciones.")
    pass
