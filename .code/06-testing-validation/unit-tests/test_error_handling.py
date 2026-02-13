#!/usr/bin/env python
"""
Script de prueba para verificar el manejo mejorado de errores en el cliente API
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

import requests
from datetime import datetime
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from frontend.services.auth_service import AuthenticationService
from frontend.services.api_client import ForgeAPIClient, APIException

def get_request_with_session():
    """Crea un request con una sesión real de Django"""
    factory = RequestFactory()
    request = factory.post('/test/')
    
    # Agregar middleware de sesión
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    return request

def test_api_availability():
    """Prueba la verificación de disponibilidad de la API"""
    print("🔍 Probando verificación de disponibilidad de la API...")
    
    request = get_request_with_session()
    api_client = ForgeAPIClient(request=request)
    
    # Probar health check
    is_available = api_client.is_api_available()
    print(f"   - API disponible: {'✅ Sí' if is_available else '❌ No'}")
    
    # Probar health check simple
    health_ok = api_client.health_check()
    print(f"   - Health check: {'✅ OK' if health_ok else '❌ Fallo'}")
    
    return is_available and health_ok

def test_authentication_error_handling():
    """Prueba el manejo de errores de autenticación"""
    print("\n🔐 Probando manejo de errores de autenticación...")
    
    request = get_request_with_session()
    api_client = ForgeAPIClient(request=request)
    
    try:
        # Intentar acceder a endpoint protegido sin autenticación
        clients_data = api_client.get_clients()
        print("❌ Error: Debería haber fallado sin autenticación")
        return False
    except APIException as e:
        if e.status_code == 401:
            print(f"✅ Error de autenticación manejado correctamente: {e.message}")
            return True
        else:
            print(f"❌ Error inesperado: {e.status_code} - {e.message}")
            return False
    except Exception as e:
        print(f"❌ Error no manejado: {e}")
        return False

def test_validation_error_handling():
    """Prueba el manejo de errores de validación"""
    print("\n📝 Probando manejo de errores de validación...")
    
    request = get_request_with_session()
    
    # Autenticar primero
    auth_service = AuthenticationService(request)
    success, message, user_data = auth_service.login('admin', 'admin123')
    
    if not success:
        print(f"❌ Error en autenticación: {message}")
        return False
    
    api_client = ForgeAPIClient(request=request)
    
    try:
        # Intentar crear cliente con datos inválidos
        invalid_client_data = {
            'client_code': '',  # Código vacío (inválido)
            'type': 'invalid_type',  # Tipo inválido
            'name': '',  # Nombre vacío (inválido)
            'email': 'invalid-email',  # Email inválido
            'credit_limit': -1000  # Límite negativo (inválido)
        }
        
        result = api_client.create_client(invalid_client_data)
        print("❌ Error: Debería haber fallado con datos inválidos")
        return False
        
    except APIException as e:
        if e.status_code == 400:
            print(f"✅ Error de validación manejado correctamente")
            print(f"   - Código de estado: {e.status_code}")
            print(f"   - Mensaje: {e.message}")
            
            # Verificar que tenemos detalles de los errores
            if e.response_data:
                print(f"   - Detalles de errores disponibles: ✅")
                return True
            else:
                print(f"   - Sin detalles de errores: ⚠️")
                return True
        else:
            print(f"❌ Error inesperado: {e.status_code} - {e.message}")
            return False
    except Exception as e:
        print(f"❌ Error no manejado: {e}")
        return False

def test_network_error_simulation():
    """Simula errores de red para probar el manejo de reintentos"""
    print("\n🌐 Probando manejo de errores de red...")
    
    request = get_request_with_session()
    
    # Crear cliente API con URL inválida para simular error de red
    api_client = ForgeAPIClient(base_url="http://invalid-host:9999/api/v1/", request=request)
    
    try:
        # Intentar hacer una petición que fallará por error de red
        clients_data = api_client.get_clients()
        print("❌ Error: Debería haber fallado por error de red")
        return False
        
    except APIException as e:
        if "Network error" in e.message:
            print(f"✅ Error de red manejado correctamente: {e.message}")
            return True
        else:
            print(f"❌ Error inesperado: {e.message}")
            return False
    except Exception as e:
        print(f"❌ Error no manejado: {e}")
        return False

def test_successful_operation():
    """Prueba una operación exitosa para verificar que todo funciona normalmente"""
    print("\n✨ Probando operación exitosa...")
    
    request = get_request_with_session()
    
    # Autenticar
    auth_service = AuthenticationService(request)
    success, message, user_data = auth_service.login('admin', 'admin123')
    
    if not success:
        print(f"❌ Error en autenticación: {message}")
        return False
    
    api_client = ForgeAPIClient(request=request)
    
    try:
        # Obtener lista de clientes (operación que debería funcionar)
        clients_data = api_client.get_clients(page=1, page_size=5)
        
        print(f"✅ Operación exitosa")
        print(f"   - Clientes encontrados: {clients_data.get('count', 0)}")
        print(f"   - Respuesta válida: {'✅' if 'results' in clients_data else '❌'}")
        
        return True
        
    except APIException as e:
        print(f"❌ Error inesperado en operación exitosa: {e.message}")
        return False
    except Exception as e:
        print(f"❌ Error no manejado: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando pruebas de manejo de errores...")
    
    # Ejecutar todas las pruebas
    tests = [
        ("Disponibilidad de API", test_api_availability),
        ("Errores de autenticación", test_authentication_error_handling),
        ("Errores de validación", test_validation_error_handling),
        ("Errores de red", test_network_error_simulation),
        ("Operación exitosa", test_successful_operation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en prueba '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n📊 Resumen de pruebas:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   - {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎊 ¡Todas las pruebas de manejo de errores pasaron!")
    else:
        print("💥 Algunas pruebas fallaron. El manejo de errores necesita mejoras.")
        sys.exit(1)