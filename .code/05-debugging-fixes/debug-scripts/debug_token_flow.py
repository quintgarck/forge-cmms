#!/usr/bin/env python3
"""
Script para diagnosticar el flujo de tokens JWT paso a paso.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import requests


def create_admin_user():
    """Crea usuario admin."""
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@forgedb.com',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
    
    return admin_user


def test_direct_jwt_flow():
    """Prueba el flujo JWT directo."""
    print("🔐 1. PROBANDO FLUJO JWT DIRECTO")
    print("-" * 40)
    
    try:
        # Get JWT token directly
        auth_url = "http://localhost:8000/api/v1/auth/login/"
        auth_data = {'username': 'admin', 'password': 'admin123'}
        
        print(f"📡 POST {auth_url}")
        print(f"📋 Data: {auth_data}")
        
        response = requests.post(auth_url, json=auth_data, timeout=10)
        print(f"📊 Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access')
            refresh_token = data.get('refresh')
            
            print(f"✅ Access token: {access_token[:50]}..." if access_token else "❌ No access token")
            print(f"✅ Refresh token: {refresh_token[:50]}..." if refresh_token else "❌ No refresh token")
            
            return access_token, refresh_token
        else:
            print(f"❌ Auth failed: {response.text[:200]}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None


def test_api_with_token(token):
    """Prueba la API con token."""
    print(f"\n🧪 2. PROBANDO API CON TOKEN")
    print("-" * 40)
    
    if not token:
        print("⚠️ No token disponible")
        return False
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test clients endpoint
        clients_url = "http://localhost:8000/api/v1/clients/"
        print(f"📡 GET {clients_url}")
        print(f"📋 Headers: Authorization: Bearer {token[:30]}...")
        
        response = requests.get(clients_url, headers=headers, timeout=10)
        print(f"📊 Response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API funciona con token")
            return True
        else:
            print(f"❌ API failed: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_django_login_flow():
    """Prueba el flujo de login de Django."""
    print(f"\n🌐 3. PROBANDO FLUJO DE LOGIN DJANGO")
    print("-" * 40)
    
    create_admin_user()
    django_client = Client()
    
    # Login
    login_success = django_client.login(username='admin', password='admin123')
    print(f"📊 Django login: {'✅ Success' if login_success else '❌ Failed'}")
    
    if not login_success:
        return False, None
    
    # Check session
    session = django_client.session
    print(f"📋 Session keys: {list(session.keys())}")
    
    # Check for auth tokens
    auth_token = session.get('auth_token')
    refresh_token = session.get('refresh_token')
    user_data = session.get('user_data')
    
    print(f"🔑 Auth token in session: {'✅ Yes' if auth_token else '❌ No'}")
    print(f"🔄 Refresh token in session: {'✅ Yes' if refresh_token else '❌ No'}")
    print(f"👤 User data in session: {'✅ Yes' if user_data else '❌ No'}")
    
    if auth_token:
        print(f"🔍 Token preview: {auth_token[:50]}...")
    
    return True, django_client


def test_client_creation_step_by_step(django_client):
    """Prueba la creación de cliente paso a paso."""
    print(f"\n📝 4. PROBANDO CREACIÓN DE CLIENTE PASO A PASO")
    print("-" * 40)
    
    if not django_client:
        print("⚠️ No Django client disponible")
        return False
    
    # Step 1: GET form
    print("📄 Paso 1: Cargando formulario...")
    try:
        response = django_client.get('/clients/create/')
        print(f"📊 GET /clients/create/: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ No se pudo cargar el formulario")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando formulario: {e}")
        return False
    
    # Step 2: Check session before POST
    print("\n🔍 Paso 2: Verificando sesión antes de POST...")
    session = django_client.session
    auth_token = session.get('auth_token')
    print(f"🔑 Token en sesión: {'✅ Present' if auth_token else '❌ Missing'}")
    
    if auth_token:
        print(f"🔍 Token: {auth_token[:50]}...")
        
        # Test if token works directly
        try:
            headers = {'Authorization': f'Bearer {auth_token}'}
            test_response = requests.get('http://localhost:8000/api/v1/clients/', headers=headers, timeout=5)
            print(f"🧪 Token test: {test_response.status_code}")
        except Exception as e:
            print(f"🧪 Token test error: {e}")
    
    # Step 3: POST form
    print("\n📤 Paso 3: Enviando formulario...")
    client_data = {
        'client_code': 'CLI-DEBUG-STEP',
        'type': 'individual',
        'name': 'Cliente Debug Step by Step',
        'email': 'debug@step.com',
        'phone': '82363829',
        'address': 'Debug Address',
        'credit_limit': '1000.00',
    }
    
    try:
        print(f"📋 Data: {client_data}")
        response = django_client.post('/clients/create/', data=client_data, follow=True)
        print(f"📊 POST /clients/create/: {response.status_code}")
        
        # Check response content
        content = response.content.decode('utf-8')
        
        # Look for specific error messages
        if 'Las credenciales de autenticación no se proveyeron' in content:
            print("❌ Error específico: Credenciales no provistas")
        elif 'Token expired' in content:
            print("❌ Error específico: Token expirado")
        elif 'Cliente Debug Step by Step' in content:
            print("✅ Cliente creado exitosamente")
            return True
        elif 'creado exitosamente' in content.lower():
            print("✅ Mensaje de éxito detectado")
            return True
        else:
            print("⚠️ Respuesta ambigua")
            
            # Show first 500 chars for debugging
            print(f"📄 Contenido (primeros 500 chars):")
            print(content[:500])
        
        return False
        
    except Exception as e:
        print(f"❌ Error enviando formulario: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 DIAGNÓSTICO DETALLADO DEL FLUJO DE TOKENS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Direct JWT flow
    access_token, refresh_token = test_direct_jwt_flow()
    results.append(bool(access_token))
    
    # Test 2: API with token
    if access_token:
        results.append(test_api_with_token(access_token))
    else:
        results.append(False)
    
    # Test 3: Django login flow
    django_success, django_client = test_django_login_flow()
    results.append(django_success)
    
    # Test 4: Client creation step by step
    if django_client:
        results.append(test_client_creation_step_by_step(django_client))
    else:
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    # Specific recommendations
    print("\n🔧 DIAGNÓSTICO ESPECÍFICO:")
    
    if not results[0]:
        print("❌ JWT directo falló - problema con backend auth")
    elif not results[1]:
        print("❌ API con token falló - problema con headers o permisos")
    elif not results[2]:
        print("❌ Django login falló - problema con frontend auth service")
    elif not results[3]:
        print("❌ Creación de cliente falló - problema con integración")
    else:
        print("✅ Todos los componentes funcionan individualmente")
        print("🔍 El problema puede estar en la integración entre componentes")
    
    return 0 if success_rate >= 75 else 1


if __name__ == '__main__':
    sys.exit(main())