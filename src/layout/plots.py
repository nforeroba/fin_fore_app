# ============================================================
# plots.py — Funciones de visualización con Plotly
# Genera los gráficos interactivos de validación y forecast
# con la estética de terminal financiero oscuro.
# ============================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.layout.components import COLORES


# ============================================================
# CONFIGURACIÓN BASE DE GRÁFICOS
# ============================================================

COLORES_MODELOS = {
    "AutoARIMA"      : "#58A6FF",
    "AutoETS"        : "#F0B429",
    "Theta"          : "#E879F9",
    "Prophet"        : "#FB923C",
    "Prophet+XGBoost": "#FF4D8F",
    "ElasticNet"     : "#34D399",
    "RandomForest"   : "#F87171",
    "XGBoost"        : "#A78BFA",
}

LAYOUT_BASE = dict(
    paper_bgcolor=COLORES["fondo_card"],
    plot_bgcolor =COLORES["fondo"],
    font=dict(
        family="'Space Mono', monospace",
        color =COLORES["texto_secundario"],
        size  =11,
    ),
    xaxis=dict(
        gridcolor=COLORES["borde"],
        linecolor=COLORES["borde"],
        tickcolor=COLORES["borde"],
        showgrid =True,
        zeroline =False,
    ),
    yaxis=dict(
        gridcolor=COLORES["borde"],
        linecolor=COLORES["borde"],
        tickcolor=COLORES["borde"],
        showgrid =True,
        zeroline =False,
    ),
    legend=dict(
        bgcolor     =COLORES["fondo_card"],
        bordercolor =COLORES["borde"],
        borderwidth =1,
        font=dict(size=10, family="'Space Mono', monospace"),
        orientation ="v",
        x=1.01, y=1,
    ),
    margin=dict(l=50, r=180, t=50, b=50),
    hovermode="closest",
)


# ============================================================
# UTILIDAD — Convertir hex a rgba
# ============================================================

