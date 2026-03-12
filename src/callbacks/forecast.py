# ============================================================
# forecast.py — Callbacks de Dash para la interactividad
# Maneja los eventos de usuario: selección de símbolo,
# ejecución del forecast y reset de la aplicación.
# ============================================================

from dash import Input, Output, State, callback, html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from src.data.loader import obtener_info_activo
from src.models.orchestrator import ejecutar_pipeline
from src.layout.components import (
    crear_info_activo,
    COLORES,
    ESTILO_CARD
)
from src.layout.plots import (
    grafico_validacion,
    grafico_forecast,
    crear_tabla_metricas
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
    # CALLBACK — Labels dinámicos de los sliders
    # ============================================================

    @app.callback(
        Output("label-meses-test", "children"),
        Input("input-meses-test", "value")
    )
    def actualizar_label_test(meses):
        """Muestra el valor actual del slider de test split."""
        return f"{meses} {'mes' if meses == 1 else 'meses'}"

    @app.callback(
        Output("label-meses-horizonte", "children"),
        Input("input-meses-horizonte", "value")
    )
    def actualizar_label_horizonte(meses):
        """Muestra el valor actual del slider de horizonte."""
        return f"{meses} {'mes' if meses == 1 else 'meses'}"

    # ============================================================
    # CALLBACK — Info del activo al seleccionar símbolo
    # ============================================================

    @app.callback(
        Output("seccion-info-activo", "children"),
        Input("input-simbolo", "value"),
        prevent_initial_call=False
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
        State("input-simbolo", "value"),
        State("input-fecha-inicio", "date"),
        State("input-fecha-fin", "date"),
        State("input-meses-test", "value"),
        State("input-meses-horizonte", "value"),
        prevent_initial_call=True
    )
    def ejecutar_forecast(n_clicks, simbolo, fecha_inicio, fecha_fin,
                          meses_test, meses_horizonte):
        """
        Ejecuta el pipeline completo de forecasting y renderiza
        los resultados — gráfico de validación, tabla de métricas
        y gráfico de forecast hacia adelante.
        """
        if not n_clicks or not simbolo:
            return html.Div()

        try:
            # Ejecutar pipeline completo
            resultados = ejecutar_pipeline(
                simbolo         = simbolo,
                fecha_inicio    = str(fecha_inicio),
                fecha_fin       = str(fecha_fin),
                meses_test      = meses_test,
                meses_horizonte = meses_horizonte
            )

            # Generar gráficos
            fig_validacion = grafico_validacion(
                df_completo = resultados["df_completo"],
                df_test     = resultados["df_test"],
                pred_test   = resultados["pred_test"],
                simbolo     = simbolo
            )

            fig_forecast = grafico_forecast(
                df_completo     = resultados["df_completo"],
                pred_forecast   = resultados["pred_forecast"],
                simbolo         = simbolo,
                meses_horizonte = meses_horizonte
            )

            fig_metricas = crear_tabla_metricas(resultados["metricas"])

            # Construir sección de resultados
            return html.Div([

                # Gráfico de validación
                html.Div([
                    html.H6(
                        "VALIDACIÓN DE MODELOS",
                        style={
                            "color"        : COLORES["texto_secundario"],
                            "fontFamily"   : "'Space Mono', monospace",
                            "fontSize"     : "0.7rem",
                            "letterSpacing": "2px",
                            "marginBottom" : "12px",
                        }
                    ),
                    dcc.Graph(
                        figure=fig_validacion,
                        config={"displayModeBar": True, "responsive": True, "modeBarButtonsToAdd": ["hoverClosestCartesian", "hoverCompareCartesian"]},
                        style={"width": "100%"}
                    ),
                ], style=ESTILO_CARD),

                # Tabla de métricas
                html.Div([
                    html.H6(
                        "MÉTRICAS DE ACCURACY — TEST SET",
                        style={
                            "color"        : COLORES["texto_secundario"],
                            "fontFamily"   : "'Space Mono', monospace",
                            "fontSize"     : "0.7rem",
                            "letterSpacing": "2px",
                            "marginBottom" : "12px",
                        }
                    ),
                    html.P(
                        "★ Mejor modelo por métrica resaltado en verde",
                        style={
                            "color"     : COLORES["acento_verde"],
                            "fontSize"  : "0.75rem",
                            "fontFamily": "'DM Sans', sans-serif",
                            "marginBottom": "8px",
                        }
                    ),
                    dcc.Graph(
                        figure=fig_metricas,
                        config={"displayModeBar": False},
                        style={"width": "100%"}
                    ),
                ], style=ESTILO_CARD),

                # Gráfico de forecast
                html.Div([
                    html.H6(
                        f"FORECAST — {meses_horizonte} MESES",
                        style={
                            "color"        : COLORES["texto_secundario"],
                            "fontFamily"   : "'Space Mono', monospace",
                            "fontSize"     : "0.7rem",
                            "letterSpacing": "2px",
                            "marginBottom" : "12px",
                        }
                    ),
                    dcc.Graph(
                        figure=fig_forecast,
                        config={"displayModeBar": True, "responsive": True, "modeBarButtonsToAdd": ["hoverClosestCartesian", "hoverCompareCartesian"]},
                        style={"width": "100%"}
                    ),
                ], style=ESTILO_CARD),

            ])

        except Exception as e:
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
        Output("contenido-forecast", "children", allow_duplicate=True),
        Output("input-simbolo", "value"),
        Output("input-fecha-inicio", "date"),
        Output("input-fecha-fin", "date"),
        Output("input-meses-test", "value"),
        Output("input-meses-horizonte", "value"),
        Input("btn-reset", "n_clicks"),
        prevent_initial_call=True
    )
    def resetear_app(n_clicks):
        """
        Resetea todos los inputs a sus valores por defecto
        y limpia el área de resultados.
        """
        from datetime import date
        return (
            html.Div(),       # Limpiar resultados sin placeholder
            "AAPL",           # Símbolo por defecto
            date(2019, 1, 1), # Fecha inicio por defecto
            date.today(),     # Fecha fin por defecto
            4,                # Meses test por defecto
            6,                # Meses horizonte por defecto
        )
