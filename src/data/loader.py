# ============================================================
# loader.py — Descarga y preparación de datos financieros
# usando yfinance. También provee las listas de símbolos
# disponibles por categoría obtenidas dinámicamente.
# ============================================================

import yfinance as yf
import pandas as pd
import requests
import re


# ============================================================
# OBTENCIÓN DINÁMICA DE SÍMBOLOS POR CATEGORÍA
# ============================================================

def obtener_simbolos_sp500() -> list:
    """
    Obtiene la lista completa y actualizada de símbolos del S&P500
    desde la API de Wikipedia en formato JSON, extrayendo los símbolos
    con regex desde el wikitext de la página.

    Retorna:
        Lista de símbolos en formato string (ej. ['AAPL', 'MSFT', ...])
    """
    try:
        # API de Wikipedia en formato JSON — evita problemas con pd.read_html
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": "List of S&P 500 companies",
            "prop": "wikitext",
            "format": "json"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        respuesta = requests.get(url, params=params, headers=headers, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
        wikitext = datos["parse"]["wikitext"]["*"]

        # Los símbolos aparecen como {{NyseSymbol|XXX}} o {{NasdaqSymbol|XXX}}
        simbolos = re.findall(r'\{\{(?:Nyse|Nasdaq)Symbol\|([A-Z.\-]+)\}\}', wikitext)

        # Reemplazar punto por guion (ej. BRK.B → BRK-B) para yfinance
        simbolos = [s.replace(".", "-") for s in simbolos]

        return sorted(set(simbolos))

    except Exception as e:
        print(f"Error obteniendo símbolos S&P500: {e}")
        return []


def obtener_simbolos_crypto() -> list:
    """
    Obtiene las top 100 criptomonedas por capitalización de mercado
    desde la API pública de CoinGecko (sin API key).

    Retorna:
        Lista de símbolos en formato yfinance (ej. ['BTC-USD', 'ETH-USD', ...])
    """
    try:
        # CoinGecko API pública — top 100 por market cap
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        )
        respuesta = requests.get(url, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()

        # Convertir símbolo a formato yfinance — uppercase + sufijo -USD
        simbolos = [f"{moneda['symbol'].upper()}-USD" for moneda in datos]

        return simbolos

    except Exception as e:
        print(f"Error obteniendo símbolos crypto: {e}")
        return []


def obtener_simbolos_divisas() -> list:
    """
    Retorna la lista de pares de divisas principales disponibles
    en yfinance, incluyendo pares con el peso colombiano (COP).

    Los pares de divisas en yfinance usan el sufijo =X.
    Formato: XXXYYY=X donde XXX es la divisa base y YYY la cotizada.

    Retorna:
        Lista de símbolos de divisas en formato yfinance
    """
    divisas = [
        # Pares mayores contra USD
        "EURUSD=X",   # Euro
        "GBPUSD=X",   # Libra esterlina
        "JPYUSD=X",   # Yen japonés
        "CHFUSD=X",   # Franco suizo
        "AUDUSD=X",   # Dólar australiano
        "CADUSD=X",   # Dólar canadiense
        "NZDUSD=X",   # Dólar neozelandés
        "CNYUSD=X",   # Yuan chino
        "HKDUSD=X",   # Dólar de Hong Kong
        "SGDUSD=X",   # Dólar de Singapur

        # Pares menores contra USD
        "MXNUSD=X",   # Peso mexicano
        "BRLUSD=X",   # Real brasileño
        "ARSUSD=X",   # Peso argentino
        "CLPUSD=X",   # Peso chileno
        "SEKUSD=X",   # Corona sueca
        "NOKUSD=X",   # Corona noruega
        "DKKUSD=X",   # Corona danesa
        "ZARUSD=X",   # Rand sudafricano
        "INRUSD=X",   # Rupia india
        "KRWUSD=X",   # Won surcoreano
        "TRYUSD=X",   # Lira turca
        "PLNUSD=X",   # Esloti polaco
        "THBUSD=X",   # Baht tailandés
        "IDRUSD=X",   # Rupia indonesia
        "MYRUSD=X",   # Ringgit malayo

        # Pares con peso colombiano (COP)
        "COPUSD=X",   # Peso colombiano a USD
        "COPEUR=X",   # Peso colombiano a Euro
        "COPGBP=X",   # Peso colombiano a Libra esterlina
    ]

    return divisas


# ============================================================
# DESCARGA DE DATOS HISTÓRICOS
# ============================================================

def descargar_datos(simbolo: str, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
    """
    Descarga los precios de cierre históricos de un activo.

    Parámetros:
        simbolo     : símbolo del activo (ej. 'AAPL', 'BTC-USD', 'EURUSD=X')
        fecha_inicio: fecha de inicio en formato 'YYYY-MM-DD'
        fecha_fin   : fecha de fin en formato 'YYYY-MM-DD'

    Retorna:
        DataFrame con columnas 'date' y 'value' (precio de cierre)
    """
    # Descargar datos desde yfinance
    ticker = yf.Ticker(simbolo)
    df = ticker.history(start=fecha_inicio, end=fecha_fin)

    # Verificar que se obtuvieron datos
    if df.empty:
        raise ValueError(
            f"No se encontraron datos para el símbolo '{simbolo}' "
            f"en el rango {fecha_inicio} a {fecha_fin}."
        )

    # Conservar solo el precio de cierre y limpiar el índice
    df = df[["Close"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)  # Eliminar timezone
    df = df.reset_index()
    df.columns = ["date", "value"]

    # Eliminar filas con valores nulos
    df = df.dropna()

    # Ordenar por fecha ascendente
    df = df.sort_values("date").reset_index(drop=True)

    return df


# ============================================================
# INFORMACIÓN DEL ACTIVO
# ============================================================

def obtener_info_activo(simbolo: str) -> dict:
    """
    Obtiene información general del activo para mostrar
    en las cards de la sección de información.

    Parámetros:
        simbolo: símbolo del activo (ej. 'AAPL', 'BTC-USD', 'EURUSD=X')

    Retorna:
        Diccionario con nombre, precio, variación, volumen, moneda y sector
    """
    try:
        ticker = yf.Ticker(simbolo)
        info = ticker.info

        # Extraer campos relevantes con valores por defecto
        nombre   = info.get("longName") or info.get("shortName") or simbolo
        precio   = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        variacion = info.get("regularMarketChangePercent") or 0.0
        volumen  = info.get("regularMarketVolume") or info.get("volume") or 0
        moneda   = info.get("currency") or "USD"
        sector   = info.get("sector") or "N/A"

        return {
            "nombre"  : nombre,
            "simbolo" : simbolo,
            "precio"  : round(precio, 4),
            "variacion": round(variacion, 2),
            "volumen" : volumen,
            "moneda"  : moneda,
            "sector"  : sector
        }

    except Exception as e:
        # Si falla la consulta, retornar datos mínimos sin crashear la app
        print(f"Error obteniendo info del activo '{simbolo}': {e}")
        return {
            "nombre"  : simbolo,
            "simbolo" : simbolo,
            "precio"  : 0.0,
            "variacion": 0.0,
            "volumen" : 0,
            "moneda"  : "USD",
            "sector"  : "N/A"
        }