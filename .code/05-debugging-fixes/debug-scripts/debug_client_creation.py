#!/usr/bin/env python
"""
Script simple para diagnosticar la creación de clientes
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from frontend.forms.client_forms import ClientForm

def test_form():
    """Probar el formulario"""
    print("=== PROBANDO FORMULARIO ===")
    
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
        print("✅ Formulario válido")
        print("Datos limpios:")
        for field, value in form.cleaned_data.items():
            print(f"  {field}: {value}")

def check_users():
    """Verificar usuarios en el sistema"""
    print("\n=== VERIFICANDO USUARIOS ===")
    
    try:
        from core.models import TechnicianUser
        users = TechnicianUser.objects.all()
        print(f"Total de usuarios: {users.count()}")
        
        if users.exists():
            for user in users[:3]:  # Mostrar primeros 3
                print(f"  - {user.username} ({user.email})")
        else:
            print("⚠️  No hay usuarios en el sistema")
            
    except Exception as e:
        print(f"Error al verificar usuarios: {e}")

def check_api_endpoints():
    """Verificar endpoints del API"""
    print("\n=== VERIFICANDO ENDPOINTS ===")
    
    import requests
    
    base_url = "http://127.0.0.1:8000/api/v1/"
    
    endpoints = [
        "health/",
        "clients/",
        "auth/login/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"  {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"  {endpoint}: ERROR - {e}")

if __name__ == '__main__':
    test_form()
    check_users()
    check_api_endpoints()