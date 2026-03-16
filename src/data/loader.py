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
    desde la API de Wikipedia en formato JSON.

    Retorna:
        Lista de símbolos en formato string (ej. ['AAPL', 'MSFT', ...])
    """
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page"  : "List of S&P 500 companies",
            "prop"  : "wikitext",
            "format": "json"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        respuesta = requests.get(url, params=params, headers=headers, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
        wikitext = datos["parse"]["wikitext"]["*"]

        simbolos = re.findall(r'\{\{(?:Nyse|Nasdaq)Symbol\|([A-Z.\-]+)\}\}', wikitext)
        simbolos = [s.replace(".", "-") for s in simbolos]

        return sorted(set(simbolos))

    except Exception as e:
        print(f"Error obteniendo símbolos S&P500: {e}")
        return []


def obtener_simbolos_indices() -> list:
    """
    Retorna los índices bursátiles más relevantes del mundo.
    Disponibles en yfinance con el prefijo ^.

    Retorna:
        Lista de símbolos de índices en formato yfinance
    """
    return [
        # Estados Unidos
        "^GSPC",   # S&P 500
        "^DJI",    # Dow Jones Industrial Average
        "^IXIC",   # NASDAQ Composite
        "^RUT",    # Russell 2000
        "^VIX",    # CBOE Volatility Index

        # Europa
        "^FTSE",   # FTSE 100 (UK)
        "^GDAXI",  # DAX (Alemania)
        "^FCHI",   # CAC 40 (Francia)
        "^STOXX50E", # Euro Stoxx 50
        "^IBEX",   # IBEX 35 (España)

        # Asia / Pacífico
        "^N225",   # Nikkei 225 (Japón)
        "^HSI",    # Hang Seng (Hong Kong)
        "000001.SS", # Shanghai Composite (China)
        "^AXJO",   # ASX 200 (Australia)
        "^KS11",   # KOSPI (Corea del Sur)

        # Latinoamérica
        "^BVSP",   # Bovespa (Brasil)
        "^MXX",    # IPC (México)
        "^IPSA",   # IPSA (Chile)
        "^COLCAP",  # COLCAP (Colombia)

        # Materias primas / otros
        "GC=F",    # Oro (Gold Futures)
        "SI=F",    # Plata (Silver Futures)
        "CL=F",    # Petróleo WTI
        "BZ=F",    # Petróleo Brent
    ]


def obtener_simbolos_crypto() -> list:
    """
    Obtiene las top 100 criptomonedas por capitalización de mercado
    desde la API pública de CoinGecko (sin API key).

    Retorna:
        Lista de símbolos en formato yfinance (ej. ['BTC-USD', 'ETH-USD', ...])
    """
    try:
        url = (
            "https://api.coingecko.com/api/v3/coins/markets"
            "?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        )
        respuesta = requests.get(url, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()

        simbolos = [f"{moneda['symbol'].upper()}-USD" for moneda in datos]
        return simbolos

    except Exception as e:
        print(f"Error obteniendo símbolos crypto: {e}")
        return []


def obtener_simbolos_divisas() -> list:
    """
    Returns the list of main currency pairs available in yfinance.

    Convention: all pairs express how many units of the quote currency
    equal 1 USD (or 1 EUR / 1 GBP for COP pairs), so that values are
    always human-readable and MAPE is well-behaved numerically.

    Pairs that would express how many USD equals 1 unit of a low-value
    currency (JPY, KRW, IDR, CLP, THB, MYR) are inverted to USD-base
    convention — the same approach used for the COP pairs.

    Returns:
        List of currency pair symbols in yfinance format
    """
    divisas = [
        # Major pairs — how many USD per 1 unit of base currency
        # (base currencies with value > 1 USD keep the natural direction)
        "EURUSD=X",   # Euro
        "GBPUSD=X",   # British pound
        "CHFUSD=X",   # Swiss franc
        "AUDUSD=X",   # Australian dollar
        "CADUSD=X",   # Canadian dollar
        "NZDUSD=X",   # New Zealand dollar
        "SGDUSD=X",   # Singapore dollar

        # Inverted pairs — how many units of quote currency per 1 USD
        # Used for currencies whose value per USD is < 1 (avoids tiny values)
        "USDJPY=X",   # Japanese yen
        "USDCNY=X",   # Chinese yuan
        "USDHKD=X",   # Hong Kong dollar
        "USDMXN=X",   # Mexican peso
        "USDBRL=X",   # Brazilian real
        "USDARS=X",   # Argentine peso
        "USDCLP=X",   # Chilean peso
        "USDSEK=X",   # Swedish krona
        "USDNOK=X",   # Norwegian krone
        "USDDKK=X",   # Danish krone
        "USDZAR=X",   # South African rand
        "USDINR=X",   # Indian rupee
        "USDKRW=X",   # South Korean won
        "USDTRY=X",   # Turkish lira
        "USDPLN=X",   # Polish zloty
        "USDTHB=X",   # Thai baht
        "USDIDR=X",   # Indonesian rupiah
        "USDMYR=X",   # Malaysian ringgit

        # Colombian peso pairs — how many COP per 1 unit of foreign currency
        "USDCOP=X",   # USD to Colombian peso
        "EURCOP=X",   # Euro to Colombian peso
        "GBPCOP=X",   # Pound to Colombian peso
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
    ticker = yf.Ticker(simbolo)
    df = ticker.history(start=fecha_inicio, end=fecha_fin)

    if df.empty:
        raise ValueError(
            f"No se encontraron datos para el símbolo '{simbolo}' "
            f"en el rango {fecha_inicio} a {fecha_fin}."
        )

    df = df[["Close"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.reset_index()
    df.columns = ["date", "value"]
    df = df.dropna()
    df = df.sort_values("date").reset_index(drop=True)

    return df


# ============================================================
# INFORMACIÓN DEL ACTIVO
# ============================================================

def obtener_info_activo(simbolo: str) -> dict:
    """
    Obtiene información general del activo para mostrar
    en la franja de información.

    Campos retornados:
        nombre, simbolo, precio, variacion, volumen, moneda,
        sector, market_cap, pe_ratio, beta, semana_52_max,
        semana_52_min, industria

    Parámetros:
        simbolo: símbolo del activo

    Retorna:
        Diccionario con todos los campos disponibles
    """
    try:
        ticker = yf.Ticker(simbolo)
        info = ticker.info

        nombre    = info.get("longName") or info.get("shortName") or simbolo
        precio    = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        variacion = info.get("regularMarketChangePercent") or 0.0
        volumen   = info.get("regularMarketVolume") or info.get("volume") or 0
        moneda    = info.get("currency") or "USD"
        sector    = info.get("sector") or None
        industria = info.get("industry") or None

        # Métricas adicionales — disponibles para acciones, no para crypto/divisas
        market_cap    = info.get("marketCap") or None
        pe_ratio      = info.get("trailingPE") or info.get("forwardPE") or None
        beta          = info.get("beta") or None
        semana_52_max = info.get("fiftyTwoWeekHigh") or None
        semana_52_min = info.get("fiftyTwoWeekLow") or None
        dividendo     = info.get("dividendYield") or None

        return {
            "nombre"      : nombre,
            "simbolo"     : simbolo,
            "precio"      : round(float(precio), 2),
            "variacion"   : round(float(variacion), 2),
            "volumen"     : volumen,
            "moneda"      : moneda,
            "sector"      : sector,
            "industria"   : industria,
            "market_cap"  : market_cap,
            "pe_ratio"    : round(float(pe_ratio), 2) if pe_ratio else None,
            "beta"        : round(float(beta), 2) if beta else None,
            "semana_52_max": round(float(semana_52_max), 2) if semana_52_max else None,
            "semana_52_min": round(float(semana_52_min), 2) if semana_52_min else None,
            "dividendo"   : round(float(dividendo), 2) if dividendo else None,
        }

    except Exception as e:
        print(f"Error obteniendo info del activo '{simbolo}': {e}")
        return {
            "nombre"      : simbolo,
            "simbolo"     : simbolo,
            "precio"      : 0.0,
            "variacion"   : 0.0,
            "volumen"     : 0,
            "moneda"      : "USD",
            "sector"      : None,
            "industria"   : None,
            "market_cap"  : None,
            "pe_ratio"    : None,
            "beta"        : None,
            "semana_52_max": None,
            "semana_52_min": None,
            "dividendo"   : None,
        }
