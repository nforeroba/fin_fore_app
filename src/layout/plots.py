# ============================================================
# plots.py — Funciones de visualización con Plotly
# Genera los gráficos interactivos de validación y forecast
# con la estética de terminal financiero oscuro.
# ============================================================

import pandas as pd
import plotly.graph_objects as go
from dash import html
import dash_bootstrap_components as dbc
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

# ============================================================
# TABLA DE MÉTRICAS HTML CON TOOLTIPS
# ============================================================

# Display-friendly family labels with accent colors
FAMILIA_DISPLAY = {
    "statistical": ("Statistical",  "#58A6FF"),   # blue
    "additive"   : ("Additive",     "#FB923C"),   # orange
    "hybrid"     : ("Hybrid",       "#E879F9"),   # purple
    "lag_based"  : ("Lag-Based",    "#34D399"),   # teal
}

# Tooltip text for each metric header
TOOLTIPS_METRICAS = {
    "MODEL"  : "Model name.",
    "FAMILY" : (
        "Model family based on forecasting mechanism. "
        "Statistical: classical time-series models (ARIMA, ETS, Theta). "
        "Additive: trend + seasonality decomposition (Prophet). "
        "Hybrid: additive decomposition + boosted residuals (Prophet+XGBoost). "
        "Lag-Based: ML models using lagged values as features."
    ),
    "MAE"    : (
        "Mean Absolute Error. Average absolute difference between predicted "
        "and actual values, in price units. Lower is better. "
        "Scale-dependent — not comparable across different assets."
    ),
    "RMSE"   : (
        "Root Mean Squared Error. Like MAE but penalizes large errors more "
        "heavily due to squaring. In price units. Lower is better."
    ),
    "MAPE"   : (
        "Mean Absolute Percentage Error. Average absolute error as a "
        "percentage of the actual value. Scale-independent — comparable "
        "across assets. Lower is better."
    ),
    "SMAPE"  : (
        "Symmetric MAPE. Like MAPE but normalizes by the average of actual "
        "and predicted values, removing the asymmetry that makes MAPE "
        "penalize underestimates more than overestimates. Lower is better."
    ),
    "BIAS"   : (
        "Bias % (Mean Percentage Error). Signed version of MAPE — errors "
        "do not cancel in absolute value, revealing systematic direction. "
        "Positive = model consistently overestimates. "
        "Negative = consistently underestimates. "
        "Close to zero = no systematic directional bias."
    ),
    "OVERFIT": (
        "Overfitting indicator based on the Train MAPE / Test MAPE ratio. "
        "A ratio close to 1 means similar performance on training and test data. "
        "A low ratio means the model fits training data well but fails to generalize. "
        "Thresholds are differentiated by model family. "        
    ),
}

# Overfit thresholds by family (ok_min, moderate_min)
_OVERFIT_THRESHOLDS = {
    "statistical": (0.65, 0.40),
    "additive"   : (0.50, 0.30),
    "hybrid"     : (0.40, 0.25),
    "lag_based"  : (0.30, 0.15),
}


