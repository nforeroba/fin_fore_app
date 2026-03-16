# ============================================================
# forecast.py — Callbacks de Dash para la interactividad
# Maneja los eventos de usuario: tabs de categoría, selección
# de símbolo, steppers, ejecución del forecast y reset.
# ============================================================

from dash import Input, Output, State, html, dcc, no_update
import dash_bootstrap_components as dbc

from src.data.loader import obtener_info_activo
from src.models.orchestrator import ejecutar_pipeline
from src.layout.components import (
    crear_info_activo,
    COLORES,
    ESTILO_CARD,
    DEFAULTS_CATEGORIA,
)
from src.layout.plots import (
    grafico_validacion,
    grafico_forecast,
    crear_tabla_metricas,
)


# ============================================================
# REGISTRO DE CALLBACKS
# ============================================================

def registrar_callbacks(app):
    """
    Registra todos los callbacks de la aplicación.
    Se llama desde app.py después de inicializar Dash.

    Parámetros:
        app: instancia de la aplicación Dash
    """

    # ============================================================
    # CALLBACK — Tabs de categoría
    # Actualiza el store de categoría activa, las clases CSS de los
    # tabs, las opciones del dropdown y el valor por defecto.
    # ============================================================

    @app.callback(
        Output("store-categoria",   "data"),
        Output("tab-sp500",         "className"),
        Output("tab-crypto",        "className"),
        Output("tab-fx",            "className"),
        Output("input-simbolo",     "options"),
        Output("input-simbolo",     "value"),
        Input("tab-sp500",          "n_clicks"),
        Input("tab-crypto",         "n_clicks"),
        Input("tab-fx",             "n_clicks"),
        State("store-simbolos-sp500",  "data"),
        State("store-simbolos-crypto", "data"),
        State("store-simbolos-fx",     "data"),
        State("store-categoria",       "data"),
        prevent_initial_call=True,
    )
    def cambiar_categoria(n_sp500, n_crypto, n_fx,
                          simbolos_sp500, simbolos_crypto, simbolos_fx,
                          categoria_actual):
        """
        Al hacer click en un tab:
        - Actualiza el store de categoría
        - Marca el tab activo con clase CSS tab-activo
        - Carga las opciones del dropdown correspondientes
        - Resetea el dropdown al símbolo por defecto de esa categoría
        """
        from dash import ctx

        trigger = ctx.triggered_id
        if not trigger:
            return no_update, no_update, no_update, no_update, no_update, no_update

        BASE   = "tab-categoria"
        ACTIVO = "tab-categoria tab-activo"

        if trigger == "tab-sp500":
            opciones  = [{"label": s, "value": s} for s in (simbolos_sp500 or [])]
            return (
                "sp500",
                ACTIVO, BASE, BASE,
                opciones,
                DEFAULTS_CATEGORIA["sp500"],
            )
        elif trigger == "tab-crypto":
            opciones  = [{"label": s, "value": s} for s in (simbolos_crypto or [])]
            return (
                "crypto",
                BASE, ACTIVO, BASE,
                opciones,
                DEFAULTS_CATEGORIA["crypto"],
            )
        elif trigger == "tab-fx":
            opciones  = [{"label": s, "value": s} for s in (simbolos_fx or [])]
            return (
                "fx",
                BASE, BASE, ACTIVO,
                opciones,
                DEFAULTS_CATEGORIA["fx"],
            )

        return no_update, no_update, no_update, no_update, no_update, no_update


    # ============================================================
    # CALLBACK — Stepper Test Split
    # ============================================================

    @app.callback(
        Output("input-meses-test", "value"),
        Input("btn-test-menos",    "n_clicks"),
        Input("btn-test-mas",      "n_clicks"),
        State("input-meses-test",  "value"),
        prevent_initial_call=True,
    )
    def stepper_test(n_menos, n_mas, valor_actual):
        """Decrementa o incrementa el valor de test split (1–24)."""
        from dash import ctx
        valor = int(valor_actual or 4)
        if ctx.triggered_id == "btn-test-menos":
            return max(1, valor - 1)
        if ctx.triggered_id == "btn-test-mas":
            return min(24, valor + 1)
        return valor


    # ============================================================
    # CALLBACK — Stepper Horizonte
    # ============================================================

    @app.callback(
        Output("input-meses-horizonte", "value"),
        Input("btn-horizonte-menos",    "n_clicks"),
        Input("btn-horizonte-mas",      "n_clicks"),
        State("input-meses-horizonte",  "value"),
        prevent_initial_call=True,
    )
    def stepper_horizonte(n_menos, n_mas, valor_actual):
        """Decrementa o incrementa el valor de horizonte (1–24)."""
        from dash import ctx
        valor = int(valor_actual or 6)
        if ctx.triggered_id == "btn-horizonte-menos":
            return max(1, valor - 1)
        if ctx.triggered_id == "btn-horizonte-mas":
            return min(24, valor + 1)
        return valor


    # ============================================================
    # CALLBACK — Info del activo al seleccionar símbolo
    # ============================================================

    @app.callback(
        Output("seccion-info-activo", "children"),
        Input("input-simbolo", "value"),
        prevent_initial_call=False,
    )
    def actualizar_info_activo(simbolo):
        """
        Descarga y muestra la información del activo seleccionado
        inmediatamente al cambiar el símbolo en el dropdown.
        """
        if not simbolo:
            return html.Div()
        info = obtener_info_activo(simbolo)
        return crear_info_activo(info)


    # ============================================================
    # CALLBACK — Ejecutar forecast al presionar RUN
    # ============================================================

    @app.callback(
        Output("contenido-forecast", "children"),
        Input("btn-run", "n_clicks"),
        State("input-simbolo",        "value"),
        State("input-fecha-inicio",   "date"),
        State("input-fecha-fin",      "date"),
        State("input-meses-test",     "value"),
        State("input-meses-horizonte","value"),
        prevent_initial_call=True,
    )
    def ejecutar_forecast(n_clicks, simbolo, fecha_inicio, fecha_fin,
                          meses_test, meses_horizonte):
        """
        Ejecuta el pipeline completo de forecasting y renderiza
        los resultados: validación, métricas y forecast.
        """
        if not n_clicks or not simbolo:
            return html.Div()

        try:
            resultados = ejecutar_pipeline(
                simbolo         = simbolo,
                fecha_inicio    = str(fecha_inicio),
                fecha_fin       = str(fecha_fin),
                meses_test      = int(meses_test or 6),
                meses_horizonte = int(meses_horizonte or 6),
            )

            fig_validacion = grafico_validacion(
                df_completo = resultados["df_completo"],
                df_test     = resultados["df_test"],
                pred_test   = resultados["pred_test"],
                simbolo     = simbolo,
            )
            fig_forecast = grafico_forecast(
                df_completo     = resultados["df_completo"],
                pred_forecast   = resultados["pred_forecast"],
                simbolo         = simbolo,
                meses_horizonte = int(meses_horizonte or 6),
            )
            fig_metricas = crear_tabla_metricas(resultados["metricas"])

            estilo_titulo = {
                "color"        : COLORES["texto_secundario"],
                "fontFamily"   : "'Space Mono', monospace",
                "fontSize"     : "0.7rem",
                "letterSpacing": "2px",
                "marginBottom" : "12px",
            }

            return html.Div([

                # Validation chart
                html.Div([
                    html.H6("MODEL VALIDATION", style=estilo_titulo),
                    dcc.Graph(
                        figure=fig_validacion,
                        config={
                            "displayModeBar": True,
                            "responsive"    : True,
                            "modeBarButtonsToAdd": [
                                "hoverClosestCartesian",
                                "hoverCompareCartesian",
                            ],
                        },
                        style={"width": "100%"},
                    ),
                ], style=ESTILO_CARD),

                # Metrics table
                html.Div([
                    html.H6("ACCURACY METRICS — TEST SET", style=estilo_titulo),
                    html.P(
                        "★ Best model per metric highlighted in green  ·  Bias % = MPE (signed)  ·  Overfit = Train MAPE / Test MAPE ratio",
                        style={
                            "color"       : COLORES["acento_verde"],
                            "fontSize"    : "0.75rem",
                            "fontFamily"  : "'DM Sans', sans-serif",
                            "marginBottom": "8px",
                        }
                    ),
                    dcc.Graph(
                        figure=fig_metricas,
                        config={"displayModeBar": False},
                        style={"width": "100%"},
                    ),
                ], style=ESTILO_CARD),

                # Forecast chart
                html.Div([
                    html.H6(
                        f"FORECAST — {meses_horizonte} MONTHS",
                        style=estilo_titulo,
                    ),
                    dcc.Graph(
                        figure=fig_forecast,
                        config={
                            "displayModeBar": True,
                            "responsive"    : True,
                            "modeBarButtonsToAdd": [
                                "hoverClosestCartesian",
                                "hoverCompareCartesian",
                            ],
                        },
                        style={"width": "100%"},
                    ),
                ], style=ESTILO_CARD),

            ])

        except Exception:
            import traceback
            return html.Div([
                html.P(
                    "⚠ Error al ejecutar el forecast",
                    style={
                        "color"     : COLORES["acento_rojo"],
                        "fontFamily": "'Space Mono', monospace",
                        "fontSize"  : "0.9rem",
                    }
                ),
                html.Pre(
                    traceback.format_exc(),
                    style={
                        "color"     : COLORES["texto_secundario"],
                        "fontFamily": "'DM Sans', sans-serif",
                        "fontSize"  : "0.75rem",
                        "whiteSpace": "pre-wrap",
                    }
                ),
            ], style=ESTILO_CARD)


    # ============================================================
    # CALLBACK — Reset de la aplicación
    # ============================================================

    @app.callback(
        Output("contenido-forecast",    "children",  allow_duplicate=True),
        Output("tab-sp500",             "className", allow_duplicate=True),
        Output("tab-crypto",            "className", allow_duplicate=True),
        Output("tab-fx",                "className", allow_duplicate=True),
        Output("store-categoria",       "data",      allow_duplicate=True),
        Output("input-simbolo",         "options",   allow_duplicate=True),
        Output("input-simbolo",         "value",     allow_duplicate=True),
        Output("input-fecha-inicio",    "date"),
        Output("input-fecha-fin",       "date"),
        Output("input-meses-test",      "value",     allow_duplicate=True),
        Output("input-meses-horizonte", "value",     allow_duplicate=True),
        Input("btn-reset", "n_clicks"),
        State("store-simbolos-sp500", "data"),
        prevent_initial_call=True,
    )
    def resetear_app(n_clicks, simbolos_sp500):
        """
        Resets all inputs to their default values:
        - Active tab → S&P 500
        - Symbol → AAPL
        - Dates → 2022-01-01 to yesterday
        - Test split → 6, Horizon → 6
        - Clears results area
        """
        from datetime import date, timedelta
        BASE   = "tab-categoria"
        ACTIVO = "tab-categoria tab-activo"
        opciones_sp500 = [{"label": s, "value": s} for s in (simbolos_sp500 or [])]

        return (
            html.Div(),                          # Clear results
            ACTIVO, BASE, BASE,                  # Tabs: S&P 500 active
            "sp500",                             # Category store
            opciones_sp500,                      # Dropdown options
            DEFAULTS_CATEGORIA["sp500"],         # Symbol: AAPL
            date(2022, 1, 1),                   # Start date
            date.today() - timedelta(days=1),    # End date: yesterday
            6,                                   # Test split months
            6,                                   # Horizon months
        )
