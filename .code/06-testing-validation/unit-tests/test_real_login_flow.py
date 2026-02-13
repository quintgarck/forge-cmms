#!/usr/bin/env python3
"""
Script para probar el flujo real de login usando las vistas del frontend.
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
        print("✅ Usuario admin creado")
    else:
        print("✅ Usuario admin ya existe")
    
    return admin_user


def test_real_login_flow():
    """Prueba el flujo real de login usando las vistas del frontend."""
    print("🔐 PROBANDO FLUJO REAL DE LOGIN")
    print("-" * 40)
    
    create_admin_user()
    django_client = Client()
    
    # Step 1: GET login form
    print("📄 Paso 1: Cargando formulario de login...")
    try:
        response = django_client.get('/login/')
        print(f"📊 GET /login/: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ No se pudo cargar el formulario de login")
            return False, None
            
    except Exception as e:
        print(f"❌ Error cargando formulario de login: {e}")
        return False, None
    
    # Step 2: POST login credentials
    print("\n🔑 Paso 2: Enviando credenciales de login...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = django_client.post('/login/', data=login_data, follow=True)
        print(f"📊 POST /login/: {response.status_code}")
        
        # Check if redirected to dashboard (successful login)
        if response.status_code == 200:
            final_url = response.request['PATH_INFO']
            print(f"📍 Final URL: {final_url}")
            
            if '/dashboard/' in final_url or final_url == '/':
                print("✅ Login exitoso - redirigido al dashboard")
            else:
                print("⚠️ Login procesado pero no redirigido al dashboard")
        
        # Step 3: Check session for JWT tokens
        print("\n🔍 Paso 3: Verificando tokens en sesión...")
        session = django_client.session
        
        auth_token = session.get('auth_token')
        refresh_token = session.get('refresh_token')
        user_data = session.get('user_data')
        token_timestamp = session.get('token_timestamp')
        
        print(f"🔑 Auth token: {'✅ Present' if auth_token else '❌ Missing'}")
        print(f"🔄 Refresh token: {'✅ Present' if refresh_token else '❌ Missing'}")
        print(f"👤 User data: {'✅ Present' if user_data else '❌ Missing'}")
        print(f"⏰ Token timestamp: {'✅ Present' if token_timestamp else '❌ Missing'}")
        
        if auth_token:
            print(f"🔍 Token preview: {auth_token[:50]}...")
            
        if user_data:
            print(f"👤 User: {user_data.get('username')} ({user_data.get('email')})")
        
        # Success if we have tokens
        has_tokens = bool(auth_token and refresh_token)
        return has_tokens, django_client
        
    except Exception as e:
        print(f"❌ Error durante login: {e}")
        return False, None


def test_client_creation_with_real_login(django_client):
    """Prueba la creación de cliente después del login real."""
    print(f"\n📝 PROBANDO CREACIÓN DE CLIENTE CON LOGIN REAL")
    print("-" * 40)
    
    if not django_client:
        print("⚠️ No Django client disponible")
        return False
    
    # Verify we still have tokens
    session = django_client.session
    auth_token = session.get('auth_token')
    print(f"🔑 Token antes de crear cliente: {'✅ Present' if auth_token else '❌ Missing'}")
    
    # Step 1: GET create form
    print("\n📄 Paso 1: Cargando formulario de creación...")
    try:
        response = django_client.get('/clients/create/')
        print(f"📊 GET /clients/create/: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ No se pudo cargar el formulario")
            return False
            
    except Exception as e:
        print(f"❌ Error cargando formulario: {e}")
        return False
    
    # Step 2: POST client data
    print("\n📤 Paso 2: Enviando datos del cliente...")
    client_data = {
        'client_code': 'CLI-REAL-LOGIN',
        'type': 'individual',
        'name': 'Cliente Con Login Real',
        'email': 'correo@gmail.com',
        'phone': '82363829',
        'address': 'Dirección con login real',
        'credit_limit': '2000.00',
    }
    
    try:
        response = django_client.post('/clients/create/', data=client_data, follow=True)
        print(f"📊 POST /clients/create/: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for success/error indicators
            if 'Cliente Con Login Real' in content:
                print("✅ Cliente creado - nombre encontrado en respuesta")
                return True
            elif 'creado exitosamente' in content.lower():
                print("✅ Cliente creado - mensaje de éxito encontrado")
                return True
            elif 'Las credenciales de autenticación no se proveyeron' in content:
                print("❌ Error: Credenciales no provistas (token no enviado)")
                return False
            else:
                print("⚠️ Respuesta ambigua")
                # Show snippet for debugging
                print(f"📄 Snippet: {content[:300]}...")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        return False


def test_api_integration_after_login(django_client):
    """Prueba que el API client funcione después del login real."""
    print(f"\n🔌 PROBANDO INTEGRACIÓN API DESPUÉS DE LOGIN REAL")
    print("-" * 40)
    
    if not django_client:
        print("⚠️ No Django client disponible")
        return False
    
    # Create a mock request with the session
    class MockRequest:
        def __init__(self, session):
            self.session = session
            self.META = {'HTTP_HOST': 'localhost:8000'}
            
        def is_secure(self):
            return False
            
        def get_host(self):
            return 'localhost:8000'
    
    try:
        from frontend.services.api_client import ForgeAPIClient
        
        mock_request = MockRequest(django_client.session)
        api_client = ForgeAPIClient(request=mock_request)
        
        print("🔍 Verificando headers de autenticación...")
        auth_header = api_client.session.headers.get('Authorization')
        print(f"📋 Auth header: {'✅ Present' if auth_header else '❌ Missing'}")
        
        if auth_header:
            print(f"🔍 Header preview: {auth_header[:50]}...")
        
        # Test API call
        print("\n📡 Probando llamada a la API...")
        try:
            dashboard_data = api_client.get('dashboard/')
            print("✅ API call exitosa")
            print(f"📊 Keys recibidas: {list(dashboard_data.keys())[:5]}")
            return True
        except Exception as api_error:
            print(f"❌ API call falló: {api_error}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando API: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO FLUJO COMPLETO CON LOGIN REAL")
    print("=" * 60)
    print("🎯 Objetivo: Usar las vistas reales de login para obtener tokens JWT")
    print("=" * 60)
    
    results = []
    
    # Test 1: Real login flow
    login_success, django_client = test_real_login_flow()
    results.append(login_success)
    
    # Test 2: API integration after login
    if django_client:
        results.append(test_api_integration_after_login(django_client))
    else:
        results.append(False)
    
    # Test 3: Client creation with real login
    if django_client:
        results.append(test_client_creation_with_real_login(django_client))
    else:
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("\n🎉 FLUJO COMPLETO FUNCIONANDO")
        print("✅ Login real almacena tokens JWT correctamente")
        print("✅ API client puede usar los tokens")
        print("✅ Creación de cliente funciona con autenticación")
        print("\n📝 INSTRUCCIONES PARA EL USUARIO:")
        print("   1. Ir a /login/")
        print("   2. Usar credenciales: admin / admin123")
        print("   3. Ir a /clients/create/")
        print("   4. Usar email: correo@gmail.com")
        print("   5. Usar teléfono: 82363829")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS")
        if not results[0]:
            print("❌ Login real no almacena tokens JWT")
            print("   → Revisar AuthenticationService.login()")
        if not results[1]:
            print("❌ API client no puede usar tokens")
            print("   → Revisar ForgeAPIClient._set_auth_headers()")
        if not results[2]:
            print("❌ Creación de cliente falla")
            print("   → Revisar integración frontend-backend")
        return 1


if __name__ == '__main__':
    sys.exit(main())