def crear_tabla_metricas(df_metricas: pd.DataFrame) -> html.Div:
    """
    Generates an HTML metrics table with tooltips on each column header,
    a Family column, Bias % and Overfit columns with traffic-light coloring,
    and best-model highlighting per metric.

    Parameters:
        df_metricas: DataFrame with columns modelo, familia, MAE, RMSE,
                     MAPE, SMAPE, MPE, and optionally MAPE_train.

    Returns:
        html.Div containing the styled table and dbc.Tooltips
    """

    # ---- Helper: cell background colors -------------------------

    def _best_color(val, col_vals):
        return hex_a_rgba(COLORES["acento_verde"], 0.20) if val == col_vals.min() else COLORES["fondo_input"]

    def _bias_bg(mpe):
        if mpe is None:
            return COLORES["fondo_input"]
        a = abs(mpe)
        if a < 2.0:   return hex_a_rgba(COLORES["acento_verde"], 0.15)
        if a < 5.0:   return hex_a_rgba("#F0B429", 0.20)
        return hex_a_rgba(COLORES["acento_rojo"], 0.20)

    def _overfit_info(row):
        if "MAPE_train" not in row or row["MAPE"] == 0:
            return "—", COLORES["fondo_input"]
        ratio   = row["MAPE_train"] / row["MAPE"]
        familia = row.get("familia", "lag_based")
        ok, mod = _OVERFIT_THRESHOLDS.get(familia, (0.30, 0.15))
        if ratio >= ok:
            return "✓ OK",       hex_a_rgba(COLORES["acento_verde"], 0.15)
        if ratio >= mod:
            return "⚠ Moderate", hex_a_rgba("#F0B429", 0.20)
        return "✗ High",         hex_a_rgba(COLORES["acento_rojo"], 0.20)

    # ---- Styles -------------------------------------------------

    th_style = {
        "color"        : COLORES["acento_verde"],
        "fontFamily"   : "'Space Mono', monospace",
        "fontSize"     : "0.7rem",
        "fontWeight"   : "700",
        "letterSpacing": "0.5px",
        "padding"      : "10px 12px",
        "borderBottom" : f"1px solid {COLORES['borde']}",
        "borderRight"  : f"1px solid {COLORES['borde']}",
        "backgroundColor": COLORES["fondo_card"],
        "whiteSpace"   : "nowrap",
        "cursor"       : "default",
    }
    td_style = {
        "fontFamily": "'Space Mono', monospace",
        "fontSize"  : "0.75rem",
        "color"     : COLORES["texto_principal"],
        "padding"   : "8px 12px",
        "borderBottom": f"1px solid {COLORES['borde']}",
        "borderRight" : f"1px solid {COLORES['borde']}",
        "whiteSpace"  : "nowrap",
    }

    def _th(label, tooltip_id, tooltip_text):
        return html.Th(
            [
                label,
                html.Span(
                    " ⓘ",
                    id=tooltip_id,
                    style={
                        "color"     : COLORES["texto_secundario"],
                        "fontSize"  : "0.65rem",
                        "cursor"    : "help",
                    }
                ),
                dbc.Tooltip(
                    tooltip_text,
                    target=tooltip_id,
                    placement="top",
                    style={
                        "fontFamily": "'DM Sans', sans-serif",
                        "fontSize"  : "0.78rem",
                        "maxWidth"  : "320px",
                    }
                ),
            ],
            style=th_style,
        )

    # ---- Header row ---------------------------------------------

    headers = [
        html.Th("MODEL",  style=th_style),
        _th("FAMILY",  "tt-family",  TOOLTIPS_METRICAS["FAMILY"]),
        _th("MAE",     "tt-mae",     TOOLTIPS_METRICAS["MAE"]),
        _th("RMSE",    "tt-rmse",    TOOLTIPS_METRICAS["RMSE"]),
        _th("MAPE %",  "tt-mape",    TOOLTIPS_METRICAS["MAPE"]),
        _th("SMAPE %", "tt-smape",   TOOLTIPS_METRICAS["SMAPE"]),
        _th("BIAS %",  "tt-bias",    TOOLTIPS_METRICAS["BIAS"]),
        _th("OVERFIT", "tt-overfit", TOOLTIPS_METRICAS["OVERFIT"]),
    ]

    # ---- Data rows ----------------------------------------------

    rows = []
    for _, row in df_metricas.iterrows():

        familia      = row.get("familia", "lag_based")
        fam_label, fam_color = FAMILIA_DISPLAY.get(familia, ("Unknown", COLORES["texto_secundario"]))
        overfit_label, overfit_bg = _overfit_info(row)
        mpe          = row.get("MPE")
        bias_label   = (f"+{mpe:,.2f}%" if mpe >= 0 else f"{mpe:,.2f}%") if mpe is not None else "—"

        cells = [
            html.Td(row["modelo"],                                     style=td_style),
            html.Td(fam_label, style={**td_style, "color": fam_color}),
            html.Td(f"{row['MAE']:,.4f}",  style={**td_style, "backgroundColor": _best_color(row["MAE"],  df_metricas["MAE"])}),
            html.Td(f"{row['RMSE']:,.4f}", style={**td_style, "backgroundColor": _best_color(row["RMSE"], df_metricas["RMSE"])}),
            html.Td(f"{row['MAPE']:,.2f}%",  style={**td_style, "backgroundColor": _best_color(row["MAPE"],  df_metricas["MAPE"])}),
            html.Td(f"{row['SMAPE']:,.2f}%", style={**td_style, "backgroundColor": _best_color(row["SMAPE"], df_metricas["SMAPE"])}),
            html.Td(bias_label,    style={**td_style, "backgroundColor": _bias_bg(mpe)}),
            html.Td(overfit_label, style={**td_style, "backgroundColor": overfit_bg}),
        ]
        rows.append(html.Tr(cells))

    table = html.Table(
        [html.Thead(html.Tr(headers)), html.Tbody(rows)],
        style={
            "width"          : "100%",
            "borderCollapse" : "collapse",
            "backgroundColor": COLORES["fondo_input"],
        }
    )

    # ---- Footer with threshold legend ---------------------------

    sep_foot = html.Span(
        "  ·  ",
        style={"color": COLORES["borde"], "margin": "0 4px"}
    )

    def _foot_badge(text, bg):
        return html.Span(
            text,
            style={
                "backgroundColor": bg,
                "color"          : COLORES["texto_principal"],
                "fontFamily"     : "'Space Mono', monospace",
                "fontSize"       : "0.65rem",
                "padding"        : "1px 6px",
                "borderRadius"   : "3px",
                "marginRight"    : "4px",
            }
        )

    footer = html.Div([

        # Row 1 — threshold badges
        html.Div([
            html.Span("BIAS %:", style={"color": COLORES["texto_secundario"], "fontFamily": "'Space Mono', monospace", "fontSize": "0.65rem", "marginRight": "6px"}),
            _foot_badge("< 2%  low",         hex_a_rgba(COLORES["acento_verde"], 0.15)),
            _foot_badge("2–5%  moderate",    hex_a_rgba("#F0B429", 0.20)),
            _foot_badge("> 5%  high",        hex_a_rgba(COLORES["acento_rojo"], 0.20)),
            sep_foot,
            html.Span("OVERFIT:", style={"color": COLORES["texto_secundario"], "fontFamily": "'Space Mono', monospace", "fontSize": "0.65rem", "marginRight": "6px"}),
            _foot_badge("✓ OK",       hex_a_rgba(COLORES["acento_verde"], 0.15)),
            _foot_badge("⚠ Moderate", hex_a_rgba("#F0B429", 0.20)),
            _foot_badge("✗ High",     hex_a_rgba(COLORES["acento_rojo"], 0.20)),
        ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap", "gap": "4px"}),

        # Row 2 — explanation of family-differentiated thresholds
        html.Span(
            (
                "Overfit thresholds differ by family. "
                "Statistical models (AutoARIMA, ETS, Theta) have few parameters and are regularized by design, "
                "so their train and test errors are naturally similar — a low ratio is a genuine warning. "
                "Additive models (Prophet) decompose the series into trend and seasonality without using lagged values, "
                "making their in-sample fit honest and directly comparable to the test error. "
                "Hybrid models (Prophet+XGBoost) add a boosting layer over in-sample residuals, "
                "slightly inflating train-set fit — thresholds are adjusted accordingly. "
                "Lag-based models (ElasticNet, RandomForest, XGBoost) use true past prices as input features during training "
                "but must rely on their own previous predictions at forecast time. "
                "This structural difference makes their in-sample error artificially low regardless of overfitting, "
                "so only a very low ratio is treated as a real concern."
            ),
            style={
                "color"     : COLORES["texto_secundario"],
                "fontFamily": "'DM Sans', sans-serif",
                "fontSize"  : "0.65rem",
                "fontStyle" : "italic",
                "marginTop" : "6px",
                "display"   : "block",
                "lineHeight": "1.6",
            },
        ),

    ], style={"marginTop": "10px"})

    return html.Div([
        html.Div(table, style={"overflowX": "auto"}),
        footer,
    ])
