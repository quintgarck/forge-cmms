#!/usr/bin/env python3
"""
Script para diagnosticar y arreglar problemas de autenticación JWT.
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
from frontend.services import AuthenticationService
from frontend.services.api_client import ForgeAPIClient
import requests


def create_admin_user():
    """Crea o verifica que existe un usuario admin."""
    print("👤 Verificando usuario admin...")
    
    try:
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
        
    except Exception as e:
        print(f"❌ Error creando usuario admin: {e}")
        return None


def test_direct_api_authentication():
    """Prueba la autenticación directa con la API."""
    print("\n🔐 Probando autenticación directa con API...")
    
    try:
        # Try to get JWT token directly
        auth_url = "http://localhost:8000/api/v1/auth/login/"
        
        auth_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        print(f"📡 Enviando credenciales a: {auth_url}")
        response = requests.post(auth_url, json=auth_data, timeout=10)
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Autenticación directa exitosa")
            print(f"🔑 Token recibido: {data.get('access', 'No access token')[:50]}...")
            return data.get('access'), data.get('refresh')
        else:
            print(f"❌ Autenticación directa falló: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 Error: {error_data}")
            except:
                print(f"📋 Respuesta: {response.text[:200]}")
            return None, None
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor de autenticación")
        return None, None
    except Exception as e:
        print(f"❌ Error en autenticación directa: {e}")
        return None, None


def test_api_with_token(access_token):
    """Prueba llamadas a la API con el token JWT."""
    print("\n🧪 Probando API con token JWT...")
    
    if not access_token:
        print("⚠️ No hay token disponible para probar")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test dashboard endpoint
        dashboard_url = "http://localhost:8000/api/v1/dashboard/"
        print(f"📡 Probando dashboard: {dashboard_url}")
        
        response = requests.get(dashboard_url, headers=headers, timeout=10)
        print(f"📊 Dashboard response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard API funciona con token")
        else:
            print(f"❌ Dashboard API falló: {response.status_code}")
        
        # Test clients endpoint
        clients_url = "http://localhost:8000/api/v1/clients/"
        print(f"📡 Probando clientes: {clients_url}")
        
        response = requests.get(clients_url, headers=headers, timeout=10)
        print(f"📊 Clients response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Clients API funciona con token")
            return True
        else:
            print(f"❌ Clients API falló: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando API con token: {e}")
        return False


def test_frontend_authentication_service():
    """Prueba el servicio de autenticación del frontend."""
    print("\n🔧 Probando servicio de autenticación del frontend...")
    
    # Create a mock request
    class MockRequest:
        def __init__(self):
            self.session = {}
            self.META = {'HTTP_HOST': 'localhost:8000'}
            
        def is_secure(self):
            return False
            
        def get_host(self):
            return 'localhost:8000'
    
    mock_request = MockRequest()
    auth_service = AuthenticationService(mock_request)
    
    try:
        print("🔐 Intentando login con AuthenticationService...")
        success, message, user_data = auth_service.login('admin', 'admin123')
        
        if success:
            print("✅ AuthenticationService login exitoso")
            print(f"📋 Mensaje: {message}")
            print(f"👤 Usuario: {user_data}")
            
            # Check if token was stored in session
            if 'auth_token' in mock_request.session:
                token = mock_request.session['auth_token']
                print(f"🔑 Token almacenado en sesión: {token[:50]}...")
                return True, mock_request
            else:
                print("⚠️ Token no almacenado en sesión")
                return False, None
        else:
            print("❌ AuthenticationService login falló")
            print(f"📋 Mensaje: {message}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error en AuthenticationService: {e}")
        return False, None


def test_api_client_with_session():
    """Prueba el API client con sesión autenticada."""
    print("\n🔌 Probando API client con sesión...")
    
    success, mock_request = test_frontend_authentication_service()
    if not success:
        print("⚠️ No se puede probar API client - autenticación falló")
        return False
    
    try:
        api_client = ForgeAPIClient(request=mock_request)
        
        print("📡 Probando llamada a dashboard...")
        dashboard_data = api_client.get('dashboard/')
        
        if dashboard_data:
            print("✅ API client funciona correctamente")
            print(f"📊 Datos recibidos: {list(dashboard_data.keys())[:5]}")
            return True
        else:
            print("❌ API client no recibió datos")
            return False
            
    except Exception as e:
        print(f"❌ Error en API client: {e}")
        return False


def create_test_client_via_api():
    """Intenta crear un cliente usando la API directamente."""
    print("\n📝 Intentando crear cliente via API...")
    
    access_token, _ = test_direct_api_authentication()
    if not access_token:
        print("⚠️ No se puede crear cliente - no hay token")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        client_data = {
            'client_code': 'CLI-JWT-TEST',
            'type': 'individual',
            'name': 'Cliente JWT Test',
            'email': 'jwt@test.com',
            'phone': '82363829',
            'address': 'Dirección JWT Test',
            'credit_limit': 1000.00
        }
        
        clients_url = "http://localhost:8000/api/v1/clients/"
        print(f"📡 Enviando datos a: {clients_url}")
        
        response = requests.post(clients_url, json=client_data, headers=headers, timeout=10)
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ Cliente creado via API directa")
            print(f"📋 Cliente ID: {result.get('id')}")
            return True
        else:
            print(f"❌ Error creando cliente: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 Error: {error_data}")
            except:
                print(f"📋 Respuesta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error creando cliente via API: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 DIAGNÓSTICO Y CORRECCIÓN DE AUTENTICACIÓN JWT")
    print("=" * 60)
    
    # Step 1: Ensure admin user exists
    admin_user = create_admin_user()
    if not admin_user:
        print("❌ No se puede continuar sin usuario admin")
        return 1
    
    results = []
    
    # Step 2: Test direct API authentication
    access_token, refresh_token = test_direct_api_authentication()
    results.append(bool(access_token))
    
    # Step 3: Test API calls with token
    if access_token:
        results.append(test_api_with_token(access_token))
    else:
        results.append(False)
    
    # Step 4: Test frontend authentication service
    results.append(test_frontend_authentication_service()[0])
    
    # Step 5: Test API client with session
    results.append(test_api_client_with_session())
    
    # Step 6: Try to create a client
    if access_token:
        results.append(create_test_client_via_api())
    else:
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO JWT")
    print("=" * 60)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    # Provide recommendations
    print("\n🔧 RECOMENDACIONES:")
    
    if not results[0]:  # Direct API auth failed
        print("❌ Autenticación directa con API falló")
        print("   → Verificar que el servidor esté ejecutándose")
        print("   → Verificar credenciales admin/admin123")
        print("   → Revisar configuración JWT en settings.py")
    
    if not results[1]:  # API calls with token failed
        print("❌ Llamadas API con token fallaron")
        print("   → Verificar configuración de permisos")
        print("   → Revisar middleware de autenticación")
    
    if not results[2]:  # Frontend auth service failed
        print("❌ Servicio de autenticación del frontend falló")
        print("   → Revisar frontend/services/__init__.py")
        print("   → Verificar manejo de tokens en sesión")
    
    if not results[3]:  # API client failed
        print("❌ Cliente API falló")
        print("   → Revisar frontend/services/api_client.py")
        print("   → Verificar headers de autorización")
    
    if success_rate >= 80:
        print("\n🎉 AUTENTICACIÓN JWT FUNCIONANDO CORRECTAMENTE")
        print("✅ El problema puede estar en otro lugar")
        return 0
    elif success_rate >= 60:
        print("\n⚠️ AUTENTICACIÓN PARCIALMENTE FUNCIONAL")
        print("🔧 Se requieren ajustes menores")
        return 0
    else:
        print("\n❌ PROBLEMAS CRÍTICOS DE AUTENTICACIÓN")
        print("🚨 Se requiere atención inmediata")
        return 1


if __name__ == '__main__':
    sys.exit(main())