# ============================================================
# components.py — Componentes reutilizables de la interfaz
# Define el header, panel de control, cards de información
# del activo y estructura general del layout.
# ============================================================

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import date, timedelta


# ============================================================
# PALETA DE COLORES — Terminal Financiero Moderno
# ============================================================

COLORES = {
    "fondo"          : "#0D1117",
    "fondo_card"     : "#161B22",
    "fondo_input"    : "#1C2128",
    "borde"          : "#30363D",
    "texto_principal": "#E6EDF3",
    "texto_secundario": "#8B949E",
    "acento_verde"   : "#00C896",
    "acento_rojo"    : "#FF6B6B",
    "acento_azul"    : "#58A6FF",
    "acento_amarillo": "#F0B429",
}

# Estilo base para cards
ESTILO_CARD = {
    "backgroundColor": COLORES["fondo_card"],
    "border"         : f"1px solid {COLORES['borde']}",
    "borderRadius"   : "8px",
    "padding"        : "20px",
    "marginBottom"   : "16px",
}

# Estilo base para inputs
ESTILO_INPUT = {
    "backgroundColor": COLORES["fondo_input"],
    "border"         : f"1px solid {COLORES['borde']}",
    "borderRadius"   : "6px",
    "color"          : COLORES["texto_principal"],
    "width"          : "100%",
}


# ============================================================
# HEADER
# ============================================================

def crear_header() -> html.Div:
    """
    Crea el header principal de la aplicación con título
    y descripción.
    """
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.H1(
                        "FinForecast",
                        style={
                            "color"       : COLORES["acento_verde"],
                            "fontFamily"  : "'Space Mono', monospace",
                            "fontSize"    : "2rem",
                            "fontWeight"  : "700",
                            "marginBottom": "4px",
                            "letterSpacing": "2px",
                        }
                    ),
                    html.P(
                        "Financial Asset Price Forecasting — S&P 500 · Crypto · FX",
                        style={
                            "color"      : COLORES["texto_secundario"],
                            "fontFamily" : "'DM Sans', sans-serif",
                            "fontSize"   : "0.9rem",
                            "margin"     : "0",
                        }
                    ),
                ],
                style={"flex": "1"}
            ),
        ],
        style={
            "backgroundColor": COLORES["fondo_card"],
            "borderBottom"   : f"1px solid {COLORES['borde']}",
            "padding"        : "20px 32px",
            "display"        : "flex",
            "alignItems"     : "center",
            "justifyContent" : "space-between",
        }
    )


# ============================================================
# PANEL DE CONTROL
# ============================================================

