FROM python:3.11-slim

# Evitar generación de archivos .pyc y forzar salida inmediata en logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Instalar dependencias del sistema mínimas si fueran necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/

# Crear directorio de datos persistente
RUN mkdir -p /app/data

EXPOSE 8501

# Ejecutar proceso de ingesta MQTT en segundo plano y servidor Streamlit
CMD sh -c "python src/ingesta_mqtt.py & streamlit run src/dashboard.py"
