from utils.nav_fetcher import get_nav_yfinance

def test_yfinance_ticker(ticker):
    print(f"Testing ticker: {ticker}")
    result = get_nav_yfinance(ticker)
    if result:
        print("✅ NAV info:", result)
    else:
        print("❌ No NAV found.")

if __name__ == "__main__":
    test_yfinance_ticker("AAPL")     # debería funcionar
    test_yfinance_ticker("VEUR.L")   # prueba para ETF UCITS
    test_yfinance_ticker("0P00016YQ5.F") #Azvalor Internacional
    test_yfinance_ticker("0P00000P2M.F") #Bestinver Internacional
    test_yfinance_ticker("0P0000RU7W.L") #Bestinver Internacional
    test_yfinance_ticker("NOEXISTE") # debe fallar