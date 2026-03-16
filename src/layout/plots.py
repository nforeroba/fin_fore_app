# ============================================================
# plots.py — Funciones de visualización con Plotly
# Genera los gráficos interactivos de validación y forecast
# con la estética de terminal financiero oscuro.
# ============================================================

import pandas as pd
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
        orientation ="h",
        x=0.5, y=-0.22,
        xanchor="center",
        yanchor="top",
        groupclick="toggleitem",
    ),
    margin=dict(l=50, r=30, t=50, b=110),
    hovermode="x unified",
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
# UTILIDAD — Construir error_y para intervalos de confianza
# ============================================================

def _construir_error_y(df_modelo: pd.DataFrame, color: str) -> dict:
    """
    Construye el dict error_y para go.Scatter con intervalos de confianza
    asimétricos (yhat_lower / yhat_upper).

    Las error bars son parte de la misma traza que la línea, por lo que
    el toggle de leyenda las oculta/muestra automáticamente junto con ella.

    Parámetros:
        df_modelo: DataFrame con columnas yhat, yhat_lower, yhat_upper
        color    : color hex del modelo para las barras

    Retorna:
        Dict compatible con el parámetro error_y de go.Scatter
    """
    array_plus  = (df_modelo["yhat_upper"] - df_modelo["yhat"]).clip(lower=0).tolist()
    array_minus = (df_modelo["yhat"]       - df_modelo["yhat_lower"]).clip(lower=0).tolist()

    return dict(
        type      ="data",
        array     =array_plus,
        arrayminus=array_minus,
        visible   =True,
        color     =hex_a_rgba(color, 0.45),
        thickness =1.2,
        width     =0,           # sin caps horizontales — más limpio
    )


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

    El legendgroup vincula la línea y la banda CI de cada modelo
    para que aparezcan y desaparezcan juntas al hacer clic en la leyenda.

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
        legendgroup="ACTUAL",
        line=dict(color=COLORES["texto_principal"], width=1.5),
        hovertemplate="%{x|%Y-%m-%d}  %{y:,.2f}<extra>ACTUAL</extra>"
    ))

    # --- Predicciones por modelo ---
    for modelo in pred_test["modelo"].unique():
        df_modelo = pred_test[pred_test["modelo"] == modelo].copy()
        color = COLORES_MODELOS.get(modelo, "#FFFFFF")

        # Línea de predicción con error bars CI — toggle funciona porque son la misma traza
        fig.add_trace(go.Scatter(
            x=df_modelo["ds"],
            y=df_modelo["yhat"],
            name=modelo,
            legendgroup=modelo,
            line=dict(color=color, width=1.5, dash="dot"),
            error_y=_construir_error_y(df_modelo, color),
            hovertemplate=(
                f"<b>{modelo}</b><br>"
                "Date: %{x|%Y-%m-%d}<br>"
                "Pred: %{y:,.2f}<br>"
                "CI±: [%{customdata[0]:,.2f} – %{customdata[1]:,.2f}]"
                "<extra></extra>"
            ),
            customdata=list(zip(
                df_modelo["yhat_lower"].tolist(),
                df_modelo["yhat_upper"].tolist()
            )),
        ))

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
            text=f"{simbolo} — Model Validation",
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

    El legendgroup vincula la línea y la banda CI de cada modelo
    para que aparezcan y desaparezcan juntas al hacer clic en la leyenda.

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
        legendgroup="ACTUAL",
        line=dict(color=COLORES["texto_principal"], width=1.5),
        hovertemplate="%{x|%Y-%m-%d}  %{y:,.2f}<extra>ACTUAL</extra>"
    ))

    # --- Forecast por modelo ---
    for modelo in pred_forecast["modelo"].unique():
        df_modelo = pred_forecast[pred_forecast["modelo"] == modelo].copy()
        color = COLORES_MODELOS.get(modelo, "#FFFFFF")

        # Línea de forecast con error bars CI — toggle funciona porque son la misma traza
        fig.add_trace(go.Scatter(
            x=df_modelo["ds"],
            y=df_modelo["yhat"],
            name=modelo,
            legendgroup=modelo,
            line=dict(color=color, width=1.5),
            error_y=_construir_error_y(df_modelo, color),
            hovertemplate=(
                f"<b>{modelo}</b><br>"
                "Date: %{x|%Y-%m-%d}<br>"
                "Pred: %{y:,.2f}<br>"
                "CI±: [%{customdata[0]:,.2f} – %{customdata[1]:,.2f}]"
                "<extra></extra>"
            ),
            customdata=list(zip(
                df_modelo["yhat_lower"].tolist(),
                df_modelo["yhat_upper"].tolist()
            )),
        ))

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
            text=f"{simbolo} — {meses_horizonte}-Month Forecast",
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
    Generates a styled metrics table with Plotly,
    highlighting the best model per metric in green,
    flagging overfitting via the Train/Test MAPE ratio,
    and showing MPE (Bias %) with traffic-light coloring.

    Parameters:
        df_metricas: DataFrame with columns modelo, MAE, RMSE, MAPE, SMAPE, MPE,
                     and optionally MAPE_train for overfit detection.

    Returns:
        Plotly Figure with the table
    """
    metricas = ["MAE", "RMSE", "MAPE", "SMAPE"]

    # Overfit thresholds differentiated by model family.
    # Rationale: ML models with lag features have structurally lower
    # train MAPE (they "see" true past values in-sample but use predicted
    # values recursively at forecast time), so their OK threshold is lower.
    OVERFIT_THRESHOLDS = {
        "statistical": (0.65, 0.40),
        "additive"   : (0.50, 0.30),
        "hybrid"     : (0.40, 0.25),
        "lag_based"  : (0.30, 0.15),
    }

    # --- Overfit label & color ---
    def _overfit_label(row):
        if "MAPE_train" not in row or row["MAPE"] == 0:
            return "—"
        ratio     = row["MAPE_train"] / row["MAPE"]
        familia   = row.get("familia", "lag_based")
        ok_min, mod_min = OVERFIT_THRESHOLDS.get(familia, (0.30, 0.15))
        if ratio >= ok_min:
            return "✓ OK"
        elif ratio >= mod_min:
            return "⚠ Moderate"
        else:
            return "✗ High"

    def _overfit_color(row):
        if "MAPE_train" not in row or row["MAPE"] == 0:
            return COLORES["fondo_input"]
        ratio     = row["MAPE_train"] / row["MAPE"]
        familia   = row.get("familia", "lag_based")
        ok_min, mod_min = OVERFIT_THRESHOLDS.get(familia, (0.30, 0.15))
        if ratio >= ok_min:
            return hex_a_rgba(COLORES["acento_verde"], 0.15)
        elif ratio >= mod_min:
            return hex_a_rgba("#F0B429", 0.20)
        else:
            return hex_a_rgba(COLORES["acento_rojo"], 0.20)

    # --- Bias label & color ---
    def _bias_label(row):
        if "MPE" not in row:
            return "—"
        mpe = row["MPE"]
        sign = "+" if mpe >= 0 else ""
        return f"{sign}{mpe:,.2f}%"

    def _bias_color(row):
        if "MPE" not in row:
            return COLORES["fondo_input"]
        abs_mpe = abs(row["MPE"])
        if abs_mpe < 2.0:
            return hex_a_rgba(COLORES["acento_verde"], 0.15)
        elif abs_mpe < 5.0:
            return hex_a_rgba("#F0B429", 0.20)
        else:
            return hex_a_rgba(COLORES["acento_rojo"], 0.20)

    overfit_labels = df_metricas.apply(_overfit_label, axis=1).tolist()
    overfit_colors = df_metricas.apply(_overfit_color, axis=1).tolist()
    bias_labels    = df_metricas.apply(_bias_label,    axis=1).tolist()
    bias_colors    = df_metricas.apply(_bias_color,    axis=1).tolist()

    # --- Cell colors: best model per metric highlighted in green ---
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

    colores_celdas.append(bias_colors)
    colores_celdas.append(overfit_colors)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["<b>MODEL</b>", "<b>MAE</b>", "<b>RMSE</b>",
                    "<b>MAPE %</b>", "<b>SMAPE %</b>",
                    "<b>BIAS %</b>", "<b>OVERFIT</b>"],
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
                bias_labels,
                overfit_labels,
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
