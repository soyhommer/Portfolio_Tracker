import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.morningstar_fetcher import buscar_nav_morningstar

def test_morningstar(nombre):
    print(f"\n🧪 TEST: Buscando en Morningstar -> {nombre}\n")
    try:
        resultado = buscar_nav_morningstar(nombre)
        if resultado:
            print("✅ Resultado encontrado:")
            for k, v in resultado.items():
                print(f"  {k}: {v}")
        else:
            print("❌ No se encontró NAV o hubo error.")
    except Exception as e:
        print(f"❌ Excepción en test: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m tests.test_morningstar_fetcher \"Nombre del fondo o ISIN\"")
    else:
        nombre_fondo = " ".join(sys.argv[1:])
        test_morningstar(nombre_fondo)