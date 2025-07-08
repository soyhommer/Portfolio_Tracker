import sys
from utils.finect_fetcher import buscar_nav_finect

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Debes pasar el nombre o ISIN como argumento")
        print("✅ Ejemplo:")
        print("    python -m tests.test_finect_fetcher \"ES0112611001\"")
        sys.exit(1)

    query = sys.argv[1]
    print(f"\n🧪 TEST: Buscando en Finect -> {query}\n")
    PORTFOLIO = "TestPortfolio"
    resultado = buscar_nav_finect(query, PORTFOLIO)
    print("\n✅ Resultado:", resultado)
