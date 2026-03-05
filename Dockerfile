# Imagen base oficial de Python
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar primero requirements para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto que usa Dash por defecto
EXPOSE 7860

# Variable de entorno para HF Spaces
ENV HOST=0.0.0.0
ENV PORT=7860

# Comando para arrancar la app
CMD ["python", "app.py"]