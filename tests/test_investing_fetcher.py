import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.investing_fetcher import buscar_nav_investing

def test_investing(nombre):
    # print(f"🔍 Buscando NAV en Investing.com para: {nombre}")
    resultado = buscar_nav_investing(nombre)
    if resultado:
        print("✅ Resultado:")
        for k, v in resultado.items():
            print(f"  {k}: {v}")
    else:
        print("❌ No se encontró NAV o hubo error.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m tests.test_investing_fetcher \"Nombre del fondo\"")
    else:
        nombre_fondo = " ".join(sys.argv[1:])
        test_investing(nombre_fondo)