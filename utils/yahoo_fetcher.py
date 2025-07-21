import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.investing_fetcher import buscar_url_investing_por_isin
from utils.formatting import parsear_numero_con_miles_y_decimales

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

SUFIJOS_YAHOO = ["", ".F", ".MC", ".SW", ".MI"]

def buscar_nav_yahoo_por_isin(isin: str) -> dict | None:
    """
    Paso completo: ISIN → Ticker Yahoo (por caché o descubrimiento) → NAV
    """
    from utils.isin_yahoo_cache import obtener_ticker_yahoo_para_isin as obtener_ticker  # 🔁 evitar import circular

    ticker = obtener_ticker(isin)
    if ticker:
        resultado = buscar_nav_yahoo_por_id(ticker)
        if resultado:
            resultado["isin"] = isin
            return resultado
    return None

def obtener_ticker_yahoo_por_isin(isin: str) -> str | None:
    """
    Fallback directo para descubrir ticker Yahoo por ISIN
    (sin usar caché, usado internamente desde isin_yahoo_cache)
    """
    # 1️⃣ API oficial de Yahoo
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {
            "q": isin,
            "quotesCount": 1,
            "newsCount": 0,
            "listsCount": 0,
            "quotesQueryId": "tss_match_phrase_query"
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get("quotes"):
            symbol = data["quotes"][0].get("symbol")
            if symbol:
                print(f"✅ Ticker Yahoo encontrado vía API para {isin}: {symbol}")
                return symbol
    except Exception as e:
        print(f"⚠️ Error usando la API de Yahoo para {isin}: {e}")

    # 2️⃣ Fallback: Scraping de Investing + prueba de sufijos
    url = buscar_url_investing_por_isin(isin)
    if not url:
        print(f"❌ No se encontró fondo en Investing para {isin}")
        return None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for script in soup.find_all("script"):
            if script.string and "0P000" in script.string:
                match = re.search(r"0P000\w{5}", script.string)
                if match:
                    base_id = match.group(0)
                    print(f"🔁 Probar sufijos para base ID desde Investing: {base_id}")
                    return buscar_ticker_yahoo_probando_sufijos(base_id)
    except Exception as e:
        print(f"⚠️ Error extrayendo ID desde Investing para {isin}: {e}")

    return None

def buscar_ticker_yahoo_probando_sufijos(base_id: str) -> str | None:
    for sufijo in SUFIJOS_YAHOO:
        ticker = f"{base_id}{sufijo}"
        print(f"🔄 Probar ticker: {ticker}")
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="5d", interval="1d")
            if not hist.empty and "Close" in hist.columns:
                print(f"✅ Ticker válido con datos: {ticker}")
                return ticker
        except Exception as e:
            print(f"⚠️ Error al probar ticker {ticker}: {e}")

    print(f"❌ Ningún sufijo funcionó para base ID: {base_id}")
    return None

def buscar_nav_yahoo_por_id(ticker_symbol: str) -> dict | None:
    print(f"🔎 Consultando Yahoo Finance con ticker: {ticker_symbol}")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = ticker.history(period="5d", interval="1d")

        if hist.empty or "Close" not in hist.columns:
            print("❌ No se encontró histórico válido en Yahoo")
            return None

        nav = hist["Close"].iloc[-1]
        fecha = hist.index[-1].date().isoformat()

        variacion_1d = None
        if len(hist) >= 2:
            close_ayer = hist["Close"].iloc[-2]
            variacion_1d = ((nav - close_ayer) / close_ayer) * 100

        return {
            "nombre": info.get("longName") or info.get("shortName") or ticker_symbol,
            "isin": None,
            "nav": round(nav, 4),
            "fecha": fecha,
            "divisa": info.get("currency") or "EUR",
            "fuente": "Yahoo Finance",
            "variacion_1d": round(variacion_1d, 2) if variacion_1d is not None else None
        }

    except Exception as e:
        print(f"❌ Error al consultar datos de Yahoo Finance para {ticker_symbol}: {e}")
        return None
