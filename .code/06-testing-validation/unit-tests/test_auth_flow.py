#!/usr/bin/env python
"""
Script de prueba para verificar el flujo completo de autenticación JWT
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

import requests
import json
from datetime import datetime
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.db import SessionStore
from frontend.services.auth_service import AuthenticationService
from frontend.services.api_client import ForgeAPIClient

def get_request_with_session():
    """Crea un request con una sesión real de Django"""
    factory = RequestFactory()
    request = factory.post('/login/')
    
    # Agregar middleware de sesión
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    return request

def test_jwt_authentication():
    """Prueba el flujo completo de autenticación JWT"""
    print("🔐 Iniciando pruebas de autenticación JWT...")
    
    # 1. Probar autenticación directa con API
    print("\n1️⃣ Probando autenticación directa con API...")
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/v1/auth/login/',
            json={'username': 'admin', 'password': 'admin123'},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Autenticación exitosa")
            print(f"   - Access token: {token_data.get('access', '')[:50]}...")
            print(f"   - Refresh token: {token_data.get('refresh', '')[:50]}...")
        else:
            print(f"❌ Error en autenticación: {response.status_code}")
            print(f"   - Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    # 2. Probar servicio de autenticación del frontend
    print("\n2️⃣ Probando servicio de autenticación del frontend...")
    try:
        request = get_request_with_session()
        
        auth_service = AuthenticationService(request)
        success, message, user_data = auth_service.login('admin', 'admin123')
        
        if success:
            print(f"✅ Login del frontend exitoso")
            print(f"   - Mensaje: {message}")
            print(f"   - Usuario: {user_data.get('username', 'N/A')}")
            print(f"   - Token en sesión: {'Sí' if request.session.get('auth_token') else 'No'}")
        else:
            print(f"❌ Error en login del frontend: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error en servicio de autenticación: {e}")
        return False
    
    # 3. Probar cliente API con token
    print("\n3️⃣ Probando cliente API con token...")
    try:
        api_client = ForgeAPIClient(request=request)
        
        # Probar endpoint protegido
        clients_data = api_client.get_clients(page=1, page_size=5)
        print(f"✅ Cliente API funcionando")
        print(f"   - Clientes encontrados: {clients_data.get('count', 0)}")
        
    except Exception as e:
        print(f"❌ Error en cliente API: {e}")
        return False
    
    # 4. Probar refresh de token
    print("\n4️⃣ Probando refresh de token...")
    try:
        refresh_success = auth_service.refresh_token()
        if refresh_success:
            print(f"✅ Refresh de token exitoso")
            print(f"   - Nuevo token en sesión: {'Sí' if request.session.get('auth_token') else 'No'}")
        else:
            print(f"⚠️  Refresh de token falló (puede ser normal si el token aún es válido)")
            
    except Exception as e:
        print(f"❌ Error en refresh de token: {e}")
        return False
    
    print("\n🎉 Todas las pruebas de autenticación completadas exitosamente!")
    return True

def test_client_creation_with_auth():
    """Prueba la creación de cliente con autenticación"""
    print("\n🏗️  Probando creación de cliente con autenticación...")
    
    try:
        request = get_request_with_session()
        
        # Autenticar primero
        auth_service = AuthenticationService(request)
        success, message, user_data = auth_service.login('admin', 'admin123')
        
        if not success:
            print(f"❌ Error en autenticación: {message}")
            return False
        
        # Crear cliente usando API
        api_client = ForgeAPIClient(request=request)
        
        client_data = {
            'client_code': f'TEST{datetime.now().strftime("%H%M%S")}',
            'type': 'individual',
            'name': 'Cliente de Prueba Auth',
            'email': 'test.auth@example.com',
            'phone': '1234567890',
            'credit_limit': 5000
        }
        
        result = api_client.create_client(client_data)
        
        print(f"✅ Cliente creado exitosamente")
        print(f"   - ID: {result.get('client_id', 'N/A')}")
        print(f"   - Código: {result.get('client_code', 'N/A')}")
        print(f"   - Nombre: {result.get('name', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en creación de cliente: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando pruebas completas de autenticación y API...")
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get('http://127.0.0.1:8000/api/v1/health/', timeout=5)
        if response.status_code != 200:
            print("❌ El servidor API no está respondiendo correctamente")
            sys.exit(1)
    except:
        print("❌ No se puede conectar al servidor API. ¿Está corriendo en el puerto 8000?")
        sys.exit(1)
    
    # Ejecutar pruebas
    auth_success = test_jwt_authentication()
    client_success = test_client_creation_with_auth()
    
    if auth_success and client_success:
        print("\n🎊 ¡Todas las pruebas pasaron exitosamente!")
        print("   El sistema de autenticación JWT está funcionando correctamente.")
    else:
        print("\n💥 Algunas pruebas fallaron. Revisar los errores arriba.")
        sys.exit(1)