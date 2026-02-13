#!/usr/bin/env python3
"""
Script simple para verificar conectividad básica del sistema ForgeDB.
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
from django.urls import reverse
from django.contrib.auth.models import User


def test_api_health():
    """Prueba el health check de la API."""
    print("🔍 Probando API Health Check...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health Check: {data.get('status')}")
            return True
        else:
            print(f"❌ API Health Check: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Check: {e}")
        return False


def test_frontend_basic():
    """Prueba básica del frontend."""
    print("\n🔍 Probando Frontend Básico...")
    
    client = Client()
    
    try:
        # Test login page
        response = client.get('/login/')
        if response.status_code == 200:
            print("✅ Login page accessible")
            return True
        else:
            print(f"❌ Login page: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend test: {e}")
        return False


def test_authentication():
    """Prueba la autenticación JWT."""
    print("\n🔍 Probando Autenticación...")
    
    # Create test user
    try:
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
        
        # Test JWT login
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json={'username': 'testuser', 'password': 'testpass123'},
            timeout=5
        )
        
        if response.status_code == 200:
            token_data = response.json()
            if 'access' in token_data:
                print("✅ JWT Authentication working")
                return token_data['access']
            else:
                print("❌ JWT Authentication: No access token")
                return None
        else:
            print(f"❌ JWT Authentication: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication test: {e}")
        return None


def test_api_with_auth(token):
    """Prueba endpoints de la API con autenticación."""
    print("\n🔍 Probando API con Autenticación...")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        # Test clients endpoint
        response = requests.get(
            "http://localhost:8000/api/v1/clients/",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Clients API endpoint working")
            return True
        else:
            print(f"❌ Clients API: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API with auth test: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PRUEBAS SIMPLES DE CONECTIVIDAD FORGEDB")
    print("=" * 50)
    
    results = []
    
    # Test API health
    results.append(test_api_health())
    
    # Test frontend basic
    results.append(test_frontend_basic())
    
    # Test authentication
    token = test_authentication()
    if token:
        results.append(True)
        # Test API with auth
        results.append(test_api_with_auth(token))
    else:
        results.append(False)
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    print("=" * 50)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("\n🎉 CONECTIVIDAD BÁSICA FUNCIONANDO")
        print("✅ Puedes proceder con la implementación de Task 6.3")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DE CONECTIVIDAD DETECTADOS")
        print("❌ Revisar configuración antes de continuar")
        return 1


if __name__ == '__main__':
    sys.exit(main())