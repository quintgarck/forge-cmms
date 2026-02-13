#!/usr/bin/env python
"""
Script para verificar la conexión a la base de datos y listar las tablas
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

def check_database():
    """Verificar la conexión y listar las tablas de la base de datos"""
    try:
        with connection.cursor() as cursor:
            # Verificar conexión
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Conexión exitosa a PostgreSQL: {version[0]}")
            
            # Listar esquemas
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name;
            """)
            schemas = cursor.fetchall()
            print(f"\n📁 Esquemas encontrados ({len(schemas)}):")
            for schema in schemas:
                print(f"  - {schema[0]}")
            
            # Listar tablas por esquema
            for schema in schemas:
                schema_name = schema[0]
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """, [schema_name])
                tables = cursor.fetchall()
                
                print(f"\n📋 Tablas en esquema '{schema_name}' ({len(tables)}):")
                for table in tables:
                    print(f"  - {schema_name}.{table[0]}")
                    
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_database()