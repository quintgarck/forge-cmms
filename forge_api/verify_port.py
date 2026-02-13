import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

print(f"Host: {connection.settings_dict['HOST']}")
print(f"Port: {connection.settings_dict['PORT']}")
print(f"Database: {connection.settings_dict['NAME']}")
print(f"User: {connection.settings_dict['USER']}")

cursor = connection.cursor()
cursor.execute("SELECT COUNT(*) FROM cat.technicians")
print(f"\nTécnicos en cat.technicians: {cursor.fetchone()[0]}")

cursor.execute("SELECT employee_code, first_name, last_name FROM cat.technicians LIMIT 3")
for row in cursor.fetchall():
    print(f"  - {row[0]}: {row[1]} {row[2]}")
