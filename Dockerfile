FROM python:3.12-slim

# Evitar que Python escriba archivos .pyc y forzar que la salida estándar se envíe directamente a la terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/

# Recolectar archivos estáticos
RUN python manage.py collectstatic --no-input

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar migraciones y luego iniciar gunicorn
CMD bash -c "python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:8000"
