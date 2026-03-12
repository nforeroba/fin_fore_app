# ============================================================
# Dockerfile — FinForecast
# Hugging Face Spaces — Python 3.11
# Puerto: 7860 (requerido por HF Spaces)
# ============================================================

# Imagen base oficial de Python
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Dependencias del sistema requeridas por Prophet y statsforecast:
#   build-essential / gcc : compilar extensiones C de Prophet y NumPy
#   cmake                 : requerido por algunas versiones de Prophet
#   libpython3-dev        : headers de Python para compilación
#   libgomp1              : OpenMP — paralelismo de statsforecast (n_jobs=-1)
# Se limpia el cache de apt en el mismo RUN para reducir tamaño de imagen
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    cmake \
    libpython3-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar primero requirements para aprovechar cache de Docker —
# si no cambian las dependencias, esta capa no se reconstruye
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Variables de entorno
ENV HOST=0.0.0.0
ENV PORT=7860
# PYTHONUNBUFFERED=1 hace que los logs aparezcan en tiempo real en HF Spaces
ENV PYTHONUNBUFFERED=1

# Puerto requerido por HF Spaces
EXPOSE 7860

# Gunicorn como servidor WSGI de producción.
# app:server referencia el objeto `server` del app.py de Dash.
# --workers 1 porque los modelos de ML se cargan en memoria por worker —
# múltiples workers multiplicarían el uso de RAM en HF Spaces (free tier: 16GB).
# --timeout 300 porque el pipeline completo puede tardar varios minutos.
CMD ["gunicorn", "app:server", \
     "--bind", "0.0.0.0:7860", \
     "--workers", "1", \
     "--timeout", "300", \
     "--log-level", "info"]
