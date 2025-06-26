import os
import pandas as pd
import streamlit as st

TRANSACCIONES_DIR = "data/transacciones"

def cargar_transacciones(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

def calcular_flujos_trimestrales(df):
    if df.empty:
        return pd.DataFrame(columns=["Trimestre", "Compras Netas (EUR)", "Ventas Netas (EUR)", "Gastos (EUR)", "Flujo Neto (EUR)"])

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Año-Trimestre"] = df["Fecha"].dt.to_period("Q")
    df["Importe"] = df["Participaciones"] * df["Precio"]

    df["Compra"] = df.apply(lambda row: row["Importe"] if row["Tipo"] == "Compra" else 0, axis=1)
    df["Venta"] = df.apply(lambda row: row["Importe"] if row["Tipo"] in ["Venta", "Venta total"] else 0, axis=1)
    df["Gasto"] = df["Gasto"].fillna(0)

    resumen = df.groupby("Año-Trimestre").agg({
        "Compra": "sum",
        "Venta": "sum",
        "Gasto": "sum"
    }).reset_index()

    resumen["Flujo Neto (EUR)"] = resumen["Compra"] - resumen["Venta"] - resumen["Gasto"]

    resumen.rename(columns={
        "Año-Trimestre": "Trimestre",
        "Compra": "Compras Netas (EUR)",
        "Venta": "Ventas Netas (EUR)",
        "Gasto": "Gastos (EUR)"
    }, inplace=True)

    resumen["Compras Netas (EUR)"] = resumen["Compras Netas (EUR)"].round(2)
    resumen["Ventas Netas (EUR)"] = resumen["Ventas Netas (EUR)"].round(2)
    resumen["Gastos (EUR)"] = resumen["Gastos (EUR)"].round(2)
    resumen["Flujo Neto (EUR)"] = resumen["Flujo Neto (EUR)"].round(2)

    return resumen

def mostrar_flujos(cartera):
    df = cargar_transacciones(cartera)
    resumen = calcular_flujos_trimestrales(df)
    st.dataframe(resumen, use_container_width=True)