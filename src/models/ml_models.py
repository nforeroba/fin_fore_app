# ============================================================
# ml_models.py — Modelos de Machine Learning para forecasting
# Implementa Elastic Net, Random Forest y XGBoost con
# features temporales. Usa MAPIE para generar intervalos
# de confianza via conformal prediction para todos los modelos.
# ============================================================

import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from mapie.regression import TimeSeriesRegressor


# ============================================================
# INGENIERÍA DE FEATURES TEMPORALES
# ============================================================

def crear_features_temporales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea features temporales a partir de la columna 'date'
    para alimentar los modelos de Machine Learning.

    Parámetros:
        df: DataFrame con columnas 'date' y 'value'

    Retorna:
        DataFrame con features temporales añadidas
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Features de calendario
    df["año"]         = df["date"].dt.year
    df["mes"]         = df["date"].dt.month
    df["dia"]         = df["date"].dt.day
    df["dia_semana"]  = df["date"].dt.dayofweek   # 0=lunes, 4=viernes
    df["dia_año"]     = df["date"].dt.dayofyear
    df["semana_año"]  = df["date"].dt.isocalendar().week.astype(int)
    df["trimestre"]   = df["date"].dt.quarter

    # Features de Fourier para capturar estacionalidad
    # Período 5 para estacionalidad semanal (5 días hábiles)
    # Período 21 para estacionalidad mensual (~21 días hábiles)
    for periodo in [5, 21, 63, 252]:
        df[f"sen_{periodo}"] = np.sin(2 * np.pi * df["dia_año"] / periodo)
        df[f"cos_{periodo}"] = np.cos(2 * np.pi * df["dia_año"] / periodo)

    # Features de lag — valores pasados como predictores
    for lag in [1, 2, 3, 5, 10, 21]:
        df[f"lag_{lag}"] = df["value"].shift(lag)

    # Features de media móvil
    for ventana in [5, 10, 21]:
        df[f"media_movil_{ventana}"] = df["value"].rolling(window=ventana).mean()
        df[f"std_movil_{ventana}"]   = df["value"].rolling(window=ventana).std()

    # Eliminar filas con NaN generados por lags y medias móviles
    df = df.dropna().reset_index(drop=True)

    return df


