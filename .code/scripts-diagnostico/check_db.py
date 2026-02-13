#!/usr/bin/env python
"""
Check database schemas and data for ForgeDB
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

def check_database():
    cursor = connection.cursor()

    print("=== DATABASE CHECK ===")

    try:
        # Check if ForgeDB schemas exist
        cursor.execute("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name IN ('cat', 'inv', 'svc', 'doc', 'kpi', 'app', 'oem');
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        print(f"Found schemas: {schemas}")

        if 'cat' in schemas:
            print("\n=== CLIENTS TABLE ===")
            cursor.execute("SELECT COUNT(*) FROM cat.clients;")
            client_count = cursor.fetchone()[0]
            print(f"Clients in database: {client_count}")

            if client_count > 0:
                cursor.execute("SELECT client_code, name FROM cat.clients LIMIT 5;")
                clients = cursor.fetchall()
                print("Sample clients:")
                for client in clients:
                    print(f"  - {client[0]}: {client[1]}")

        if 'inv' in schemas:
            print("\n=== PRODUCTS TABLE ===")
            cursor.execute("SELECT COUNT(*) FROM inv.product_master;")
            product_count = cursor.fetchone()[0]
            print(f"Products in database: {product_count}")

        if 'svc' in schemas:
            print("\n=== WORK ORDERS TABLE ===")
            cursor.execute("SELECT COUNT(*) FROM svc.work_orders;")
            wo_count = cursor.fetchone()[0]
            print(f"Work orders in database: {wo_count}")

    except Exception as e:
        print(f"Database error: {e}")

if __name__ == '__main__':
    check_database()