#!/usr/bin/env python
"""
Script de diagnóstico para probar la creación de clientes
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from frontend.services.api_client import ForgeAPIClient, APIException
from frontend.forms.client_forms import ClientForm

def test_client_form():
    """Probar el formulario de cliente"""
    print("=== PROBANDO FORMULARIO DE CLIENTE ===")
    
    # Datos de prueba
    form_data = {
        'client_code': 'TEST-001',
        'type': 'individual',
        'name': 'Cliente de Prueba',
        'email': 'test@example.com',
        'phone': '1234567890',
        'address': 'Dirección de prueba',
        'credit_limit': '1000.00'
    }
    
    form = ClientForm(data=form_data)
    
    print(f"Formulario válido: {form.is_valid()}")
    
    if not form.is_valid():
        print("Errores del formulario:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    else:
        print("Datos limpios del formulario:")
        for field, value in form.cleaned_data.items():
            print(f"  {field}: {value}")
    
    return form.is_valid(), form.cleaned_data if form.is_valid() else None

def test_api_client():
    """Probar el cliente API"""
    print("\n=== PROBANDO CLIENTE API ===")
    
    # Crear request simulado
    factory = RequestFactory()
    request = factory.post('/clients/create/')
    request.user = AnonymousUser()
    
    # Agregar sesión
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Crear cliente API
    api_client = ForgeAPIClient(request=request)
    
    print(f"Base URL: {api_client.base_url}")
    print(f"Headers: {dict(api_client.session.headers)}")
    
    # Probar endpoint de salud
    try:
        health_response = api_client.get('health/')
        print(f"Health check: {health_response}")
    except APIException as e:
        print(f"Error en health check: {e.message} (Status: {e.status_code})")
    
    # Probar creación de cliente sin autenticación
    client_data = {
        'client_code': 'TEST-002',
        'type': 'individual',
        'name': 'Cliente API Test',
        'email': 'apitest@example.com',
        'phone': '9876543210',
        'address': 'API Test Address',
        'credit_limit': 500.00
    }
    
    try:
        result = api_client.create_client(client_data)
        print(f"Cliente creado exitosamente: {result}")
        return True
    except APIException as e:
        print(f"Error al crear cliente: {e.message}")
        print(f"Status code: {e.status_code}")
        print(f"Response data: {e.response_data}")
        return False

def test_authentication():
    """Probar autenticación"""
    print("\n=== PROBANDO AUTENTICACIÓN ===")
    
    # Crear request simulado
    factory = RequestFactory()
    request = factory.post('/auth/login/')
    request.user = AnonymousUser()
    
    # Agregar sesión
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Crear cliente API
    api_client = ForgeAPIClient(request=request)
    
    # Intentar login con credenciales de prueba
    try:
        # Primero verificar si hay usuarios en el sistema
        from core.models import TechnicianUser
        users = TechnicianUser.objects.all()
        print(f"Usuarios en el sistema: {users.count()}")
        
        if users.exists():
            user = users.first()
            print(f"Primer usuario: {user.username}")
            
            # Intentar login
            login_data = {
                'username': user.username,
                'password': 'admin123'  # Contraseña por defecto
            }
            
            login_response = api_client.post('auth/login/', data=login_data)
            print(f"Login response: {login_response}")
            
            # Guardar token en sesión
            if 'access' in login_response:
                request.session['auth_token'] = login_response['access']
                request.session['refresh_token'] = login_response.get('refresh')
                request.session.save()
                
                print("Token guardado en sesión")
                
                # Probar creación de cliente con autenticación
                client_data = {
                    'client_code': 'TEST-AUTH-001',
                    'type': 'individual',
                    'name': 'Cliente Autenticado',
                    'email': 'auth@example.com',
                    'phone': '5555555555',
                    'address': 'Auth Test Address',
                    'credit_limit': 1500.00
                }
                
                result = api_client.create_client(client_data)
                print(f"Cliente creado con autenticación: {result}")
                return True
        else:
            print("No hay usuarios en el sistema")
            return False
            
    except APIException as e:
        print(f"Error en autenticación: {e.message}")
        print(f"Status code: {e.status_code}")
        print(f"Response data: {e.response_data}")
        return False

def main():
    """Función principal"""
    print("DIAGNÓSTICO DE CREACIÓN DE CLIENTES")
    print("=" * 50)
    
    # Probar formulario
    form_valid, form_data = test_client_form()
    
    # Probar API client
    api_success = test_api_client()
    
    # Probar autenticación
    auth_success = test_authentication()
    
    print("\n=== RESUMEN ===")
    print(f"Formulario válido: {'✓' if form_valid else '✗'}")
    print(f"API client funcional: {'✓' if api_success else '✗'}")
    print(f"Autenticación funcional: {'✓' if auth_success else '✗'}")
    
    if not form_valid:
        print("\n⚠️  El problema está en el formulario")
    elif not auth_success:
        print("\n⚠️  El problema está en la autenticación")
    elif not api_success:
        print("\n⚠️  El problema está en el API client")
    else:
        print("\n✅ Todo funciona correctamente")

if __name__ == '__main__':
    main()