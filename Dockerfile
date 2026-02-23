# Imagen ligera de Python
FROM python:3.10-slim

# Instalamos dependencias del sistema para mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Dependencias e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Exponemos el puerto de Flask
EXPOSE 5000

# Comando para iniciar la app
CMD ["python", "app.py"]