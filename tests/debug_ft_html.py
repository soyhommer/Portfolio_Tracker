import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def descargar_html_ft(isin):
    url = f"https://markets.ft.com/data/funds/tearsheet/summary?s={isin}"
    print(f"🔍 Descargando HTML de: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    with open(f"debug_ft_{isin}.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    print(f"✅ Guardado como debug_ft_{isin}.html")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python debug_ft_html.py ES0112611001")
    else:
        descargar_html_ft(sys.argv[1])