def hex_a_rgba(hex_color: str, opacidad: float = 0.10) -> str:
    """
    Convierte un color hex a formato rgba compatible con Plotly.

    Parámetros:
        hex_color: color en formato hex (ej. '#58A6FF')
        opacidad : valor entre 0 y 1

    Retorna:
        String en formato rgba (ej. 'rgba(88, 166, 255, 0.10)')
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {opacidad})"


# ============================================================
# UTILIDAD — Agregar traza de modelo con banda CI integrada
# ============================================================

def _agregar_traza_modelo(
    fig: go.Figure,
    df_modelo: pd.DataFrame,
    nombre: str,
    color: str,
    dash: str = "solid",
) -> None:
    """
    Agrega dos trazas para un modelo: banda CI y línea de predicción.

    La banda CI usa fill='toself' con un polígono cerrado.
    La razón por la que el toggle falla con legendgroup es que
    Plotly no garantiza sincronización entre trazas no contiguas.
    La solución es no usar legendgroup en absoluto:

    - La banda CI tiene showlegend=False — no aparece en la leyenda
    - La línea tiene showlegend=True — aparece en la leyenda
    - Ambas comparten el mismo nombre para que el toggle de
      visibilidad las afecte: al hacer clic en la leyenda, Plotly
      oculta TODAS las trazas con el mismo 'name' en la figura.

    Esto funciona porque Plotly vincula trazas por 'name' cuando
    no hay legendgroup, siempre que ambas trazas tengan el mismo
    nombre exacto.

    Parámetros:
        fig      : figura Plotly a modificar
        df_modelo: DataFrame con columnas ds, yhat, yhat_lower, yhat_upper
        nombre   : nombre del modelo (aparece en la leyenda)
        color    : color hex del modelo
        dash     : estilo de línea ('solid', 'dot', 'dash')
    """
    ds      = df_modelo["ds"]
    y_upper = df_modelo["yhat_upper"]
    y_lower = df_modelo["yhat_lower"]

    # Polígono cerrado: superior de izq a der, inferior de der a izq
    x_banda = pd.concat([ds, ds.iloc[::-1]], ignore_index=True)
    y_banda = pd.concat([y_upper, y_lower.iloc[::-1]], ignore_index=True)

    # Traza 1 — banda CI, mismo nombre que la línea, sin entrada en leyenda
    fig.add_trace(go.Scatter(
        x=x_banda,
        y=y_banda,
        fill="toself",
        fillcolor=hex_a_rgba(color, 0.12),
        line=dict(color="rgba(0,0,0,0)", width=0),
        name=nombre,
        showlegend=False,
        hoverinfo="skip",
    ))

    # Traza 2 — línea de predicción, aparece en la leyenda
    fig.add_trace(go.Scatter(
        x=ds,
        y=df_modelo["yhat"],
        name=nombre,
        line=dict(color=color, width=1.5, dash=dash),
        hovertemplate=f"%{{y:,.4f}}<extra>{nombre}</extra>",
    ))


# ============================================================
# GRÁFICO DE VALIDACIÓN
# ============================================================

def grafico_validacion(
    df_completo: pd.DataFrame,
    df_test: pd.DataFrame,
    pred_test: pd.DataFrame,
    simbolo: str
) -> go.Figure:
    """
    Genera el gráfico de validación mostrando la serie histórica
    completa y las predicciones de cada modelo sobre el test set,
    con bandas de intervalos de confianza.

    Al hacer clic en un modelo en la leyenda, su línea y su banda
    CI desaparecen juntas (comparten el mismo 'name').

    Parámetros:
        df_completo: serie histórica completa
        df_test    : datos del test set con valores reales
        pred_test  : predicciones sobre test en formato largo
        simbolo    : símbolo del activo para el título

    Retorna:
        Figura Plotly
    """
    fig = go.Figure()

    # --- Serie histórica completa ---
    fig.add_trace(go.Scatter(
        x=df_completo["date"],
        y=df_completo["value"],
        name="ACTUAL",
        line=dict(color=COLORES["texto_principal"], width=1.5),
        hovertemplate="%{y:,.4f}<extra>ACTUAL</extra>"
    ))

    # --- Predicciones por modelo ---
    for modelo in pred_test["modelo"].unique():
        df_modelo = pred_test[pred_test["modelo"] == modelo].copy()
        color = COLORES_MODELOS.get(modelo, "#FFFFFF")
        _agregar_traza_modelo(fig, df_modelo, modelo, color, dash="dot")

    # Línea vertical — inicio del test set
    fecha_inicio_test = str(df_test["date"].iloc[0])
    fig.add_shape(
        type="line",
        x0=fecha_inicio_test, x1=fecha_inicio_test,
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color=COLORES["texto_secundario"], width=1, dash="dash")
    )
    fig.add_annotation(
        x=fecha_inicio_test, y=1,
        xref="x", yref="paper",
        text="TEST SET",
        showarrow=False,
        font=dict(color=COLORES["texto_secundario"], size=10),
        xanchor="left", yanchor="bottom"
    )

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(
            text=f"{simbolo} — Validación de Modelos",
            font=dict(color=COLORES["texto_principal"], size=14),
            x=0.01
        ),
        height=450,
    )

    return fig


# ============================================================
# GRÁFICO DE FORECAST
# ============================================================

def grafico_forecast(
    df_completo: pd.DataFrame,
    pred_forecast: pd.DataFrame,
    simbolo: str,
    meses_horizonte: int
) -> go.Figure:
    """
    Genera el gráfico de forecast mostrando la serie histórica
    completa y las predicciones hacia adelante de cada modelo,
    con bandas de intervalos de confianza.

    Al hacer clic en un modelo en la leyenda, su línea y su banda
    CI desaparecen juntas (comparten el mismo 'name').

    Parámetros:
        df_completo    : serie histórica completa
        pred_forecast  : predicciones hacia adelante en formato largo
        simbolo        : símbolo del activo para el título
        meses_horizonte: meses de horizonte para el título

    Retorna:
        Figura Plotly
    """
    fig = go.Figure()

    # --- Serie histórica completa ---
    fig.add_trace(go.Scatter(
        x=df_completo["date"],
        y=df_completo["value"],
        name="ACTUAL",
        line=dict(color=COLORES["texto_principal"], width=1.5),
        hovertemplate="%{y:,.4f}<extra>ACTUAL</extra>"
    ))

    # --- Forecast por modelo ---
    for modelo in pred_forecast["modelo"].unique():
        df_modelo = pred_forecast[pred_forecast["modelo"] == modelo].copy()
        color = COLORES_MODELOS.get(modelo, "#FFFFFF")
        _agregar_traza_modelo(fig, df_modelo, modelo, color, dash="solid")

    # Línea vertical — inicio del forecast
    fecha_inicio_forecast = str(pred_forecast["ds"].min())
    fig.add_shape(
        type="line",
        x0=fecha_inicio_forecast, x1=fecha_inicio_forecast,
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color=COLORES["acento_verde"], width=1, dash="dash")
    )
    fig.add_annotation(
        x=fecha_inicio_forecast, y=1,
        xref="x", yref="paper",
        text="FORECAST",
        showarrow=False,
        font=dict(color=COLORES["acento_verde"], size=10),
        xanchor="left", yanchor="bottom"
    )

    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(
            text=f"{simbolo} — Forecast {meses_horizonte} meses",
            font=dict(color=COLORES["texto_principal"], size=14),
            x=0.01
        ),
        height=450,
    )

    return fig


# ============================================================
# TABLA DE MÉTRICAS ESTILIZADA
# ============================================================

def crear_tabla_metricas(df_metricas: pd.DataFrame) -> go.Figure:
    """
    Genera una tabla de métricas estilizada con Plotly,
    destacando el mejor modelo por cada métrica en verde.

    Parámetros:
        df_metricas: DataFrame con columnas modelo, MAE, RMSE, MAPE, SMAPE

    Retorna:
        Figura Plotly con la tabla
    """
    metricas = ["MAE", "RMSE", "MAPE", "SMAPE"]

    colores_celdas = []
    col_modelo = [COLORES["fondo_input"]] * len(df_metricas)
    colores_celdas.append(col_modelo)

    for metrica in metricas:
        col_colores = []
        idx_mejor = df_metricas[metrica].idxmin()
        for i in range(len(df_metricas)):
            if i == idx_mejor:
                col_colores.append(hex_a_rgba(COLORES["acento_verde"], 0.20))
            else:
                col_colores.append(COLORES["fondo_input"])
        colores_celdas.append(col_colores)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["<b>MODELO</b>", "<b>MAE</b>", "<b>RMSE</b>",
                    "<b>MAPE %</b>", "<b>SMAPE %</b>"],
            fill_color=COLORES["fondo_card"],
            align="left",
            font=dict(
                color =COLORES["acento_verde"],
                family="'Space Mono', monospace",
                size  =11
            ),
            line_color=COLORES["borde"],
            height=36,
        ),
        cells=dict(
            values=[
                df_metricas["modelo"],
                df_metricas["MAE"].apply(lambda x: f"{x:,.4f}"),
                df_metricas["RMSE"].apply(lambda x: f"{x:,.4f}"),
                df_metricas["MAPE"].apply(lambda x: f"{x:,.2f}%"),
                df_metricas["SMAPE"].apply(lambda x: f"{x:,.2f}%"),
            ],
            fill_color=colores_celdas,
            align="left",
            font=dict(
                color =COLORES["texto_principal"],
                family="'Space Mono', monospace",
                size  =11
            ),
            line_color=COLORES["borde"],
            height=32,
        )
    )])

    fig.update_layout(
        paper_bgcolor=COLORES["fondo_card"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=len(df_metricas) * 32 + 80,
    )

    return fig
