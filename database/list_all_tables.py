"""
Script para listar todas las tablas en la base de datos y compararlas con los modelos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Obtener todas las tablas de los esquemas relevantes
cursor.execute("""
    SELECT schemaname, tablename 
    FROM pg_tables 
    WHERE schemaname IN ('cat', 'inv', 'svc', 'doc', 'app', 'oem', 'kpi') 
    ORDER BY schemaname, tablename
""")

tables = cursor.fetchall()

print("\n" + "="*80)
print("TABLAS EN LA BASE DE DATOS")
print("="*80)

current_schema = None
for schema, table in tables:
    if schema != current_schema:
        print(f"\n[{schema.upper()}]")
        current_schema = schema
    print(f"  - {table}")

print(f"\n{'='*80}")
print(f"Total: {len(tables)} tablas")
print("="*80)

