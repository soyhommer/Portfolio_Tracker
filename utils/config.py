# utils/config.py

import json
from pathlib import Path

# Tiempo en horas tras el cual se considera que los NAVs están expirados
CACHE_TTL_HORAS = 24

with open("config/settings.json", "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

CARTERAS_PATH = SETTINGS["carteras_path"]

# Rutas de datos
DATA_DIR = Path("data")
TRANSACCIONES_DIR = DATA_DIR / "transacciones"
NAV_HISTORICO_DIR = DATA_DIR / "nav_historico"

# Crear directorios si no existen
TRANSACCIONES_DIR.mkdir(parents=True, exist_ok=True)
NAV_HISTORICO_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------
# CACHE PARA NOMBRE DE ACTIVO
# --------------------------
CACHE_NOMBRE_PATH = NAV_HISTORICO_DIR / "cache_nombre_activo.json"