import os
import re
import json
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.merge_nav_data import merge_nav_data


CACHE_PATH = Path("data/cache_nav_real.json")
CACHE_PATH.parent.mkdir(exist_ok=True, parents=True)

CACHE_TTL_HORAS = 24

def es_isin(valor):
    return isinstance(valor, str) and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", valor.strip())

def limpiar_isin(df):
    """
    Limpia y valida la columna 'ISIN' de un DataFrame de transacciones.
    Elimina caracteres invisibles, convierte valores no válidos en None.
    """
    if "ISIN" not in df.columns:
        return df

    def normalizar(x):
        if not isinstance(x, str):
            return None
        x = x.strip().replace("\u200b", "").replace("\u00a0", "")
        return x if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", x) else None

    df["ISIN"] = df["ISIN"].apply(normalizar)
    return df

def validar_isin_vs_nombre(df):
    if "ISIN" not in df.columns or "Posición" not in df.columns:
        return

    conflictos = (
        df.dropna(subset=["ISIN", "Posición"])
          .groupby("ISIN")["Posición"]
          .nunique()
          .reset_index(name="nombres_distintos")
          .query("nombres_distintos > 1")
    )

    if not conflictos.empty:
        print("⚠️ Conflicto detectado: ISIN con múltiples nombres en el CSV.")
        conflictos_detalle = (
            df[df["ISIN"].isin(conflictos["ISIN"])]
              .drop_duplicates(subset=["ISIN", "Posición"])
              .sort_values(["ISIN", "Posición"])
        )
        print(conflictos_detalle.to_string(index=False))

        # Mostrar solo si estamos en entorno Streamlit
        try:
            st.warning("⚠️ Algunos ISIN están asociados a más de un nombre. Consulta consola para detalles.")
        except:
            pas

def cargar_cache_nav():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            base = json.load(f)
        # 🔁 Añadir clave por nombre explícitamente si no existe
        extendido = dict(base)
        for val in base.values():
            nombre = val.get("nombre")
            if nombre and nombre not in extendido:
                extendido[nombre] = val
        return extendido
    return {}

