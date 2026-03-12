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
        "date_num"   : (ds - ds.min()).dt.days,
        # Componentes de calendario
        "mes"        : ds.dt.month,
        "trimestre"  : ds.dt.quarter,
        "dia_semana" : ds.dt.dayofweek,
        "semana_anio": ds.dt.isocalendar().week.astype(int),
        "dia_anio"   : ds.dt.dayofyear,
        # Señales cíclicas para capturar periodicidad
        "mes_sin"    : np.sin(2 * np.pi * ds.dt.month / 12),
        "mes_cos"    : np.cos(2 * np.pi * ds.dt.month / 12),
        "sem_sin"    : np.sin(2 * np.pi * ds.dt.dayofweek / 7),
        "sem_cos"    : np.cos(2 * np.pi * ds.dt.dayofweek / 7),
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

    Parámetros:
        df_prophet: DataFrame con columnas 'ds' e 'y'
        es_crypto : True si el activo opera 7 días a la semana

    Retorna:
        Modelo Prophet entrenado
    """
    modelo = Prophet(
        growth                  = "linear",
        n_changepoints          = 25,
        changepoint_range       = 0.8,
        yearly_seasonality      = "auto",
        weekly_seasonality      = "auto",
        daily_seasonality       = False,
        seasonality_mode        = "additive",
        changepoint_prior_scale = 0.05,
        seasonality_prior_scale = 10.0,
        holidays_prior_scale    = 10.0,
        interval_width          = 0.90,
        uncertainty_samples     = 1000,
    )

    if not es_crypto:
        modelo.add_country_holidays(country_name="US")

    modelo.fit(df_prophet)
    return modelo


# ============================================================
# UTILIDAD — Construir DataFrame de fechas futuras
# ============================================================

def _construir_futuro(
    modelo: Prophet,
    ultima_fecha: pd.Timestamp,
    horizonte: int,
    es_crypto: bool
) -> pd.DataFrame:
    """
    Construye el DataFrame de fechas futuras para Prophet usando
    make_future_dataframe con freq correcto según tipo de activo.
    Solo retorna las fechas estrictamente posteriores a ultima_fecha.

    Usar esta función para el FORECAST (fechas desconocidas).
    Para el TEST usar _construir_futuro_desde_fechas().

    Parámetros:
        modelo      : Prophet ya entrenado
        ultima_fecha: última fecha del train
        horizonte   : número de períodos a predecir
        es_crypto   : True si el activo opera 7 días a la semana

    Retorna:
        DataFrame con columna 'ds' de fechas futuras
    """
    frecuencia = "D" if es_crypto else "B"
    futuro = modelo.make_future_dataframe(periods=horizonte, freq=frecuencia)
    # Retornar solo las fechas posteriores al último dato del train
    return futuro[futuro["ds"] > ultima_fecha].reset_index(drop=True)


def _construir_futuro_desde_fechas(df_test: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el DataFrame de fechas para Prophet usando las fechas
    exactas del test set retornadas por yfinance.

    Por qué: make_future_dataframe con freq='B' usa días hábiles del
    calendario gregoriano, pero yfinance omite feriados del mercado
    (Thanksgiving, Christmas, etc.). Esa diferencia acumula un desfase
    de varios días que hace que Prophet termine antes que los otros modelos.
    Pasar las fechas exactas del test garantiza alineación perfecta.

    Usar esta función para la VALIDACIÓN (test set conocido).

    Parámetros:
        df_test: DataFrame del test con columna 'date'

    Retorna:
        DataFrame con columna 'ds' de fechas exactas del test
    """
    fechas = pd.to_datetime(df_test["date"]).dt.tz_localize(None)
    return pd.DataFrame({"ds": fechas.values})


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
    X_train  = _crear_features_xgb(df_prophet["ds"])
    date_min = df_prophet["ds"].min()

    # Paso 4 — Entrenar XGBoost sobre residuos
    # Hiperparámetros por defecto de modeltime: nrounds=15, eta=0.3, max_depth=6
    dtrain = xgb.DMatrix(X_train.values, label=residuos)
    params = {
        "objective": "reg:squarederror",
        "max_depth": 6,
        "eta"      : 0.3,
        "subsample": 1.0,
        "verbosity": 0,
        "nthread"  : 1,
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
    pred_prophet = modelo_prophet.predict(ds_futuro)

    X_fut = _crear_features_xgb(ds_futuro["ds"])
    X_fut["date_num"] = (pd.to_datetime(ds_futuro["ds"]) - date_min).dt.days
    dfut = xgb.DMatrix(X_fut.values)
    correccion_xgb = modelo_xgb.predict(dfut)

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
    Entrena Prophet y genera predicciones de forecast hacia adelante.
    Usa make_future_dataframe con freq correcto — solo para fechas futuras.

    Parámetros:
        df_train  : DataFrame con columnas 'date' y 'value'
        horizonte : número de períodos a predecir hacia adelante
        es_crypto : True si el activo es crypto

    Retorna:
        Tupla (modelo_fitted, predicciones_dataframe)
    """
    df_prophet = preparar_datos_prophet(df_train)
    modelo = _entrenar_prophet_base(df_prophet, es_crypto)

    ultima_fecha = df_prophet["ds"].max()
    futuro = _construir_futuro(modelo, ultima_fecha, horizonte, es_crypto)
    predicciones = modelo.predict(futuro)

    return modelo, predicciones


def predecir_test_prophet(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    es_crypto: bool = False
) -> pd.DataFrame:
    """
    Genera predicciones de Prophet sobre el test set.
    Usa las fechas exactas del test (no make_future_dataframe) para
    garantizar alineación perfecta con yfinance independientemente
    del calendario de feriados del mercado.

    Parámetros:
        df_train : DataFrame de entrenamiento
        df_test  : DataFrame de prueba
        es_crypto: True si el activo es crypto

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    df_prophet = preparar_datos_prophet(df_train)
    modelo = _entrenar_prophet_base(df_prophet, es_crypto)

    # Predecir exactamente sobre las fechas del test set
    futuro_test = _construir_futuro_desde_fechas(df_test)
    predicciones = modelo.predict(futuro_test)

    return predicciones[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True)


# ============================================================
# API PÚBLICA — PROPHET + XGBOOST ERRORS
# ============================================================

def entrenar_prophet_xgboost(
    df_train: pd.DataFrame,
    horizonte: int,
    es_crypto: bool = False
) -> tuple:
    """
    Entrena Prophet+XGBoost errors y genera predicciones de forecast.
    Usa make_future_dataframe — solo para fechas futuras.

    Parámetros:
        df_train  : DataFrame con columnas 'date' y 'value'
        horizonte : número de períodos a predecir hacia adelante
        es_crypto : True si el activo es crypto

    Retorna:
        Tupla (modelo_prophet, modelo_xgb, predicciones_df, date_min)
    """
    modelo_prophet, modelo_xgb, date_min = _entrenar_prophet_xgb(df_train, es_crypto)

    df_prophet   = preparar_datos_prophet(df_train)
    ultima_fecha = df_prophet["ds"].max()
    futuro = _construir_futuro(modelo_prophet, ultima_fecha, horizonte, es_crypto)

    predicciones = _predecir_prophet_xgb(modelo_prophet, modelo_xgb, date_min, futuro)

    return modelo_prophet, modelo_xgb, predicciones, date_min


def predecir_test_prophet_xgboost(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    es_crypto: bool = False
) -> pd.DataFrame:
    """
    Genera predicciones de Prophet+XGBoost sobre el test set.
    Usa las fechas exactas del test para garantizar alineación
    perfecta con yfinance.

    Parámetros:
        df_train : DataFrame de entrenamiento
        df_test  : DataFrame de prueba
        es_crypto: True si el activo es crypto

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    modelo_prophet, modelo_xgb, date_min = _entrenar_prophet_xgb(df_train, es_crypto)

    # Predecir exactamente sobre las fechas del test set
    futuro_test  = _construir_futuro_desde_fechas(df_test)
    predicciones = _predecir_prophet_xgb(
        modelo_prophet, modelo_xgb, date_min, futuro_test
    )

    return predicciones[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True)
