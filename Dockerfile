FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias esenciales del sistema para compilar extensiones de C si es necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar primero requirements para cachear la instalación de dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . .

# Crear el directorio uploads
RUN mkdir -p uploads

# Exponer el puerto
EXPOSE 5000

# Variables de entorno por defecto
ENV PORT=5000
ENV UPLOAD_FOLDER=/app/uploads

# Arrancar el servidor Flask
CMD ["python", "app.py"]
