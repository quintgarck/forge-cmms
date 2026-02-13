"""
Script para ejecutar populate_oem_test_data.sql
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

# Leer archivo SQL
sql_file_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'database',
    'populate_oem_test_data.sql'
)

print(f"\n{'='*80}")
print(f"EJECUTANDO: {sql_file_path}")
print('='*80)

with open(sql_file_path, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Ejecutar el SQL
with connection.cursor() as cursor:
    try:
        cursor.execute(sql_content)
        print(f"\n✅ Script SQL ejecutado exitosamente\n")
        print(f"{'='*80}\n")
    except Exception as e:
        print(f"\n❌ ERROR al ejecutar SQL:")
        print(f"   {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
