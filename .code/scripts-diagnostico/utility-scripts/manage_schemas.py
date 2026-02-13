"""
Script para verificar y corregir esquemas de base de datos.

Este script verifica qué tablas están en qué esquemas y ayuda a moverlas
a los esquemas correctos según la definición en los modelos Django.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

def check_schemas():
    """Verificar qué esquemas existen"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        print("Schemas existentes:")
        for schema in schemas:
            print(f"  - {schema}")
        return schemas

def check_tables():
    """Verificar en qué esquemas están las tablas"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename
        """)
        tables = cursor.fetchall()
        print("\nTablas por esquema:")
        current_schema = None
        for schema, table in tables:
            if schema != current_schema:
                print(f"\n[{schema}]")
                current_schema = schema
            print(f"  - {table}")
        return tables

def create_schemas():
    """Crear los esquemas necesarios si no existen"""
    schemas = ['cat', 'inv', 'svc', 'doc', 'kpi', 'app', 'oem']
    with connection.cursor() as cursor:
        for schema in schemas:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        connection.commit()
        print(f"\nEsquemas creados/verificados: {', '.join(schemas)}")

if __name__ == '__main__':
    print("=== Verificación de Esquemas de Base de Datos ===\n")
    
    # Verificar esquemas existentes
    existing_schemas = check_schemas()
    
    # Verificar tablas
    tables = check_tables()
    
    # Crear esquemas si no existen
    print("\n=== Creando esquemas si no existen ===")
    create_schemas()
    
    print("\n=== Análisis completado ===")
    print("\nSi las tablas están en el esquema incorrecto, necesitarás:")
    print("1. Ejecutar el script SQL de creación de esquemas (database/forge_db.sql)")
    print("2. Mover las tablas manualmente usando ALTER TABLE")
    print("3. O recrear las migraciones de Django")

