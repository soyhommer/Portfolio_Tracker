import json
import os
from utils.merge_nav_data import merge_nav_data

CACHE_NAV_REAL_PATH = os.path.join("data", "cache_nav_real.json")

def actualizar_cache_isin(nombre, nuevo_isin):
    """Actualiza el ISIN en el cache_nav_real.json, y lo complementa con datos reales si es posible."""

    try:
        # --- 1. Leer cache_nav_real ---
        if os.path.exists(CACHE_NAV_REAL_PATH):
            with open(CACHE_NAV_REAL_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
        else:
            cache = {}

        # --- 2. Ejecutar merge_nav_data con el ISIN para obtener datos reales ---
        resultado = merge_nav_data(nuevo_isin.strip())
        if not resultado or not resultado.get("nav"):
            print(f"⚠️ No se pudo obtener NAV al actualizar cache para: {nuevo_isin}")
            resultado = {
                "isin": nuevo_isin.strip(),
                "nombre": nombre
            }
        else:
            resultado["isin"] = nuevo_isin.strip()
            resultado["nombre"] = nombre

        # --- 3. Guardar en cache bajo el nombre como clave ---
        cache[nuevo_isin.strip()] = resultado
        with open(CACHE_NAV_REAL_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

        print(f"✅ Cache NAV actualizado para {nombre} (ISIN: {nuevo_isin})")

    except Exception as e:
        print(f"⚠️ Error actualizando cache_nav_real.json: {e}")