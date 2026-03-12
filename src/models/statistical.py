# ============================================================
# statistical.py — Modelos estadísticos de series de tiempo
# Implementa AutoARIMA, ETS y Theta usando statsforecast
# de Nixtla, que es más rápido que las implementaciones
# tradicionales de estos modelos.
# ============================================================

import pandas as pd
import numpy as np
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, DynamicOptimizedTheta


# ============================================================
# PREPARACIÓN DE DATOS PARA STATSFORECAST
# ============================================================

def preparar_datos_statsforecast(df: pd.DataFrame, simbolo: str) -> pd.DataFrame:
    """
    Convierte el DataFrame estándar del loader al formato
    requerido por statsforecast:
    - Columna 'unique_id': identificador de la serie
    - Columna 'ds': fecha
    - Columna 'y': valor a predecir

    Parámetros:
        df     : DataFrame con columnas 'date' y 'value'
        simbolo: símbolo del activo para usar como unique_id

    Retorna:
        DataFrame en formato statsforecast
    """
    df_sf = df.rename(columns={"date": "ds", "value": "y"})
    df_sf["unique_id"] = simbolo
    df_sf = df_sf[["unique_id", "ds", "y"]]

    # statsforecast requiere fechas sin timezone
    df_sf["ds"] = pd.to_datetime(df_sf["ds"]).dt.tz_localize(None)

    return df_sf


# ============================================================
# ENTRENAMIENTO Y PREDICCIÓN — MODELOS ESTADÍSTICOS
# ============================================================

def entrenar_modelos_estadisticos(
    df_train: pd.DataFrame,
    simbolo: str,
    horizonte: int,
    frecuencia: str = "B"
) -> tuple[StatsForecast, pd.DataFrame]:
    """
    Entrena AutoARIMA (con drift), ETS y Theta sobre los datos de entrenamiento.

    Parámetros:
        df_train  : DataFrame con columnas 'date' y 'value' (solo train)
        simbolo   : símbolo del activo
        horizonte : número de períodos a predecir hacia adelante
        frecuencia: frecuencia de la serie — 'B' para días hábiles (acciones),
                    'D' para días calendario (crypto)

    Retorna:
        Tupla (modelo_fitted, predicciones_dataframe)
    """
    df_sf = preparar_datos_statsforecast(df_train, simbolo)

    # allowdrift=True replica el comportamiento de modeltime (R):
    # ARIMA with drift captura tendencia lineal en series financieras alcistas
    modelos = [
        AutoARIMA(season_length=5, allowdrift=True),
        AutoETS(season_length=5),
        DynamicOptimizedTheta(season_length=5)
    ]

    sf = StatsForecast(
        models=modelos,
        freq=frecuencia,
        n_jobs=-1
    )

    sf.fit(df_sf)

    # Generar predicciones con intervalos de confianza al 90%
    predicciones = sf.predict(h=horizonte, level=[90])

    return sf, predicciones


# ============================================================
# PREDICCIONES SOBRE EL TEST SET (VALIDACIÓN)
# ============================================================

def predecir_test_estadisticos(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    simbolo: str,
    frecuencia: str = "B"
) -> pd.DataFrame:
    """
    Genera predicciones sobre el test set para evaluar
    el desempeño de los modelos estadísticos.

    Parámetros:
        df_train  : DataFrame de entrenamiento
        df_test   : DataFrame de prueba
        simbolo   : símbolo del activo
        frecuencia: frecuencia de la serie

    Retorna:
        DataFrame con predicciones sobre el período de test
    """
    horizonte_test = len(df_test)

    _, predicciones = entrenar_modelos_estadisticos(
        df_train=df_train,
        simbolo=simbolo,
        horizonte=horizonte_test,
        frecuencia=frecuencia
    )

    return predicciones


# ============================================================
# DETECCIÓN DE FRECUENCIA SEGÚN TIPO DE ACTIVO
# ============================================================

def detectar_frecuencia(simbolo: str) -> str:
    """
    Detecta la frecuencia apropiada según el tipo de activo.

    Reglas:
        'D' — Crypto: sufijo -USD con letras (BTC-USD, ETH-USD, etc.)
        'B' — Todo lo demás: acciones, divisas, índices (^DJI, ^GSPC),
              futuros (GC=F, CL=F), pares COP (USDCOP=X), etc.

    Los índices bursátiles y futuros operan en días hábiles.
    Las divisas también operan en días hábiles desde el punto de
    vista de los datos disponibles en yfinance.

    Parámetros:
        simbolo: símbolo del activo

    Retorna:
        'D' para crypto (todos los días)
        'B' para acciones, índices, futuros y divisas (días hábiles)
    """
    # Crypto: sufijo -USD con parte alfabética antes del guion
    # Ejemplos: BTC-USD, ETH-USD, SOL-USD
    # Excluir: pares de divisas que también terminan en -USD pero son letras
    # La distinción es que las crypto no tienen =X al final
    if simbolo.endswith("-USD") and "=" not in simbolo:
        parte_base = simbolo.replace("-USD", "")
        if parte_base.isalpha():
            return "D"

    # Todo lo demás opera en días hábiles:
    # Acciones: AAPL, MSFT, BRK-B
    # Índices: ^DJI, ^GSPC, ^IXIC, ^N225, ^BVSP, ^COLCAP
    # Futuros: GC=F, CL=F, SI=F, BZ=F
    # Divisas: EURUSD=X, USDCOP=X, GBPUSD=X
    # Acciones internacionales: 000001.SS, ^KS11
    return "B"
