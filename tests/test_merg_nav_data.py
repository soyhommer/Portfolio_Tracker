from utils.merge_nav_data import merge_nav_data
from utils.investing_fetcher import buscar_nav_investing
from utils.morningstar_fetcher import buscar_nav_morningstar
from utils.ft_fetcher import buscar_nav_ft

import json
from pathlib import Path

def dump_json(nombre, data):
    Path("debug_nav_dumps").mkdir(exist_ok=True)
    with open(f"debug_nav_dumps/{nombre}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

fondos_prueba = [
    "IE00B2NXKW18",
    "IE0031724234",    
]

print("\n🧪 Test de merge_nav_data con múltiples identificadores:\n")

for identificador in fondos_prueba:
    print(f"🔎 {identificador}")

    morning = buscar_nav_morningstar(identificador)
    ft = buscar_nav_ft(identificador)
    invest = buscar_nav_investing(identificador)
    merged = merge_nav_data(identificador)

    dump_json(f"{identificador}_morningstar", morning or {})
    dump_json(f"{identificador}_ft", ft or {})
    dump_json(f"{identificador}_investing", invest or {})
    dump_json(f"{identificador}_merged", merged)

    for campo, valor in merged.items():
        print(f"  {campo}: {valor}")
    print("\u2014" * 40)
