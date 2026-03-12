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
                    "gap"           : "0",
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
    simbolos_sp500  : list,
    simbolos_crypto : list,
    simbolos_divisas: list,
) -> html.Div:
    """
    Barra de control horizontal con todos los inputs del forecast.
    Dropdown de símbolo con grupos: S&P 500 / Crypto / FX.

    Parámetros:
        simbolos_sp500  : lista de símbolos S&P500
        simbolos_crypto : lista de símbolos crypto
        simbolos_divisas: lista de símbolos de divisas
    """
    opciones = [
        {
            "label": html.Span("S&P 500", style={
                "color": "#7D8590", "fontFamily": "'Space Mono', monospace",
                "fontSize": "0.65rem", "letterSpacing": "1px",
            }),
            "value": "group_sp500", "disabled": True,
        },
        *[{"label": s, "value": s} for s in simbolos_sp500],
        {
            "label": html.Span("─────────────", style={"color": "#30363D", "fontSize": "0.5rem"}),
            "value": "sep1", "disabled": True,
        },
        {
            "label": html.Span("CRYPTO", style={
                "color": "#7D8590", "fontFamily": "'Space Mono', monospace",
                "fontSize": "0.65rem", "letterSpacing": "1px",
            }),
            "value": "group_crypto", "disabled": True,
        },
        *[{"label": s, "value": s} for s in simbolos_crypto],
        {
            "label": html.Span("─────────────", style={"color": "#30363D", "fontSize": "0.5rem"}),
            "value": "sep2", "disabled": True,
        },
        {
            "label": html.Span("FX / DIVISAS", style={
                "color": "#7D8590", "fontFamily": "'Space Mono', monospace",
                "fontSize": "0.65rem", "letterSpacing": "1px",
            }),
            "value": "group_fx", "disabled": True,
        },
        *[{"label": s, "value": s} for s in simbolos_divisas],
    ]

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
                            className="dropdown-dark dropdown-grouped",
                            style={"minWidth": "180px"},
                        ),
                    ], style={"flex": "2", "minWidth": "180px"}),

                    separador_v(),

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

                    separador_v(),

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
                style={
                    "display"   : "flex",
                    "alignItems": "flex-end",
                    "gap"       : "16px",
                    "flexWrap"  : "wrap",
                    "maxWidth"  : MAX_WIDTH,
                    "margin"    : "0 auto",
                    "width"     : "100%",
                }
            )
        ],
        style={
            **ESTILO_CARD,
            "borderRadius": "8px",
            "margin"      : f"{GAP_V} {PADDING_H}",
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
    # Mostrar industria si existe, sector como fallback
    etiqueta_sector = industria if industria and industria != "N/A" else sector

    return html.Div(
        children=[
            html.Div(
                children=[

                    # Símbolo · Nombre
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
                    ], style={"display": "flex", "alignItems": "center", "flex": "1", "minWidth": "160px"}),

                    sep(),
                    item("Precio",    precio_fmt),
                    sep(),
                    item("Var. día",  variacion_fmt, color_variacion),
                    sep(),
                    item("Volumen",   volumen_fmt),

                    # Campos opcionales — solo se muestran si tienen valor
                    *opcional("Mkt Cap",   market_cap_fmt, market_cap > 0),
                    *opcional("P/E",       pe_fmt,         pe_ratio is not None),
                    *opcional("Beta",      beta_fmt,       beta is not None),
                    *opcional("52w",       rango_fmt,      s52_max and s52_min),
                    *opcional("Div. yield",dividendo_fmt,  dividendo is not None),
                    *opcional("Sector",    etiqueta_sector,
                               bool(etiqueta_sector and etiqueta_sector != "N/A")),

                ],
                style={
                    "display"   : "flex",
                    "alignItems": "center",
                    "gap"       : "20px",
                    "maxWidth"  : MAX_WIDTH,
                    "margin"    : "0 auto",
                    "width"     : "100%",
                    "flexWrap"  : "wrap",
                }
            )
        ],
        style={
            **ESTILO_CARD,
            "margin": f"0 {PADDING_H} {GAP_V} {PADDING_H}",
        }
    )