def crear_panel_control(
    simbolos_sp500: list,
    simbolos_crypto: list,
    simbolos_divisas: list
) -> html.Div:
    """
    Crea el panel lateral de control con todos los inputs
    necesarios para configurar el forecast.

    Parámetros:
        simbolos_sp500  : lista de símbolos del S&P500
        simbolos_crypto : lista de símbolos de crypto
        simbolos_divisas: lista de símbolos de divisas
    """
    # Construir opciones agrupadas para el dropdown
    opciones = (
        [{"label": f"📈 {s}", "value": s} for s in simbolos_sp500] +
        [{"label": f"₿ {s}", "value": s}  for s in simbolos_crypto] +
        [{"label": f"💱 {s}", "value": s} for s in simbolos_divisas]
    )

    return html.Div(
        children=[
            # Título del panel
            html.H6(
                "CONFIGURACIÓN",
                style={
                    "color"        : COLORES["texto_secundario"],
                    "fontFamily"   : "'Space Mono', monospace",
                    "fontSize"     : "0.7rem",
                    "letterSpacing": "2px",
                    "marginBottom" : "20px",
                }
            ),

            # Selector de símbolo
            html.Label(
                "Símbolo",
                style={"color": COLORES["texto_secundario"], "fontSize": "0.8rem",
                       "fontFamily": "'DM Sans', sans-serif"}
            ),
            dcc.Dropdown(
                id="input-simbolo",
                options=opciones,
                value="AAPL",
                searchable=True,
                clearable=False,
                style={"marginBottom": "16px", **ESTILO_INPUT},
                className="dropdown-dark"
            ),

            # Fecha inicio
            html.Label(
                "Fecha Inicio",
                style={"color": COLORES["texto_secundario"], "fontSize": "0.8rem",
                       "fontFamily": "'DM Sans', sans-serif"}
            ),
            dcc.DatePickerSingle(
                id="input-fecha-inicio",
                date=date(2019, 1, 1),
                display_format="YYYY-MM-DD",
                style={"marginBottom": "16px", "width": "100%"},
                className="date-picker-dark"
            ),

            # Fecha fin
            html.Label(
                "Fecha Fin",
                style={"color": COLORES["texto_secundario"], "fontSize": "0.8rem",
                       "fontFamily": "'DM Sans', sans-serif"}
            ),
            dcc.DatePickerSingle(
                id="input-fecha-fin",
                date=date.today(),
                display_format="YYYY-MM-DD",
                style={"marginBottom": "16px", "width": "100%"},
                className="date-picker-dark"
            ),

            # Slider test split
            html.Label(
                "Test Split",
                style={"color": COLORES["texto_secundario"], "fontSize": "0.8rem",
                       "fontFamily": "'DM Sans', sans-serif"}
            ),
            html.Div(
                id="label-meses-test",
                style={"color": COLORES["acento_verde"], "fontSize": "0.85rem",
                       "fontFamily": "'Space Mono', monospace", "marginBottom": "4px"}
            ),
            dcc.Slider(
                id="input-meses-test",
                min=1, max=12, step=1, value=4,
                marks={i: {"label": str(i), "style": {"color": COLORES["texto_secundario"]}}
                       for i in [1, 3, 6, 9, 12]},
                tooltip={"always_visible": False},
                className="slider-dark"
            ),
            html.Div(style={"marginBottom": "16px"}),

            # Slider horizonte
            html.Label(
                "Horizonte de Forecast",
                style={"color": COLORES["texto_secundario"], "fontSize": "0.8rem",
                       "fontFamily": "'DM Sans', sans-serif"}
            ),
            html.Div(
                id="label-meses-horizonte",
                style={"color": COLORES["acento_verde"], "fontSize": "0.85rem",
                       "fontFamily": "'Space Mono', monospace", "marginBottom": "4px"}
            ),
            dcc.Slider(
                id="input-meses-horizonte",
                min=1, max=24, step=1, value=6,
                marks={i: {"label": str(i), "style": {"color": COLORES["texto_secundario"]}}
                       for i in [1, 6, 12, 18, 24]},
                tooltip={"always_visible": False},
                className="slider-dark"
            ),
            html.Div(style={"marginBottom": "24px"}),

            # Botón Run Forecast
            html.Button(
                "▶  RUN FORECAST",
                id="btn-run",
                n_clicks=0,
                style={
                    "backgroundColor": COLORES["acento_verde"],
                    "color"          : COLORES["fondo"],
                    "border"         : "none",
                    "borderRadius"   : "6px",
                    "padding"        : "12px 0",
                    "width"          : "100%",
                    "fontFamily"     : "'Space Mono', monospace",
                    "fontSize"       : "0.85rem",
                    "fontWeight"     : "700",
                    "letterSpacing"  : "1px",
                    "cursor"         : "pointer",
                    "marginBottom"   : "8px",
                    "transition"     : "opacity 0.2s",
                }
            ),

            # Botón Reset
            html.Button(
                "↺  RESET",
                id="btn-reset",
                n_clicks=0,
                style={
                    "backgroundColor": "transparent",
                    "color"          : COLORES["texto_secundario"],
                    "border"         : f"1px solid {COLORES['borde']}",
                    "borderRadius"   : "6px",
                    "padding"        : "10px 0",
                    "width"          : "100%",
                    "fontFamily"     : "'Space Mono', monospace",
                    "fontSize"       : "0.8rem",
                    "cursor"         : "pointer",
                    "transition"     : "opacity 0.2s",
                }
            ),
        ],
        style={
            **ESTILO_CARD,
            "position"  : "sticky",
            "top"       : "16px",
        }
    )


# ============================================================
# CARDS DE INFORMACIÓN DEL ACTIVO
# ============================================================