def guardar_cache_nav(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

# def get_nav_real(nombre_o_isin, forzar=False):
    # """Devuelve los datos de NAV (nav, fecha, divisa, variación, etc.) a partir del nombre o ISIN del activo."""
    # nombre_o_isin = nombre_o_isin.strip()
    
    # import inspect

    # if not nombre_o_isin.startswith("IE") and "Seilern" in nombre_o_isin:
        # print(f"\n🧭 get_nav_real llamado con: '{nombre_o_isin}'")
        # for f in inspect.stack()[1:4]:
            # print(f"↪️ llamado desde {f.function} en {f.filename}:{f.lineno}")
        
        # print(f"\n🧭 get_nav_real llamado con: '{nombre_o_isin}'")

    # # 🔍 Diagnóstico: mostrar el lugar de la llamada
    # stack = inspect.stack()
    # for frame in stack[1:4]:  # Mostramos los 3 niveles superiores
        # print(f"↪️ llamado desde {frame.function} en {frame.filename}:{frame.lineno}")
     
        
    # cache = cargar_cache_nav()

    # # 1️⃣ Si es ISIN: buscar como clave o como valor
    # if es_isin(nombre_o_isin):
        # if nombre_o_isin in cache and cache[nombre_o_isin].get("nav") is not None:
            # return cache[nombre_o_isin]
        # for datos in cache.values():
            # if datos.get("isin", "").upper() == nombre_o_isin.upper() and datos.get("nav") is not None:
                # return datos

    # # 2️⃣ Buscar por nombre como clave exacta
    # if nombre_o_isin in cache and cache[nombre_o_isin].get("nav") is not None:
        # return cache[nombre_o_isin]

    # # 3️⃣ Buscar por coincidencia de nombre dentro de los valores
    # for datos in cache.values():
        # if nombre_o_isin.lower() in datos.get("nombre", "").lower() and datos.get("nav") is not None:
            # return datos


    # # 4️⃣ No encontrado, hacer scraping y guardar en cache
    # resultado = merge_nav_data(nombre_o_isin)
    # if not resultado or not resultado.get("nav"):
        # print(f"⛔ No se pudo obtener NAV para: {nombre_o_isin}")
        # return None

    # # 5️⃣ Determinar ISIN para indexar (intenta usar el extraído, si no inventa uno)
    # isin = resultado.get("isin")
    # if not isin or not es_isin(isin):
        # isin = f"SINISIN-{nombre_o_isin[:8].upper().replace(' ', '')}"
    # resultado["isin"] = isin
    # resultado.setdefault("nombre", nombre_o_isin)  # redundante pero explícito

    # # 6️⃣ Guardar en cache tanto por nombre como por ISIN
    # cache[isin] = resultado
    # cache[nombre_o_isin] = resultado
    # guardar_cache_nav(cache)

    # print(f"📦 NAV cacheado: {nombre_o_isin} → {isin}")
    # return resultado

def get_nav_real(nombre_o_isin, forzar=False):
    """Devuelve los datos de NAV (nav, fecha, divisa, variación, etc.) a partir del nombre o ISIN del activo."""
    nombre_o_isin = nombre_o_isin.strip()
    cache = cargar_cache_nav()

    import inspect
    if not nombre_o_isin.startswith("IE") and "Seilern" in nombre_o_isin:
        print(f"\n🧭 get_nav_real llamado con: '{nombre_o_isin}'")
        for f in inspect.stack()[1:4]:
            print(f"↪️ llamado desde {f.function} en {f.filename}:{f.lineno}")

    # Si no se fuerza, intentar usar caché
    if not forzar:
        if es_isin(nombre_o_isin):
            if nombre_o_isin in cache and cache[nombre_o_isin].get("nav") is not None:
                return cache[nombre_o_isin]
            for datos in cache.values():
                if datos.get("isin", "").upper() == nombre_o_isin.upper() and datos.get("nav") is not None:
                    return datos

        if nombre_o_isin in cache and cache[nombre_o_isin].get("nav") is not None:
            return cache[nombre_o_isin]

        for datos in cache.values():
            if nombre_o_isin.lower() in datos.get("nombre", "").lower() and datos.get("nav") is not None:
                return datos

    # Si no hay datos válidos o se ha forzado, hacer scraping
    resultado = merge_nav_data(nombre_o_isin)
    if not resultado or not resultado.get("nav"):
        print(f"⛔ No se pudo obtener NAV para: {nombre_o_isin}")
        return None

    # Determinar ISIN válido
    isin = resultado.get("isin")
    if not isin or not es_isin(isin):
        isin = f"SINISIN-{nombre_o_isin[:8].upper().replace(' ', '')}"
    resultado["isin"] = isin
    resultado.setdefault("nombre", nombre_o_isin)

    # Guardar en caché por ISIN y por nombre
    cache[isin] = resultado
    cache[nombre_o_isin] = resultado
    guardar_cache_nav(cache)

    print(f"📦 NAV cacheado: {nombre_o_isin} → {isin}")
    return resultado

def refrescar_navs_si_expirados(df, forzar=False):
    """
    Revisa los ISIN en el DataFrame y actualiza su NAV si ha expirado,
    o siempre si se fuerza el refresco.
    """
    cache = cargar_cache_nav()
    ahora = datetime.now()
    isins = df["ISIN"].dropna().unique()

    for isin in isins:
        if not es_isin(isin):
            continue

        datos = cache.get(isin)

        # 🔁 Si no hay datos o forzamos, refrescamos sin más
        if not datos or forzar:
            motivo = "no está en caché" if not datos else "refresco forzado"
            print(f"🔄 ISIN {isin} → {motivo} → actualizando...")
            get_nav_real(isin, forzar=True)
            continue

        # ⏳ Validar timestamp y decidir si refrescar
        fecha_str = datos.get("fecha")
        try:
            fecha_obj = datetime.fromisoformat(fecha_str)
            segundos = (ahora - fecha_obj).total_seconds()
            expirado = segundos > CACHE_TTL_HORAS * 3600

            if expirado:
                print(f"⏳ ISIN {isin} con NAV expirado ({fecha_str}) → actualizando...")
                get_nav_real(isin, forzar=True)
            else:
                minutos = int(segundos / 60)
                print(f"✅ ISIN {isin} con NAV reciente ({minutos} min de antigüedad)")
        except Exception as e:
            print(f"⚠️ Fecha inválida en caché para {isin}: {e} → forzando actualización")
            get_nav_real(isin, forzar=True)

# # Función anterior mantenida como fallback
# import random

# def get_nav_simulado(nombre_activo):
    # return {
        # "nombre": nombre_activo,
        # "isin": f"SIMU{random.randint(1000,9999)}",
        # "nav": round(random.uniform(90, 150), 2),
        # "fecha": datetime.today().date().isoformat(),
        # "divisa": "EUR",
        # "fuente": "simulado"
    # }
