from utils.historial_nav import descargar_historico_nav

# ⚠️ Prueba 1: requiere tener sesión de Investing.com abierta en Chrome (perfil persistente)
# Ejecutar con Chrome abierto o usar perfil configurado ('.chrome_profile')

if __name__ == "__main__":
    ISIN = "ES0116567035"
    URL_FONDO = "https://www.investing.com/funds/cartesio-x-fi-historical-data"
    FECHA_INICIO = "05/26/2023"
    FECHA_FIN = "06/26/2025"

    ruta_csv = descargar_historico_nav(
        isin=ISIN,
        url_fondo=URL_FONDO,
        start_date=FECHA_INICIO,
        end_date=FECHA_FIN,
        overwrite=True
    )

    print(f"📄 Archivo generado: {ruta_csv}")
