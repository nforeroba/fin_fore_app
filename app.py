# ============================================================
# app.py — Entry point principal de la aplicación Dash
# Layout: franja título (full width) → topbar card → contenido
# ============================================================

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from src.data.loader import (
    obtener_simbolos_sp500,
    obtener_simbolos_crypto,
    obtener_simbolos_divisas
)
from src.layout.components import (
    crear_header,
    crear_topbar,
    COLORES
)
from src.callbacks.forecast import registrar_callbacks


# ============================================================
# INICIALIZACIÓN DE LA APP
# ============================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

app.title = "FinForecast — Financial Asset Forecasting"


# ============================================================
# CARGA DE SÍMBOLOS AL INICIAR
# ============================================================

print("Cargando símbolos S&P500...")
simbolos_sp500 = obtener_simbolos_sp500()

print("Cargando símbolos crypto...")
simbolos_crypto = obtener_simbolos_crypto()

simbolos_divisas = obtener_simbolos_divisas()

print(f"Símbolos cargados: {len(simbolos_sp500)} SP500 · "
      f"{len(simbolos_crypto)} crypto · {len(simbolos_divisas)} divisas")


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

app.layout = html.Div(
    children=[

        # 1. Franja de título — full width
        crear_header(),

        # 2. Topbar de control — card con padding lateral
        crear_topbar(
            simbolos_sp500=simbolos_sp500,
            simbolos_crypto=simbolos_crypto,
            simbolos_divisas=simbolos_divisas
        ),

        # 3. Área de contenido principal
        html.Div(
            children=[

                # Franja info del activo — aparece al seleccionar símbolo
                html.Div(id="seccion-info-activo"),

                # Resultados del forecast con spinner de carga
                dcc.Loading(
                    id="loading-forecast",
                    type="circle",
                    color=COLORES["acento_verde"],
                    children=html.Div(id="contenido-forecast")
                ),
            ],
            style={
                "padding" : "0 24px 24px 24px",
                "maxWidth": "1400px",
                "margin"  : "0 auto",
                "width"   : "100%",
            }
        ),
    ],
    style={
        "backgroundColor": COLORES["fondo"],
        "minHeight"      : "100vh",
        "fontFamily"     : "'DM Sans', sans-serif",
    }
)


# ============================================================
# REGISTRO DE CALLBACKS
# ============================================================

registrar_callbacks(app)


# ============================================================
# SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=7860,
        debug=False
    )
