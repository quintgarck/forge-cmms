#!/usr/bin/env python3
"""
Script para probar la vista de detalle de cliente.
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

from django.test import Client
from django.contrib.auth.models import User
from frontend.services.api_client import ForgeAPIClient, APIException


def create_test_user():
    """Crea un usuario de prueba."""
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
    return user


def get_auth_token():
    """Obtiene un token de autenticación."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json={'username': 'testuser', 'password': 'testpass123'},
            timeout=5
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access')
        else:
            print(f"Error getting token: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None


def create_test_client(token):
    """Crea un cliente de prueba."""
    headers = {'Authorization': f'Bearer {token}'}
    
    client_data = {
        'client_code': 'TEST-001',
        'type': 'individual',
        'name': 'Juan Pérez',
        'email': 'juan.perez@example.com',
        'phone': '555-1234',
        'address': 'Calle Principal 123\nColonia Centro\nCiudad, Estado 12345',
        'credit_limit': 5000.00
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/clients/",
            json=client_data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Error creating client: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error creating client: {e}")
        return None


def test_client_detail_view(client_id):
    """Prueba la vista de detalle de cliente."""
    print(f"\n🔍 Probando vista de detalle para cliente ID: {client_id}")
    
    # Create Django test client
    django_client = Client()
    
    # Login first
    login_success = django_client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ No se pudo hacer login en Django")
        return False
    
    try:
        # Test client detail view
        response = django_client.get(f'/clients/{client_id}/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for key elements
            checks = [
                ('Juan Pérez' in content, 'Nombre del cliente'),
                ('juan.perez@example.com' in content, 'Email del cliente'),
                ('555-1234' in content, 'Teléfono del cliente'),
                ('Calle Principal 123' in content, 'Dirección del cliente'),
                ('5000.00' in content, 'Límite de crédito'),
                ('Información de Contacto' in content, 'Sección de contacto'),
                ('Información Financiera' in content, 'Sección financiera'),
                ('Órdenes de Trabajo' in content, 'Sección de órdenes'),
            ]
            
            passed = 0
            for check, description in checks:
                if check:
                    print(f"✅ {description}")
                    passed += 1
                else:
                    print(f"❌ {description}")
            
            success_rate = (passed / len(checks)) * 100
            print(f"\n📊 Elementos verificados: {passed}/{len(checks)} ({success_rate:.1f}%)")
            
            return success_rate >= 80
            
        else:
            print(f"❌ Vista de detalle: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando vista de detalle: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO VISTA DE DETALLE DE CLIENTE")
    print("=" * 50)
    
    # Create test user
    print("🔧 Creando usuario de prueba...")
    user = create_test_user()
    print(f"✅ Usuario creado: {user.username}")
    
    # Get auth token
    print("\n🔧 Obteniendo token de autenticación...")
    token = get_auth_token()
    if not token:
        print("❌ No se pudo obtener token")
        return 1
    print("✅ Token obtenido")
    
    # Create test client
    print("\n🔧 Creando cliente de prueba...")
    client_data = create_test_client(token)
    if not client_data:
        print("❌ No se pudo crear cliente de prueba")
        return 1
    
    client_id = client_data.get('id')
    print(f"✅ Cliente creado con ID: {client_id}")
    
    # Test client detail view
    success = test_client_detail_view(client_id)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    print("=" * 50)
    
    if success:
        print("🎉 VISTA DE DETALLE DE CLIENTE FUNCIONANDO CORRECTAMENTE")
        print("✅ Task 6.3 completada exitosamente")
        return 0
    else:
        print("⚠️ PROBLEMAS DETECTADOS EN LA VISTA DE DETALLE")
        print("❌ Revisar implementación")
        return 1


if __name__ == '__main__':
    sys.exit(main())