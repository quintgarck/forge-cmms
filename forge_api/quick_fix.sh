#!/bin/bash
# Script de solución rápida para problemas de creación de técnicos

echo "=== SOLUCION RAPIDA - CREACION DE TECNICOS ==="

# 1. Limpiar sesiones
echo "Limpiando sesiones..."
python manage.py clearsessions

# 2. Verificar migraciones
echo "Verificando migraciones..."
python manage.py makemigrations --dry-run

# 3. Aplicar migraciones pendientes
echo "Aplicando migraciones..."
python manage.py migrate

# 4. Crear superusuario si no existe
echo "Verificando superusuario..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"

echo "=== SOLUCION COMPLETADA ==="
echo "Ahora puedes:"
echo "1. Iniciar el servidor: python manage.py runserver"
echo "2. Acceder a /admin/ y probar login"
echo "3. Probar crear un cliente primero"
echo "4. Luego probar crear un técnico"
