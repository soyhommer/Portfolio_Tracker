import re
from datetime import datetime
from utils.investing_fetcher import buscar_nav_investing
from utils.ft_fetcher import buscar_nav_ft
from utils.finect_fetcher import buscar_nav_finect

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

def merge_nav_data(identificador: str, portfolio_name: str) -> dict | None:
    """
    Intenta obtener datos de NAV desde múltiples fuentes y fusionarlos en un único resultado consolidado.
    
    Args:
        identificador (str): ISIN o nombre del fondo a buscar.
        portfolio_name (str): Nombre de la cartera (para la caché).
    
    Returns:
        dict | None: Resultado consolidado con campos estándar.
    """

    import inspect
    if "Seilern" in identificador:
        print(f"\n🚨 merge_nav_data llamado con: '{identificador}'")
        for f in inspect.stack()[1:4]:
            print(f"↪️ desde {f.function} en {f.filename}:{f.lineno}")

    # Definir las fuentes como funciones "lazy"
    fuentes = [
        ("investing", buscar_nav_investing),
        ("ft", buscar_nav_ft),
        # ("finect", buscar_nav_finect),
    ]

    resultados = []
    for nombre, fetcher in fuentes:
        try:
            print(f"🔎 Probando fuente: {nombre}")
            resultado = fetcher(identificador, portfolio_name)
            if resultado:
                resultados.append((nombre, resultado))
        except Exception as e:
            print(f"⚠️ Error en fetcher {nombre}: {e}")

    if not resultados:
        print("⚠️ No se obtuvo resultado de ninguna fuente.")
        return None

    # Filtrado y selección de campos
    campos = ["nombre", "isin", "nav", "fecha", "divisa", "variacion_1d"]
    validadores = {
        "isin": es_valido_isin,
        "nav": es_valido_nav,
        "fecha": es_valido_fecha,
        "nombre": es_valido_nombre,
        "divisa": es_valido_divisa,
        "variacion_1d": es_valido_variacion_1d,
    }

    resultado_final = {}

    for campo in campos:
        for fuente, datos in resultados:
            if datos and campo in datos and validadores[campo](datos[campo]):
                resultado_final[campo] = datos[campo]
                break
        else:
            resultado_final[campo] = None

    # Información sobre la fuente prioritaria
    resultado_final["fuente"] = next(
        (fuente for fuente, datos in resultados if datos and es_valido_nav(datos.get("nav"))),
        None
    )
    resultado_final["fuente_variacion"] = next(
        (fuente for fuente, datos in resultados if datos and es_valido_variacion_1d(datos.get("variacion_1d"))),
        None
    )

    return resultado_final

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python -m utils.merge_nav_data \"Identificador\" \"NombreCartera\"")
    else:
        identificador = sys.argv[1]
        portfolio_name = sys.argv[2]
        resultado = merge_nav_data(identificador, portfolio_name)
        print("\n✅ Resultado combinado:")
        for k, v in resultado.items():
            print(f"  {k}: {v}")
