# ============================================================
# orchestrator.py — Coordinador central de todos los modelos
# Recibe los parámetros del usuario, ejecuta el pipeline
# completo de forecasting y retorna resultados unificados.
# ============================================================

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.data.loader import descargar_datos
from src.models.statistical import (
    entrenar_modelos_estadisticos,
    predecir_test_estadisticos,
    detectar_frecuencia
)
from src.models.prophet_model import entrenar_prophet, predecir_test_prophet
from src.models.ml_models import (
    entrenar_elastic_net,
    entrenar_random_forest,
    entrenar_xgboost,
    predecir_con_intervalos,
    forecast_ml
)


# ============================================================
# SPLIT TRAIN / TEST
# ============================================================

def split_train_test(
    df: pd.DataFrame,
    meses_test: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide el DataFrame en train y test usando los últimos
    N meses como test set. Split temporal, no aleatorio.

    Parámetros:
        df        : DataFrame completo con columnas 'date' y 'value'
        meses_test: número de meses a usar como test set

    Retorna:
        Tupla (df_train, df_test)
    """
    # Calcular la fecha de corte
    fecha_max = pd.to_datetime(df["date"].max())
    fecha_corte = fecha_max - pd.DateOffset(months=meses_test)

    # Split temporal
    df_train = df[df["date"] <= fecha_corte].reset_index(drop=True)
    df_test  = df[df["date"] > fecha_corte].reset_index(drop=True)

    return df_train, df_test


# ============================================================
# CÁLCULO DE MÉTRICAS
# ============================================================

def calcular_metricas(
    y_real: pd.Series,
    y_pred: pd.Series,
    nombre_modelo: str
) -> dict:
    """
    Calcula MAE, RMSE, MAPE y SMAPE para un modelo.

    Parámetros:
        y_real       : valores reales del test set
        y_pred       : predicciones del modelo
        nombre_modelo: nombre del modelo para identificación

    Retorna:
        Diccionario con las métricas calculadas
    """
    # Alinear longitudes — puede haber diferencias mínimas por fechas
    n = min(len(y_real), len(y_pred))
    y_real = y_real.iloc[:n].values
    y_pred = y_pred.iloc[:n].values

    # MAE — error absoluto medio en unidades del precio
    mae = mean_absolute_error(y_real, y_pred)

    # RMSE — raíz del error cuadrático medio, penaliza errores grandes
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))

    # MAPE — error porcentual absoluto medio
    # Evitar división por cero
    mask = y_real != 0
    mape = np.mean(np.abs((y_real[mask] - y_pred[mask]) / y_real[mask])) * 100

    # SMAPE — error porcentual absoluto medio simétrico
    # Más robusto que MAPE cuando los valores son cercanos a cero
    denominador = (np.abs(y_real) + np.abs(y_pred)) / 2
    mask_smape = denominador != 0
    smape = np.mean(
        np.abs(y_real[mask_smape] - y_pred[mask_smape]) / denominador[mask_smape]
    ) * 100

    return {
        "modelo": nombre_modelo,
        "MAE"   : round(mae, 4),
        "RMSE"  : round(rmse, 4),
        "MAPE"  : round(mape, 4),
        "SMAPE" : round(smape, 4)
    }


# ============================================================
# NORMALIZACIÓN DE PREDICCIONES AL FORMATO ESTÁNDAR
# ============================================================

def normalizar_predicciones_sf(
    predicciones_sf: pd.DataFrame,
    nombre_modelo: str,
    col_yhat: str,
    col_lower: str,
    col_upper: str
) -> pd.DataFrame:
    """
    Normaliza las predicciones de statsforecast al formato estándar:
    columnas 'modelo', 'ds', 'yhat', 'yhat_lower', 'yhat_upper'.

    Parámetros:
        predicciones_sf: DataFrame de statsforecast
        nombre_modelo  : nombre del modelo
        col_yhat       : nombre de la columna de predicción
        col_lower      : nombre de la columna del límite inferior
        col_upper      : nombre de la columna del límite superior

    Retorna:
        DataFrame en formato estándar
    """
    df = predicciones_sf[["ds", col_yhat, col_lower, col_upper]].copy()
    df.columns = ["ds", "yhat", "yhat_lower", "yhat_upper"]
    df["modelo"] = nombre_modelo
    return df[["modelo", "ds", "yhat", "yhat_lower", "yhat_upper"]]


def normalizar_predicciones_prophet(
    predicciones_prophet: pd.DataFrame,
    nombre_modelo: str = "Prophet"
) -> pd.DataFrame:
    """
    Normaliza las predicciones de Prophet al formato estándar.

    Parámetros:
        predicciones_prophet: DataFrame de Prophet
        nombre_modelo       : nombre del modelo

    Retorna:
        DataFrame en formato estándar
    """
    df = predicciones_prophet[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    df["modelo"] = nombre_modelo
    return df[["modelo", "ds", "yhat", "yhat_lower", "yhat_upper"]]


def normalizar_predicciones_ml(
    predicciones_ml: pd.DataFrame,
    nombre_modelo: str
) -> pd.DataFrame:
    """
    Normaliza las predicciones de los modelos ML al formato estándar.

    Parámetros:
        predicciones_ml: DataFrame de modelos ML
        nombre_modelo  : nombre del modelo

    Retorna:
        DataFrame en formato estándar
    """
    df = predicciones_ml[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    df["modelo"] = nombre_modelo
    return df[["modelo", "ds", "yhat", "yhat_lower", "yhat_upper"]]


# ============================================================
# PIPELINE COMPLETO DE FORECASTING
# ============================================================

def ejecutar_pipeline(
    simbolo: str,
    fecha_inicio: str,
    fecha_fin: str,
    meses_test: int,
    meses_horizonte: int
) -> dict:
    """
    Ejecuta el pipeline completo de forecasting para un activo.
    Coordina descarga de datos, split, entrenamiento de todos
    los modelos, cálculo de métricas y generación de forecasts.

    Parámetros:
        simbolo         : símbolo del activo (ej. 'AAPL', 'BTC-USD')
        fecha_inicio    : fecha de inicio en formato 'YYYY-MM-DD'
        fecha_fin       : fecha de fin en formato 'YYYY-MM-DD'
        meses_test      : meses a usar como test set
        meses_horizonte : meses a predecir hacia adelante

    Retorna:
        Diccionario con:
        - 'df_completo'      : serie histórica completa
        - 'df_train'         : datos de entrenamiento
        - 'df_test'          : datos de prueba
        - 'pred_test'        : predicciones sobre test (formato largo)
        - 'pred_forecast'    : forecast hacia adelante (formato largo)
        - 'metricas'         : DataFrame con métricas por modelo
    """

    # ----------------------------------------------------------
    # 1. Descargar datos
    # ----------------------------------------------------------
    df = descargar_datos(simbolo, fecha_inicio, fecha_fin)

    # ----------------------------------------------------------
    # 2. Split train / test
    # ----------------------------------------------------------
    df_train, df_test = split_train_test(df, meses_test)

    # ----------------------------------------------------------
    # 3. Detectar frecuencia y tipo de activo
    # ----------------------------------------------------------
    frecuencia = detectar_frecuencia(simbolo)
    es_crypto  = simbolo.endswith("-USD") and any(
        c.isalpha() for c in simbolo.replace("-USD", "")
    )

    # Calcular horizonte en días según frecuencia
    dias_por_mes = 30 if frecuencia == "D" else 21
    horizonte_dias = meses_horizonte * dias_por_mes

    # ----------------------------------------------------------
    # 4. Modelos estadísticos — AutoARIMA, AutoETS, Theta
    # ----------------------------------------------------------
    pred_test_sf = predecir_test_estadisticos(df_train, df_test, simbolo, frecuencia)
    _, pred_forecast_sf = entrenar_modelos_estadisticos(
        df, simbolo, horizonte_dias, frecuencia
    )

    # Normalizar predicciones de statsforecast al formato estándar
    modelos_sf = {
        "AutoARIMA": ("AutoARIMA", "AutoARIMA-lo-90", "AutoARIMA-hi-90"),
        "AutoETS"  : ("AutoETS",   "AutoETS-lo-90",   "AutoETS-hi-90"),
        "Theta"    : ("DynamicOptimizedTheta", "DynamicOptimizedTheta-lo-90", "DynamicOptimizedTheta-hi-90")
    }

    pred_test_lista     = []
    pred_forecast_lista = []

    for nombre, (col_y, col_lo, col_hi) in modelos_sf.items():
        # Filtrar solo las fechas del test para las predicciones de validación
        fechas_test = pd.to_datetime(df_test["date"])
        pred_test_sf["ds"] = pd.to_datetime(pred_test_sf["ds"]).dt.tz_localize(None)
        pred_test_sf_filtrado = pred_test_sf[
            pred_test_sf["ds"].isin(fechas_test)
]

        # Si aún faltan fechas, completar con forward fill
        if len(pred_test_sf_filtrado) < len(df_test):
            pred_test_sf_filtrado = pred_test_sf_filtrado.set_index("ds")
            pred_test_sf_filtrado = pred_test_sf_filtrado.reindex(fechas_test)
            pred_test_sf_filtrado = pred_test_sf_filtrado.ffill().reset_index()
            pred_test_sf_filtrado.columns = ["ds"] + list(pred_test_sf_filtrado.columns[1:])

        pred_test_lista.append(
            normalizar_predicciones_sf(pred_test_sf_filtrado, nombre, col_y, col_lo, col_hi)
        )

        # Para el forecast, filtrar solo fechas futuras
        fecha_fin_dt = pd.to_datetime(fecha_fin)
        pred_forecast_sf_filtrado = pred_forecast_sf[
            pred_forecast_sf["ds"] > fecha_fin_dt
        ]
        pred_forecast_lista.append(
            normalizar_predicciones_sf(pred_forecast_sf_filtrado, nombre, col_y, col_lo, col_hi)
        )

    # ----------------------------------------------------------
    # 5. Prophet
    # ----------------------------------------------------------
    pred_test_prophet = predecir_test_prophet(df_train, df_test, es_crypto)
    _, pred_forecast_prophet_raw = entrenar_prophet(df, horizonte_dias, es_crypto)

    # Filtrar solo fechas futuras para el forecast de Prophet
    fecha_fin_dt = pd.to_datetime(fecha_fin)
    pred_forecast_prophet = pred_forecast_prophet_raw[
        pd.to_datetime(pred_forecast_prophet_raw["ds"]) > fecha_fin_dt
    ]

    pred_test_lista.append(normalizar_predicciones_prophet(pred_test_prophet))
    pred_forecast_lista.append(normalizar_predicciones_prophet(pred_forecast_prophet))

    # ----------------------------------------------------------
    # 6. Modelos ML — Elastic Net, Random Forest, XGBoost
    # ----------------------------------------------------------
    modelos_ml = {
        "ElasticNet"  : entrenar_elastic_net(df_train),
        "RandomForest": entrenar_random_forest(df_train),
        "XGBoost"     : entrenar_xgboost(df_train)
    }

    for nombre_ml, modelo_ml in modelos_ml.items():
        # Predicciones sobre test
        pred_test_ml = predecir_con_intervalos(modelo_ml, df_train, df_test)
        pred_test_lista.append(normalizar_predicciones_ml(pred_test_ml, nombre_ml))

        # Forecast hacia adelante
        pred_forecast_ml = forecast_ml(modelo_ml, df, horizonte_dias, frecuencia)
        pred_forecast_lista.append(normalizar_predicciones_ml(pred_forecast_ml, nombre_ml))

    # ----------------------------------------------------------
    # 7. Unificar predicciones en DataFrames largos
    # ----------------------------------------------------------
    pred_test_unificado     = pd.concat(pred_test_lista,     ignore_index=True)
    pred_forecast_unificado = pd.concat(pred_forecast_lista, ignore_index=True)

    # ----------------------------------------------------------
    # 8. Calcular métricas sobre el test set
    # ----------------------------------------------------------
    metricas_lista = []
    y_real = df_test["value"].reset_index(drop=True)

    for nombre_modelo in pred_test_unificado["modelo"].unique():
        pred_modelo = pred_test_unificado[
            pred_test_unificado["modelo"] == nombre_modelo
        ]["yhat"].reset_index(drop=True)

        metricas_lista.append(calcular_metricas(y_real, pred_modelo, nombre_modelo))

    df_metricas = pd.DataFrame(metricas_lista).sort_values("MAPE").reset_index(drop=True)

    return {
        "df_completo"  : df,
        "df_train"     : df_train,
        "df_test"      : df_test,
        "pred_test"    : pred_test_unificado,
        "pred_forecast": pred_forecast_unificado,
        "metricas"     : df_metricas
    }