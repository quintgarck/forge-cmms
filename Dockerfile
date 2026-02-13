# Dockerfile para Forge CMMS API
# Python 3.11 slim image
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no root para seguridad
RUN groupadd -r django && useradd -r -g django django

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY forge_api/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY forge_api/ /app/

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

# Cambiar a usuario no root
USER django

# Exponer puerto
EXPOSE 8000

# Script de inicio
COPY docker-entrypoint.sh /docker-entrypoint.sh
USER root
RUN chmod +x /docker-entrypoint.sh
USER django

# Comando por defecto
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "forge_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
