import os
import pandas as pd
import streamlit as st
import plotly.express as px
from utils.historial_nav import cargar_historico_isin

TRANSACCIONES_DIR = "data/transacciones"

def cargar_transacciones(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

def load_transactions_clean(cartera):
    """
    Carga las transacciones de la cartera en formato limpio.
    Filtra y estandariza columnas clave.
    """
    df = cargar_transacciones(cartera)
    if df.empty:
        return df

    cols_needed = ["ISIN", "Tipo", "Participaciones", "Fecha", "Precio", "Gasto"]
    df = df[[col for col in cols_needed if col in df.columns]].copy()
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df = df.dropna(subset=["Fecha", "ISIN", "Participaciones"])
    df = df.sort_values("Fecha").reset_index(drop=True)
    return df

def compute_portfolio_valuation(df_holdings, df_navs):
    """
    Combina participaciones diarias con precios NAV para calcular
    el valor total de la cartera en el tiempo.
    """
    if df_holdings.empty or df_navs.empty:
        return pd.DataFrame(columns=["Fecha", "PortfolioValue"])

    df = pd.merge(df_holdings, df_navs, on=["Fecha", "ISIN"], how="left")
    df = df.dropna(subset=["Price"])
    df["Valor"] = df["Participaciones"] * df["Price"]
    df_portfolio = df.groupby("Fecha")["Valor"].sum().reset_index()
    df_portfolio.rename(columns={"Valor": "PortfolioValue"}, inplace=True)
    return df_portfolio

def load_all_navs(isin_list):
    """
    Carga todos los históricos NAV disponibles para los ISIN dados.
    Devuelve DataFrame consolidado con Fecha, ISIN, Price.
    """
    nav_frames = []
    for isin in isin_list:
        df_nav = cargar_historico_isin(isin)
        if df_nav.empty:
            continue
        df_nav = df_nav[["Date", "Price"]].rename(columns={"Date": "Fecha"})
        df_nav["ISIN"] = isin
        df_nav["Fecha"] = pd.to_datetime(df_nav["Fecha"], errors="coerce")
        nav_frames.append(df_nav)

    if nav_frames:
        df_navs = pd.concat(nav_frames, ignore_index=True)
        df_navs = df_navs.dropna(subset=["Fecha", "Price"])
        return df_navs
    else:
        return pd.DataFrame(columns=["Fecha", "ISIN", "Price"])

def build_holdings_over_time(df_transactions):
    """
    Genera un DataFrame con participaciones acumuladas diarias por ISIN.
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["Fecha", "ISIN", "Participaciones"])

    holdings_list = []
    for isin in df_transactions["ISIN"].unique():
        df_isin = df_transactions[df_transactions["ISIN"] == isin].copy()
        df_isin["Delta"] = df_isin.apply(
            lambda row: row["Participaciones"] if row["Tipo"] == "Compra" else -row["Participaciones"], axis=1
        )

        df_isin = df_isin.groupby("Fecha")["Delta"].sum().cumsum().reset_index()
        df_isin["ISIN"] = isin

        # Daily date range
        date_range = pd.date_range(df_isin["Fecha"].min(), df_isin["Fecha"].max(), freq="D")
        df_all = pd.DataFrame({"Fecha": date_range})
        df_all = df_all.merge(df_isin, how="left", on="Fecha")
        df_all["Delta"] = df_all["Delta"].fillna(method="ffill").fillna(0)
        df_all["ISIN"] = isin
        df_all.rename(columns={"Delta": "Participaciones"}, inplace=True)

        holdings_list.append(df_all[["Fecha", "ISIN", "Participaciones"]])

    df_holdings = pd.concat(holdings_list, ignore_index=True)
    df_holdings["Fecha"] = pd.to_datetime(df_holdings["Fecha"])
    return df_holdings

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
    
    st.header("🚀 [EXPERIMENTAL] Valor diario de la cartera")

    df_tx = load_transactions_clean(cartera)
    st.write("Transacciones limpias:", df_tx)

    df_holdings = build_holdings_over_time(df_tx)
    st.write("Holdings diarios:", df_holdings)

    isin_list = df_holdings["ISIN"].unique()
    df_navs = load_all_navs(isin_list)
    st.write("NAVs disponibles:", df_navs)

    df_portfolio = compute_portfolio_valuation(df_holdings, df_navs)
    st.line_chart(df_portfolio.set_index("Fecha"))
