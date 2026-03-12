# ============================================================
# prophet_model.py — Modelos Prophet y Prophet+XGBoost errors
# Prophet usa defaults idénticos a modeltime (R).
# Prophet+XGBoost errors replica el flujo de prophet_boost:
#   1. Prophet modela tendencia y estacionalidad
#   2. XGBoost modela los residuos usando features temporales
#   3. Predicción final = Prophet(x) + XGBoost(residuos)
# ============================================================

import pandas as pd
import numpy as np
from prophet import Prophet
import xgboost as xgb


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
# FEATURES TEMPORALES PARA XGBOOST DE RESIDUOS
# ============================================================

def _crear_features_xgb(ds_series: pd.Series) -> pd.DataFrame:
    """
    Genera features temporales para el XGBoost de residuos.
    Replica las variables que modeltime pasa vía fórmula:
    fit(y ~ date + as.numeric(date) + month(date, label=TRUE))

    Parámetros:
        ds_series: Serie de fechas tipo datetime

    Retorna:
        DataFrame con features temporales numéricas
    """
    ds = pd.to_datetime(ds_series)
    df_feat = pd.DataFrame({
        # Tendencia numérica — equivalente a as.numeric(date) en R
        "date_num"     : (ds - ds.min()).dt.days,
        # Componentes de calendario
        "mes"          : ds.dt.month,
        "trimestre"    : ds.dt.quarter,
        "dia_semana"   : ds.dt.dayofweek,
        "semana_anio"  : ds.dt.isocalendar().week.astype(int),
        "dia_anio"     : ds.dt.dayofyear,
        # Señales cíclicas para capturar periodicidad
        "mes_sin"      : np.sin(2 * np.pi * ds.dt.month / 12),
        "mes_cos"      : np.cos(2 * np.pi * ds.dt.month / 12),
        "sem_sin"      : np.sin(2 * np.pi * ds.dt.dayofweek / 7),
        "sem_cos"      : np.cos(2 * np.pi * ds.dt.dayofweek / 7),
    })
    return df_feat


# ============================================================
# ENTRENAMIENTO — PROPHET (solo)
# ============================================================

def _entrenar_prophet_base(
    df_prophet: pd.DataFrame,
    es_crypto: bool
) -> Prophet:
    """
    Entrena Prophet con los defaults exactos de modeltime (R).
    Parámetros idénticos a prophet_fit_impl y prophet_xgboost_fit_impl.

    Parámetros:
        df_prophet: DataFrame con columnas 'ds' e 'y'
        es_crypto : True si el activo opera 7 días a la semana

    Retorna:
        Modelo Prophet entrenado
    """
    modelo = Prophet(
        growth                  = "linear",   # default modeltime
        n_changepoints          = 25,          # default modeltime
        changepoint_range       = 0.8,         # default modeltime
        yearly_seasonality      = "auto",      # default modeltime
        weekly_seasonality      = "auto",      # default modeltime
        daily_seasonality       = False,       # desactivado para datos diarios
        seasonality_mode        = "additive",  # default modeltime
        changepoint_prior_scale = 0.05,        # default modeltime
        seasonality_prior_scale = 10.0,        # default modeltime
        holidays_prior_scale    = 10.0,        # default modeltime
        interval_width          = 0.90,        # intervalo de confianza 90%
        uncertainty_samples     = 1000,
    )

    # Holidays solo para activos que no son crypto
    if not es_crypto:
        modelo.add_country_holidays(country_name="US")

    modelo.fit(df_prophet)
    return modelo


# ============================================================
# ENTRENAMIENTO — PROPHET + XGBOOST ERRORS
# ============================================================

def _entrenar_prophet_xgb(
    df_train: pd.DataFrame,
    es_crypto: bool
) -> tuple:
    """
    Entrena el modelo híbrido Prophet + XGBoost errors:
    1. Entrena Prophet sobre los datos de train
    2. Calcula residuos in-sample: residuos = y_real - y_prophet
    3. Entrena XGBoost sobre esos residuos usando features temporales

    Replica exactamente prophet_xgboost_fit_impl de modeltime.

    Parámetros:
        df_train : DataFrame con columnas 'date' y 'value'
        es_crypto: True si el activo opera 7 días a la semana

    Retorna:
        Tupla (modelo_prophet, modelo_xgb, date_min_train)
    """
    df_prophet = preparar_datos_prophet(df_train)

    # Paso 1 — Entrenar Prophet
    modelo_prophet = _entrenar_prophet_base(df_prophet, es_crypto)

    # Paso 2 — Predicciones in-sample y residuos
    pred_insample = modelo_prophet.predict(df_prophet[["ds"]])
    residuos = df_prophet["y"].values - pred_insample["yhat"].values

    # Paso 3 — Features temporales para XGBoost
    X_train = _crear_features_xgb(df_prophet["ds"])
    date_min = df_prophet["ds"].min()

    # Paso 4 — Entrenar XGBoost sobre residuos
    # Hiperparámetros por defecto de modeltime: nrounds=15, eta=0.3, max_depth=6
    dtrain = xgb.DMatrix(X_train.values, label=residuos)
    params = {
        "objective"  : "reg:squarederror",
        "max_depth"  : 6,
        "eta"        : 0.3,
        "subsample"  : 1.0,
        "verbosity"  : 0,
        "nthread"    : 1,
    }
    modelo_xgb = xgb.train(params, dtrain, num_boost_round=15, verbose_eval=False)

    return modelo_prophet, modelo_xgb, date_min


