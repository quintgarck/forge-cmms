import time
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from core.models import FuelCode
from core.serializers import FuelCodeSerializer

print("=== Diagnóstico de Rendimiento ===\n")

# Medir tiempo de query
print("1. Query a base de datos:")
start = time.time()
list(FuelCode.objects.all())
elapsed = time.time() - start
print(f"   Tiempo: {elapsed:.4f} segundos")

# Medir tiempo de serialización
print("\n2. Serialización:")
start = time.time()
qs = FuelCode.objects.all()
data = FuelCodeSerializer(qs, many=True).data
elapsed = time.time() - start
print(f"   Tiempo: {elapsed:.4f} segundos")

# Medir tiempo de API completa
print("\n3. API completa (list):")
start = time.time()
from rest_framework.test import APIRequestFactory
from core.views.catalog_views import FuelCodeViewSet

factory = APIRequestFactory()
view = FuelCodeViewSet.as_view({'get': 'list'})

request = factory.get('/fuel-codes/')
response = view(request)
elapsed = time.time() - start
print(f"   Tiempo: {elapsed:.4f} segundos")
print(f"   Status: {response.status_code}")

print("\n=== Fin del diagnóstico ===")
