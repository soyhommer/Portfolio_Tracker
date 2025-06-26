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

def simular_benchmark(df_valor, crecimiento_anual=0.06):
    if df_valor.empty:
        return pd.DataFrame(columns=["Mes", "Valor de Cartera", "Benchmark Simulado"])
    
    df = df_valor.copy()
    df = df.sort_values("Mes").reset_index(drop=True)
    df["Benchmark Simulado"] = df["Valor de Cartera"].iloc[0]  # mismo punto de partida
    factor_mensual = (1 + crecimiento_anual) ** (1/12)

    for i in range(1, len(df)):
        df.loc[i, "Benchmark Simulado"] = df.loc[i - 1, "Benchmark Simulado"] * factor_mensual

    df["Benchmark Simulado"] = df["Benchmark Simulado"].round(2)
    return df

def comparar_con_benchmark(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if not os.path.exists(path):
        st.warning("No hay transacciones para esta cartera.")
        return

    df = pd.read_csv(path)
    if df.empty:
        st.info("No hay datos suficientes para simular el benchmark.")
        return

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)
    df["Valor"] = df["Participaciones"] * df["Precio"]
    df_valor_mensual = df.groupby("Mes").agg({"Valor": "sum"}).reset_index()
    df_valor_mensual.rename(columns={"Valor": "Valor de Cartera"}, inplace=True)

    df_comparado = simular_benchmark(df_valor_mensual)

    st.subheader("📊 Comparativa Cartera vs Benchmark Simulado")
    fig = px.line(df_comparado, x="Mes", y=["Valor de Cartera", "Benchmark Simulado"],
                  title="Evolución comparativa", markers=True)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_comparado, use_container_width=True)