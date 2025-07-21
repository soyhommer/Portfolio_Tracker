import yfinance as yf
from datetime import datetime
from utils.formatting import parsear_numero_con_miles_y_decimales

def buscar_nav_yahoo_por_id(morningstar_id: str) -> dict | None:
    """
    Consulta Yahoo Finance usando el ID Morningstar como ticker (ej. '0P00016YQ5.F').

    Args:
        morningstar_id (str): Código Morningstar (ej. '0P00016YQ5').

    Returns:
        dict | None: Datos del fondo si se encuentra, o None.
    """
    #ticker_symbol = f"{morningstar_id}.F"  # Sufijo típico para fondos (puede variar: .MC, .DE, .SW, etc.)
    ticker_symbol = morningstar_id  # Ya viene con el sufijo incluido (ej. "0P00016YQ5.F")
    print(f"🔎 Consultando Yahoo Finance con ticker: {ticker_symbol}")
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = ticker.history(period="5d", interval="1d")  # último NAV y variación reciente

        if hist.empty or "Close" not in hist.columns:
            print("❌ No se encontró histórico válido")
            return None

        nav = hist["Close"][-1]
        fecha = hist.index[-1].date().isoformat()

        # Calcular variación 1d si hay 2 o más días
        variacion_1d = None
        if len(hist) >= 2:
            close_ayer = hist["Close"][-2]
            variacion_1d = ((nav - close_ayer) / close_ayer) * 100

        resultado = {
            "nombre": info.get("longName") or info.get("shortName") or ticker_symbol,
            "isin": None,  # Yahoo Finance no lo proporciona
            "nav": round(nav, 4),
            "fecha": fecha,
            "divisa": info.get("currency") or "EUR",
            "fuente": "Yahoo Finance",
            "variacion_1d": round(variacion_1d, 2) if variacion_1d is not None else None
        }

        return resultado

    except Exception as e:
        print(f"❌ Error al consultar Yahoo Finance: {e}")
        return None