def crear_cards_activo(info: dict) -> html.Div:
    """
    Crea las cards con información del activo seleccionado.
    Se muestra precio, variación diaria, volumen y sector.

    Parámetros:
        info: diccionario retornado por obtener_info_activo()
    """
    # Color de la variación según positivo o negativo
    color_variacion = (
        COLORES["acento_verde"] if info["variacion"] >= 0
        else COLORES["acento_rojo"]
    )
    simbolo_variacion = "▲" if info["variacion"] >= 0 else "▼"

    def crear_card_metrica(titulo, valor, color=None):
        """Card individual de métrica."""
        return html.Div(
            children=[
                html.P(
                    titulo,
                    style={
                        "color"        : COLORES["texto_secundario"],
                        "fontSize"     : "0.7rem",
                        "fontFamily"   : "'Space Mono', monospace",
                        "letterSpacing": "1px",
                        "margin"       : "0 0 4px 0",
                    }
                ),
                html.P(
                    valor,
                    style={
                        "color"     : color or COLORES["texto_principal"],
                        "fontSize"  : "1.3rem",
                        "fontFamily": "'Space Mono', monospace",
                        "fontWeight": "700",
                        "margin"    : "0",
                    }
                ),
            ],
            style={**ESTILO_CARD, "flex": "1", "minWidth": "140px", "marginRight": "12px"}
        )

    return html.Div(
        children=[
            # Nombre del activo
            html.Div(
                children=[
                    html.H4(
                        info["nombre"],
                        style={
                            "color"     : COLORES["texto_principal"],
                            "fontFamily": "'DM Sans', sans-serif",
                            "fontWeight": "600",
                            "margin"    : "0 0 4px 0",
                        }
                    ),
                    html.Span(
                        f"{info['simbolo']} · {info['moneda']} · {info['sector']}",
                        style={
                            "color"    : COLORES["texto_secundario"],
                            "fontSize" : "0.8rem",
                            "fontFamily": "'DM Sans', sans-serif",
                        }
                    ),
                ],
                style={**ESTILO_CARD, "marginBottom": "12px"}
            ),

            # Cards de métricas
            html.Div(
                children=[
                    crear_card_metrica(
                        "PRECIO ACTUAL",
                        f"{info['moneda']} {info['precio']:,.4f}",
                        COLORES["acento_azul"]
                    ),
                    crear_card_metrica(
                        "VARIACIÓN DÍA",
                        f"{simbolo_variacion} {abs(info['variacion']):.2f}%",
                        color_variacion
                    ),
                    crear_card_metrica(
                        "VOLUMEN",
                        f"{info['volumen']:,}" if info["volumen"] else "N/A"
                    ),
                ],
                style={
                    "display"  : "flex",
                    "flexWrap" : "wrap",
                    "gap"      : "0",
                }
            ),
        ]
    )


# ============================================================
# SECCIÓN DE LOADING
# ============================================================

def crear_loading_spinner() -> html.Div:
    """
    Crea un indicador de carga que se muestra mientras
    se ejecuta el pipeline de forecasting.
    """
    return dcc.Loading(
        id="loading-forecast",
        type="circle",
        color=COLORES["acento_verde"],
        children=html.Div(id="contenido-forecast")
    )


# ============================================================
# PLACEHOLDER — antes de correr el forecast
# ============================================================

def crear_placeholder() -> html.Div:
    """
    Mensaje que se muestra en el área de resultados
    antes de que el usuario ejecute el primer forecast.
    """
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.P(
                        "▶",
                        style={
                            "fontSize"  : "3rem",
                            "color"     : COLORES["acento_verde"],
                            "margin"    : "0 0 16px 0",
                            "fontFamily": "'Space Mono', monospace",
                        }
                    ),
                    html.P(
                        "Selecciona un activo y presiona RUN FORECAST",
                        style={
                            "color"     : COLORES["texto_secundario"],
                            "fontFamily": "'DM Sans', sans-serif",
                            "fontSize"  : "1rem",
                            "margin"    : "0",
                        }
                    ),
                ],
                style={
                    "textAlign": "center",
                    "padding"  : "80px 40px",
                }
            )
        ],
        style=ESTILO_CARD
    )