# ============================================================
# app.py — Entry point principal de la aplicación Dash
# Inicializa la app, define el layout principal y registra
# los callbacks. Este es el archivo que ejecuta el servidor.
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
    crear_panel_control,
    crear_placeholder,
    COLORES
)
from src.callbacks.forecast import registrar_callbacks


# ============================================================
# INICIALIZACIÓN DE LA APP
# ============================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        # Bootstrap para layout responsivo
        dbc.themes.CYBORG,
        # Fuentes Google — Space Mono y DM Sans
        "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap"
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        # Responsividad en móvil
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Título en la pestaña del navegador
app.title = "FinForecast — Financial Asset Forecasting"

# ============================================================
# CARGA DE SÍMBOLOS AL INICIAR
# ============================================================

# Se cargan una sola vez al arrancar el servidor
print("Cargando símbolos S&P500...")
simbolos_sp500 = obtener_simbolos_sp500()

print("Cargando símbolos crypto...")
simbolos_crypto = obtener_simbolos_crypto()

# Divisas — lista estática, no requiere llamada externa
simbolos_divisas = obtener_simbolos_divisas()

print(f"Símbolos cargados: {len(simbolos_sp500)} SP500 · "
      f"{len(simbolos_crypto)} crypto · {len(simbolos_divisas)} divisas")


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

app.layout = html.Div(
    children=[

        # Header
        crear_header(),

        # Layout principal — sidebar + contenido
        html.Div(
            children=[

                # Panel lateral de control
                html.Div(
                    crear_panel_control(
                        simbolos_sp500=simbolos_sp500,
                        simbolos_crypto=simbolos_crypto,
                        simbolos_divisas=simbolos_divisas
                    ),
                    className="panel-lateral",
                    style={
                        "width"    : "280px",
                        "minWidth" : "280px",
                        "padding"  : "16px",
                    }
                ),

                # Área de contenido principal
                html.Div(
                    children=[

                        # Sección info del activo
                        html.Div(
                            id="seccion-info-activo",
                            style={"marginBottom": "0"}
                        ),

                        # Área de resultados con loading
                        dcc.Loading(
                            id="loading-forecast",
                            type="circle",
                            color=COLORES["acento_verde"],
                            children=html.Div(
                                id="contenido-forecast",
                                children=crear_placeholder()
                            )
                        ),
                    ],
                    style={
                        "flex"    : "1",
                        "padding" : "16px",
                        "minWidth": "0",  # Evita overflow en flex
                    }
                ),
            ],
            style={
                "display"  : "flex",
                "minHeight": "calc(100vh - 70px)",
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