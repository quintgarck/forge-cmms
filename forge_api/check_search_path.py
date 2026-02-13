import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Verificar search_path de la conexión
cursor.execute("SHOW search_path")
print(f"Search path: {cursor.fetchone()[0]}")

# Probar sin esquema cualificado
cursor.execute("SELECT COUNT(*) FROM catalog_items")
print(f"COUNT without schema: {cursor.fetchone()[0]}")

# Probar con esquema cualificado
cursor.execute("SELECT COUNT(*) FROM oem.catalog_items")
print(f"COUNT with oem schema: {cursor.fetchone()[0]}")

# Verificar tablas en esquema oem
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'oem'")
print(f"OEM tables: {cursor.fetchall()}")
