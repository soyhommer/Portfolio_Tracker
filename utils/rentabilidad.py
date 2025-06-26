import os
import pandas as pd
import streamlit as st
import plotly.express as px

TRANSACCIONES_DIR = "data/transacciones"

def cargar_transacciones(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

def calcular_rentabilidad_mensual(df):
    if df.empty:
        return pd.DataFrame(columns=["Mes", "Rentabilidad Total (%)"])

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Importe"] = df["Participaciones"] * df["Precio"]

    df_mensual = df.copy()
    df_mensual["Mes"] = df_mensual["Fecha"].dt.to_period("M")
    df_mensual = df_mensual.groupby("Mes").agg({"Importe": "sum"}).reset_index()
    df_mensual["Mes"] = df_mensual["Mes"].astype(str)

    df_mensual["Rentabilidad Total (%)"] = df_mensual["Importe"].pct_change().fillna(0) * 100
    df_mensual["Rentabilidad Total (%)"] = df_mensual["Rentabilidad Total (%)"].round(2)

    return df_mensual[["Mes", "Rentabilidad Total (%)"]]

def calcular_rentabilidad_anual(df):
    if df.empty:
        return pd.DataFrame(columns=["Año", "Rentabilidad Total (%)"])

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Importe"] = df["Participaciones"] * df["Precio"]

    df_anual = df.copy()
    df_anual["Año"] = df_anual["Fecha"].dt.year
    df_anual = df_anual.groupby("Año").agg({"Importe": "sum"}).reset_index()
    df_anual["Rentabilidad Total (%)"] = df_anual["Importe"].pct_change().fillna(0) * 100
    df_anual["Rentabilidad Total (%)"] = df_anual["Rentabilidad Total (%)"].round(2)

    return df_anual[["Año", "Rentabilidad Total (%)"]]

def mostrar_rentabilidad(cartera):
    df = cargar_transacciones(cartera)

    st.subheader("📅 Rentabilidad mensual (total)")
    df_mensual = calcular_rentabilidad_mensual(df)
    st.plotly_chart(px.bar(df_mensual, x="Mes", y="Rentabilidad Total (%)", title="Rentabilidad mensual", text_auto=True), use_container_width=True)
    st.dataframe(df_mensual, use_container_width=True)

    st.subheader("📆 Rentabilidad anual (total)")
    df_anual = calcular_rentabilidad_anual(df)
    st.plotly_chart(px.bar(df_anual, x="Año", y="Rentabilidad Total (%)", title="Rentabilidad anual", text_auto=True), use_container_width=True)
    st.dataframe(df_anual, use_container_width=True)