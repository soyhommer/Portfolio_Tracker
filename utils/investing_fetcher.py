import re
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from unidecode import unidecode
from urllib.parse import quote
from lxml import html 
from utils.nav_cache import cargar_valido_de_cache, guardar_en_cache
from utils.formatting import parsear_numero_con_miles_y_decimales

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

def buscar_nav_investing(identificador: str, portfolio_name: str) -> dict | None:
    print(f"🔍 Buscando NAV en Investing.com para: {identificador}")
    clave_cache = (f"isin:{identificador}" if es_isin(identificador) else f"nombre:{identificador}").lower()

    # Intentar recuperar de caché
    resultado_cache = cargar_valido_de_cache("investing", portfolio_name, clave_cache)
    if resultado_cache:
        return resultado_cache

    # # 2. Si clave_cache no existe, pero es un ISIN, buscar dentro del contenido cacheado
    # if es_isin(identificador):
        # for key, entrada in cache.items():
            # datos = entrada["data"]
            # if "isin" in datos and datos["isin"] == identificador.upper():
                # print(f"📦 Recuperado de caché por ISIN ({identificador}) en entrada {key}")
                # return datos

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
        nav = parsear_numero_con_miles_y_decimales(nav_str)

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

        guardar_en_cache("investing", portfolio_name, clave_cache, resultado)
        return resultado

    except Exception as e:
        print(f"⚠️ Error al buscar fondo: {e}")
        return None
