#!/usr/bin/env python3
"""
Quick test to check equipment types in database vs API
"""

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from core.models import EquipmentType
import requests

print("=== DATABASE CHECK ===")
print(f"Total equipment types in DB: {EquipmentType.objects.count()}")
for et in EquipmentType.objects.all():
    print(f"- {et.type_code}: {et.name}")

print("\n=== API CHECK ===")
try:
    # Test direct API access
    response = requests.get('http://localhost:8000/api/v1/equipment-types/')
    print(f"API Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"API Count: {data.get('count', 0)}")
        print("API Results:")
        for item in data.get('results', []):
            print(f"- {item['type_code']}: {item['name']}")
    else:
        print(f"API Error: {response.text}")
except Exception as e:
    print(f"API Connection Error: {e}")