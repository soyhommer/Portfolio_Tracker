"""
Modulo FIFO:
- Aplica lógica FIFO para asignar costes de venta de participaciones.
- Devuelve saldo de stock pendiente y coste vendido.
"""

import pandas as pd
from typing import Dict

#####################################
# Calculo FIFO de las participaciones
##################################### 

# FIFO por activo

def process_fifo_for_isin(df_isin: pd.DataFrame) -> dict:
    """
    Procesa todas las transacciones de un ISIN aplicando lógica FIFO.
    Devuelve resumen: participaciones en stock, desembolso pendiente,
    coste total vendido, reembolso total, etc.
    """
    df_isin = df_isin.sort_values("Fecha")
    stock_fifo = []  # lista de lotes
    coste_vendido_total = 0.0
    reembolso_total = 0.0

    for _, row in df_isin.iterrows():
        tipo = row["Tipo"].lower()
        participaciones = row["Participaciones"]
        precio_unitario = row["Precio"]
        gasto = row.get("Gasto", 0.0)
        importe = participaciones * precio_unitario

        if tipo.startswith("compra"):
            coste_total = importe + gasto
            precio_unitario_con_gasto = coste_total / participaciones
            stock_fifo.append({
                "participaciones": participaciones,
                "precio_unitario": precio_unitario_con_gasto
            })

        elif tipo.startswith("venta"):
            participaciones_por_vender = participaciones
            coste_asignado = 0.0

            while participaciones_por_vender > 0 and stock_fifo:
                lote = stock_fifo[0]
                consumidas = min(participaciones_por_vender, lote["participaciones"])
                coste_lote = consumidas * lote["precio_unitario"]

                coste_asignado += coste_lote
                participaciones_por_vender -= consumidas
                lote["participaciones"] -= consumidas

                if lote["participaciones"] <= 0:
                    stock_fifo.pop(0)

            coste_vendido_total += coste_asignado
            # Reembolso neto con gasto
            reembolso_neto = importe - gasto
            reembolso_total += reembolso_neto

    # Sumar el stock pendiente
    participaciones_stock = sum(lote["participaciones"] for lote in stock_fifo)
    coste_stock = sum(lote["participaciones"] * lote["precio_unitario"] for lote in stock_fifo)

    return {
        "ISIN": df_isin["ISIN"].iloc[0],
        "Nombre del activo": df_isin["Posición"].mode().iloc[0] if not df_isin["Posición"].mode().empty else "",
        "Participaciones": participaciones_stock,
        "Desembolso": coste_stock,
        "Reembolso": reembolso_total,
        "Coste vendido": coste_vendido_total
    }

# FIFO a todo un dataframe

def apply_fifo_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica la lógica FIFO a todo el DataFrame de transacciones,
    devolviendo un DataFrame resumen con métricas por ISIN.
    """
    resultados = []

    for isin in df["ISIN"].dropna().unique():
        df_isin = df[df["ISIN"] == isin].copy()
        if df_isin.empty:
            continue

        resumen_isin = process_fifo_for_isin(df_isin)
        resultados.append(resumen_isin)

    if resultados:
        return pd.DataFrame(resultados)
    else:
        return pd.DataFrame(columns=[
            "ISIN", "Nombre del activo", "Participaciones",
            "Desembolso", "Reembolso", "Coste vendido"
        ])