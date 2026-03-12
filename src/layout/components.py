# ============================================================
# components.py — Componentes UI reutilizables
# Define el layout visual de la aplicación: franja de título,
# topbar de control, franja de info del activo y utilidades.
# ============================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import date


# ============================================================
# PALETA DE COLORES — TEMA OSCURO "TERMINAL FINANCIERO"
# ============================================================

COLORES = {
    "fondo"            : "#0D1117",
    "fondo_card"       : "#161B22",
    "fondo_input"      : "#1C2128",
    "borde"            : "#30363D",
    "texto_principal"  : "#E6EDF3",
    "texto_secundario" : "#7D8590",
    "acento_verde"     : "#00C896",
    "acento_rojo"      : "#FF6B6B",
    "acento_azul"      : "#58A6FF",
}

# Estilo base reutilizable para cards/secciones
ESTILO_CARD = {
    "backgroundColor": COLORES["fondo_card"],
    "border"         : f"1px solid {COLORES['borde']}",
    "borderRadius"   : "8px",
    "padding"        : "20px",
    "marginBottom"   : "16px",
}


# ============================================================
# FRANJA DE TÍTULO — FULL WIDTH
# ============================================================

def crear_header() -> html.Div:
    """
    Franja superior full width con título y subtítulo.
    Fondo ligeramente distinto al fondo principal para dar jerarquía.
    """
    return html.Div(
        children=[
            html.Div(
                children=[
                    html.Span(
                        "Fin",
                        style={
                            "color"     : COLORES["acento_verde"],
                            "fontFamily": "'Space Mono', monospace",
                            "fontWeight": "700",
                            "fontSize"  : "1.4rem",
                        }
                    ),
                    html.Span(
                        "Forecast",
                        style={
                            "color"     : COLORES["texto_principal"],
                            "fontFamily": "'Space Mono', monospace",
                            "fontWeight": "700",
                            "fontSize"  : "1.4rem",
                        }
                    ),
                    html.Span(
                        " — Financial Asset Forecasting",
                        style={
                            "color"     : COLORES["texto_secundario"],
                            "fontFamily": "'DM Sans', sans-serif",
                            "fontWeight": "400",
                            "fontSize"  : "0.9rem",
                            "marginLeft": "12px",
                        }
                    ),
                ],
                style={
                    "maxWidth" : "1400px",
                    "margin"   : "0 auto",
                    "padding"  : "0 24px",
                    "display"  : "flex",
                    "alignItems": "center",
                    "gap"      : "0",
                }
            )
        ],
        style={
            "backgroundColor": COLORES["fondo_card"],
            "borderBottom"   : f"1px solid {COLORES['borde']}",
            "padding"        : "14px 0",
            "width"          : "100%",
        }
    )


# ============================================================
# TOPBAR DE CONTROL — CARD
# ============================================================

def crear_topbar(
    simbolos_sp500: list,
    simbolos_crypto: list,
    simbolos_divisas: list
) -> html.Div:
    """
    Barra de control horizontal con todos los inputs del forecast:
    símbolo, fechas, test split, horizonte y botones RUN/RESET.
    Se renderiza como una card con fondo oscuro.

    Parámetros:
        simbolos_sp500  : lista de símbolos S&P500
        simbolos_crypto : lista de símbolos crypto
        simbolos_divisas: lista de símbolos de divisas
    """
    # Construir opciones del dropdown agrupadas por categoría
    opciones = (
        [{"label": f"📈 {s}", "value": s} for s in simbolos_sp500] +
        [{"label": f"₿ {s}",  "value": s} for s in simbolos_crypto] +
        [{"label": f"💱 {s}", "value": s} for s in simbolos_divisas]
    )

    # Estilo compartido para labels de los inputs
    estilo_label = {
        "color"        : COLORES["texto_secundario"],
        "fontFamily"   : "'Space Mono', monospace",
        "fontSize"     : "0.6rem",
        "letterSpacing": "1.5px",
        "marginBottom" : "4px",
        "textTransform": "uppercase",
    }

    return html.Div(
        children=[
            html.Div(
                children=[

                    # --- Símbolo ---
                    html.Div([
                        html.Div("Símbolo", style=estilo_label),
                        dcc.Dropdown(
                            id="input-simbolo",
                            options=opciones,
                            value="AAPL",
                            clearable=False,
                            searchable=True,
                            className="dropdown-dark",
                            style={"minWidth": "160px"},
                        ),
                    ], style={"flex": "2", "minWidth": "160px"}),

                    # Separador visual
                    html.Div(style={
                        "width"          : "1px",
                        "backgroundColor": COLORES["borde"],
                        "alignSelf"      : "stretch",
                        "margin"         : "0 4px",
                    }),

                    # --- Fecha Inicio ---
                    html.Div([
                        html.Div("Fecha Inicio", style=estilo_label),
                        dcc.DatePickerSingle(
                            id="input-fecha-inicio",
                            date=date(2019, 1, 1),
                            display_format="YYYY-MM-DD",
                            className="date-picker-dark",
                            style={"width": "100%"},
                        ),
                    ], style={"flex": "1.5", "minWidth": "140px"}),

                    # --- Fecha Fin ---
                    html.Div([
                        html.Div("Fecha Fin", style=estilo_label),
                        dcc.DatePickerSingle(
                            id="input-fecha-fin",
                            date=date.today(),
                            display_format="YYYY-MM-DD",
                            className="date-picker-dark",
                            style={"width": "100%"},
                        ),
                    ], style={"flex": "1.5", "minWidth": "140px"}),

                    # Separador visual
                    html.Div(style={
                        "width"          : "1px",
                        "backgroundColor": COLORES["borde"],
                        "alignSelf"      : "stretch",
                        "margin"         : "0 4px",
                    }),

                    # --- Test Split ---
                    html.Div([
                        html.Div("Test Split (meses)", style=estilo_label),
                        dcc.Input(
                            id="input-meses-test",
                            type="number",
                            value=4,
                            min=1,
                            max=24,
                            step=1,
                            className="input-number-dark",
                            style={"width": "80px"},
                        ),
                    ], style={"flex": "0 0 auto"}),

                    # --- Horizonte ---
                    html.Div([
                        html.Div("Horizonte (meses)", style=estilo_label),
                        dcc.Input(
                            id="input-meses-horizonte",
                            type="number",
                            value=6,
                            min=1,
                            max=24,
                            step=1,
                            className="input-number-dark",
                            style={"width": "80px"},
                        ),
                    ], style={"flex": "0 0 auto"}),

                    # Separador visual
                    html.Div(style={
                        "width"          : "1px",
                        "backgroundColor": COLORES["borde"],
                        "alignSelf"      : "stretch",
                        "margin"         : "0 4px",
                    }),

                    # --- Botones ---
                    html.Div([
                        html.Button(
                            "▶ RUN FORECAST",
                            id="btn-run",
                            n_clicks=0,
                            className="btn-run",
                        ),
                        html.Button(
                            "↺ RESET",
                            id="btn-reset",
                            n_clicks=0,
                            className="btn-reset",
                        ),
                    ], style={
                        "display"      : "flex",
                        "flexDirection": "column",
                        "gap"          : "6px",
                        "flex"         : "0 0 auto",
                    }),

                ],
                style={
                    "display"      : "flex",
                    "alignItems"   : "flex-end",
                    "gap"          : "16px",
                    "flexWrap"     : "wrap",
                    "maxWidth"     : "1400px",
                    "margin"       : "0 auto",
                    "width"        : "100%",
                }
            )
        ],
        style={
            **ESTILO_CARD,
            "borderRadius": "8px",
            "margin"      : "16px 24px",
        }
    )