def _predecir_prophet_xgb(
    modelo_prophet: Prophet,
    modelo_xgb,
    date_min: pd.Timestamp,
    ds_futuro: pd.DataFrame
) -> pd.DataFrame:
    """
    Genera predicciones del modelo híbrido sobre fechas nuevas.
    Predicción final = Prophet(x) + XGBoost(residuos)

    Parámetros:
        modelo_prophet: Prophet entrenado
        modelo_xgb    : XGBoost entrenado sobre residuos
        date_min      : fecha mínima del train (para date_num)
        ds_futuro     : DataFrame con columna 'ds' de fechas a predecir

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    # Predicciones Prophet
    pred_prophet = modelo_prophet.predict(ds_futuro)

    # Predicciones XGBoost sobre residuos
    X_fut = _crear_features_xgb(ds_futuro["ds"])
    # Ajustar date_num respecto al mínimo del train
    X_fut["date_num"] = (pd.to_datetime(ds_futuro["ds"]) - date_min).dt.days
    dfut = xgb.DMatrix(X_fut.values)
    correccion_xgb = modelo_xgb.predict(dfut)

    # Predicción final = Prophet + corrección XGBoost
    pred_final = pred_prophet.copy()
    pred_final["yhat"]       = pred_prophet["yhat"]       + correccion_xgb
    pred_final["yhat_lower"] = pred_prophet["yhat_lower"] + correccion_xgb
    pred_final["yhat_upper"] = pred_prophet["yhat_upper"] + correccion_xgb

    return pred_final[["ds", "yhat", "yhat_lower", "yhat_upper"]]


# ============================================================
# API PÚBLICA — PROPHET (solo)
# ============================================================

def entrenar_prophet(
    df_train: pd.DataFrame,
    horizonte: int,
    es_crypto: bool = False
) -> tuple[Prophet, pd.DataFrame]:
    """
    Entrena Prophet y genera predicciones hacia adelante.

    Parámetros:
        df_train  : DataFrame con columnas 'date' y 'value'
        horizonte : número de períodos a predecir hacia adelante
        es_crypto : True si el activo es crypto

    Retorna:
        Tupla (modelo_fitted, predicciones_dataframe)
    """
    df_prophet = preparar_datos_prophet(df_train)
    modelo = _entrenar_prophet_base(df_prophet, es_crypto)

    frecuencia = "D" if es_crypto else "B"
    futuro = modelo.make_future_dataframe(periods=horizonte, freq=frecuencia)
    predicciones = modelo.predict(futuro)

    return modelo, predicciones


def predecir_test_prophet(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    es_crypto: bool = False
) -> pd.DataFrame:
    """
    Genera predicciones de Prophet sobre el test set.

    Parámetros:
        df_train : DataFrame de entrenamiento
        df_test  : DataFrame de prueba
        es_crypto: True si el activo es crypto

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    horizonte_test = len(df_test)
    _, predicciones = entrenar_prophet(df_train, horizonte_test, es_crypto)

    fecha_inicio_test = pd.to_datetime(df_test["date"].iloc[0])
    predicciones_test = predicciones[
        predicciones["ds"] >= fecha_inicio_test
    ].reset_index(drop=True)

    columnas = ["ds", "yhat", "yhat_lower", "yhat_upper"]
    return predicciones_test[columnas].head(horizonte_test)


# ============================================================
# API PÚBLICA — PROPHET + XGBOOST ERRORS
# ============================================================

def entrenar_prophet_xgboost(
    df_train: pd.DataFrame,
    horizonte: int,
    es_crypto: bool = False
) -> tuple:
    """
    Entrena Prophet+XGBoost errors y genera predicciones hacia adelante.

    Parámetros:
        df_train  : DataFrame con columnas 'date' y 'value'
        horizonte : número de períodos a predecir hacia adelante
        es_crypto : True si el activo es crypto

    Retorna:
        Tupla (modelo_prophet, modelo_xgb, predicciones_df, date_min)
    """
    modelo_prophet, modelo_xgb, date_min = _entrenar_prophet_xgb(df_train, es_crypto)

    df_prophet = preparar_datos_prophet(df_train)
    frecuencia = "D" if es_crypto else "B"
    futuro = modelo_prophet.make_future_dataframe(periods=horizonte, freq=frecuencia)

    predicciones = _predecir_prophet_xgb(modelo_prophet, modelo_xgb, date_min, futuro)

    return modelo_prophet, modelo_xgb, predicciones, date_min


def predecir_test_prophet_xgboost(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    es_crypto: bool = False
) -> pd.DataFrame:
    """
    Genera predicciones de Prophet+XGBoost sobre el test set.

    Parámetros:
        df_train : DataFrame de entrenamiento
        df_test  : DataFrame de prueba
        es_crypto: True si el activo es crypto

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    modelo_prophet, modelo_xgb, predicciones, date_min = entrenar_prophet_xgboost(
        df_train, len(df_test), es_crypto
    )

    fecha_inicio_test = pd.to_datetime(df_test["date"].iloc[0])
    pred_test = predicciones[
        predicciones["ds"] >= fecha_inicio_test
    ].reset_index(drop=True)

    columnas = ["ds", "yhat", "yhat_lower", "yhat_upper"]
    return pred_test[columnas].head(len(df_test))