def obtener_X_y(df_features: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Separa el DataFrame de features en matriz X e vector y.

    Parámetros:
        df_features: DataFrame con features temporales

    Retorna:
        Tupla (X, y) donde X son los features e y es el target
    """
    # Columnas a excluir — no son features
    columnas_excluir = ["date", "value"]
    X = df_features.drop(columns=columnas_excluir)
    y = df_features["value"]
    return X, y


# ============================================================
# ENTRENAMIENTO DE MODELOS ML CON MAPIE
# ============================================================

def entrenar_elastic_net(
    df_train: pd.DataFrame,
    alpha: float = 0.01,
    l1_ratio: float = 0.5
) -> TimeSeriesRegressor:
    """
    Entrena un modelo Elastic Net envuelto en MAPIE para
    generar intervalos de confianza via conformal prediction.

    Parámetros:
        df_train : DataFrame de entrenamiento con columnas 'date' y 'value'
        alpha    : parámetro de regularización
        l1_ratio : balance entre L1 y L2 (0=Ridge, 1=Lasso)

    Retorna:
        Modelo TimeSeriesRegressor entrenado
    """
    # Crear features temporales
    df_features = crear_features_temporales(df_train)
    X_train, y_train = obtener_X_y(df_features)

    # Pipeline con escalado + Elastic Net
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("modelo", ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=5000))
    ])

    # Envolver en MAPIE para intervalos de confianza
    mapie = TimeSeriesRegressor(estimator=pipeline)
    mapie.fit(X_train, y_train)

    return mapie


def entrenar_random_forest(
    df_train: pd.DataFrame,
    n_estimators: int = 200,
    min_samples_leaf: int = 5
) -> TimeSeriesRegressor:
    """
    Entrena un modelo Random Forest envuelto en MAPIE.

    Parámetros:
        df_train        : DataFrame de entrenamiento
        n_estimators    : número de árboles
        min_samples_leaf: mínimo de muestras por hoja

    Retorna:
        Modelo TimeSeriesRegressor entrenado
    """
    df_features = crear_features_temporales(df_train)
    X_train, y_train = obtener_X_y(df_features)

    modelo = RandomForestRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=min_samples_leaf,
        random_state=42,
        n_jobs=-1
    )

    # Envolver en MAPIE para intervalos de confianza
    mapie = TimeSeriesRegressor(estimator=modelo)
    mapie.fit(X_train, y_train)

    return mapie


def entrenar_xgboost(
    df_train: pd.DataFrame,
    n_estimators: int = 200,
    learning_rate: float = 0.05,
    max_depth: int = 4
) -> TimeSeriesRegressor:
    """
    Entrena un modelo XGBoost envuelto en MAPIE.

    Parámetros:
        df_train     : DataFrame de entrenamiento
        n_estimators : número de árboles de boosting
        learning_rate: tasa de aprendizaje
        max_depth    : profundidad máxima de cada árbol

    Retorna:
        Modelo TimeSeriesRegressor entrenado
    """
    df_features = crear_features_temporales(df_train)
    X_train, y_train = obtener_X_y(df_features)

    modelo = XGBRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        random_state=42,
        n_jobs=-1,
        verbosity=0  # Silenciar output de XGBoost
    )

    # Envolver en MAPIE para intervalos de confianza
    mapie = TimeSeriesRegressor(estimator=modelo)
    mapie.fit(X_train, y_train)

    return mapie


# ============================================================
# PREDICCIÓN CON INTERVALOS DE CONFIANZA
# ============================================================

def predecir_con_intervalos(
    modelo: TimeSeriesRegressor,
    df_pred: pd.DataFrame,
) -> pd.DataFrame:
    """
    Genera predicciones con intervalos de confianza usando MAPIE.

    Parámetros:
        modelo  : modelo TimeSeriesRegressor entrenado
        df_pred : DataFrame con columnas 'date' y 'value' para predecir
        alpha   : confidence_level=0.90

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    df_features = crear_features_temporales(df_pred)
    X_pred, _ = obtener_X_y(df_features)

    # MAPIE retorna (predicciones, intervalos)
    yhat, intervalos = modelo.predict(X_pred, confidence_level=0.90, ensemble=True)

    resultado = pd.DataFrame({
        "ds"         : df_features["date"].values,
        "yhat"       : yhat,
        "yhat_lower" : intervalos[:, 0, 0],
        "yhat_upper" : intervalos[:, 1, 0]
    })

    return resultado


# ============================================================
# FORECAST HACIA ADELANTE CON MODELOS ML
# ============================================================

def forecast_ml(
    modelo: TimeSeriesRegressor,
    df_train: pd.DataFrame,
    horizonte: int,
    frecuencia: str = "B"
) -> pd.DataFrame:
    """
    Genera predicciones hacia adelante usando el modelo ML entrenado.
    Usa una estrategia recursiva — cada predicción se usa como
    input para la siguiente.

    Parámetros:
        modelo   : modelo TimeSeriesRegressor entrenado
        df_train : DataFrame de entrenamiento completo
        horizonte: número de períodos a predecir
        frecuencia: 'B' para días hábiles, 'D' para todos los días

    Retorna:
        DataFrame con columnas 'ds', 'yhat', 'yhat_lower', 'yhat_upper'
    """
    # Partir de los datos de entrenamiento para mantener contexto de lags
    df_extendido = df_train.copy()
    ultima_fecha = pd.to_datetime(df_train["date"].iloc[-1])

    # Generar fechas futuras
    fechas_futuras = pd.date_range(
        start=ultima_fecha + pd.tseries.frequencies.to_offset(frecuencia),
        periods=horizonte,
        freq=frecuencia
    )

    predicciones_lista = []

    for fecha in fechas_futuras:
        # Crear features para la fecha actual usando el historial extendido
        df_features = crear_features_temporales(df_extendido)

        # Tomar solo la última fila para predecir el siguiente paso
        X_ultimo = df_features.drop(columns=["date", "value"]).iloc[[-1]]

        # Predecir con MAPIE
        yhat, intervalos = modelo.predict(X_ultimo, confidence_level=0.90, ensemble=True)

        predicciones_lista.append({
            "ds"         : fecha,
            "yhat"       : float(yhat[0]),
            "yhat_lower" : float(intervalos[0, 0, 0]),
            "yhat_upper" : float(intervalos[0, 1, 0])
        })

        # Agregar la predicción al historial para el siguiente paso
        nueva_fila = pd.DataFrame({"date": [fecha], "value": [float(yhat[0])]})
        df_extendido = pd.concat([df_extendido, nueva_fila], ignore_index=True)

    return pd.DataFrame(predicciones_lista)