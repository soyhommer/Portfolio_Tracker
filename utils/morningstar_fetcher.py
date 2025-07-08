import re
import requests
import json
import time
from typing import List
from lxml import etree
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains


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

def buscar_morningstar_resultados(query: str, max_results: int = 5) -> List[str]:
    """
    Usa Selenium para automatizar la búsqueda en https://global.morningstar.com/es
    y devuelve una lista de URLs a las fichas de los fondos encontradas.

    Args:
        query (str): Nombre o ISIN del fondo a buscar.
        max_results (int): Número máximo de resultados a devolver.

    Returns:
        List[str]: Lista de URLs a las fichas de Morningstar.
    """

    urls_encontradas = []

    # 1️⃣ Configurar Chrome en modo headless
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)

    try:
        # 2️⃣ Navegar a la página principal
        driver.get("https://global.morningstar.com/es?marketID=es")
        time.sleep(2)

        # 3️⃣ Aceptar cookies si aparecen (opcional)
        try:
            aceptar_btn = driver.find_element(By.XPATH, "//button[contains(., 'Aceptar')]")
            aceptar_btn.click()
            time.sleep(1)
        except Exception:
            pass

        # 4️⃣ Localizar el campo de búsqueda
        try:     
        
            print("🔎 Buscando el input de búsqueda...")
            search_input = driver.find_element(By.CSS_SELECTOR, "input.mds-search-field__input__mdc")
            print("✅ Campo de búsqueda encontrado.")

            print(f"✅ Emulando tecleo humano con ActionChains...")
            actions = ActionChains(driver)
            actions.move_to_element(search_input).click()
            for char in query:
                actions.send_keys(char)
                actions.pause(0.15)
            actions.perform()

            print("⏳ Esperando lista de resultados sugeridos...")
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".mdc-site-search-results__group_mdc")))
            print("✅ Lista de resultados cargada. Analizando sugerencias...")

            suggestions = driver.find_elements(By.CSS_SELECTOR, "a")
            match_found = False
            for s in suggestions:
                try:
                    if es_isin(query):
                        # Buscar ISIN exacto en meta
                        meta_span = s.find_element(By.CSS_SELECTOR, "span.mdc-site-search-results__result-meta_mdc")
                        if meta_span and meta_span.text.strip().upper() == query.strip().upper():
                            print(f"✅ ISIN exacto encontrado en sugerencia: {meta_span.text}")
                            s.click()
                            match_found = True
                            break
                    else:
                        # Buscar nombre en middle
                        name_span = s.find_element(By.CSS_SELECTOR, "span.middle-truncated-text_mdc")
                        if name_span and query.lower() in name_span.text.lower():
                            print(f"✅ Nombre coincidente encontrado en sugerencia: {name_span.text}")
                            s.click()
                            match_found = True
                            break
                except Exception as e:
                    print(f"⚠️ Error analizando sugerencia: {e}")
                    continue

            if not match_found:
                print("❌ No se encontró ninguna sugerencia que coincida.")
                return []

        except TimeoutException:
            print("❌ Timeout esperando sugerencias de Morningstar. No se encontraron resultados.")
            return []

        except Exception as e:
            print(f"❌ Error en la búsqueda con Selenium: {e}")
            return []

        # 5️⃣ Extraer enlaces de resultados
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/es/inversiones/fondos/']")
        for link in links:
            href = link.get_attribute("href")
            if href and "/cotizacion" in href and href not in urls_encontradas:
                urls_encontradas.append(href)
            if len(urls_encontradas) >= max_results:
                break

    except Exception as e:
        print(f"❌ Error al buscar en Morningstar: {e}")

    finally:
        driver.quit()

    return urls_encontradas

