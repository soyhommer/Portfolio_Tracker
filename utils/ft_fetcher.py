import re
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
from lxml import html

CACHE_PATH = Path("data/cache_nav_ft.json")
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

def buscar_en_cache(nombre_clave):
    cache = cargar_cache()
    entrada = cache.get(nombre_clave.lower())
    if entrada:
        try:
            fecha_guardado = datetime.fromisoformat(entrada["timestamp"])
            if (datetime.now() - fecha_guardado).total_seconds() < CACHE_TTL_HORAS * 3600:
                print("📦 Recuperado de caché por clave")
                return entrada["data"]
        except Exception as e:
            print(f"⚠️ Error al interpretar timestamp: {e}")
    return None

def buscar_url_ft_por_nombre(nombre: str) -> str | None:
    query = quote(nombre)
    url_busqueda = f"https://markets.ft.com/data/search?query={query}&assetClass=Fund"
    try:
        resp = requests.get(url_busqueda, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        enlace = soup.select_one("a[href*='/data/funds/tearsheet/summary?s=']")
        if enlace and "href" in enlace.attrs:
            return "https://markets.ft.com" + enlace["href"]
    except Exception as e:
        print(f"⚠️ Error buscando por nombre en FT: {e}")
    return None

def buscar_nav_ft(identificador: str) -> dict | None:
    print(f"🔍 Buscando NAV en FT.com para: {identificador}")
    clave_cache = f"isin:{identificador}" if es_isin(identificador) else f"nombre:{identificador}"
    resultado_cache = buscar_en_cache(clave_cache)
    if resultado_cache:
        return resultado_cache

    if es_isin(identificador):
        url_ficha = f"https://markets.ft.com/data/funds/tearsheet/summary?s={identificador}"
    else:
        url_ficha = buscar_url_ft_por_nombre(identificador)
        if not url_ficha:
            print("❌ No se encontró enlace al fondo")
            return None

    try:
        response = requests.get(url_ficha, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Depuración HTML local (temporal)
        with open("debug_ft_last.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())

       # NAV
        nav = None
        nav_tag = soup.find("span", class_="mod-ui-data-list__value")
        if nav_tag:
            try:
                nav = float(nav_tag.text.strip().replace(",", ""))
            except Exception as e:
                print(f"⚠️ Error extrayendo NAV: {e}")

        # #Aquisicion de 1d%
        # variacion_1d_bs = None
        # variacion_1d_xpath = None

        # try:
            # # ✅ Método 1: BeautifulSoup (bloque principal)
            # var_tag = soup.find("span", class_="mod-format--neg") or soup.find("span", class_="mod-format--pos")
            # if var_tag:
                # for string in var_tag.strings:
                    # if "%" in string:
                        # porcentaje = string.split("/")[-1].strip().replace("%", "").replace(",", ".")
                        # variacion_1d_bs = float(porcentaje)
                        # break

            # # ✅ Método 2: BeautifulSoup (tabla secundaria)
            # if variacion_1d_bs is None:
                # filas = soup.select("table.mod-ui-data-list__table tr")
                # for fila in filas:
                    # encabezado = fila.find("span", class_="mod-ui-data-list__label")
                    # if encabezado and "Day Change" in encabezado.text:
                        # valor = fila.find("span", class_="mod-ui-data-list__value")
                        # if valor and "%" in valor.text:
                            # texto = valor.text.strip().split("/")[-1].replace("%", "").replace(",", ".")
                            # variacion_1d_bs = float(texto)
                            # break

            # # ✅ Método 3: XPath puro como último recurso
            # try:
                # tree = html.fromstring(response.text)
                # nodes = tree.xpath('/html/body/div[3]/div[2]/section[1]/div/div/div[1]/div[2]/ul/li[2]/span[2]/span/text()')
                # if nodes:
                    # porcentaje_xpath = nodes[0].strip().split("/")[-1].replace("%", "").replace(",", ".")
                    # variacion_1d_xpath = float(porcentaje_xpath)
            # except Exception as e:
                # print(f"⚠️ XPath fallback falló: {e}")
            
            # ✅ Selección final del valor más confiable
            # variacion_1d = None
            # if variacion_1d_bs is not None:
                # variacion_1d = variacion_1d_bs
            # elif variacion_1d_xpath is not None:
                # variacion_1d = variacion_1d_xpath

            # ⚠️ Validación cruzada (debug opcional)
            # if variacion_1d_bs and variacion_1d_xpath:
                # diferencia = abs(variacion_1d_bs - variacion_1d_xpath)
                # if diferencia > 0.05:
                    # print(f"⚠️ Discrepancia entre métodos BS={variacion_1d_bs} vs XPath={variacion_1d_xpath} -> Usando BS")

        # except Exception as e:
            # print(f"⚠️ Error extrayendo variación diaria: {e}")
        
        #Aquisicion de 1d% por Xpath
        variacion_1d = None
        try:
            tree = html.fromstring(response.text)
            nodes = tree.xpath('/html/body/div[3]/div[2]/section[1]/div/div/div[1]/div[2]/ul/li[2]/span[2]/span/text()')
            if nodes:
                texto_xpath = nodes[0].strip().split("/")[-1].replace("%", "").replace(",", ".")
                variacion_1d = float(texto_xpath)
        except Exception as e:
            print(f"⚠️ XPath fallback falló: {e}")
    
        # Fecha
        fecha = None
        fecha_tag = soup.find("div", class_="mod-disclaimer")
        if fecha_tag:
            match = re.search(r"as of (\w{3}) (\d{1,2}) (\d{4})", fecha_tag.text)
            if match:
                mes_abbr, dia, anio = match.groups()
                try:
                    fecha = datetime.strptime(f"{dia} {mes_abbr} {anio}", "%d %b %Y").date().isoformat()
                except:
                    pass

        # Nombre
        nombre = None
        nombre_tag = soup.find("h1", class_="mod-tearsheet-overview__header_name mod-tearsheet-overview__header_name--large")
        if not nombre_tag:
            nombre_tag = soup.find("h1")
        if nombre_tag:
            nombre = nombre_tag.text.strip()

        # Extraer divisa dinámica vía XPath
        divisa = "EUR"  # por defecto si falla
        try:
            divisa_nodes = tree.xpath('/html/body/div[3]/div[2]/section[1]/div/div/div[1]/div[1]/div[2]/span/text()')
            if divisa_nodes:
                texto = divisa_nodes[0].strip()
                if ":" in texto:
                    divisa = texto.split(":")[1].strip().upper()
        except Exception as e:
            print(f"⚠️ No se pudo extraer divisa: {e}")
        
        # ISIN correcto - primer intento en cabecera
        isin = None
        isin_tag = soup.find("span", class_="mod-tearsheet-overview__header_symbol")
        if isin_tag:
            match = re.search(r"([A-Z]{2}[A-Z0-9]{10})", isin_tag.text.strip())
            if match:
                isin = match.group(1)

        # ISIN alternativo: buscar en tabla de perfil
        if not isin:
            tables = soup.select("table.mod-ui-table")
            for table in tables:
                for row in table.find_all("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if th and td and th.text.strip().upper() == "ISIN":
                        posible_isin = td.text.strip().upper()
                        if es_isin(posible_isin):
                            isin = posible_isin
                            break

        if not nav:
            print("⚠️ No se pudo extraer NAV")
            return None

        resultado = {
            "nombre": nombre or "Fondo sin nombre",
            "isin": isin if isin else (identificador.upper() if es_isin(identificador) else ""),
            "nav": nav,
            "fecha": fecha,
            "divisa": divisa,
            "fuente": "FT.com",
            "variacion_1d": variacion_1d
        }

        guardar_en_cache(clave_cache, resultado)
        return resultado

    except Exception as e:
        print(f"⚠️ Error al acceder a FT.com: {e}")
        return None
