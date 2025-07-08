import json
import os
from utils.config import get_cache_nav_path, CACHE_TTL_HORAS
from datetime import datetime

CACHE_NAV_REAL_PATH = os.path.join("data", "cache_nav_real.json")


        

def cargar_cache(source: str, portfolio: str) -> dict:
    """
    Carga en memoria el contenido completo del archivo de caché correspondiente a la fuente y cartera indicadas.

    Si el archivo no existe, devuelve un diccionario vacío.

    Args:
        source (str): Nombre de la fuente de NAV (finect, ft, investing, etc.).
        portfolio (str): Nombre de la cartera.

    Returns:
        dict: Diccionario con todas las entradas cacheadas.
    """
    
    path = get_cache_nav_path(source, portfolio)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_cache(source: str, portfolio: str, cache: dict):
    """
    Escribe en disco el contenido completo del diccionario de caché para una fuente y cartera concretas.

    Sobrescribe el archivo JSON existente con el nuevo contenido.

    Args:
        source (str): Nombre de la fuente de NAV.
        portfolio (str): Nombre de la cartera.
        cache (dict): Diccionario completo con las claves y datos a persistir.
    """
    
    path = get_cache_nav_path(source, portfolio)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
               

def cargar_valido_de_cache(source: str, portfolio: str, clave: str) -> dict | None:
    """
    Intenta recuperar de caché la entrada específica por clave para una fuente y cartera,
    validando que su timestamp no haya expirado según CACHE_TTL_HORAS.

    Si la entrada existe y es válida, devuelve sus datos.
    Si está expirada o no existe, devuelve None.

    Args:
        source (str): Nombre de la fuente de NAV.
        portfolio (str): Nombre de la cartera.
        clave (str): Clave de la entrada a recuperar (tipicamente 'isin:...' o 'nombre:...').

    Returns:
        dict | None: Datos de la entrada si es válida y vigente, o None en caso contrario.
    """
    cache = cargar_cache(source, portfolio)
    entrada = cache.get(clave.lower())
    if entrada:
        try:
            fecha_guardado = datetime.fromisoformat(entrada["timestamp"])
            if (datetime.now() - fecha_guardado).total_seconds() < CACHE_TTL_HORAS * 3600:
                print(f"📦 Recuperado de caché {source} para {portfolio}")
                return entrada["data"]
            else:
                print("⏱️ Cache expirada para esta clave")
        except Exception as e:
            print(f"⚠️ Error interpretando timestamp: {e}")
    return None
    
def guardar_en_cache(source: str, portfolio: str, clave: str, data: dict):
    """
    Inserta o actualiza una entrada específica en el caché de una fuente y cartera dadas.
    Actualiza el timestamp de la entrada y guarda de nuevo todo el archivo de caché.

    Este método es la interfaz de ALTO nivel para que los fetchers puedan guardar
    una única entrada sin preocuparse por la estructura completa del archivo.

    Args:
        source (str): Nombre de la fuente de NAV.
        portfolio (str): Nombre de la cartera.
        clave (str): Clave de la entrada a guardar (usualmente 'isin:...' o 'nombre:...').
        data (dict): Diccionario con los datos del NAV y metadata asociada.
    """
    print(f"📝 Guardando en caché [{source}] para cartera {portfolio}: {clave}")
    cache = cargar_cache(source, portfolio)       # 1️⃣ leer archivo completo
    cache[clave.lower()] = {
        "timestamp": datetime.now().isoformat(),   # 2️⃣ actualizar / insertar
        "data": data
    }
    guardar_cache(source, portfolio, cache)       # 3️⃣ escribir archivo completo