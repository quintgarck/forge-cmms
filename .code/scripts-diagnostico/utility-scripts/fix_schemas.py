"""
Script para verificar y corregir el problema de esquemas.

Este script verifica si hay tablas en el esquema 'app' que deberían estar
en otros esquemas según los modelos Django.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection
from core.models import (
    Alert, BusinessRule, AuditLog, Technician, Client, Equipment,
    Warehouse, ProductMaster, Stock, Transaction, WorkOrder, Invoice, Document
)

# Mapeo de modelos a esquemas esperados
MODEL_SCHEMA_MAP = {
    'Alert': 'app',
    'BusinessRule': 'app',
    'AuditLog': 'app',
    'Technician': 'cat',
    'Client': 'cat',
    'Equipment': 'cat',
    'Warehouse': 'inv',
    'ProductMaster': 'inv',
    'Stock': 'inv',
    'Transaction': 'inv',
    'WorkOrder': 'svc',
    'Invoice': 'svc',
    'Document': 'doc',
}

def check_model_tables():
    """Verificar en qué esquema está cada tabla de modelo"""
    print("=== Verificación de Ubicación de Tablas de Modelos ===\n")
    
    with connection.cursor() as cursor:
        for model_name, expected_schema in MODEL_SCHEMA_MAP.items():
            # Obtener el modelo
            model_map = {
                'Alert': Alert,
                'BusinessRule': BusinessRule,
                'AuditLog': AuditLog,
                'Technician': Technician,
                'Client': Client,
                'Equipment': Equipment,
                'Warehouse': Warehouse,
                'ProductMaster': ProductMaster,
                'Stock': Stock,
                'Transaction': Transaction,
                'WorkOrder': WorkOrder,
                'Invoice': Invoice,
                'Document': Document,
            }
            
            model = model_map[model_name]
            table_name = model._meta.db_table
            
            # Verificar en qué esquema está la tabla
            cursor.execute("""
                SELECT schemaname 
                FROM pg_tables 
                WHERE tablename = %s 
                AND schemaname NOT IN ('pg_catalog', 'information_schema')
            """, [table_name.split('.')[-1]])
            
            result = cursor.fetchone()
            if result:
                actual_schema = result[0]
                status = "OK" if actual_schema == expected_schema else "ERROR"
                print(f"{status:6} {model_name:20} -> {table_name:30} (esperado: {expected_schema}, actual: {actual_schema})")
                
                if actual_schema != expected_schema:
                    print(f"    ADVERTENCIA: La tabla esta en el esquema incorrecto!")
            else:
                print(f"? {model_name:20} -> {table_name:30} (NO ENCONTRADA)")

def check_app_schema_tables():
    """Verificar qué tablas hay en el esquema 'app'"""
    print("\n=== Tablas en el esquema 'app' ===\n")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'app'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"Se encontraron {len(tables)} tabla(s) en el esquema 'app':")
            for (table,) in tables:
                print(f"  - {table}")
        else:
            print("No se encontraron tablas en el esquema 'app'.")
        
        return [table[0] for table in tables]

if __name__ == '__main__':
    # Verificar ubicación de tablas de modelos
    check_model_tables()
    
    # Verificar tablas en esquema app
    app_tables = check_app_schema_tables()
    
    print("\n=== Conclusión ===")
    print("Si hay tablas en el esquema 'app' que deberían estar en otros esquemas,")
    print("necesitarás moverlas usando ALTER TABLE ... SET SCHEMA ...")

