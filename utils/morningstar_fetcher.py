import re
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

CACHE_PATH = Path("data/cache_nav_morningstar.json")
CACHE_TTL_HORAS = 24

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def es_isin(valor: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", valor.upper()))

def cargar_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def guardar_en_cache(nombre_clave, data):
    print(f"📝 Guardando en caché: {nombre_clave}")
    cache = cargar_cache()
    cache[nombre_clave.lower()] = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    guardar_cache(cache)

def buscar_nav_morningstar(identificador: str) -> dict | None:
    print(f"🔍 Buscando NAV en Morningstar.es para: {identificador}")
    clave_cache = f"isin:{identificador}" if es_isin(identificador) else f"nombre:{identificador}"
    cache = cargar_cache()

    if clave_cache in cache:
        entrada = cache[clave_cache]
        try:
            fecha_guardado = datetime.fromisoformat(entrada["timestamp"])
            data = entrada["data"]

            if (datetime.now() - fecha_guardado).total_seconds() < CACHE_TTL_HORAS * 3600:
                if "nav" in data and "variacion_1d" in data:
                    print("📦 Recuperado de caché por clave")
                    return data
                else:
                    print("⏳ Datos incompletos en caché, se volverá a scrapear")
        except Exception as e:
            print(f"⚠️ Error al interpretar timestamp: {e}")

    query = quote(identificador)
    url_busqueda = f"https://www.morningstar.es/es/funds/SecuritySearchResults.aspx?search={query}&type="

    try:
        resp_busqueda = requests.get(url_busqueda, headers=HEADERS)
        resp_busqueda.raise_for_status()
        soup_busqueda = BeautifulSoup(resp_busqueda.text, "html.parser")
        enlace = soup_busqueda.select_one("a[href*='/funds/snapshot/snapshot.aspx?id=']")
        if not enlace:
            print("❌ No se encontró enlace al fondo")
            return None

        url_fondo = "https://www.morningstar.es" + enlace["href"]
        print(f"✅ Enlace preciso encontrado: {url_fondo}")

        resp_fondo = requests.get(url_fondo, headers=HEADERS)
        resp_fondo.raise_for_status()
        soup = BeautifulSoup(resp_fondo.text, "html.parser")
        tabla = soup.find("table", class_="overviewKeyStatsTable")
        if not tabla:
            print("⚠️ Tabla de estadísticas no encontrada")
            return None

        nav, fecha, isin = None, None, None

        divisa = "ERROR"  # fallback inicial
        
        for fila in tabla.find_all("tr"):
            celdas = fila.find_all("td")
            if not celdas:
                continue
            clave = celdas[0].get_text(strip=True).upper() if len(celdas) > 1 else ""
            if "VL" in clave:
                # Extraer fecha si está en un <span class="heading">
                fecha_tag = celdas[0].find("span", class_="heading")
                if fecha_tag:
                    try:
                        raw_fecha = fecha_tag.get_text(strip=True)
                        fecha = datetime.strptime(raw_fecha, "%d/%m/%Y").date().isoformat()
                    except:
                        fecha = None

                # Extraer divisa y valor
                raw_texto = celdas[1].get_text(" ", strip=True).replace("\xa0", " ").strip()
                match = re.search(r"([A-Z]{3})\s+([0-9]+[.,]?[0-9]*)", raw_texto)
                if match:
                    divisa = match.group(1)
                    nav_str = match.group(2).replace(",", ".")
                    try:
                        nav = float(nav_str)
                    except:
                        nav = None
                else:
                    print(f"⚠️ No se pudo extraer divisa y NAV de: {raw_texto}")

       
        # Fallback para NAV si no hay fila de "VL"
        if nav is None:
            celda_nav = tabla.find("td", class_="line text", string=re.compile(r"[A-Z]{3}\s*[0-9]"))
            if celda_nav:
                raw_texto = celda_nav.get_text(" ", strip=True).replace("\xa0", " ").strip()
                match = re.search(r"([A-Z]{3})\s+([0-9]+[.,]?[0-9]*)", raw_texto)
                if match:
                    divisa = match.group(1)
                    nav_str = match.group(2).replace(",", ".")
                    try:
                        nav = float(nav_str)
                    except:
                        nav = None
                else:
                    print(f"⚠️ Fallback: no se pudo extraer divisa y NAV de: {raw_texto}")

        # Fallback explícito para ISIN
        if not isin:
            for fila in tabla.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) >= 3 and "ISIN" in celdas[0].get_text(strip=True).upper():
                    posible_isin = celdas[2].get_text(strip=True).upper()
                    if es_isin(posible_isin):
                        isin = posible_isin
                        break

        nombre = soup.find("h1").text.strip() if soup.find("h1") else "Fondo sin nombre"

        # Extraer variación diaria (1 d%) con búsqueda contextual por fila "Cambio del día"
        variacion_1d = None
        try:
            for fila in tabla.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) >= 2 and "Cambio del día" in celdas[0].get_text(strip=True):
                    texto_var = celdas[-1].get_text(strip=True).replace("%", "").replace(",", ".")
                    variacion_1d = float(texto_var)
                    break
        except Exception as e:
            print(f"⚠️ Error al extraer variación diaria: {e}")
        
        if nav is None:
            print("⚠️ No se pudo extraer NAV")
            return None
             
        
        resultado = {
            "nombre": nombre,
            "isin": isin or "",
            "nav": nav,
            "fecha": fecha,
            "divisa": divisa,
            "fuente": "Morningstar.es",
            "variacion_1d": variacion_1d
        }

        guardar_en_cache(clave_cache, resultado)
        return resultado

    except Exception as e:
        print(f"⚠️ Error al buscar fondo: {e}")
        return None