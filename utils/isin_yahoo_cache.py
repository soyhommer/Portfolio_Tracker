import json
from pathlib import Path
from datetime import date
from utils.yahoo_fetcher import buscar_nav_yahoo_por_id, obtener_ticker_yahoo_por_isin
from utils.config import CACHE_DIR

CACHE_ISIN_YAHOO_PATH = CACHE_DIR / "isin_yahoo_map.json"


def cargar_cache_isin_yahoo() -> dict:
    if not CACHE_ISIN_YAHOO_PATH.exists():
        return {}
    try:
        with open(CACHE_ISIN_YAHOO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error cargando caché ISIN → Yahoo: {e}")
        return {}


def guardar_cache_isin_yahoo(mapa: dict) -> None:
    CACHE_ISIN_YAHOO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_ISIN_YAHOO_PATH, "w", encoding="utf-8") as f:
        json.dump(mapa, f, indent=2, ensure_ascii=False)


def obtener_ticker_yahoo_para_isin(isin: str) -> str | None:
    """
    Busca el ticker Yahoo para un ISIN desde la caché o mediante descubrimiento.
    Si encuentra un ticker válido con histórico, lo guarda o actualiza en la caché.
    """
    cache = cargar_cache_isin_yahoo()

    # 1️⃣ Buscar en caché
    if isin in cache:
        ticker = cache[isin]["ticker"]
        resultado = buscar_nav_yahoo_por_id(ticker)
        if resultado:
            return ticker  # ✅ Ticker aún válido
        else:
            print(f"⚠️ Ticker en caché no tiene datos: {ticker}, se volverá a buscar...")

    # 2️⃣ Redescubrir
    nuevo_ticker = obtener_ticker_yahoo_por_isin(isin)
    if nuevo_ticker:
        resultado = buscar_nav_yahoo_por_id(nuevo_ticker)
        if resultado:
            fuente = "investing" if "." in nuevo_ticker else "api"
            cache[isin] = {
                "ticker": nuevo_ticker,
                "fuente": fuente,
                "fecha": str(date.today())
            }
            guardar_cache_isin_yahoo(cache)
            return nuevo_ticker

    print(f"❌ No se pudo obtener ticker Yahoo para {isin}")
    return None


def buscar_nav_yahoo_por_isin_con_cache(isin: str) -> dict | None:
    """
    Función pública para obtener NAV de un ISIN usando caché + lógica escalonada.
    """
    ticker = obtener_ticker_yahoo_para_isin(isin)
    if ticker:
        resultado = buscar_nav_yahoo_por_id(ticker)
        if resultado:
            resultado["isin"] = isin  # ✅ Forzar inclusión del ISIN
            return resultado
    return None
