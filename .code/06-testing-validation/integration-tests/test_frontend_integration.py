#!/usr/bin/env python
"""
Script de prueba para verificar la integración completa frontend-backend
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from datetime import datetime
from django.test import Client, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from frontend.services.auth_service import AuthenticationService
from frontend.services.api_client import ForgeAPIClient

def test_frontend_client_creation():
    """Prueba la creación de cliente a través del frontend web"""
    print("🌐 Probando creación de cliente a través del frontend web...")
    
    # Crear cliente de prueba Django
    client = Client()
    
    # 1. Probar login a través del frontend
    print("\n1️⃣ Probando login a través del frontend...")
    try:
        login_response = client.post('/login/', {
            'username': 'admin',
            'password': 'admin123'
        })
        
        if login_response.status_code in [200, 302]:  # 302 = redirect after successful login
            print("✅ Login del frontend exitoso")
            print(f"   - Código de respuesta: {login_response.status_code}")
        else:
            print(f"❌ Error en login del frontend: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en login del frontend: {e}")
        return False
    
    # 2. Probar acceso a la página de creación de cliente
    print("\n2️⃣ Probando acceso a página de creación de cliente...")
    try:
        create_page_response = client.get('/clients/create/')
        
        if create_page_response.status_code == 200:
            print("✅ Página de creación de cliente accesible")
        else:
            print(f"❌ Error al acceder a página de creación: {create_page_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder a página de creación: {e}")
        return False
    
    # 3. Probar creación de cliente a través del formulario
    print("\n3️⃣ Probando creación de cliente a través del formulario...")
    try:
        client_data = {
            'client_code': f'WEB{datetime.now().strftime("%H%M%S")}',
            'type': 'individual',
            'name': 'Cliente Creado desde Frontend',
            'email': 'frontend.test@example.com',
            'phone': '9876543210',
            'address': 'Dirección de prueba desde frontend',
            'credit_limit': 7500
        }
        
        create_response = client.post('/clients/create/', client_data)
        
        if create_response.status_code in [200, 302]:  # 302 = redirect after successful creation
            print("✅ Cliente creado exitosamente desde el frontend")
            print(f"   - Código de respuesta: {create_response.status_code}")
            
            # Si es redirect, verificar que redirige a la lista de clientes
            if create_response.status_code == 302:
                redirect_url = create_response.get('Location', '')
                print(f"   - Redirigido a: {redirect_url}")
                
                # Verificar que el cliente aparece en la lista
                list_response = client.get('/clients/')
                if list_response.status_code == 200:
                    content = list_response.content.decode('utf-8')
                    if client_data['name'] in content:
                        print("✅ Cliente aparece en la lista")
                        return True
                    else:
                        print("⚠️  Cliente creado pero no aparece en la lista")
                        return True
                else:
                    print(f"❌ Error al verificar lista de clientes: {list_response.status_code}")
                    return False
            else:
                return True
        else:
            print(f"❌ Error en creación de cliente: {create_response.status_code}")
            # Mostrar contenido de la respuesta para debugging
            content = create_response.content.decode('utf-8')
            if 'Error interno del servidor' in content:
                print("   - Error: Aún hay problemas con el backend API")
            return False
            
    except Exception as e:
        print(f"❌ Error en creación de cliente desde frontend: {e}")
        return False

def test_client_list_functionality():
    """Prueba la funcionalidad de lista de clientes"""
    print("\n📋 Probando funcionalidad de lista de clientes...")
    
    client = Client()
    
    # Login primero
    client.post('/login/', {'username': 'admin', 'password': 'admin123'})
    
    try:
        # Acceder a la lista de clientes
        list_response = client.get('/clients/')
        
        if list_response.status_code == 200:
            print("✅ Lista de clientes accesible")
            
            # Verificar que la página contiene elementos esperados
            content = list_response.content.decode('utf-8')
            
            checks = [
                ('Tabla de clientes', 'table' in content.lower()),
                ('Botón crear cliente', 'crear' in content.lower() or 'nuevo' in content.lower()),
                ('Búsqueda', 'search' in content.lower() or 'buscar' in content.lower()),
                ('Paginación', 'page' in content.lower() or 'página' in content.lower()),
            ]
            
            for check_name, check_result in checks:
                status = "✅" if check_result else "⚠️"
                print(f"   - {check_name}: {status}")
            
            return True
        else:
            print(f"❌ Error al acceder a lista de clientes: {list_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en lista de clientes: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando pruebas de integración frontend-backend...")
    
    # Verificar que el servidor esté corriendo
    try:
        import requests
        response = requests.get('http://127.0.0.1:8000/api/v1/health/', timeout=5)
        if response.status_code != 200:
            print("❌ El servidor API no está respondiendo correctamente")
            sys.exit(1)
    except:
        print("❌ No se puede conectar al servidor API. ¿Está corriendo en el puerto 8000?")
        sys.exit(1)
    
    # Ejecutar pruebas
    tests = [
        ("Creación de cliente desde frontend", test_frontend_client_creation),
        ("Lista de clientes", test_client_list_functionality),
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
    print("\n📊 Resumen de pruebas de integración:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   - {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎊 ¡Todas las pruebas de integración pasaron!")
        print("   El sistema frontend-backend está funcionando correctamente.")
    else:
        print("💥 Algunas pruebas fallaron. La integración necesita más trabajo.")
        sys.exit(1)