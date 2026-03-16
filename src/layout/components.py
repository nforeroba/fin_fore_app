# ============================================================
# components.py — Componentes UI reutilizables
# Define el layout visual de la aplicación: franja de título,
# topbar de control, franja de info del activo y utilidades.
# ============================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import date, timedelta


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

ESTILO_CARD = {
    "backgroundColor": COLORES["fondo_card"],
    "border"         : f"1px solid {COLORES['borde']}",
    "borderRadius"   : "8px",
    "padding"        : "20px",
    "marginBottom"   : "16px",
}

# ============================================================
# CONSTANTES DE LAYOUT
# ============================================================

MAX_WIDTH = "1400px"
PADDING_H = "24px"
GAP_V     = "16px"

# Margen exterior unificado — topbar e info del activo usan el mismo
MARGEN_SECCION = f"{GAP_V} {PADDING_H}"

# Defaults por categoría de activo
DEFAULTS_CATEGORIA = {
    "sp500" : "AAPL",
    "crypto": "BTC-USD",
    "fx"    : "USDCOP=X",
}


# ============================================================
# FRANJA DE TÍTULO — FULL WIDTH
# ============================================================

def crear_header() -> html.Div:
    """
    Franja superior full width con título y subtítulo.
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
                    "maxWidth"      : MAX_WIDTH,
                    "margin"        : "0 auto",
                    "padding"       : f"0 {PADDING_H}",
                    "display"       : "flex",
                    "alignItems"    : "center",
                    "justifyContent": "center",
                }
            )
        ],
        style={
            "padding": "14px 0",
            "width"  : "100%",
        }
    )


# ============================================================
# STEPPER CUSTOM — botón − | input | botón +
# ============================================================

def _crear_stepper(id_input: str, id_btn_menos: str, id_btn_mas: str,
                   valor: int, minimo: int, maximo: int) -> html.Div:
    """
    Stepper custom: botón − | número | botón +
    Reemplaza dcc.Input type=number para tener controles visibles
    independientes del browser.

    Parámetros:
        id_input    : id del dcc.Input central
        id_btn_menos: id del botón de decremento
        id_btn_mas  : id del botón de incremento
        valor       : valor inicial
        minimo      : valor mínimo permitido
        maximo      : valor máximo permitido
    """
    estilo_btn_stepper = {
        "width"          : "28px",
        "height"         : "36px",
        "backgroundColor": COLORES["fondo_input"],
        "border"         : f"1px solid {COLORES['borde']}",
        "color"          : COLORES["texto_secundario"],
        "fontFamily"     : "'Space Mono', monospace",
        "fontSize"       : "1.1rem",
        "cursor"         : "pointer",
        "display"        : "flex",
        "alignItems"     : "center",
        "justifyContent" : "center",
        "padding"        : "0",
        "lineHeight"     : "1",
        "flexShrink"     : "0",
    }

    return html.Div([
        html.Button(
            "−",
            id=id_btn_menos,
            n_clicks=0,
            className="btn-stepper",
            style={
                **estilo_btn_stepper,
                "borderRadius": "6px 0 0 6px",
                "borderRight" : "none",
            },
        ),
        dcc.Input(
            id=id_input,
            type="number",
            value=valor,
            min=minimo,
            max=maximo,
            step=1,
            className="input-stepper",
            style={
                "width"          : "52px",
                "height"         : "36px",
                "backgroundColor": COLORES["fondo_input"],
                "border"         : f"1px solid {COLORES['borde']}",
                "borderLeft"     : "none",
                "borderRight"    : "none",
                "color"          : COLORES["texto_principal"],
                "fontFamily"     : "'Space Mono', monospace",
                "fontSize"       : "0.9rem",
                "textAlign"      : "center",
                "outline"        : "none",
            },
        ),
        html.Button(
            "+",
            id=id_btn_mas,
            n_clicks=0,
            className="btn-stepper",
            style={
                **estilo_btn_stepper,
                "borderRadius": "0 6px 6px 0",
                "borderLeft"  : "none",
            },
        ),
    ], style={
        "display"   : "flex",
        "alignItems": "center",
    })


# ============================================================
# TOPBAR DE CONTROL — CARD
# ============================================================

def crear_topbar(
    simbolos_sp500  : list,
    simbolos_crypto : list,
    simbolos_divisas: list,
) -> html.Div:
    """
    Barra de control con tabs de categoría (S&P 500 / Crypto / FX),
    dropdown filtrado por categoría, date pickers, steppers de
    test split y horizonte, y botones de acción.

    Los stores guardan las listas de símbolos para que los callbacks
    no dependan de variables globales de app.py.

    Parámetros:
        simbolos_sp500  : lista de símbolos S&P500
        simbolos_crypto : lista de símbolos crypto
        simbolos_divisas: lista de símbolos de divisas
    """

    estilo_label = {
        "color"        : COLORES["texto_secundario"],
        "fontFamily"   : "'Space Mono', monospace",
        "fontSize"     : "0.6rem",
        "letterSpacing": "1.5px",
        "marginBottom" : "4px",
        "textTransform": "uppercase",
    }

    def separador_v():
        return html.Div(style={
            "width"          : "1px",
            "backgroundColor": COLORES["borde"],
            "alignSelf"      : "stretch",
            "margin"         : "0 4px",
        })

    # Tabs de categoría — botones tipo toggle
    tabs_categoria = html.Div([
        html.Button("S&P 500", id="tab-sp500",  n_clicks=0, className="tab-categoria tab-activo"),
        html.Button("Crypto",  id="tab-crypto", n_clicks=0, className="tab-categoria"),
        html.Button("FX",      id="tab-fx",     n_clicks=0, className="tab-categoria"),
        # Store para la categoría activa
        dcc.Store(id="store-categoria", data="sp500"),
        # Stores con listas de símbolos — evita recalcular en callbacks
        dcc.Store(id="store-simbolos-sp500",  data=simbolos_sp500),
        dcc.Store(id="store-simbolos-crypto", data=simbolos_crypto),
        dcc.Store(id="store-simbolos-fx",     data=simbolos_divisas),
    ], style={
        "display"     : "flex",
        "gap"         : "4px",
        "marginBottom": "14px",
    })

    # Dropdown — opciones iniciales = S&P 500 (categoría por defecto)
    opciones_iniciales = [{"label": s, "value": s} for s in simbolos_sp500]

    return html.Div(
        children=[
            html.Div(
                children=[

                    # Fila de tabs
                    html.Div(tabs_categoria, style={"width": "100%"}),

                    # Fila de controles
                    html.Div(
                        children=[

                            # --- Símbolo ---
                            html.Div([
                                html.Div("Symbol", style=estilo_label),
                                dcc.Dropdown(
                                    id="input-simbolo",
                                    options=opciones_iniciales,
                                    value=DEFAULTS_CATEGORIA["sp500"],
                                    clearable=False,
                                    searchable=True,
                                    className="dropdown-dark",
                                    style={"minWidth": "180px"},
                                ),
                            ], style={"flex": "2", "minWidth": "180px"}),

                            separador_v(),

                            # --- Fecha Inicio ---
                            html.Div([
                                html.Div("Start Date", style=estilo_label),
                                dcc.DatePickerSingle(
                                    id="input-fecha-inicio",
                                    date=date(2022, 1, 1),
                                    display_format="YYYY-MM-DD",
                                    className="date-picker-dark",
                                    style={"width": "100%"},
                                ),
                            ], style={"flex": "1.5", "minWidth": "140px"}),

                            # --- Fecha Fin ---
                            html.Div([
                                html.Div("End Date", style=estilo_label),
                                dcc.DatePickerSingle(
                                    id="input-fecha-fin",
                                    date=date.today() - timedelta(days=1),
                                    display_format="YYYY-MM-DD",
                                    className="date-picker-dark",
                                    style={"width": "100%"},
                                ),
                            ], style={"flex": "1.5", "minWidth": "140px"}),

                            separador_v(),

                            # --- Test Split (stepper) ---
                            html.Div([
                                html.Div("Test Split (months)", style=estilo_label),
                                _crear_stepper(
                                    id_input    ="input-meses-test",
                                    id_btn_menos="btn-test-menos",
                                    id_btn_mas  ="btn-test-mas",
                                    valor=6, minimo=1, maximo=24,
                                ),
                            ], style={"flex": "0 0 auto"}),

                            # --- Horizonte (stepper) ---
                            html.Div([
                                html.Div("Horizon (months)", style=estilo_label),
                                _crear_stepper(
                                    id_input    ="input-meses-horizonte",
                                    id_btn_menos="btn-horizonte-menos",
                                    id_btn_mas  ="btn-horizonte-mas",
                                    valor=6, minimo=1, maximo=24,
                                ),
                            ], style={"flex": "0 0 auto"}),

                            separador_v(),

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
                        className="topbar-controles",
                        style={
                            "display"   : "flex",
                            "alignItems": "flex-end",
                            "gap"       : "16px",
                            "flexWrap"  : "wrap",
                            "width"     : "100%",
                        }
                    ),
                ],
                style={
                    "width": "fit-content",
                }
            )
        ],
        style={
            **ESTILO_CARD,
            "borderRadius": "8px",
            "margin"      : f"{GAP_V} auto",
            "width"       : "fit-content",
        }
    )


# ============================================================
# FRANJA DE INFO DEL ACTIVO
# ============================================================

def crear_info_activo(info: dict) -> html.Div:
    """
    Franja horizontal con la información completa del activo.

    Parámetros:
        info: diccionario retornado por obtener_info_activo() con:
              simbolo, nombre, precio, variacion, volumen, moneda,
              sector, industria, market_cap, pe_ratio, beta,
              semana_52_max, semana_52_min, dividendo
    """
    if not info:
        return html.Div()

    # --- Formateo de campos ---

    precio_fmt = f"{info.get('precio', 0):,.2f} {info.get('moneda', '')}"

    variacion       = info.get("variacion", 0) or 0
    variacion_fmt   = f"{'▲' if variacion >= 0 else '▼'} {abs(variacion):.2f}%"
    color_variacion = COLORES["acento_verde"] if variacion >= 0 else COLORES["acento_rojo"]

    volumen = info.get("volumen", 0) or 0
    if volumen >= 1_000_000_000:
        volumen_fmt = f"{volumen / 1_000_000_000:.1f}B"
    elif volumen >= 1_000_000:
        volumen_fmt = f"{volumen / 1_000_000:.1f}M"
    elif volumen >= 1_000:
        volumen_fmt = f"{volumen / 1_000:.1f}K"
    else:
        volumen_fmt = f"{volumen:,.0f}" if volumen else "—"

    market_cap = info.get("market_cap", 0) or 0
    if market_cap >= 1_000_000_000_000:
        market_cap_fmt = f"{market_cap / 1_000_000_000_000:.2f}T"
    elif market_cap >= 1_000_000_000:
        market_cap_fmt = f"{market_cap / 1_000_000_000:.1f}B"
    elif market_cap >= 1_000_000:
        market_cap_fmt = f"{market_cap / 1_000_000:.1f}M"
    else:
        market_cap_fmt = "—"

    pe_ratio  = info.get("pe_ratio")
    pe_fmt    = f"{pe_ratio:.1f}x" if pe_ratio else "—"

    beta      = info.get("beta")
    beta_fmt  = f"{beta:.2f}" if beta else "—"

    s52_max   = info.get("semana_52_max")
    s52_min   = info.get("semana_52_min")
    rango_fmt = (
        f"{s52_min:,.2f} – {s52_max:,.2f}"
        if s52_max and s52_min else "—"
    )

    dividendo     = info.get("dividendo")
    dividendo_fmt = f"{dividendo:.2f}%" if dividendo else "—"

    # --- Helpers de renderizado ---

    def item(label, valor, color=None):
        return html.Div([
            html.Span(
                label,
                style={
                    "color"        : COLORES["texto_secundario"],
                    "fontSize"     : "0.6rem",
                    "fontFamily"   : "'Space Mono', monospace",
                    "letterSpacing": "1px",
                    "textTransform": "uppercase",
                }
            ),
            html.Span(
                valor,
                style={
                    "color"     : color or COLORES["texto_principal"],
                    "fontSize"  : "0.85rem",
                    "fontFamily": "'Space Mono', monospace",
                    "fontWeight": "700",
                }
            ),
        ], style={"display": "flex", "flexDirection": "column", "gap": "2px"})

    def sep():
        return html.Div(style={
            "width"          : "1px",
            "height"         : "32px",
            "backgroundColor": COLORES["borde"],
            "alignSelf"      : "center",
            "flexShrink"     : "0",
        })

    def opcional(label, valor_fmt, condicion=True, color=None):
        """Retorna [sep, item] si la condicion se cumple, si no []."""
        if not condicion:
            return []
        return [sep(), item(label, valor_fmt, color)]

    industria = info.get("industria", "") or ""
    sector    = info.get("sector", "")    or ""
    etiqueta_sector = industria if industria and industria != "N/A" else sector

    return html.Div(
        children=[
            html.Div(
                children=[

                    # Symbol · Name
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
                    ], style={"display": "flex", "alignItems": "center", "flex": "0 0 auto", "maxWidth": "280px"}),

                    sep(),
                    item("Price",    precio_fmt),
                    sep(),
                    item("Day Chg",  variacion_fmt, color_variacion),

                    *opcional("Volume",   volumen_fmt,
                               not info.get("simbolo", "").endswith("=X") and volumen > 0),

                    *opcional("Mkt Cap",    market_cap_fmt, market_cap > 0),
                    *opcional("P/E",        pe_fmt,         pe_ratio is not None),
                    *opcional("Beta",       beta_fmt,       beta is not None),
                    *opcional("52w Range",  rango_fmt,      s52_max and s52_min),
                    *opcional("Div. Yield", dividendo_fmt,  dividendo is not None),
                    *opcional("Sector",     etiqueta_sector,
                               bool(etiqueta_sector and etiqueta_sector != "N/A")),

                ],
                style={
                    "display"   : "flex",
                    "alignItems": "center",
                    "gap"       : "12px",
                    "flexWrap"  : "wrap",
                }
            )
        ],
        style={
            **ESTILO_CARD,
            "margin"  : MARGEN_SECCION,
            "width"   : "fit-content",
            "maxWidth": f"calc({MAX_WIDTH} - {PADDING_H} * 2)",
            "marginLeft" : "auto",
            "marginRight": "auto",
        }
    )
