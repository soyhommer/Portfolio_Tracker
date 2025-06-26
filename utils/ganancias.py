import os
import pandas as pd
import streamlit as st
from utils.nav_fetcher import get_nav_real as get_nav

TRANSACCIONES_DIR = "data/transacciones"

def cargar_transacciones(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

def calcular_ganancias_perdidas(df):
    from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
    df = limpiar_isin(df)
    validar_isin_vs_nombre(df)
    
    if df.empty:
        return pd.DataFrame(columns=[
            "Nombre del activo", "Participaciones", "Precio medio compra (EUR)", "Desembolso", "Reembolso",
            "Valor de mercado (EUR)", "+/- desde compra (EUR)", "+/- desde compra (%)", "NAV actual", "Fuente"
        ])

    df["Importe"] = df["Participaciones"] * df["Precio"]

    df["Desembolso"] = df.apply(
        lambda row: row["Importe"] + row.get("Gasto", 0) if row["Tipo"] == "Compra" else 0,
        axis=1
    )
    df["Reembolso"] = df.apply(
        lambda row: row["Importe"] if row["Tipo"] in ["Venta", "Venta total"] else 0,
        axis=1
    )

    resumen = df.groupby("Posición").agg({
        "Participaciones": "sum",
        "Desembolso": "sum",
        "Reembolso": "sum",
        "Precio": "mean"
    }).reset_index()

    resumen.rename(columns={
        "Posición": "Nombre del activo",
        "Precio": "Precio medio compra (EUR)"
    }, inplace=True)

    resumen = resumen.merge(
        df[["Posición", "ISIN"]].drop_duplicates(),
        left_on="Nombre del activo", right_on="Posición", how="left"
    ).drop(columns="Posición")

    # Integración con NAV actual
    def obtener_nav(row):
        isin = row.get("ISIN", "")
        if isinstance(isin, str):
            isin = isin.strip().replace("\u200b", "").replace("\u00a0", "")
        nombre = row.get("Nombre del activo")

        if isin and isin not in ["", "—", None]:
            return get_nav(isin) or get_nav(nombre) or {}
        return get_nav(nombre) or {}

    nav_data = resumen.apply(obtener_nav, axis=1)

    resumen["NAV actual"] = nav_data.apply(lambda x: x.get("nav"))
    resumen["ISIN"] = nav_data.apply(lambda x: x.get("isin", "—"))

    resumen["Valor de mercado (EUR)"] = resumen["Participaciones"] * resumen["NAV actual"]
    resumen["+/- desde compra (EUR)"] = resumen["Valor de mercado (EUR)"] + resumen["Reembolso"] - resumen["Desembolso"]
    resumen["+/- desde compra (%)"] = (resumen["+/- desde compra (EUR)"] / resumen["Desembolso"].replace(0, 1)) * 100

    resumen["Participaciones"] = pd.to_numeric(resumen["Participaciones"], errors="coerce").round(4)
    resumen["Precio medio compra (EUR)"] = pd.to_numeric(resumen["Precio medio compra (EUR)"], errors="coerce").round(4)
    resumen["Valor de mercado (EUR)"] = pd.to_numeric(resumen["Valor de mercado (EUR)"], errors="coerce").round(2)
    resumen["+/- desde compra (EUR)"] = pd.to_numeric(resumen["+/- desde compra (EUR)"], errors="coerce").round(2)
    resumen["+/- desde compra (%)"] = pd.to_numeric(resumen["+/- desde compra (%)"], errors="coerce").round(2)
    resumen["NAV actual"] = pd.to_numeric(resumen["NAV actual"], errors="coerce").round(4)

    columnas = [
        "Nombre del activo", "ISIN", "Participaciones", "Precio medio compra (EUR)",
        "NAV actual", "Desembolso", "Reembolso", "Valor de mercado (EUR)",
        "+/- desde compra (EUR)", "+/- desde compra (%)"
    ]

    fila_total = {
        "Nombre del activo": "💼 TOTAL",
        "ISIN": None,
        "Participaciones": None,
        "Precio medio compra (EUR)": None,
        "NAV actual": None,
        "Desembolso": resumen["Desembolso"].sum(),
        "Reembolso": resumen["Reembolso"].sum(),
        "Valor de mercado (EUR)": resumen["Valor de mercado (EUR)"].sum(),
        "+/- desde compra (EUR)": resumen["+/- desde compra (EUR)"].sum()
    }

    total_desembolso = resumen["Desembolso"].sum()
    fila_total["+/- desde compra (%)"] = (
        fila_total["+/- desde compra (EUR)"] / total_desembolso * 100
        if total_desembolso else 0
    )

    resumen = resumen[columnas]
    
    # 1. Concatenar fila total arriba
    resumen = pd.concat([pd.DataFrame([fila_total], columns=columnas), resumen], ignore_index=True)
    
    # 2. Forzar orden explícito por índice
    return resumen.reset_index(drop=True)[columnas]


def mostrar_ganancias_perdidas(cartera):
    df = cargar_transacciones(cartera)
    resultado = calcular_ganancias_perdidas(df)
    
    # Reetiquetar índice visual para que TOTAL se vea arriba
    resultado.reset_index(drop=True, inplace=True)
    
    st.dataframe(resultado, use_container_width=True)