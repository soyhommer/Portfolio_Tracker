import os
import pandas as pd
import streamlit as st
from utils.nav_fetcher import get_nav_real as get_nav
from datetime import datetime

TRANSACCIONES_DIR = "data/transacciones"

def cargar_transacciones(cartera):
    path = os.path.join(TRANSACCIONES_DIR, f"{cartera}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=["Posición", "Tipo", "Participaciones", "Fecha", "Moneda", "Precio", "Gasto"])

from datetime import datetime

def calcular_estado_actual(df, cartera: str, forzar_nav: bool = False):
    from utils.nav_fetcher import limpiar_isin, validar_isin_vs_nombre
    df = limpiar_isin(df)
    validar_isin_vs_nombre(df)

    print("🔍 calculando estado actual")
    print(df.head(10))
    print(df.dtypes)

    if "ISIN" not in df.columns:
        df["ISIN"] = None

    if df.empty:
        return pd.DataFrame(columns=[
            "Nombre del activo", "ID", "Último NAV (EUR)", "Divisa", "1 d%",
            "#Participaciones", "Valor (EUR)", "Peso %", "Fecha", "NAV Validity"
        ])

    df["Importe"] = df["Participaciones"] * df["Precio"]
    
    # Aplicar signo a las participaciones según el tipo
    df["Sign"] = df["Tipo"].apply(lambda x: 1 if x.lower().startswith("compra") else -1)
    df["ParticipacionesAjustadas"] = df["Participaciones"] * df["Sign"]
    df["Importe"] = df["Participaciones"] * df["Precio"]
    df["ImporteAjustado"] = df["Importe"] * df["Sign"]
    
    # Agregar por ISIN
    df_agrupado = df.groupby(["ISIN"]).agg({
        "ParticipacionesAjustadas": "sum",
        "ImporteAjustado": "sum",
        "Fecha": "max"
    }).reset_index()

    # Renombrar para coherencia
    df_agrupado = df_agrupado.rename(columns={
        "ParticipacionesAjustadas": "Participaciones",
        "ImporteAjustado": "Importe"
    })

    # FILTRAR activos liquidados
    df_agrupado = df_agrupado[df_agrupado["Participaciones"] > 0]

    # Elegir nombre más frecuente por ISIN (Mismo ISIN no siempre mismo nombre)
    nombre_map = (
        df.groupby("ISIN")["Posición"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[-1])
        .reset_index()
    )

    # Merge del nombre elegido
    df_agrupado = pd.merge(df_agrupado, nombre_map, on="ISIN", how="left")

    # Renombrar para compatibilidad con el resto del código
    df_agrupado = df_agrupado.rename(columns={"Nombre": "Posición"})

    resultados = []

    print(f"📊 df_agrupado:\n{df_agrupado}")

    for _, row in df_agrupado.iterrows():
        isin = row.get("ISIN")
        nombre = row.get("Posición")
        identificador = isin if isinstance(isin, str) and isin.strip() and isin != "—" else nombre

        print(f"🔍 Buscando NAV para: {identificador}")

        if isinstance(isin, str):
            isin = isin.strip().replace("\u200b", "").replace("\u00a0", "")
        else:
            isin = ""

        datos_nav = {}
        if isin and isin != "—":
            datos_nav = get_nav(isin, cartera, forzar=forzar_nav) or get_nav(nombre, cartera, forzar=forzar_nav) or {}
        else:
            datos_nav = get_nav(nombre, cartera, forzar=forzar_nav) or {}


        print(f"📦 Resultado: {datos_nav}")

        nav_actual = datos_nav.get("nav", None)
        if nav_actual is None:
            print(f"⛔ NAV no encontrado para {identificador}")
            continue

        valor_actual = row["Participaciones"] * nav_actual
        resultados.append({
            "Nombre del activo": row["Posición"],
            "ID": datos_nav.get("isin", "—"),
            "#Participaciones": round(row["Participaciones"], 4),
            "Último NAV (EUR)": round(nav_actual, 4),
            "Divisa": datos_nav.get("divisa", "—"),
            "1 d%": datos_nav.get("variacion_1d", 0.0),
            "Valor (EUR)": round(valor_actual, 2),
            "Fecha": str(datos_nav.get("fecha", row["Fecha"])),
            "fuente_nav": datos_nav.get("fuente", "—")  # temporal
        })

    if not resultados:
        return pd.DataFrame(columns=[
            "Nombre del activo", "ID", "Último NAV (EUR)", "Divisa", "1 d%",
            "#Participaciones", "Valor (EUR)", "Peso %", "Fecha", "NAV Validity"
        ])

    df_resultado = pd.DataFrame(resultados)

    # Calcular pesos
    total_valor = df_resultado["Valor (EUR)"].sum()
    df_resultado["Peso %"] = df_resultado["Valor (EUR)"] / total_valor * 100
    df_resultado["Peso %"] = df_resultado["Peso %"].round(2)

    # Calcular 1 d% ponderado
    df_resultado["1 d% ponderado"] = df_resultado.apply(
        lambda row: row["1 d%"] * row["Valor (EUR)"] if pd.notnull(row["1 d%"]) else 0,
        axis=1
    )
    variacion_total = df_resultado["1 d% ponderado"].sum() / total_valor if total_valor else 0
    variacion_total = round(variacion_total, 2)

    # Fila total
    fila_total = {
        "Nombre del activo": "💼 TOTAL",
        "ID": None,
        "Último NAV (EUR)": None,
        "Divisa": None,
        "1 d%": variacion_total,
        "#Participaciones": None,
        "Valor (EUR)": round(total_valor, 2),
        "Peso %": 100.0 if total_valor else 0.0,
        "Fecha": None,
        "fuente_nav": None
    }
    df_resultado = pd.concat([
        pd.DataFrame([fila_total], columns=df_resultado.columns),
        df_resultado
    ], ignore_index=True)

    # Calcular NAV Validity a partir de "Fecha"
    def calcular_validez(row):
        try:
            fecha_str = row.get("Fecha")
            if not fecha_str:
                return "N/A"
            fecha_obj = datetime.fromisoformat(str(fecha_str))
            delta = datetime.now() - fecha_obj
            horas = delta.seconds // 3600 + delta.days * 24
            minutos = (delta.seconds % 3600) // 60
            return f"{horas} h {minutos} min ago"
        except Exception:
            return "N/A"

    df_resultado["NAV Validity"] = df_resultado.apply(calcular_validez, axis=1)

    # Quitar columna fuente_nav (si no quieres mostrarla más)
    df_resultado = df_resultado.drop(columns=["fuente_nav"])

    columnas_finales = [
        "Nombre del activo", "ID", "Último NAV (EUR)", "Divisa", "1 d%",
        "#Participaciones", "Valor (EUR)", "Peso %", "Fecha", "NAV Validity"
    ]

    return df_resultado[columnas_finales].reset_index(drop=True)


def mostrar_estado_general(cartera):
    df = cargar_transacciones(cartera)
    df_general = calcular_estado_actual(df)

    # Eliminar filas completamente vacías
    df_general = df_general.dropna(how='all')

    # Tipos consistentes
    df_general = df_general.astype({
        "Nombre del activo": "string",
        "ID": "string",
        "Último NAV (EUR)": "float",
        "Divisa": "string",
        "1 d%": "float",
        "#Participaciones": "float",
        "Valor (EUR)": "float",
        "Peso %": "float",
        "Fecha": "string",
        "Fuente NAV": "string"
    }, errors="ignore")

    st.dataframe(df_general, use_container_width=True)
