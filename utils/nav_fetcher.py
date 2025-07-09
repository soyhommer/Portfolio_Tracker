import os
import re
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.merge_nav_data import merge_nav_data
from utils.nav_cache import cargar_valido_de_cache, guardar_en_cache
from utils.config import get_cache_nav_path, CACHE_TTL_HORAS

def es_isin(valor):
    return isinstance(valor, str) and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", valor.strip())

def limpiar_isin(df):
    """
    Limpia y valida la columna 'ISIN' de un DataFrame de transacciones.
    Convierte cualquier valor en texto seguro, elimina espacios invisibles,
    o lo deja en None si es inválido.
    """
    if "ISIN" not in df.columns:
        return df

    def normalizar(x):
        try:
            if x is None or pd.isna(x):
                return None

            x = str(x)
            x = x.strip().replace("\u200b", "").replace("\u00a0", "")

            if not x or x.lower() == "nan":
                return None

            if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", x):
                return x

        except Exception:
            return None

        return None

    df["ISIN"] = df["ISIN"].apply(normalizar)
    return df

def normalizar_isin(valor):
    """
    Asegura que el ISIN sea string limpio o None.
    Evita errores con tipos numéricos, None o NaN.
    """
    if valor is None or pd.isna(valor):
        return None

    try:
        valor = str(valor)
    except Exception:
        return None

    valor = valor.strip().replace("\u200b", "").replace("\u00a0", "")
    if valor == "" or valor.lower() == "nan":
        return None

    return valor

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
            pass

def corregir_nombres_por_isin(df, cartera):
    """
    Usa la caché de NAV para forzar que todas las transacciones tengan el nombre oficial
    asociado al ISIN. Limpia el valor de cache y el original para evitar tipos no texto.
    """
    cache = cargar_cache_nav(cartera)
    df = df.copy()

    def limpiar_texto(x):
        if x is None or pd.isna(x):
            return None
        try:
            x = str(x)
        except Exception:
            return None
        x = x.strip().replace("\u200b", "").replace("\u00a0", "")
        if x == "" or x.lower() == "nan":
            return None
        return x

    def obtener_nombre(row):
        isin = limpiar_texto(row.get("ISIN"))
        original = limpiar_texto(row.get("Posición"))
        clave = f"isin:{isin}".lower() if isin else ""
        if clave in cache and cache[clave].get("nombre"):
            return limpiar_texto(cache[clave]["nombre"])
        return original

    df["Posición"] = df.apply(obtener_nombre, axis=1)
    return df


def cargar_cache_nav(portfolio_name: str) -> dict:
    """
    Carga la caché consolidada de merges para una cartera específica.
    Devuelve un diccionario con claves por ISIN y por nombre.
    """
    path = get_cache_nav_path("real", portfolio_name)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            base = json.load(f)
        extendido = dict(base)
        #impide añadir al dict nombres que no sean texto.
        for val in base.values():
            nombre = val.get("nombre")
            if isinstance(nombre, str) and nombre.strip() and nombre.lower() not in extendido:
                extendido[nombre.lower()] = val
        return extendido
    return {}

def guardar_cache_nav(portfolio_name: str, cache: dict):
    """
    Guarda la caché consolidada de merges para una cartera específica.
    """
    path = get_cache_nav_path("real", portfolio_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    def limpiar_valor_cache(item):
        if not isinstance(item, dict):
            return None
        nombre = item.get("nombre")
        if not isinstance(nombre, str) or not nombre.strip():
            item["nombre"] = None
        return item

    cache_limpio = {k: limpiar_valor_cache(v) for k, v in cache.items() if limpiar_valor_cache(v)}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache_limpio, f, indent=2, ensure_ascii=False)

def get_nav_real(nombre_o_isin: str, portfolio_name: str, forzar: bool = False) -> dict | None:
    """
    Devuelve los datos de NAV (nav, fecha, divisa, variación, etc.) a partir del nombre o ISIN del activo.
    """
    print(f"🪵 [LOG] get_nav_real recibe: {nombre_o_isin} (tipo: {type(nombre_o_isin)})")
    if not isinstance(nombre_o_isin, str):
        nombre_o_isin = str(nombre_o_isin)
    nombre_o_isin = nombre_o_isin.strip()
        
    cache = cargar_cache_nav(portfolio_name)

    import inspect
    if not nombre_o_isin.startswith("IE") and "Seilern" in nombre_o_isin:
        print(f"\n🧭 get_nav_real llamado con: '{nombre_o_isin}'")
        for f in inspect.stack()[1:4]:
            print(f"↪️ llamado desde {f.function} en {f.filename}:{f.lineno}")

    # Si no se fuerza, intentar usar caché
    if not forzar:
        clave_isin = f"isin:{nombre_o_isin}".lower()
        if clave_isin in cache and cache[clave_isin].get("nav") is not None:
            return cache[clave_isin]

        for datos in cache.values():
            if datos.get("isin", "").upper() == nombre_o_isin.upper() and datos.get("nav") is not None:
                return datos

        clave_nombre = nombre_o_isin.lower()
        if clave_nombre in cache and cache[clave_nombre].get("nav") is not None:
            return cache[clave_nombre]

        for datos in cache.values():
            if nombre_o_isin.lower() in datos.get("nombre", "").lower() and datos.get("nav") is not None:
                return datos

    # Si no hay datos válidos o se ha forzado, hacer scraping
    resultado = merge_nav_data(nombre_o_isin, portfolio_name)
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
    clave_isin = f"isin:{isin}".lower()
    clave_nombre = nombre_o_isin.lower()
    cache[clave_isin] = resultado
    cache[clave_nombre] = resultado
    guardar_cache_nav(portfolio_name, cache)

    print(f"📦 NAV cacheado en {portfolio_name}: {nombre_o_isin} → {isin}")
    return resultado

