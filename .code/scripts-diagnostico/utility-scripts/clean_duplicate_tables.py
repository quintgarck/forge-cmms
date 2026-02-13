"""
Script para limpiar tablas duplicadas en el esquema 'app'.

Este script identifica y opcionalmente elimina tablas duplicadas que tienen
nombres incorrectos (incluyen el esquema en el nombre de la tabla).
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

# Tablas que DEBEN estar en el esquema 'app' (correctas)
CORRECT_APP_TABLES = ['alerts', 'audit_logs', 'business_rules']

# Tablas que NO deben estar en 'app' (deben estar en otros esquemas)
WRONG_APP_TABLES = [
    'app.alerts', 'app.audit_logs', 'app.business_rules',
    'cat.clients', 'cat.equipment', 'cat.technicians',
    'inv.warehouses', 'inv.stock', 'inv.transactions', 'inv.product_master',
    'svc.work_orders', 'svc.invoices',
    'doc.documents',
]

def list_duplicate_tables():
    """Listar tablas duplicadas en el esquema 'app'"""
    print("=== Identificando Tablas Duplicadas en esquema 'app' ===\n")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'app'
            ORDER BY tablename
        """)
        all_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Total de tablas en esquema 'app': {len(all_tables)}\n")
        
        # Identificar tablas problemáticas
        problematic_tables = []
        correct_tables = []
        
        for table in all_tables:
            if table in WRONG_APP_TABLES:
                problematic_tables.append(table)
                print(f"PROBLEMA: {table} (no deberia estar en 'app')")
            elif '.' in table and table not in CORRECT_APP_TABLES:
                problematic_tables.append(table)
                print(f"PROBLEMA: {table} (nombre incluye esquema)")
            elif table in CORRECT_APP_TABLES or table.startswith('auth_') or table.startswith('django_'):
                correct_tables.append(table)
                print(f"OK: {table}")
        
        print(f"\nResumen:")
        print(f"  - Tablas correctas: {len(correct_tables)}")
        print(f"  - Tablas problematicas: {len(problematic_tables)}")
        
        return problematic_tables, correct_tables

def check_table_exists_in_correct_schema(table_name):
    """Verificar si la tabla existe en el esquema correcto"""
    # Extraer esquema y nombre de tabla
    if '.' in table_name:
        parts = table_name.split('.')
        expected_schema = parts[0]
        table_only = parts[1]
    else:
        return None
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schemaname 
            FROM pg_tables 
            WHERE schemaname = %s AND tablename = %s
        """, [expected_schema, table_only])
        
        result = cursor.fetchone()
        return result is not None

def drop_duplicate_tables(dry_run=True):
    """Eliminar tablas duplicadas (dry_run por defecto)"""
    problematic_tables, correct_tables = list_duplicate_tables()
    
    if not problematic_tables:
        print("\nNo se encontraron tablas problematicas.")
        return
    
    print(f"\n=== {'SIMULACION' if dry_run else 'ELIMINACION'} de Tablas Duplicadas ===\n")
    
    with connection.cursor() as cursor:
        for table in problematic_tables:
            # Verificar si existe en el esquema correcto
            exists_correct = check_table_exists_in_correct_schema(table)
            
            if exists_correct:
                print(f"  {'[DRY RUN]' if dry_run else ''} DROP TABLE app.\"{table}\";")
                if not dry_run:
                    try:
                        cursor.execute(f'DROP TABLE IF EXISTS app."{table}" CASCADE')
                        print(f"    -> Eliminada correctamente")
                    except Exception as e:
                        print(f"    -> ERROR: {e}")
            else:
                print(f"  ADVERTENCIA: {table} no tiene equivalente en esquema correcto")
    
    if not dry_run:
        connection.commit()
        print("\nTablas eliminadas. Cambios guardados.")
    else:
        print("\nModo DRY RUN: No se realizaron cambios.")
        print("Para eliminar realmente, ejecuta: drop_duplicate_tables(dry_run=False)")

if __name__ == '__main__':
    print("Script de Limpieza de Tablas Duplicadas\n")
    print("=" * 60)
    
    # Listar tablas duplicadas
    problematic, correct = list_duplicate_tables()
    
    if problematic:
        print("\n" + "=" * 60)
        print("Para eliminar las tablas duplicadas, modifica este script")
        print("y cambia dry_run=False en la llamada a drop_duplicate_tables()")
        print("\nO ejecuta manualmente los comandos SQL mostrados arriba.")
    else:
        print("\nNo hay tablas duplicadas que limpiar.")

