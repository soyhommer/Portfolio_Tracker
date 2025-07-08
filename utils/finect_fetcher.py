import re
import json
import time
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.nav_cache import cargar_valido_de_cache, guardar_en_cache
from utils.formatting import parsear_numero_con_miles_y_decimales


# ------------------------------------------------------
# VALIDACIÓN ISIN
# ------------------------------------------------------

def es_isin(valor: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", valor.upper()))
    
 
# ------------------------------------------------------
# PRINCIPAL: buscar_nav_finect
# ------------------------------------------------------

def buscar_nav_finect(identificador: str, portfolio_name: str) -> dict | None:
    """
    Busca la información de NAV para un fondo en Finect.com, usando Selenium para scraping
    si no hay datos válidos en caché.

    La función consulta primero el archivo de caché específico para la fuente 'finect'
    y la cartera indicada. Si encuentra datos válidos (no expirados según CACHE_TTL_HORAS),
    los devuelve directamente sin scraping.

    Si no hay datos válidos en caché, abre una sesión headless de Selenium para navegar
    a Finect.com, realiza la búsqueda por ISIN o nombre, parsea la página de resultados,
    extrae la información del fondo (NAV, fecha, divisa, ISIN, nombre) y guarda el resultado
    actualizado en caché.

    Args:
        identificador (str): ISIN o nombre del fondo a buscar.
        portfolio_name (str): Nombre de la cartera activa (determina la ruta de la caché).

    Returns:
        dict | None: Diccionario con los datos del NAV y metadatos asociados (nombre, ISIN, fecha, divisa, fuente),
                     o None si no se pudo obtener la información.
    """
            
    print(f"🔍 Buscando NAV en Finect.com para: {identificador}")

    clave_cache = (f"isin:{identificador}" if es_isin(identificador) else f"nombre:{identificador}").lower()

    # Intentar recuperar de cache
    resultado_cache = cargar_valido_de_cache("finect", portfolio_name, clave_cache)
    if resultado_cache:
        return resultado_cache

    # --------------------------------------------------
    # Selenium session
    # --------------------------------------------------
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    try:
        wait = WebDriverWait(driver, 10)

        # 1️⃣ Acceder a Finect
        driver.get("https://www.finect.com/")
        print("🌐 Accediendo a Finect.com")

        # Cookies / GDPR
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Aceptar y continuar')]")
                )
            )
            accept_btn.click()
            print("✅ Botón cookies Finect aceptado")
            time.sleep(1)
        except:
            print("ℹ️ No apareció banner Finect")

        try:
            print("⚠️ Verificando iframe GDPR ConsentManager...")
            WebDriverWait(driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, "iframe[src*='privacy-mgmt.com']"))
            )
            consent_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Aceptar')]")
                )
            )
            consent_btn.click()
            print("✅ Consentimiento GDPR aceptado")
            time.sleep(1)
            driver.switch_to.default_content()
        except:
            print("ℹ️ No apareció iframe GDPR")

        # 2️⃣ Buscar en el omnibox
        print("🔎 Buscando el input de búsqueda...")
        search_input = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[class*='OmniSearch__SearchInput']")
            )
        )
        print("✅ Input localizado")
        search_input.click()
        for char in identificador:
            search_input.send_keys(char)
            time.sleep(0.15)
        time.sleep(1)
        search_input.send_keys(Keys.RETURN)

        print("⏳ Esperando redirección...")
        time.sleep(5)
        final_url = driver.current_url
        print(f"✅ Redirigido a: {final_url}")

        # 3️⃣ Scraping de la ficha
        resultado = scrapear_ficha_finect(driver, final_url, identificador)

        # 4️⃣ Guardar en caché y devolver
        guardar_en_cache("finect", portfolio_name, clave_cache, resultado)
        return resultado

    except Exception as e:
        print(f"❌ Error general en Selenium: {e}")
        return None

    finally:
        driver.quit()

# ------------------------------------------------------
# SCRAPING FICHA FINECT
# ------------------------------------------------------


