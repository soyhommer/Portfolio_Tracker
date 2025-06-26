import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.ft_fetcher import buscar_nav_ft

def test_ft(isin):
    resultado = buscar_nav_ft(isin)
    if resultado:
        print("✅ Resultado:")
        for k, v in resultado.items():
            print(f"  {k}: {v}")
    else:
        print("❌ No se encontró NAV o hubo error.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m tests.test_ft_fetcher \"ISIN del fondo\"")
    else:
        isin_fondo = " ".join(sys.argv[1:])
        test_ft(isin_fondo)