import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Verificar permisos
cursor.execute("SELECT has_table_privilege('forge_user', 'cat.technicians', 'SELECT')")
print(f"SELECT privilege: {cursor.fetchone()[0]}")

cursor.execute("SELECT grantee, privilege_type FROM information_schema.table_privileges WHERE table_name = 'technicians'")
print(f"Table privileges: {cursor.fetchall()}")

# Probar SELECT directo
try:
    cursor.execute("SELECT COUNT(*) FROM cat.technicians")
    print(f"Direct COUNT: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Direct COUNT error: {e}")
