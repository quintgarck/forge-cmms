import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Verificar todas las tablas en el esquema cat
cursor.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'cat'
    ORDER BY table_name
""")
print("Tablas en esquema 'cat':")
for row in cursor.fetchall():
    print(f"  - {row[0]}.{row[1]}")

# Verificar si técnicos está en minúsculas
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'cat' 
    AND table_name ILIKE '%tech%'
""")
print(f"\nTablas con 'tech' en esquema 'cat': {cursor.fetchall()}")

# Probar con comillas
cursor.execute('SELECT COUNT(*) FROM "cat"."technicians"')
print(f"\nCOUNT con comillas dobles: {cursor.fetchone()[0]}")

cursor.execute('SELECT COUNT(*) FROM cat.technicians')
print(f"COUNT sin comillas: {cursor.fetchone()[0]}")
