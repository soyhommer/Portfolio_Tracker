# tests/test_yahoo_fetcher.py

import sys
from utils.yahoo_fetcher import buscar_nav_yahoo_por_id  # ✅ Import correcto

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m tests.test_yahoo_fetcher <YahooTicker>")
        print("Ejemplo: python -m tests.test_yahoo_fetcher 0P00016YQ5.F")
        return

    ticker = sys.argv[1].strip()
    print(f"🔍 Buscando en Yahoo Finance: {ticker}")
    resultado = buscar_nav_yahoo_por_id(ticker)

    if resultado:
        print("\n✅ Resultado:")
        for k, v in resultado.items():
            print(f"  {k}: {v}")
    else:
        print("❌ No se pudo obtener información del ticker.")

if __name__ == "__main__":
    main()
