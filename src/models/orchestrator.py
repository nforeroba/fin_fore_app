# ============================================================
# orchestrator.py — Coordinador central de todos los modelos
# Recibe los parámetros del usuario, ejecuta el pipeline
# completo de forecasting y retorna resultados unificados.
# ============================================================

import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.data.loader import descargar_datos
from src.models.statistical import (
    entrenar_modelos_estadisticos,
    predecir_test_estadisticos,
    detectar_frecuencia
)
from src.models.prophet_model import (
    entrenar_prophet,
    predecir_test_prophet,
    entrenar_prophet_xgboost,
    predecir_test_prophet_xgboost
)
from src.models.ml_models import (
    entrenar_elastic_net,
    entrenar_random_forest,
    entrenar_xgboost,
    predecir_con_intervalos,
    forecast_ml
)


# ============================================================
# UTILIDAD — Normalizar columna de fechas a date pura
# ============================================================

def _normalizar_fechas(serie: pd.Series) -> pd.Series:
    """
    Convierte cualquier serie de fechas a datetime64 sin hora ni timezone.
    Maneja strings, Timestamps con/sin tz, y numpy datetime64.
    .normalize() trunca la hora a 00:00:00 garantizando comparaciones exactas.

    Parámetros:
        serie: Serie con valores de fecha en cualquier formato

    Retorna:
        Serie de pandas datetime64[ns] sin timezone ni componente de hora
    """
    return pd.to_datetime(serie).dt.tz_localize(None).dt.normalize()


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
    """
    fecha_max   = pd.to_datetime(df["date"].max())
    fecha_corte = fecha_max - relativedelta(months=meses_test)

    df_train = df[df["date"] <= fecha_corte].reset_index(drop=True)
    df_test  = df[df["date"] >  fecha_corte].reset_index(drop=True)

    return df_train, df_test


# ============================================================
# CÁLCULO DE MÉTRICAS
# ============================================================

def calcular_metricas(
    y_real: pd.Series,
    y_pred: pd.Series,
    nombre_modelo: str
) -> dict:
    """Calcula MAE, RMSE, MAPE y SMAPE para un modelo."""
    n      = min(len(y_real), len(y_pred))
    y_real = y_real.iloc[:n].values
    y_pred = y_pred.iloc[:n].values

    mae  = mean_absolute_error(y_real, y_pred)
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))

    mask = y_real != 0
    mape = np.mean(np.abs((y_real[mask] - y_pred[mask]) / y_real[mask])) * 100

    denominador = (np.abs(y_real) + np.abs(y_pred)) / 2
    mask_smape  = denominador != 0
    smape       = np.mean(
        np.abs(y_real[mask_smape] - y_pred[mask_smape]) / denominador[mask_smape]
    ) * 100

    return {
        "modelo": nombre_modelo,
        "MAE"   : round(mae,  4),
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
    """Normaliza predicciones de statsforecast al formato estándar."""
    df = predicciones_sf[["ds", col_yhat, col_lower, col_upper]].copy()
    df.columns = ["ds", "yhat", "yhat_lower", "yhat_upper"]
    df["modelo"] = nombre_modelo
    df["ds"] = _normalizar_fechas(df["ds"])
    return df[["modelo", "ds", "yhat", "yhat_lower", "yhat_upper"]]


def normalizar_predicciones_prophet(
    predicciones_prophet: pd.DataFrame,
    nombre_modelo: str = "Prophet"
) -> pd.DataFrame:
    """Normaliza predicciones de Prophet al formato estándar."""
    df = predicciones_prophet[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    df["modelo"] = nombre_modelo
    df["ds"] = _normalizar_fechas(df["ds"])
    return df[["modelo", "ds", "yhat", "yhat_lower", "yhat_upper"]]


def normalizar_predicciones_ml(
    predicciones_ml: pd.DataFrame,
    nombre_modelo: str
) -> pd.DataFrame:
    """Normaliza predicciones de modelos ML al formato estándar."""
    df = predicciones_ml[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    df["modelo"] = nombre_modelo
    df["ds"] = _normalizar_fechas(df["ds"])
    return df[["modelo", "ds", "yhat", "yhat_lower", "yhat_upper"]]


# ============================================================
# UTILIDAD — FILTRAR PREDICCIONES AL RANGO CORRECTO
# ============================================================

def _filtrar_test(pred: pd.DataFrame, df_test: pd.DataFrame) -> pd.DataFrame:
    """
    Recorta las predicciones al período exacto del test set.
    Normaliza ambas series a date pura antes de comparar.
    """
    pred = pred.copy()
    pred["ds"] = _normalizar_fechas(pred["ds"])

    fechas_test = _normalizar_fechas(df_test["date"])
    fecha_inicio = fechas_test.iloc[0]
    fecha_fin    = fechas_test.iloc[-1]

    return pred[
        (pred["ds"] >= fecha_inicio) & (pred["ds"] <= fecha_fin)
    ].reset_index(drop=True)


def _filtrar_forecast(pred: pd.DataFrame, fecha_fin) -> pd.DataFrame:
    """
    Recorta las predicciones al período futuro solamente.
    Normaliza fechas a date pura para comparación robusta.
    Fecha_fin puede ser string, date o Timestamp.
    """
    pred = pred.copy()
    pred["ds"] = _normalizar_fechas(pred["ds"])
    fecha_corte = _normalizar_fechas(pd.Series([str(fecha_fin)])).iloc[0]

    return pred[pred["ds"] > fecha_corte].reset_index(drop=True)


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

    Modelos incluidos:
        Estadísticos : AutoARIMA (con drift), AutoETS, Theta
        Prophet      : Prophet, Prophet+XGBoost errors
        ML           : ElasticNet, RandomForest, XGBoost
    """

    # ----------------------------------------------------------
    # 1. Descargar y normalizar fechas
    # ----------------------------------------------------------
    df = descargar_datos(simbolo, fecha_inicio, fecha_fin)
    df["date"] = _normalizar_fechas(df["date"])

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

    dias_por_mes   = 30 if frecuencia == "D" else 21
    horizonte_dias = meses_horizonte * dias_por_mes

    # fecha_fin normalizada — referencia única para todos los filtros de forecast
    fecha_fin_norm = _normalizar_fechas(pd.Series([str(fecha_fin)])).iloc[0]

    pred_test_lista     = []
    pred_forecast_lista = []

    # ----------------------------------------------------------
    # 4. Modelos estadísticos — AutoARIMA, AutoETS, Theta
    # ----------------------------------------------------------
    pred_test_sf = predecir_test_estadisticos(df_train, df_test, simbolo, frecuencia)
    _, pred_forecast_sf = entrenar_modelos_estadisticos(
        df, simbolo, horizonte_dias, frecuencia
    )

    pred_test_sf["ds"]     = _normalizar_fechas(pred_test_sf["ds"])
    pred_forecast_sf["ds"] = _normalizar_fechas(pred_forecast_sf["ds"])

    modelos_sf = {
        "AutoARIMA": ("AutoARIMA", "AutoARIMA-lo-90", "AutoARIMA-hi-90"),
        "AutoETS"  : ("AutoETS",   "AutoETS-lo-90",   "AutoETS-hi-90"),
        "Theta"    : (
            "DynamicOptimizedTheta",
            "DynamicOptimizedTheta-lo-90",
            "DynamicOptimizedTheta-hi-90"
        )
    }

    fechas_test_norm = _normalizar_fechas(df_test["date"])

    for nombre, (col_y, col_lo, col_hi) in modelos_sf.items():
        # Reindexar sobre fechas exactas del test — ffill para feriados
        pred_sf_test = pred_test_sf[["ds", col_y, col_lo, col_hi]].copy()
        pred_sf_test = pred_sf_test.set_index("ds")
        pred_sf_test = pred_sf_test.reindex(fechas_test_norm).ffill().reset_index()
        pred_sf_test.columns = ["ds", col_y, col_lo, col_hi]

        pred_test_lista.append(
            normalizar_predicciones_sf(pred_sf_test, nombre, col_y, col_lo, col_hi)
        )

        # Forecast — solo fechas estrictamente después de fecha_fin
        pred_fc = pred_forecast_sf[
            pred_forecast_sf["ds"] > fecha_fin_norm
        ].copy()
        pred_forecast_lista.append(
            normalizar_predicciones_sf(pred_fc, nombre, col_y, col_lo, col_hi)
        )

    # ----------------------------------------------------------
    # 5. Prophet
    # ----------------------------------------------------------
    pred_test_prophet_raw = predecir_test_prophet(df_train, df_test, es_crypto)
    _, pred_forecast_prophet_raw = entrenar_prophet(df, horizonte_dias, es_crypto)

    pred_test_lista.append(
        normalizar_predicciones_prophet(
            _filtrar_test(pred_test_prophet_raw, df_test), "Prophet"
        )
    )
    pred_forecast_lista.append(
        normalizar_predicciones_prophet(
            _filtrar_forecast(pred_forecast_prophet_raw, fecha_fin), "Prophet"
        )
    )

    # ----------------------------------------------------------
    # 6. Prophet + XGBoost errors
    # ----------------------------------------------------------
    pred_test_pxgb_raw = predecir_test_prophet_xgboost(df_train, df_test, es_crypto)
    _, _, pred_forecast_pxgb_raw, _ = entrenar_prophet_xgboost(
        df, horizonte_dias, es_crypto
    )

    pred_test_lista.append(
        normalizar_predicciones_prophet(
            _filtrar_test(pred_test_pxgb_raw, df_test), "Prophet+XGBoost"
        )
    )
    pred_forecast_lista.append(
        normalizar_predicciones_prophet(
            _filtrar_forecast(pred_forecast_pxgb_raw, fecha_fin), "Prophet+XGBoost"
        )
    )

    # ----------------------------------------------------------
    # 7. Modelos ML — Elastic Net, Random Forest, XGBoost
    # ----------------------------------------------------------
    modelos_ml = {
        "ElasticNet"  : entrenar_elastic_net(df_train),
        "RandomForest": entrenar_random_forest(df_train),
        "XGBoost"     : entrenar_xgboost(df_train)
    }

    for nombre_ml, modelo_ml in modelos_ml.items():
        pred_test_ml = predecir_con_intervalos(modelo_ml, df_train, df_test)
        pred_test_lista.append(
            normalizar_predicciones_ml(
                _filtrar_test(pred_test_ml, df_test), nombre_ml
            )
        )

        pred_forecast_ml = forecast_ml(modelo_ml, df, horizonte_dias, frecuencia)
        pred_forecast_lista.append(
            normalizar_predicciones_ml(
                _filtrar_forecast(pred_forecast_ml, fecha_fin), nombre_ml
            )
        )

    # ----------------------------------------------------------
    # 8. Unificar predicciones
    # ----------------------------------------------------------
    pred_test_unificado     = pd.concat(pred_test_lista,     ignore_index=True)
    pred_forecast_unificado = pd.concat(pred_forecast_lista, ignore_index=True)

    # ----------------------------------------------------------
    # 9. Calcular métricas sobre el test set
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
