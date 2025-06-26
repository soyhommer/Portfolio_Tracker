import re
from datetime import datetime
from utils.investing_fetcher import buscar_nav_investing
from utils.morningstar_fetcher import buscar_nav_morningstar
from utils.ft_fetcher import buscar_nav_ft

def es_valido_isin(isin):
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", isin or ""))

def es_valido_nav(nav):
    try:
        return isinstance(nav, (int, float)) and 0.1 < nav < 10000
    except:
        return False

def es_valido_fecha(fecha):
    try:
        dt = datetime.fromisoformat(fecha)
        return dt.date() <= datetime.today().date() and (datetime.today().date() - dt.date()).days <= 7
    except:
        return False

def es_valido_nombre(nombre):
    if not nombre or not isinstance(nombre, str):
        return False
    return nombre.strip().lower() not in ["", "fondo sin nombre"]

def es_valido_divisa(divisa):
    return divisa in {"EUR", "USD", "GBP", "JPY", "CHF"}

def es_valido_variacion_1d(var):
    try:
        return isinstance(var, (int, float)) and -100 < var < 100
    except:
        return False

def merge_nav_data(identificador):
    
    import inspect

    if "Seilern" in identificador:
        print(f"\n🚨 merge_nav_data llamado con: '{identificador}'")
        for f in inspect.stack()[1:4]:
            print(f"↪️ desde {f.function} en {f.filename}:{f.lineno}")
    
    
    fuentes = [
        ("morningstar", buscar_nav_morningstar(identificador)),
        ("ft", buscar_nav_ft(identificador)),
        ("investing", buscar_nav_investing(identificador)),
    ]

    resultado = {}
    campos = ["nombre", "isin", "nav", "fecha", "divisa", "variacion_1d"]
    validadores = {
        "isin": es_valido_isin,
        "nav": es_valido_nav,
        "fecha": es_valido_fecha,
        "nombre": es_valido_nombre,
        "divisa": es_valido_divisa,
        "variacion_1d": es_valido_variacion_1d,
    }

    for campo in campos:
        for fuente, datos in fuentes:
            if datos and campo in datos and validadores[campo](datos[campo]):
                resultado[campo] = datos[campo]
                break
        else:
            resultado[campo] = None

    resultado["fuente"] = next((fuente for fuente, datos in fuentes if datos and es_valido_nav(datos.get("nav"))), None)
    resultado["fuente_variacion"] = next((fuente for fuente, datos in fuentes if datos and es_valido_variacion_1d(datos.get("variacion_1d"))), None)

    return resultado

if __name__ == "__main__":
    import sys
    resultado = merge_nav_data(sys.argv[1])
    print("\n✅ Resultado combinado:")
    for k, v in resultado.items():
        print(f"  {k}: {v}")