def refrescar_navs_si_expirados(df, portfolio_name: str, forzar: bool = False):
    """
    Revisa los ISIN en el DataFrame y actualiza su NAV si ha expirado,
    o siempre si se fuerza el refresco.
    """
    cache = cargar_cache_nav(portfolio_name)
    ahora = datetime.now()
    isins = df["ISIN"].dropna().unique()

    for isin in isins:
        if not es_isin(isin):
            continue

        datos = cache.get(f"isin:{isin}".lower())

        if not datos or forzar:
            motivo = "no está en caché" if not datos else "refresco forzado"
            print(f"🔄 ISIN {isin} → {motivo} → actualizando...")
            get_nav_real(isin, portfolio_name, forzar=True)
            continue

        fecha_str = datos.get("fecha")
        try:
            fecha_obj = datetime.fromisoformat(fecha_str)
            segundos = (ahora - fecha_obj).total_seconds()
            expirado = segundos > CACHE_TTL_HORAS * 3600

            if expirado:
                print(f"⏳ ISIN {isin} con NAV expirado ({fecha_str}) → actualizando...")
                get_nav_real(isin, portfolio_name, forzar=True)
            else:
                minutos = int(segundos / 60)
                print(f"✅ ISIN {isin} con NAV reciente ({minutos} min de antigüedad)")
        except Exception as e:
            print(f"⚠️ Fecha inválida en caché para {isin}: {e} → forzando actualización")
            get_nav_real(isin, portfolio_name, forzar=True)

def actualizar_cache_isin(nombre: str, nuevo_isin: str, portfolio_name: str):
    """
    Actualiza o inserta una entrada en el archivo cache_nav_real.json usando un ISIN proporcionado.

    Este método permite forzar la actualización del NAV consolidado para un activo específico,
    intentando obtener datos reales mediante merge_nav_data. Si la búsqueda es exitosa, guarda
    los datos enriquecidos con NAV, fecha y divisa. Si falla, guarda al menos el ISIN y nombre.

    Es útil para sincronizar o corregir el cache real cuando se añade o corrige un ISIN
    para un nombre de activo existente en la cartera.

    Args:
        nombre (str): Nombre del activo asociado al ISIN (ejemplo: "Azvalor Internacional FI").
        nuevo_isin (str): Código ISIN válido del activo a actualizar o insertar.
    """

    try:
        # 1. Leer caché por cartera
        cache = cargar_cache_nav(portfolio_name)

        # 2. Ejecutar merge_nav_data para obtener datos reales
        resultado = merge_nav_data(nuevo_isin.strip(), portfolio_name)
        if not resultado or not resultado.get("nav"):
            print(f"⚠️ No se pudo obtener NAV al actualizar cache para: {nuevo_isin}")
            resultado = {
                "isin": nuevo_isin.strip(),
                "nombre": nombre
            }
        else:
            resultado["isin"] = nuevo_isin.strip()
            # Garantizar nombre siempre sea string limpio o None
            if nombre is None or pd.isna(nombre):
                resultado["nombre"] = None
            else:
                try:
                    resultado["nombre"] = str(nombre).strip().replace("\u200b", "").replace("\u00a0", "")
                    if resultado["nombre"] == "" or resultado["nombre"].lower() == "nan":
                        resultado["nombre"] = None
                except Exception:
                    resultado["nombre"] = None

        # 3. Guardar en cache bajo las claves por ISIN y por nombre
        clave_isin = f"isin:{nuevo_isin.strip()}".lower()
        clave_nombre = nombre.strip().lower()
        cache[clave_isin] = resultado
        cache[clave_nombre] = resultado

        guardar_cache_nav(portfolio_name, cache)
        print(f"✅ Cache NAV actualizado para {nombre} (ISIN: {nuevo_isin}) en {portfolio_name}")

    except Exception as e:
        print(f"⚠️ Error actualizando cache_nav_real para {portfolio_name}: {e}")