# ============================================================
# FRANJA DE INFO DEL ACTIVO
# ============================================================

def crear_info_activo(info: dict) -> html.Div:
    """
    Franja horizontal con la información del activo seleccionado.
    Sin cards individuales — todos los datos en una sola línea.

    Parámetros:
        info: diccionario con nombre, precio, variacion, volumen,
              moneda, sector, simbolo

    Retorna:
        Div con la franja de información
    """
    if not info:
        return html.Div()

    # Formatear precio con 2 decimales
    precio_fmt = f"{info.get('precio', 0):,.2f} {info.get('moneda', '')}"

    # Formatear variación con color y signo
    variacion = info.get("variacion", 0)
    variacion_fmt  = f"{'▲' if variacion >= 0 else '▼'} {abs(variacion):.2f}%"
    color_variacion = COLORES["acento_verde"] if variacion >= 0 else COLORES["acento_rojo"]

    # Formatear volumen abreviado
    volumen = info.get("volumen", 0)
    if volumen >= 1_000_000_000:
        volumen_fmt = f"{volumen / 1_000_000_000:.1f}B"
    elif volumen >= 1_000_000:
        volumen_fmt = f"{volumen / 1_000_000:.1f}M"
    elif volumen >= 1_000:
        volumen_fmt = f"{volumen / 1_000:.1f}K"
    else:
        volumen_fmt = f"{volumen:,.0f}" if volumen else "—"

    # Estilo de cada dato en la franja
    def item(label, valor, color=None):
        return html.Div([
            html.Span(
                label + " ",
                style={
                    "color"        : COLORES["texto_secundario"],
                    "fontSize"     : "0.65rem",
                    "fontFamily"   : "'Space Mono', monospace",
                    "letterSpacing": "1px",
                    "textTransform": "uppercase",
                }
            ),
            html.Span(
                valor,
                style={
                    "color"     : color or COLORES["texto_principal"],
                    "fontSize"  : "0.9rem",
                    "fontFamily": "'Space Mono', monospace",
                    "fontWeight": "700",
                }
            ),
        ], style={"display": "flex", "flexDirection": "column", "gap": "2px"})

    def separador():
        return html.Div(style={
            "width"          : "1px",
            "height"         : "32px",
            "backgroundColor": COLORES["borde"],
            "alignSelf"      : "center",
        })

    return html.Div(
        children=[
            html.Div(
                children=[
                    # Nombre y símbolo
                    html.Div([
                        html.Span(
                            info.get("simbolo", ""),
                            style={
                                "color"     : COLORES["acento_verde"],
                                "fontFamily": "'Space Mono', monospace",
                                "fontWeight": "700",
                                "fontSize"  : "1rem",
                            }
                        ),
                        html.Span(
                            f" · {info.get('nombre', '')}",
                            style={
                                "color"     : COLORES["texto_secundario"],
                                "fontFamily": "'DM Sans', sans-serif",
                                "fontSize"  : "0.85rem",
                            }
                        ),
                    ], style={"display": "flex", "alignItems": "center", "flex": "1"}),

                    separador(),
                    item("Precio", precio_fmt),
                    separador(),
                    item("Var. día", variacion_fmt, color_variacion),
                    separador(),
                    item("Volumen", volumen_fmt),

                    # Sector (si está disponible y no es N/A)
                    *([
                        separador(),
                        item("Sector", info.get("sector", "")),
                    ] if info.get("sector") and info.get("sector") != "N/A" else []),
                ],
                style={
                    "display"    : "flex",
                    "alignItems" : "center",
                    "gap"        : "20px",
                    "maxWidth"   : "1400px",
                    "margin"     : "0 auto",
                    "width"      : "100%",
                    "flexWrap"   : "wrap",
                }
            )
        ],
        style={
            **ESTILO_CARD,
            "margin": "0 24px 16px 24px",
        }
    )
