# ============================================================
# prophet_model.py — Modelo Prophet de Meta para forecasting
# Prophet es especialmente bueno capturando tendencias y
# estacionalidades en series de tiempo financieras.
# ============================================================

import pandas as pd
import numpy as np
from prophet import Prophet


# ============================================================
# PREPARACIÓN DE DATOS PARA PROPHET
# ============================================================

def preparar_datos_prophet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte el DataFrame estándar del loader al formato
    requerido por Prophet:
    - Columna 'ds': fecha
    - Columna 'y': valor a predecir

    Parámetros:
        df: DataFrame con columnas 'date' y 'value'

    Retorna:
        DataFrame en formato Prophet
    """
    df_prophet = df.rename(columns={"date": "ds", "value": "y"})
    df_prophet["ds"] = pd.to_datetime(df_prophet["ds"]).dt.tz_localize(None)
    return df_prophet[["ds", "y"]]


# ============================================================
# ENTRENAMIENTO Y PREDICCIÓN — PROPHET
# ============================================================

def entrenar_prophet(
    df_train: pd.DataFrame,
    horizonte: int,
    es_crypto: bool = False
) -> tuple[Prophet, pd.DataFrame]:
    """
    Entrena el modelo Prophet y genera predicciones hacia adelante.

    Parámetros:
        df_train  : DataFrame con columnas 'date' y 'value' (solo train)
        horizonte : número de períodos a predecir hacia adelante
        es_crypto : True si el activo es crypto (opera todos los días),
                    False para acciones y divisas (días hábiles)

    Retorna:
        Tupla (modelo_fitted, predicciones_dataframe)
    """
    # Preparar datos en formato Prophet
    df_prophet = preparar_datos_prophet(df_train)

    # Configurar el modelo
    # - yearly_seasonality: captura patrones anuales
    # - weekly_seasonality: captura patrones semanales
    # - daily_seasonality: desactivado para datos diarios
    modelo = Prophet(
    growth="flat",
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    changepoint_prior_scale=0.01,
    interval_width=0.90
)

    # Las crypto no tienen fines de semana sin datos — no aplicar holidays
    if not es_crypto:
        modelo.add_country_holidays(country_name="US")

    # Entrenar el modelo
    modelo.fit(df_prophet)

    # Crear dataframe de fechas futuras
    # Para crypto usamos frecuencia diaria, para acciones días hábiles
    frecuencia = "D" if es_crypto else "B"
    futuro = modelo.make_future_dataframe(periods=horizonte, freq=frecuencia)

    # Generar predicciones
    predicciones = modelo.predict(futuro)

    return modelo, predicciones


# ============================================================
# PREDICCIONES SOBRE EL TEST SET (VALIDACIÓN)
# ============================================================

def predecir_test_prophet(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    es_crypto: bool = False
) -> pd.DataFrame:
    """
    Genera predicciones de Prophet sobre el test set para
    evaluar su desempeño comparado con los demás modelos.

    Parámetros:
        df_train : DataFrame de entrenamiento
        df_test  : DataFrame de prueba
        es_crypto: True si el activo es crypto

    Retorna:
        DataFrame con predicciones sobre el período de test,
        con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    horizonte_test = len(df_test)

    # Entrenar y predecir
    _, predicciones = entrenar_prophet(df_train, horizonte_test, es_crypto)

    # Filtrar solo las fechas del test set — Prophet predice desde el inicio
    fecha_inicio_test = pd.to_datetime(df_test["date"].iloc[0])
    predicciones_test = predicciones[
        predicciones["ds"] >= fecha_inicio_test
    ].reset_index(drop=True)

    # Conservar solo las columnas relevantes
    columnas = ["ds", "yhat", "yhat_lower", "yhat_upper"]
    return predicciones_test[columnas].head(horizonte_test)