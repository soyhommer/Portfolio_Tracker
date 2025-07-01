# utils/config.py

import json
from pathlib import Path

# Tiempo en horas tras el cual se considera que los NAVs están expirados
CACHE_TTL_HORAS = 24

# Leer configuración general
with open("config/settings.json", "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

CARTERAS_PATH = SETTINGS["carteras_path"]

# --------------------------
# Rutas base de datos locales
# --------------------------
DATA_DIR = Path("data")

TRANSACCIONES_DIR = DATA_DIR / "transacciones"
NAV_HISTORICO_DIR = DATA_DIR / "nav_historico"
BENCHMARK_DIR = DATA_DIR / "benchmark"
OUTPUT_DIR = DATA_DIR / "outputs"

# Asegurar existencia de directorios
TRANSACCIONES_DIR.mkdir(parents=True, exist_ok=True)
NAV_HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------
# CACHE PARA NOMBRE DE ACTIVO
# --------------------------
CACHE_NOMBRE_PATH = NAV_HISTORICO_DIR / "cache_nombre_activo.json"


# Any module get the path for a given portfolio without knowing the structure. Remove hard-coded paths in the backend
def get_transactions_path(portfolio_name: str):
    """
    Returns the Path to the transactions CSV for a specific portfolio.
    """
    return TRANSACCIONES_DIR / f"{portfolio_name}.csv"


def get_benchmark_path(portfolio_name: str):
    """
    Returns the Path to the benchmark CSV for a specific portfolio.
    """
    return BENCHMARK_DIR / f"{portfolio_name}_benchmark.csv"
