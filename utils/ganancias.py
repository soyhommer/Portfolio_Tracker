import os
import pandas as pd
import streamlit as st
import numpy as np
from utils.nav_fetcher import get_nav_real as get_nav
from utils.config import get_ganancias_cache_path
from utils.fifo import process_fifo_for_isin, apply_fifo_to_dataframe
from utils.config import get_transactions_path, get_ganancias_cache_path

import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")
logger = logging.getLogger(__name__)

###############################
# Helpers para manejo de cache
############################### 
def cache_es_valido(cartera):
    trans_file = get_transactions_path(cartera)
    cache_file = get_ganancias_cache_path(cartera)

    if not cache_file.exists() or not trans_file.exists():
        return False

    trans_mtime = os.path.getmtime(trans_file)
    cache_mtime = os.path.getmtime(cache_file)

    return cache_mtime > trans_mtime

def guardar_cache_ganancias(df, cartera):
    cache_file = get_ganancias_cache_path(cartera)
    df.to_csv(cache_file, index=False)

def cargar_cache_ganancias(cartera):
    cache_file = get_ganancias_cache_path(cartera)
    return pd.read_csv(cache_file)


def cargar_transacciones(cartera):
    path = get_transactions_path(cartera)
    if path.exists():
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])


def calcular_balance_fila(row):
    participaciones = row.get("Participaciones", 0)
    logger.debug(f"Fila evaluada: {row.to_dict()}")

    if pd.isna(participaciones) or np.isclose(participaciones, 0):
        logger.debug(">>> Caso: Activo liquidado detectado")
        result = row["Reembolso"] - row["Coste vendido"]
        logger.debug(f"Reembolso: {row['Reembolso']}, Coste vendido: {row['Coste vendido']}, Resultado calculado: {result}")
        return result
    else:
        resultado_vendido = row["Reembolso"] - row["Coste vendido"]
        resultado_stock = row["Valor de mercado (EUR)"] - row["Desembolso"]
        result = resultado_vendido + resultado_stock
        logger.debug(f"Resultado vendido: {resultado_vendido}, Resultado stock: {resultado_stock}, Resultado total: {result}")
        return result



def calcular_balance_pct_fila(row):
    participaciones = row.get("Participaciones", 0)
    logger.debug(f"Fila evaluada para porcentaje: {row.to_dict()}")

    if pd.isna(participaciones) or np.isclose(participaciones, 0):
        base = row["Coste vendido"]
        if base and base > 0:
            result = ((row["Reembolso"] - row["Coste vendido"]) / base) * 100
            logger.debug(f"Base Coste vendido: {base}, Resultado %: {result}")
            return result
        else:
            logger.debug("Base Coste vendido nulo o 0, devolviendo 0%")
            return 0
    else:
        base = row["Desembolso"] + row["Coste vendido"]
        resultado_vendido = row["Reembolso"] - row["Coste vendido"]
        resultado_stock = row["Valor de mercado (EUR)"] - row["Desembolso"]
        if base and base > 0:
            result = ((resultado_vendido + resultado_stock) / base) * 100
            logger.debug(f"Base: {base}, Resultado vendido: {resultado_vendido}, Resultado stock: {resultado_stock}, Resultado %: {result}")
            return result
        else:
            logger.debug("Base Desembolso + Coste vendido nulo o 0, devolviendo 0%")
            return 0


