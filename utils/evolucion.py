import os
import pandas as pd
import streamlit as st
import plotly.express as px

TRANSACCIONES_DIR = "data/transacciones"

def cargar_transacciones(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

def calcular_valor_total_mensual(df):
    if df.empty:
        return pd.DataFrame(columns=["Mes", "Valor de Cartera"])

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)
    df["Valor"] = df["Participaciones"] * df["Precio"]

    df_mensual = df.groupby("Mes").agg({"Valor": "sum"}).reset_index()
    df_mensual.rename(columns={"Valor": "Valor de Cartera"}, inplace=True)
    df_mensual["Valor de Cartera"] = df_mensual["Valor de Cartera"].round(2)
    return df_mensual

def mostrar_evolucion_valor_cartera(cartera):
    df = cargar_transacciones(cartera)
    df_valor = calcular_valor_total_mensual(df)
    st.subheader("📈 Evolución del valor total de la cartera")
    st.plotly_chart(
        px.line(df_valor, x="Mes", y="Valor de Cartera", markers=True, title="Evolución mensual del valor total de la cartera"),
        use_container_width=True
    )
    st.dataframe(df_valor, use_container_width=True)