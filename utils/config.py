# utils/config.py

import json

# Tiempo en horas tras el cual se considera que los NAVs están expirados
CACHE_TTL_HORAS = 24

with open("config/settings.json", "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

CARTERAS_PATH = SETTINGS["carteras_path"]