def calcular_ganancias_perdidas(df):
    from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
    df = limpiar_isin(df)
    validar_isin_vs_nombre(df)

    if df.empty:
        return pd.DataFrame(columns=[
            "Nombre del activo", "Participaciones", "Precio medio compra (EUR)", "Desembolso", "Reembolso",
            "Valor de mercado (EUR)", "+/- desde compra (EUR)", "+/- desde compra (%)", "NAV actual"
        ])

    df["Importe"] = df["Participaciones"] * df["Precio"]
    df["Desembolso"] = df.apply(lambda r: r["Importe"] + r.get("Gasto", 0) if r["Tipo"].lower().startswith("compra") else 0, axis=1)
    df["Reembolso"] = df.apply(
        lambda r: r["Importe"] - r.get("Gasto", 0) if r["Tipo"].lower().startswith("venta") else 0,
        axis=1
    )

    df["Sign"] = df["Tipo"].apply(lambda x: 1 if x.lower().startswith("compra") else -1)
    df["ParticipacionesAjustadas"] = df["Participaciones"] * df["Sign"]

    # resumen = df.groupby("ISIN").agg({
    #     "ParticipacionesAjustadas": "sum",
    #     "Desembolso": "sum",
    #     "Reembolso": "sum",
    #     "Precio": "mean"
    # }).reset_index()

    resumen = apply_fifo_to_dataframe(df)

    resumen.rename(columns={
        "ParticipacionesAjustadas": "Participaciones",
        "Precio": "Precio medio compra (EUR)"
    }, inplace=True)

    nombre_map = df.groupby("ISIN")["Posición"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[-1]).reset_index()
    resumen = pd.merge(resumen, nombre_map, on="ISIN", how="left").rename(columns={"Posición": "Nombre del activo"})

    def obtener_nav(row):
        isin = row.get("ISIN", "").strip().replace("\u200b", "").replace("\u00a0", "") if isinstance(row.get("ISIN"), str) else ""
        nombre = row.get("Nombre del activo")
        return get_nav(isin) or get_nav(nombre) or {}

    nav_data = resumen.apply(obtener_nav, axis=1)
    resumen["NAV actual"] = nav_data.apply(lambda x: x.get("nav"))
    resumen["ISIN"] = nav_data.apply(lambda x: x.get("isin", "—"))

    
    #Calcular valor de mercado
    resumen["Valor de mercado (EUR)"] = resumen["Participaciones"] * resumen["NAV actual"]
    resumen.loc[resumen["Participaciones"] <= 0, "Valor de mercado (EUR)"] = 0.0
    
    #Calcular +/- desde compra (EUR)
    resumen["+/- desde compra (EUR)"] = resumen.apply(calcular_balance_fila, axis=1)
    
    #Calcular +/- desde compra (%)
    resumen["+/- desde compra (%)"] = resumen.apply(calcular_balance_pct_fila, axis=1)

    resumen = resumen.round({
        "Participaciones": 4,
        "Desembolso": 4,
        "Reembolso": 4,
        "Coste vendido": 4,
        "NAV actual": 4,
        "Valor de mercado (EUR)": 4,
        "+/- desde compra (EUR)": 4,
        "+/- desde compra (%)": 2
    })

    resumen["+/- desde compra (%)"] = resumen["+/- desde compra (%)"].apply(
        lambda x: f"{x:.2f}%" if pd.notnull(x) else ""
    )       

    total_desembolso = resumen["Desembolso"].sum()
    total_reembolso = resumen["Reembolso"].sum()
    total_valor_mercado = resumen["Valor de mercado (EUR)"].sum()
    total_coste_vendido = resumen["Coste vendido"].sum()

    total_gastado = total_desembolso + total_coste_vendido
    total_obtenido = total_valor_mercado + total_reembolso

    total_balance_eur = total_obtenido - total_gastado

    if total_gastado > 0:
        total_balance_pct = ((total_obtenido / total_gastado) - 1) * 100
    else:
        total_balance_pct = 0

    total_balance_pct = round(total_balance_pct, 2)
    total_balance_eur = round(total_balance_eur, 4)

    fila_total = {
        "Nombre del activo": "💼 TOTAL",
        "ISIN": None,
        "Participaciones": None,
        "Desembolso": round(total_desembolso, 4),
        "Reembolso": round(total_reembolso, 4),
        "Coste vendido": round(total_coste_vendido, 4),
        "NAV actual": None,
        "Valor de mercado (EUR)": round(total_valor_mercado, 4),
        "+/- desde compra (EUR)": round(total_balance_eur, 4),
        "+/- desde compra (%)": f"{total_balance_pct:.2f}%"
    }

    columnas = [
        "Nombre del activo", "ISIN", "Participaciones",
        "Desembolso", "Reembolso", "Coste vendido",
        "NAV actual", "Valor de mercado (EUR)",
        "+/- desde compra (EUR)", "+/- desde compra (%)"
    ]

    # Asegurar todas las columnas requeridas
    for col in columnas:
        if col not in resumen.columns:
            resumen[col] = None

    # Eliminar columnas duplicadas si existen
    resumen = resumen.loc[:, ~resumen.columns.duplicated()]

    # Concatenar fila TOTAL
    resumen = pd.concat([pd.DataFrame([fila_total]), resumen], ignore_index=True)

    # Devolver solo columnas en orden correcto
    return resumen.reset_index(drop=True)[columnas]

def highlight_cells(val):
    try:
        if pd.isna(val):
            return ""
        if float(val) < 0:
            return "color: red;"
    except (ValueError, TypeError):
        pass
    return ""

def mostrar_ganancias_perdidas(cartera):
    if cache_es_valido(cartera):
        resultado = cargar_cache_ganancias(cartera)
    else:
        df_trans = cargar_transacciones(cartera)
        resultado = calcular_ganancias_perdidas(df_trans)
        guardar_cache_ganancias(resultado, cartera)

    resultado.reset_index(drop=True, inplace=True)

    resultado_styled = resultado.style.applymap(
        highlight_cells,
        subset=["+/- desde compra (EUR)", "+/- desde compra (%)"]
    )

    st.dataframe(resultado_styled, use_container_width=True)
