"""
Script para ejecutar part1.sql
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
    'part1.sql'
)

print(f"\n{'='*80}")
print(f"EJECUTANDO: {sql_file_path}")
print('='*80)

with open(sql_file_path, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Ejecutar el SQL - separar en declaraciones individuales
statements = sql_content.split(';')
with connection.cursor() as cursor:
    for i, stmt in enumerate(statements):
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--') and not stmt.startswith('SET'):
            try:
                cursor.execute(stmt)
                print(f"Statement {i+1}: OK")
            except Exception as e:
                print(f"Statement {i+1}: ERROR - {e}")

print(f"\n✅ Script SQL ejecutado exitosamente\n")
print(f"{'='*80}\n")
