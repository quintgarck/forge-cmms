#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
import django
django.setup()

from core.models import OEMCatalogItem

print("=== Testing OEMCatalogItem Model ===")
items = OEMCatalogItem.objects.all()
print(f"Queryset type: {type(items)}")
print(f"Count: {items.count()}")

# Force evaluation
list_items = list(items[:5])
print(f"List length: {len(list_items)}")

for item in list_items:
    print(f"  - ID: {item.catalog_id}, OEM: {item.oem_code}, Part: {item.part_number}")
