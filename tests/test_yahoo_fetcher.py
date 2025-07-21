import sys
from utils.yahoo_fetcher import buscar_nav_yahoo_por_isin, buscar_nav_yahoo_por_id

from utils.yahoo_fetcher import (
    buscar_nav_yahoo_por_id,
    buscar_nav_yahoo_por_isin
)

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python -m tests.test_yahoo_fetcher <ticker_o_isin>")
        print("Ejemplos:")
        print("   python -m tests.test_yahoo_fetcher 0P00016YQ5.F")
        print("   python -m tests.test_yahoo_fetcher ES0112611001")
        return

    entrada = sys.argv[1].strip()

    es_isin = len(entrada) == 12 and entrada[:2].isalpha() and entrada[2:].isalnum()

    if es_isin:
        print(f"🔎 Interpretando entrada como ISIN → usando lógica escalonada con caché: {entrada}")
        resultado = buscar_nav_yahoo_por_isin(entrada)
    else:
        print(f"🔎 Interpretando entrada como ticker Yahoo directo: {entrada}")
        resultado = buscar_nav_yahoo_por_id(entrada)

    if resultado:
        print("\n✅ Resultado obtenido:")
        for k, v in resultado.items():
            print(f"  {k}: {v}")
    else:
        print("❌ No se pudo obtener información.")

if __name__ == "__main__":
    main()
