#!/bin/bash
set -e

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-forge_db}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD}

# Intentar conectar hasta 30 veces (60 segundos máximo)
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', '5432')),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', ''),
        dbname=os.environ.get('DB_NAME', 'forge_db'),
        connect_timeout=2
    )
    conn.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
    echo "Base de datos lista!"
    break
  else
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Intento $RETRY_COUNT/$MAX_RETRIES: Base de datos no disponible - esperando..."
    sleep 2
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "ADVERTENCIA: No se pudo conectar a la base de datos después de $MAX_RETRIES intentos"
  echo "Continuando de todas formas..."
fi

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --clear || true

# Crear superusuario si no existe (solo en desarrollo)
if [ "$DEBUG" = "True" ] && [ -z "$SKIP_SUPERUSER" ]; then
  echo "Verificando superusuario..."
  python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
EOF
fi

# Ejecutar comando principal
exec "$@"
