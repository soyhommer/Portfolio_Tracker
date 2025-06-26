import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

DOWNLOAD_DIR = os.path.abspath("data/nav_historico")
PROFILE_DIR = os.path.abspath(".chrome_profile")


def iniciar_driver_chrome(persistente=True, headless=False, user_data_dir=None):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    if persistente:
        if not user_data_dir:
            user_data_dir = PROFILE_DIR
        options.add_argument(f"--user-data-dir={user_data_dir}")
        print(f"🧠 Usando perfil persistente en: {user_data_dir}")

    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": DOWNLOAD_DIR,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver


def cargar_cookies(driver, cookies_path):
    with open(cookies_path, "r") as f:
        cookies = json.load(f)
    driver.get("https://www.investing.com")
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()


def aceptar_modal_cookies(driver, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "onetrust-banner-sdk"))
        )
        aceptar_btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        aceptar_btn.click()
        print("🍪 Modal de cookies aceptado.")
        time.sleep(1)
    except:
        print("⚠️ No apareció modal de cookies.")


def descargar_csv_investing(driver, url_fondo, fecha_inicio, fecha_fin, timeout=15):
    driver.get(url_fondo)
    aceptar_modal_cookies(driver)

    # Calendario
    rango_fecha = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="widgetFieldDateRange"]'))
    )
    rango_fecha.click()

    input_desde = driver.find_element(By.ID, "startDate")
    input_hasta = driver.find_element(By.ID, "endDate")
    input_desde.clear()
    input_desde.send_keys(fecha_inicio)
    input_hasta.clear()
    input_hasta.send_keys(fecha_fin)

    aplicar_btn = driver.find_element(By.ID, "applyBtn")
    aplicar_btn.click()

    WebDriverWait(driver, timeout).until(
        EC.text_to_be_present_in_element((By.ID, "widgetFieldDateRange"), fecha_inicio[-4:])
    )

    # Descargar
    download_btn = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="column-content"]/div[4]/div/a'))
    )
    download_btn.click()

    print("⏳ Esperando descarga...")
    time.sleep(5)


def mover_csv_descargado(isin: str):
    archivos = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".csv")]
    archivos.sort(key=lambda f: os.path.getmtime(os.path.join(DOWNLOAD_DIR, f)), reverse=True)

    if not archivos:
        print("❌ No se encontró CSV descargado.")
        return None

    archivo_origen = os.path.join(DOWNLOAD_DIR, archivos[0])
    archivo_destino = os.path.join(DOWNLOAD_DIR, f"{isin}.csv")
    os.rename(archivo_origen, archivo_destino)
    print(f"✅ CSV guardado como: {archivo_destino}")
    return archivo_destino


def descargar_historico_nav(isin, url_fondo, start_date, end_date, overwrite=False):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    if not os.path.exists(PROFILE_DIR):
        os.makedirs(PROFILE_DIR)

    output_path = os.path.join(DOWNLOAD_DIR, f"{isin}.csv")
    if os.path.exists(output_path) and not overwrite:
        print(f"✅ Archivo ya existe: {output_path}")
        return output_path

    driver = iniciar_driver_chrome(persistente=True, headless=False, user_data_dir=PROFILE_DIR)
    try:
        descargar_csv_investing(driver, url_fondo, start_date, end_date)
        return mover_csv_descargado(isin)
    finally:
        driver.quit()


if __name__ == "__main__":
    # Ejemplo de uso
    descargar_historico_nav(
        isin="ES0116567035",
        url_fondo="https://www.investing.com/funds/cartesio-x-fi-historical-data",
        start_date="05/26/2020",
        end_date="06/26/2025",
        overwrite=True
    )
