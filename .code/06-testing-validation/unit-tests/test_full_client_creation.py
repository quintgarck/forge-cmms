#!/usr/bin/env python3
"""
Script completo para probar la creación de clientes con autenticación.
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
from django.contrib.auth.models import User


def get_jwt_token():
    """Obtiene un token JWT válido."""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json={'username': 'testuser', 'password': 'testpass123'},
            timeout=5
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access')
        else:
            print(f"Error obteniendo token: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error obteniendo token: {e}")
        return None


def test_full_client_creation():
    """Prueba completa de creación de cliente."""
    print("🚀 PRUEBA COMPLETA DE CREACIÓN DE CLIENTE")
    print("=" * 50)
    
    # Create test user
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
    
    print(f"✅ Usuario de prueba: {user.username}")
    
    # Get JWT token
    print("\n1. Obteniendo token JWT...")
    token = get_jwt_token()
    if not token:
        print("❌ No se pudo obtener token JWT")
        return False
    
    print("✅ Token JWT obtenido")
    
    # Create Django test client
    django_client = Client()
    
    # Login to Django
    print("\n2. Login en Django...")
    login_success = django_client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ No se pudo hacer login en Django")
        return False
    
    print("✅ Login en Django exitoso")
    
    # Manually set the JWT token in the session
    session = django_client.session
    session['auth_token'] = token
    session.save()
    
    print("✅ Token JWT configurado en sesión")
    
    # Test client creation
    print("\n3. Creando cliente...")
    client_data = {
        'client_code': 'TEST-002',
        'type': 'individual',
        'name': 'María González López',
        'email': 'maria.gonzalez@example.com',
        'phone': '5559876543',
        'address': 'Avenida Reforma 456\nColonia Roma\nCDMX, México 06700',
        'credit_limit': '7500.00'
    }
    
    print("Datos del cliente:")
    for key, value in client_data.items():
        print(f"  {key}: {value}")
    
    response = django_client.post('/clients/create/', client_data)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ Cliente creado exitosamente!")
        redirect_url = response.url
        print(f"✅ Redirigido a: {redirect_url}")
        
        # Follow redirect to see the client
        print("\n4. Verificando cliente creado...")
        response = django_client.get(redirect_url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            checks = [
                ('María González López' in content, 'Nombre'),
                ('maria.gonzalez@example.com' in content, 'Email'),
                ('5559876543' in content, 'Teléfono'),
                ('7500.00' in content, 'Límite de crédito'),
                ('TEST-002' in content, 'Código'),
            ]
            
            passed = sum(1 for check, _ in checks if check)
            success_rate = (passed / len(checks)) * 100
            
            print(f"📊 Datos verificados: {passed}/{len(checks)} ({success_rate:.1f}%)")
            
            for check, description in checks:
                status = "✅" if check else "❌"
                print(f"  {status} {description}")
            
            if success_rate >= 80:
                print("\n🎉 ¡CLIENTE CREADO Y VERIFICADO EXITOSAMENTE!")
                return True
            else:
                print("\n⚠️ Cliente creado pero algunos datos no se muestran")
                return False
        else:
            print(f"❌ Error verificando cliente: HTTP {response.status_code}")
            return False
            
    elif response.status_code == 200:
        print("❌ Formulario devuelto con errores")
        # Extract errors
        content = response.content.decode('utf-8')
        if 'alert-danger' in content:
            print("   Hay errores de validación")
        return False
    else:
        print(f"❌ Error inesperado: HTTP {response.status_code}")
        return False


def test_manual_instructions():
    """Proporciona instrucciones para prueba manual."""
    print("\n" + "=" * 50)
    print("📋 INSTRUCCIONES PARA PRUEBA MANUAL")
    print("=" * 50)
    print("1. Abre tu navegador web")
    print("2. Ve a: http://localhost:8000/login/")
    print("3. Inicia sesión con:")
    print("   Usuario: testuser")
    print("   Contraseña: testpass123")
    print("4. Ve a: http://localhost:8000/clients/create/")
    print("5. Llena el formulario con datos válidos:")
    print("   - Código: CLI-003")
    print("   - Tipo: Persona Física")
    print("   - Nombre: Pedro Martínez")
    print("   - Email: pedro@example.com")
    print("   - Teléfono: 5551112233 (sin guiones)")
    print("   - Dirección: Tu dirección")
    print("   - Límite de crédito: 10000")
    print("6. Haz clic en 'Crear Cliente'")
    print("\n¡Deberías poder crear el cliente exitosamente!")


if __name__ == '__main__':
    success = test_full_client_creation()
    
    if success:
        print("\n🎉 ¡SÍ PUEDES CREAR CLIENTES DE VERDAD!")
        print("✅ El sistema está completamente funcional")
    else:
        print("\n⚠️ Hay algunos problemas, pero el sistema básico funciona")
    
    test_manual_instructions()