def buscar_nav_morningstar(identificador: str) -> dict | None:
    print(f"🔍 Buscando NAV en Morningstar para: {identificador}")
    clave_cache = f"isin:{identificador}" if es_isin(identificador) else f"nombre:{identificador}"
    cache = cargar_cache()

    # 1️⃣ Verificar si está en caché y es válido
    if clave_cache in cache:
        entrada = cache[clave_cache]
        try:
            fecha_guardado = datetime.fromisoformat(entrada["timestamp"])
            data = entrada["data"]

            if (datetime.now() - fecha_guardado).total_seconds() < CACHE_TTL_HORAS * 3600:
                if "nav" in data and "variacion_1d" in data:
                    print("📦 Recuperado de caché")
                    return data
                else:
                    print("⏳ Datos incompletos en caché, se volverá a scrapear")
        except Exception as e:
            print(f"⚠️ Error interpretando timestamp de caché: {e}")

    # 2️⃣ Intentar scrapear usando Selenium y requests
    try:
        # 2.1 Obtener el enlace correcto desde el buscador Morningstar Global
        enlaces = buscar_morningstar_resultados(identificador)
        if not enlaces:
            print("❌ No se encontró ningún resultado en Morningstar")
            return None

        url_fondo = enlaces[0]
        print(f"✅ Enlace obtenido: {url_fondo}")

        # 2.2 Descargar la página del fondo
        resp_fondo = requests.get(url_fondo, headers=HEADERS)
        resp_fondo.raise_for_status()
        soup = BeautifulSoup(resp_fondo.text, "html.parser")
        html_bytes = resp_fondo.content

        # Parser lxml para XPath
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_bytes, parser)

        # Variables de salida
        nav, fecha, isin, nombre, divisa, variacion_1d = None, None, None, "Fondo sin nombre", "ERROR", None

        # 3️⃣ Extraer ISIN
        try:
            isin_tag = soup.select_one("h1 abbr.investments-page__title-identifier_mdc")
            if isin_tag and isin_tag.get_text(strip=True):
                isin = isin_tag.get_text(strip=True)
            else:
                xpath_result = tree.xpath("//h1/abbr")
                if xpath_result and xpath_result[0].text:
                    isin = xpath_result[0].text.strip()
        except Exception as e:
            print(f"⚠️ Error extrayendo ISIN: {e}")

        # 4️⃣ Extraer Nombre
        try:
            nombre_tag = soup.select_one("h1 span[itemprop='name']")
            if nombre_tag and nombre_tag.get_text(strip=True):
                nombre = nombre_tag.get_text(strip=True)
            else:
                xpath_result = tree.xpath("//h1/span")
                if xpath_result and xpath_result[0].text:
                    nombre = xpath_result[0].text.strip()
        except Exception as e:
            print(f"⚠️ Error extrayendo nombre: {e}")

        # 5️⃣ Extraer Fecha
        try:
            time_tag = soup.select_one("time.mdc-data-point--date")
            if time_tag:
                fecha = time_tag.get("datetime", "").strip() or time_tag.get_text(strip=True)
            else:
                xpath_result = tree.xpath("//time")
                if xpath_result:
                    fecha = xpath_result[0].get("datetime", "").strip() or xpath_result[0].text.strip()
        except Exception as e:
            print(f"⚠️ Error extrayendo fecha: {e}")

        # 6️⃣ Extraer NAV                
        try:
            nav_tags = soup.select("p.sal-dp-value")
            if nav_tags and len(nav_tags) >= 1:
                nav_str = nav_tags[0].get_text(strip=True).replace(".", "").replace(",", ".")
                nav = float(nav_str)
            else:
                xpath_result = tree.xpath("//p[contains(@class, 'sal-dp-value')]")
                if xpath_result and len(xpath_result) >= 1 and xpath_result[0].text:
                    nav_raw = xpath_result[0].text.strip().replace(".", "").replace(",", ".")
                    nav = float(nav_raw)
        except Exception as e:
            print(f"⚠️ Error extrayendo NAV: {e}")
            nav = None


        # 7️⃣ Extraer variación 1d%
        try:
            var_tags = soup.select("p.sal-dp-value")
            if var_tags and len(var_tags) >= 2:
                var_str = var_tags[1].get_text(strip=True).replace("%", "").replace(".", "").replace(",", ".")
                variacion_1d = float(var_str)
            else:
                xpath_result = tree.xpath("//p[contains(@class, 'sal-dp-value')]")
                if xpath_result and len(xpath_result) >= 2 and xpath_result[1].text:
                    var_raw = xpath_result[1].text.strip().replace("%", "").replace(".", "").replace(",", ".")
                    variacion_1d = float(var_raw)
        except Exception as e:
            print(f"⚠️ Error extrayendo variacion_1d: {e}")
            variacion_1d = None

        # 8️⃣ Extraer Divisa
        try:
            divisa_tag = soup.select_one("h3.sal-mip-cost-projection__title")
            if divisa_tag and divisa_tag.get_text(strip=True):
                match = re.search(r"\((.*?)\)", divisa_tag.get_text(strip=True))
                if match:
                    divisa = match.group(1).strip()
            else:
                xpath_result = tree.xpath("//h3[contains(@class, 'sal-mip-cost-projection__title')]")
                if xpath_result and xpath_result[0].text:
                    match = re.search(r"\((.*?)\)", xpath_result[0].text.strip())
                    if match:
                        divisa = match.group(1).strip()
        except Exception as e:
            print(f"⚠️ Error extrayendo divisa: {e}")

        # 9️⃣ Empaquetar resultado
        resultado = {
            "nombre": nombre,
            "isin": isin or "",
            "nav": nav,
            "fecha": fecha,
            "divisa": divisa,
            "fuente": "Morningstar.es",
            "variacion_1d": variacion_1d
        }

        # 10️⃣ Guardar en caché y retornar
        guardar_en_cache(clave_cache, resultado)
        return resultado

    except Exception as e:
        print(f"⚠️ Error general al buscar fondo: {e}")
        return None
