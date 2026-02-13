#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
import django
django.setup()

from django.db import connection

print("=== Database Connection Test ===")
print(f"Database: {connection.settings_dict['NAME']}")

with connection.cursor() as cursor:
    # Check public schema
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 10")
    print("\nTables in 'public' schema:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    
    # Check oem schema
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'oem' LIMIT 10")
    print("\nTables in 'oem' schema:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    
    # Check cat schema
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'cat' LIMIT 10")
    print("\nTables in 'cat' schema:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

print("\n=== OEM Catalog Items ===")
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM oem.catalog_items")
    count = cursor.fetchone()[0]
    print(f"Total records in oem.catalog_items: {count}")
    
    if count > 0:
        cursor.execute("SELECT catalog_id, oem_code, part_number FROM oem.catalog_items LIMIT 5")
        print("\nFirst 5 records:")
        for row in cursor.fetchall():
            print(f"  - ID: {row[0]}, OEM: {row[1]}, Part: {row[2]}")
