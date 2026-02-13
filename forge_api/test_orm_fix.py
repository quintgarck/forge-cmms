import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection
from core.models import Technician

print("=== Probando Django ORM ===\n")

# 1. Verificar configuración
print(f"1. Configuración de conexión:")
print(f"   Tabla del modelo: {Technician._meta.db_table}")

# 2. Probar consulta SQL directa con las mismas comillas que Django
cursor = connection.cursor()
print(f"\n2. Consulta directa con comillas dobles:")
try:
    cursor.execute('SELECT COUNT(*) FROM "cat.technicians"')
    print(f"   COUNT con \"cat.technicians\": {cursor.fetchone()[0]}")
except Exception as e:
    print(f"   ERROR: {e}")

# 3. Probar sin comillas
try:
    cursor.execute('SELECT COUNT(*) FROM cat.technicians')
    print(f"   COUNT sin comillas: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"   ERROR: {e}")

# 4. Probar Django ORM
print(f"\n3. Probando Django ORM:")
try:
    count = Technician.objects.count()
    print(f"   Technician.objects.count(): {count}")
except Exception as e:
    print(f"   ERROR en ORM: {e}")

# 5. Listar técnicos
print(f"\n4. Listando técnicos:")
for tech in Technician.objects.all()[:3]:
    print(f"   - {tech.employee_code}: {tech.first_name} {tech.last_name}")
