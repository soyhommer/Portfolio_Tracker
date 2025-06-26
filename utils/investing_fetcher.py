import re
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from unidecode import unidecode
from urllib.parse import quote
from lxml import html 

CACHE_PATH = Path("data/cache_nav_investing.json")
CACHE_TTL_HORAS = 24

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def es_isin(valor: str) -> bool:
    """
    Determina si una cadena es un ISIN válido.
    Un ISIN tiene 12 caracteres: 2 letras + 10 caracteres alfanuméricos.
    """
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

def guardar_en_cache(nombre_fondo, data):
    print(f"📝 Guardando en caché: {nombre_fondo}")
    cache = cargar_cache()
    cache[nombre_fondo.lower()] = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    guardar_cache(cache)

def buscar_url_investing_por_isin(isin: str) -> str | None:
    query = quote(isin)
    url_busqueda = f"https://www.investing.com/search/?q={query}"
    try:
        response = requests.get(url_busqueda, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        enlaces = soup.select("a.js-inner-all-results-quote-item")

        for enlace in enlaces:
            href = enlace.get("href")
            if href and href.startswith("/funds/"):
                return f"https://www.investing.com{href}"
    except Exception as e:
        print(f"⚠️ Error en búsqueda por ISIN: {e}")
    return None

def buscar_url_investing_por_nombre(nombre_fondo: str) -> str | None:
    query = quote(nombre_fondo)
    url_busqueda = f"https://www.investing.com/search/?q={query}"
    try:
        response = requests.get(url_busqueda, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        enlaces = soup.select("a.js-inner-all-results-quote-item")

        for enlace in enlaces:
            href = enlace.get("href", "")
            if href.startswith("/funds/"):
                return f"https://www.investing.com{href}"
    except Exception as e:
        print(f"⚠️ Error en búsqueda por nombre: {e}")
    return None

def buscar_nav_investing(identificador: str) -> dict | None:
    print(f"🔍 Buscando NAV en Investing.com para: {identificador}")
    clave_cache = f"isin:{identificador}" if es_isin(identificador) else f"nombre:{identificador}"

    # Buscar en caché
    cache = cargar_cache()
    if clave_cache in cache:
        entrada = cache[clave_cache]
        try:
            fecha_guardado = datetime.fromisoformat(entrada["timestamp"])
            if (datetime.now() - fecha_guardado).total_seconds() < CACHE_TTL_HORAS * 3600:
                print("📦 Recuperado de caché por clave")
                return entrada["data"]
            else:
                print("⏱️ Caché expirada para esta clave")
        except Exception as e:
            print(f"⚠️ Error al interpretar timestamp en caché: {e} → se ignorará y se hará búsqueda online")

    # 2. Si clave_cache no existe, pero es un ISIN, buscar dentro del contenido cacheado
    if es_isin(identificador):
        for key, entrada in cache.items():
            datos = entrada["data"]
            if "isin" in datos and datos["isin"] == identificador.upper():
                print(f"📦 Recuperado de caché por ISIN ({identificador}) en entrada {key}")
                return datos

    # Búsqueda online
    if es_isin(identificador):
        url = buscar_url_investing_por_isin(identificador)
    else:
        url = buscar_url_investing_por_nombre(identificador)

    if not url:
        print("❌ No se encontró un enlace válido")
        return None

    print(f"✅ Enlace preciso encontrado: {url}")
    try:
        response_fondo = requests.get(url, headers=HEADERS)
        response_fondo.raise_for_status()
        soup_fondo = BeautifulSoup(response_fondo.text, "html.parser")

        # Extraer NAV
        nav_tag = soup_fondo.find("span", id="last_last")
        if not nav_tag:
            return None
        nav_str = nav_tag.text.strip().replace("\xa0", "")
        if "." in nav_str and "," in nav_str:
            nav_str = nav_str.replace(".", "").replace(",", ".")
        else:
            nav_str = nav_str.replace(",", ".")
        nav = float(nav_str)

        # Extraer variación diaria (1 d%) desde clase específica "pcp"
        variacion_1d = None
        try:
            span_var = soup_fondo.find("span", class_=re.compile(r"pid-\d+-pcp"))
            if span_var:
                texto_var = span_var.text.strip().replace("%", "").replace(",", ".")
                variacion_1d = float(texto_var)
        except Exception as e:
            print(f"⚠️ Error al extraer variación relativa diaria: {e}")

        # Extraer ISIN
        isin = None
        for span in soup_fondo.find_all("span", string="ISIN:"):
            next_span = span.find_next_sibling("span", class_="elp")
            if next_span:
                isin = (next_span.get("title") or next_span.text).strip()
                break

        # Extraer fecha
        fecha_tag = soup_fondo.find("span", class_=lambda x: x and x.startswith("bold pid-") and x.endswith("-time"))
        if fecha_tag:
            try:
                raw_fecha = fecha_tag.text.strip()
                fecha = datetime.strptime(raw_fecha, "%d/%m").replace(year=datetime.today().year).date().isoformat()
            except:
                fecha = None
        else:
            fecha = None

        # Extraer Divisa
        divisa = "ERROR"
        try:
            tree = html.fromstring(response_fondo.text)
            divisa_node = tree.xpath('/html/body/div[7]/section/div[4]/div[1]/div[1]/div[2]/div[2]/span[4]/text()')
            if divisa_node:
                divisa_raw = divisa_node[0].strip().upper()
                if re.fullmatch(r"[A-Z]{3}", divisa_raw):
                    divisa = divisa_raw
        except Exception as e:
            print(f"⚠️ XPath divisa fallo: {e}")
        
        nombre_web = soup_fondo.find("h1").text.strip()
        resultado = {
            "nombre": nombre_web,
            "isin": isin,
            "nav": nav,
            "fecha": fecha,
            "divisa": divisa,
            "fuente": "Investing.com",
            "variacion_1d": variacion_1d
        }

        guardar_en_cache(clave_cache, resultado)
        return resultado

    except Exception as e:
        print(f"⚠️ Error al buscar fondo: {e}")
        return None
