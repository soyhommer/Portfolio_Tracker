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
            "Valor de mercado (EUR)", "+/- desde compra (EUR)", "+/- desde compra (%)", "NAV actual"
        ])

    df["Importe"] = df["Participaciones"] * df["Precio"]
    df["Desembolso"] = df.apply(lambda r: r["Importe"] + r.get("Gasto", 0) if r["Tipo"].lower().startswith("compra") else 0, axis=1)
    df["Reembolso"] = df.apply(lambda r: r["Importe"] if r["Tipo"].lower().startswith("venta") else 0, axis=1)

    df["Sign"] = df["Tipo"].apply(lambda x: 1 if x.lower().startswith("compra") else -1)
    df["ParticipacionesAjustadas"] = df["Participaciones"] * df["Sign"]

    resumen = df.groupby("ISIN").agg({
        "ParticipacionesAjustadas": "sum",
        "Desembolso": "sum",
        "Reembolso": "sum",
        "Precio": "mean"
    }).reset_index()

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

    resumen["Valor de mercado (EUR)"] = resumen["Participaciones"] * resumen["NAV actual"]
    resumen.loc[resumen["Participaciones"] <= 0, "Valor de mercado (EUR)"] = 0.0

    resumen["+/- desde compra (EUR)"] = resumen["Valor de mercado (EUR)"] + resumen["Reembolso"] - resumen["Desembolso"]
    resumen["+/- desde compra (%)"] = resumen.apply(
        lambda row: ((row["Valor de mercado (EUR)"] + row["Reembolso"] - row["Desembolso"]) / row["Desembolso"] * 100)
        if row["Desembolso"] > 0 else 0,
        axis=1
    )

    resumen = resumen.round({
        "Participaciones": 4,
        "Precio medio compra (EUR)": 4,
        "NAV actual": 4,
        "Desembolso": 4,
        "Reembolso": 4,
        "Valor de mercado (EUR)": 4,
        "+/- desde compra (EUR)": 4,
        "+/- desde compra (%)": 2
    })

    resumen["+/- desde compra (%)"] = resumen["+/- desde compra (%)"].apply(
        lambda x: f"{x:.2f}%" if pd.notnull(x) else ""
    )
    columnas = [
        "Nombre del activo", "ISIN", "Participaciones", "Precio medio compra (EUR)",
        "NAV actual", "Desembolso", "Reembolso", "Valor de mercado (EUR)",
        "+/- desde compra (EUR)", "+/- desde compra (%)"
    ]

    total_desembolso = resumen["Desembolso"].sum()
    total_reembolso = resumen["Reembolso"].sum()
    total_valor_mercado = resumen["Valor de mercado (EUR)"].sum()

    total_balance_eur = total_valor_mercado + total_reembolso - total_desembolso
    total_balance_pct = (
        (total_balance_eur / total_desembolso * 100)
        if total_desembolso else 0
    )

    fila_total = {
        "Nombre del activo": "💼 TOTAL",
        "ISIN": None,
        "Participaciones": None,
        "Precio medio compra (EUR)": None,
        "NAV actual": None,
        "Desembolso": round(total_desembolso, 4),
        "Reembolso": round(total_reembolso, 4),
        "Valor de mercado (EUR)": round(total_valor_mercado, 4),
        "+/- desde compra (EUR)": round(total_balance_eur, 4),
        "+/- desde compra (%)": f"{total_balance_pct:.2f}%"
    }

    resumen = resumen[columnas]
    resumen = pd.concat([pd.DataFrame([fila_total], columns=columnas), resumen], ignore_index=True) 

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
    df = cargar_transacciones(cartera)
    resultado = calcular_ganancias_perdidas(df)

    # Reetiquetar índice visual para que TOTAL se vea arriba
    resultado.reset_index(drop=True, inplace=True)

    # Aplicar formato condicional en las columnas numéricas relevantes
    resultado_styled = resultado.style.applymap(
        highlight_cells,
        subset=["+/- desde compra (EUR)", "+/- desde compra (%)"]
    )
    st.dataframe(resultado_styled, use_container_width=True)