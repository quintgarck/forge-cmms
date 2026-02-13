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

        if schemas:
            print("ForgeDB schemas found!")
        else:
            print("ForgeDB schemas NOT found - database may not be initialized")

    except Exception as e:
        print(f"Database error: {e}")

if __name__ == '__main__':
    check_database()