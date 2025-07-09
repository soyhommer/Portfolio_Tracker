import pandas as pd

# Carga el histórico
df_hist = pd.read_csv("Prueba.csv")
print("✅ Histórico cargado:")
print(df_hist.head())

# Carga el Excel adicional
df_new = pd.read_excel("Transacciones adicionales_20250708.xlsx")
print("✅ Nuevas transacciones cargadas:")
print(df_new.head())

# Concatenar como haría la app
df_total = pd.concat([df_hist, df_new], ignore_index=True)
print(f"✅ Total transacciones después de merge: {len(df_total)}")

# Normalizar columnas de texto
for col in ["ISIN", "Tipo"]:
    df_total[col] = df_total[col].astype(str).str.strip().str.upper()

# Verificar columnas críticas
print(df_total[["ISIN", "Tipo", "Participaciones"]].head())

# Calcular stock final por ISIN
stock = {}
for isin, grupo in df_total.groupby("ISIN"):
    total = 0
    for _, row in grupo.iterrows():
        tipo = row["Tipo"].lower()
        participaciones = row["Participaciones"]
        if tipo == "compra":
            total += participaciones
        elif tipo == "venta":
            total -= participaciones
    stock[isin] = total

# Mostrar resultado
print("\n✅ STOCK FINAL POR ISIN:")
for isin, valor in stock.items():
    print(f"{isin}: {valor}")

# Identificar negativos
print("\n❌ ISINs con stock negativo:")
for isin, valor in stock.items():
    if valor < 0:
        print(f"⚠️ {isin}: {valor}")
