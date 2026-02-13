#!/usr/bin/env python3
"""
Script para crear clientes de muestra en ForgeDB.
"""

import os
import sys
import django
from pathlib import Path
import requests

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.contrib.auth.models import User


def get_jwt_token():
    """Obtiene un token JWT válido."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json={'username': 'testuser', 'password': 'testpass123'},
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json().get('access')
        return None
    except:
        return None


def create_sample_clients():
    """Crea clientes de muestra."""
    print("🚀 CREANDO CLIENTES DE MUESTRA")
    print("=" * 50)
    
    # Ensure test user exists
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_active': True
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Get token
    token = get_jwt_token()
    if not token:
        print("❌ No se pudo obtener token")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Sample clients data
    sample_clients = [
        {
            'client_code': 'CLI-001',
            'type': 'individual',
            'name': 'Juan Pérez García',
            'email': 'juan.perez@example.com',
            'phone': '5551234567',
            'address': 'Calle Principal 123\nColonia Centro\nCiudad, Estado 12345',
            'credit_limit': 5000.00
        },
        {
            'client_code': 'CLI-002',
            'type': 'business',
            'name': 'Transportes González S.A.',
            'email': 'contacto@transportesgonzalez.com',
            'phone': '5559876543',
            'address': 'Avenida Industrial 456\nParque Industrial\nCiudad, Estado 54321',
            'credit_limit': 15000.00
        },
        {
            'client_code': 'CLI-003',
            'type': 'individual',
            'name': 'María López Hernández',
            'email': 'maria.lopez@gmail.com',
            'phone': '5555678901',
            'address': 'Calle Reforma 789\nColonia Roma\nCDMX, México 06700',
            'credit_limit': 7500.00
        },
        {
            'client_code': 'CLI-004',
            'type': 'fleet',
            'name': 'Flota Ejecutiva Premium',
            'email': 'admin@flotaejecutiva.com',
            'phone': '5552345678',
            'address': 'Boulevard Corporativo 321\nZona Empresarial\nCiudad, Estado 67890',
            'credit_limit': 25000.00
        }
    ]
    
    created_count = 0
    
    for i, client_data in enumerate(sample_clients, 1):
        print(f"\n{i}. Creando: {client_data['name']}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/clients/",
                json=client_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                created_client = response.json()
                print(f"   ✅ Cliente creado con ID: {created_client.get('id')}")
                created_count += 1
            elif response.status_code == 400:
                error_data = response.json()
                print(f"   ❌ Error de validación: {error_data}")
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 RESUMEN: {created_count}/{len(sample_clients)} clientes creados")
    
    if created_count > 0:
        print("\n🎉 ¡CLIENTES DE MUESTRA CREADOS EXITOSAMENTE!")
        print("✅ Ahora puedes ver la lista en: http://localhost:8000/clients/")
        return True
    else:
        print("\n⚠️ No se pudieron crear clientes de muestra")
        return False


def main():
    """Función principal."""
    # Setup environment
    if not setup_test_environment():
        print("\n❌ PROBLEMA EN LA CONFIGURACIÓN")
        return 1
    
    # Create sample clients
    success = create_sample_clients()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 ¡LISTO PARA USAR!")
        print("=" * 60)
        print("1. Ve a: http://localhost:8000/login/")
        print("2. Usuario: testuser, Contraseña: testpass123")
        print("3. Explora los clientes creados en: http://localhost:8000/clients/")
        print("4. Crea nuevos clientes en: http://localhost:8000/clients/create/")
        print("\n✅ El sistema ForgeDB está completamente funcional")
        return 0
    else:
        print("\n⚠️ Hubo algunos problemas, pero puedes crear clientes manualmente")
        return 1


if __name__ == '__main__':
    sys.exit(main())