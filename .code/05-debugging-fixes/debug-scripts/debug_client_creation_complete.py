#!/usr/bin/env python3
"""
Script completo de diagnóstico para problemas de creación de cliente.
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
from frontend.services.api_client import ForgeAPIClient, APIException
from frontend.services import AuthenticationService
from frontend.forms import ClientForm


def setup_test_user():
    """Configura el usuario de prueba."""
    user, created = User.objects.get_or_create(
        username='debuguser',
        defaults={
            'email': 'debug@example.com',
            'is_active': True
        }
    )
    if created:
        user.set_password('debugpass123')
        user.save()
    return user


def test_form_validation():
    """Prueba la validación del formulario Django."""
    print("🔍 1. PROBANDO VALIDACIÓN DEL FORMULARIO DJANGO")
    print("-" * 50)
    
    form_data = {
        'client_code': 'CLI-DEBUG-001',
        'type': 'individual',
        'name': 'Cliente de Debug',
        'email': 'correo@gmail.com',
        'phone': '82363829',
        'address': 'Dirección de debug',
        'credit_limit': '1000.00'
    }
    
    form = ClientForm(data=form_data)
    is_valid = form.is_valid()
    
    if is_valid:
        print("✅ Formulario Django válido")
        print("📋 Datos limpios:")
        for field, value in form.cleaned_data.items():
            print(f"   {field}: {value}")
        return True
    else:
        print("❌ Formulario Django inválido")
        print("🚫 Errores:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return False


def test_authentication_service():
    """Prueba el servicio de autenticación."""
    print("\n🔍 2. PROBANDO SERVICIO DE AUTENTICACIÓN")
    print("-" * 50)
    
    # Create a mock request object
    class MockRequest:
        def __init__(self):
            self.session = {}
            self.user = None
    
    mock_request = MockRequest()
    auth_service = AuthenticationService(mock_request)
    
    try:
        # Try to login with admin credentials
        success, message, user_data = auth_service.login('admin', 'admin123')
        
        if success:
            print("✅ Autenticación exitosa")
            print(f"📋 Mensaje: {message}")
            print(f"👤 Usuario: {user_data}")
            return True, mock_request
        else:
            print("❌ Autenticación fallida")
            print(f"📋 Mensaje: {message}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return False, None


def test_api_client_direct():
    """Prueba el cliente API directamente."""
    print("\n🔍 3. PROBANDO CLIENTE API DIRECTAMENTE")
    print("-" * 50)
    
    success, mock_request = test_authentication_service()
    if not success:
        print("⚠️ Saltando prueba de API - autenticación falló")
        return False
    
    try:
        api_client = ForgeAPIClient(request=mock_request)
        
        # Test API health
        print("🏥 Probando salud de la API...")
        health = api_client.health_check()
        print(f"📊 Estado de la API: {health}")
        
        # Try to create a client
        client_data = {
            'client_code': 'CLI-API-TEST',
            'type': 'individual',
            'name': 'Cliente API Test',
            'email': 'api@test.com',
            'phone': '82363829',
            'address': 'Dirección API Test',
            'credit_limit': 1500.00
        }
        
        print("📝 Intentando crear cliente via API...")
        result = api_client.create_client(client_data)
        
        if result:
            print("✅ Cliente creado via API")
            print(f"📋 Resultado: {result}")
            return True
        else:
            print("❌ No se pudo crear cliente via API")
            return False
            
    except APIException as e:
        print(f"❌ Error de API: {e}")
        print(f"📊 Código de estado: {e.status_code}")
        print(f"📋 Datos de respuesta: {e.response_data}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False


def test_django_view_integration():
    """Prueba la integración completa con las vistas Django."""
    print("\n🔍 4. PROBANDO INTEGRACIÓN CON VISTAS DJANGO")
    print("-" * 50)
    
    setup_test_user()
    django_client = Client()
    
    # Login to Django
    login_success = django_client.login(username='debuguser', password='debugpass123')
    if not login_success:
        print("❌ No se pudo hacer login a Django")
        return False
    
    print("✅ Login a Django exitoso")
    
    # Test GET request to create form
    try:
        print("📄 Probando GET al formulario de creación...")
        response = django_client.get('/clients/create/')
        
        if response.status_code == 200:
            print("✅ Formulario de creación cargado")
            
            # Check if form is in the response
            content = response.content.decode('utf-8')
            if 'name="name"' in content and 'name="email"' in content:
                print("✅ Campos del formulario presentes")
            else:
                print("❌ Campos del formulario no encontrados")
                return False
        else:
            print(f"❌ Error al cargar formulario: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder al formulario: {e}")
        return False
    
    # Test POST request to create client
    try:
        print("📝 Probando POST para crear cliente...")
        
        client_data = {
            'client_code': 'CLI-DJANGO-TEST',
            'type': 'individual',
            'name': 'Cliente Django Test',
            'email': 'correo@gmail.com',
            'phone': '82363829',
            'address': 'Dirección Django Test',
            'credit_limit': '2000.00',
        }
        
        response = django_client.post('/clients/create/', data=client_data, follow=True)
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for success indicators
            success_indicators = [
                'Cliente Django Test' in content,
                'creado exitosamente' in content.lower(),
                'success' in content.lower(),
                '/clients/' in response.request['PATH_INFO']  # Redirected to client detail
            ]
            
            success_count = sum(success_indicators)
            print(f"📊 Indicadores de éxito: {success_count}/4")
            
            if success_count >= 2:
                print("✅ Cliente creado exitosamente via Django")
                return True
            else:
                print("⚠️ Respuesta recibida pero éxito incierto")
                
                # Check for error messages
                if 'error' in content.lower() or 'invalid' in content.lower():
                    print("❌ Errores detectados en la respuesta")
                    # Try to extract error messages
                    if 'alert-danger' in content:
                        print("🚫 Alertas de error encontradas")
                
                return False
        else:
            print(f"❌ Error en la creación: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la creación: {e}")
        return False


def test_backend_connectivity():
    """Prueba la conectividad con el backend."""
    print("\n🔍 5. PROBANDO CONECTIVIDAD CON BACKEND")
    print("-" * 50)
    
    import requests
    
    try:
        # Test basic connectivity
        base_url = "http://localhost:8000/api/v1/"
        
        print(f"🌐 Probando conectividad a: {base_url}")
        response = requests.get(base_url, timeout=5)
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code in [200, 404, 403]:  # Any response means server is running
            print("✅ Servidor backend respondiendo")
            
            # Test specific endpoints
            endpoints_to_test = [
                'auth/login/',
                'clients/',
                'dashboard/',
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    test_response = requests.get(f"{base_url}{endpoint}", timeout=3)
                    print(f"📡 {endpoint}: HTTP {test_response.status_code}")
                except Exception as e:
                    print(f"📡 {endpoint}: Error - {e}")
            
            return True
        else:
            print(f"❌ Servidor backend no responde correctamente: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor backend")
        print("💡 Asegúrate de que el servidor Django esté ejecutándose en localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False


def main():
    """Función principal de diagnóstico."""
    print("🚀 DIAGNÓSTICO COMPLETO DE CREACIÓN DE CLIENTE")
    print("=" * 60)
    print("🎯 Objetivo: Identificar por qué no se pueden crear/editar clientes")
    print("=" * 60)
    
    results = []
    
    # Run all diagnostic tests
    results.append(test_form_validation())
    results.append(test_backend_connectivity())
    
    # Skip API tests if backend is not available
    if results[-1]:  # If backend connectivity passed
        results.append(test_api_client_direct())
    else:
        print("\n⚠️ Saltando pruebas de API - backend no disponible")
        results.append(False)
    
    results.append(test_django_view_integration())
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    # Provide specific recommendations
    print("\n🔧 RECOMENDACIONES:")
    
    if not results[0]:  # Form validation failed
        print("❌ Problema con validación de formulario Django")
        print("   → Revisar frontend/forms.py")
    
    if not results[1]:  # Backend connectivity failed
        print("❌ Problema de conectividad con backend")
        print("   → Asegurar que el servidor Django esté ejecutándose")
        print("   → Verificar que el puerto 8000 esté disponible")
    
    if not results[2]:  # API client failed
        print("❌ Problema con cliente API")
        print("   → Revisar autenticación JWT")
        print("   → Verificar endpoints de la API")
    
    if not results[3]:  # Django view integration failed
        print("❌ Problema con integración de vistas Django")
        print("   → Revisar frontend/views.py")
        print("   → Verificar manejo de errores de API")
    
    if success_rate >= 75:
        print("\n🎉 SISTEMA MAYORMENTE FUNCIONAL")
        print("✅ La mayoría de componentes están trabajando correctamente")
        return 0
    else:
        print("\n⚠️ PROBLEMAS CRÍTICOS DETECTADOS")
        print("❌ Se requiere atención inmediata")
        return 1


if __name__ == '__main__':
    sys.exit(main())