def scrapear_ficha_finect(driver, final_url, identificador) -> dict:
    resultado = {
        "nombre": "sin parsear",
        "isin": identificador.upper(),
        "nav": None,
        "fecha": None,
        "divisa": "sin parsear",
        "fuente": "Finect.com",
        "variacion_1d": None
    }

    # ------------------------------
    # Nombre del fondo
    # ------------------------------
    try:
        print("🔎 Buscando NOMBRE del fondo con CSS selector...")
        h1_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1[class*='Headings__H1']")
            )
        )
        resultado["nombre"] = h1_name.text.strip()
        print(f"✅ Nombre del fondo encontrado: {resultado['nombre']}")

    except Exception as e_css:
        print(f"⚠️ CSS selector falló: {e_css}")
        try:
            print("🔎 Intentando fallback con XPath...")
            h1_name_xpath = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div/div[2]/main/div[2]/div[1]/div[1]/section[1]/div/div/div[1]/h1")
                )
            )
            resultado["nombre"] = h1_name_xpath.text.strip()
            print(f"✅ Nombre del fondo (XPath): {resultado['nombre']}")
        except Exception as e_xpath:
            print(f"❌ Error al parsear nombre: {e_xpath}")
            resultado["nombre"] = "Fondo sin nombre"

    
    # ------------------------------
    # NAV y DIVISA del fondo
    # ------------------------------

    def parsear_nav_y_divisa(texto: str) -> tuple[float | None, str]:
        """
        Extrae el número y la divisa de un texto como '238,91€' o '136,46$'.
        Devuelve (NAV como float, Divisa como str)
        """
        # if not texto:
            # return None, "sin parsear"

        # texto = texto.strip().replace(",", ".")
       
       # # Extraer número decimal
        # numero_match = re.search(r"(\d+(?:\.\d+)?)", texto)
        # numero = float(numero_match.group(1)) if numero_match else None

        if not texto:
            return None, "sin parsear"

        texto = texto.strip()

        # EXTRAER SOLO LA PARTE NUMÉRICA
        numero_texto = "".join(c for c in texto if c.isdigit() or c in ",.")
        numero = parsear_numero_con_miles_y_decimales(numero_texto)


        # Detectar símbolo de divisa
        if "€" in texto or "EUR" in texto.upper():
            divisa = "EUR"
        elif "$" in texto or "USD" in texto.upper():
            divisa = "USD"
        elif "£" in texto or "GBP" in texto.upper():
            divisa = "GBP"
        elif "¥" in texto or "JPY" in texto.upper():
            divisa = "JPY"
        elif "CHF" in texto.upper():
            divisa = "CHF"

        return numero, divisa


    nav = None
    divisa_final = "sin parsear"

    try:
        print("🔎 Intentando CSS selector general (opción 1)...")
        nav_container = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[class*='StyledPercentLabel']")
            )
        )
        spans = nav_container.find_elements(By.TAG_NAME, "span")
        if len(spans) >= 2:
            nav_texto = spans[0].text.strip()
            divisa_texto = spans[1].text.strip()
            print(f"✅ Encontrado por CSS: NAV={nav_texto}, Divisa={divisa_texto}")
        else:
            raise ValueError("No hay suficientes spans")
    except Exception as e:
        print(f"⚠️ CSS selector general falló: {e}")
        nav_texto = None
        divisa_texto = None

    # Fallback con tus XPaths exactos
    if not nav_texto or not divisa_texto:
        try:
            print("🔎 Intentando XPaths exactos proporcionados...")
            nav_span_xpath = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH, "/html/body/div/div[2]/main/div[2]/div[1]/div[1]/section[1]/div/div/div[1]/div[1]/div/div/span/span[1]"
                ))
            )
            nav_texto = nav_span_xpath.text.strip()

            divisa_span_xpath = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((
                    By.XPATH, "/html/body/div/div[2]/main/div[2]/div[1]/div[1]/section[1]/div/div/div[1]/div[1]/div/div/span/span[2]"
                ))
            )
            divisa_texto = divisa_span_xpath.text.strip()

            print(f"✅ Encontrado por XPATH: NAV={nav_texto}, Divisa={divisa_texto}")

        except Exception as e:
            print(f"❌ Error en XPaths exactos: {e}")
            nav_texto = None
            divisa_texto = None

    # ------------------------------
    # Procesar resultado NAV y DIVISA
    # ------------------------------
    if nav_texto:
        nav, divisa_detectada = parsear_nav_y_divisa(nav_texto)
        if nav is not None:
            resultado["nav"] = nav
            print(f"✅ NAV parseado: {nav}")
        else:
            print(f"⚠️ NAV no se pudo parsear desde: {nav_texto}")

        resultado["divisa"] = divisa_detectada
        print(f"✅ Divisa detectada desde NAV: {divisa_detectada}")

    elif divisa_texto:
        # Si no había NAV combinado, parsear solo la divisa del segundo span
        try:
            divisa_texto = divisa_texto.strip().upper()
            if "€" in divisa_texto:
                divisa_final = "EUR"
            elif "$" in divisa_texto:
                divisa_final = "USD"
            elif "£" in divisa_texto or "GBP" in divisa_texto:
                divisa_final = "GBP"
            else:
                divisa_final = divisa_texto
            resultado["divisa"] = divisa_final
            print(f"✅ Divisa detectada (solo divisa_texto): {divisa_final}")
        except Exception as e:
            print(f"❌ Error al parsear divisa: {e}")

    else:
        print("⚠️ No se encontró texto para NAV ni para la divisa")
 
    
    #------------------------------
    # FECHA del fondo
    #------------------------------

    try:
        print("🔎 Buscando FECHA del fondo con CSS selector...")
        wait = WebDriverWait(driver, 5)
        time_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "time")))
        
        fecha_valor = time_el.get_attribute("datetime") or time_el.text.strip()
        if fecha_valor:
            print(f"✅ Fecha encontrada por CSS: {fecha_valor}")
            resultado["fecha"] = fecha_valor.strip()
        else:
            raise ValueError("sin contenido")
    
    except Exception as e:
        print(f"⚠️ CSS selector FECHA falló: {e}")

    # Fallback con XPATH absoluto
    try:
        print("🔎 Intentando fallback con XPath...")
        time_el = driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/main/div[2]/div[1]/section[1]/div/div/div[1]/div[1]/span/time')
        fecha_valor = time_el.get_attribute("datetime") or time_el.text.strip()
        if fecha_valor:
            print(f"✅ Fecha encontrada por XPath: {fecha_valor}")
            resultado["fecha"] = fecha_valor.strip()
        else:
            raise ValueError("sin contenido")
    
    except Exception as e:
        print(f"❌ Error al parsear FECHA: {e}")

    print("✅ Scraping Finect completado:", resultado)
    
    return resultado

