#!/usr/bin/env python3
"""
Script para probar la creación real de un cliente con los datos del usuario.
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


def test_client_creation_form():
    """Prueba la creación de cliente a través del formulario web."""
    print("🔍 Probando creación de cliente con datos reales...")
    
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
    
    # Create Django test client
    django_client = Client()
    
    # Login
    login_success = django_client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ No se pudo hacer login")
        return False
    
    print("✅ Login exitoso")
    
    # Test client creation form GET
    try:
        response = django_client.get('/clients/create/')
        
        if response.status_code == 200:
            print("✅ Formulario de creación cargado correctamente")
        else:
            print(f"❌ Error al cargar formulario: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder al formulario: {e}")
        return False
    
    # Test client creation form POST with user data
    client_data = {
        'client_code': 'CLI-TEST-001',
        'type': 'individual',
        'name': 'Juan Pérez García',
        'email': 'correo@gmail.com',
        'phone': '82363829',
        'address': 'Calle Principal 123, Colonia Centro',
        'credit_limit': '5000.00',
        'csrfmiddlewaretoken': 'dummy_token'  # This will be handled by Django test client
    }
    
    try:
        response = django_client.post('/clients/create/', data=client_data, follow=True)
        
        print(f"📊 Respuesta del servidor: HTTP {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check if we were redirected to client detail (success)
            if 'Cliente creado exitosamente' in content or 'Juan Pérez García' in content:
                print("✅ Cliente creado exitosamente")
                print("📋 Datos del cliente:")
                print(f"   Código: CLI-TEST-001")
                print(f"   Nombre: Juan Pérez García")
                print(f"   Email: correo@gmail.com")
                print(f"   Teléfono: 82363829")
                print(f"   Límite de crédito: $5,000.00")
                return True
            elif 'Error' in content or 'error' in content.lower():
                print("❌ Error en la creación del cliente")
                # Try to extract error messages
                if 'field-error' in content or 'alert-danger' in content:
                    print("🚫 Errores de validación detectados en la respuesta")
                return False
            else:
                print("⚠️ Respuesta inesperada del servidor")
                print("📄 Contenido parcial de la respuesta:")
                # Show first 500 characters of response for debugging
                print(content[:500] + "..." if len(content) > 500 else content)
                return False
        else:
            print(f"❌ Error del servidor: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la creación: {e}")
        return False


def test_client_list_access():
    """Prueba el acceso a la lista de clientes."""
    print("\n🔍 Probando acceso a la lista de clientes...")
    
    # Create Django test client
    django_client = Client()
    
    # Login
    django_client.login(username='testuser', password='testpass123')
    
    try:
        response = django_client.get('/clients/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for key elements
            checks = [
                ('Gestión de Clientes' in content, 'Título de la página'),
                ('Nuevo Cliente' in content, 'Botón de crear cliente'),
                ('table' in content.lower() or 'No hay clientes' in content, 'Tabla o mensaje de clientes'),
            ]
            
            passed = sum(1 for check, _ in checks if check)
            success_rate = (passed / len(checks)) * 100
            
            print(f"✅ Lista de clientes: {passed}/{len(checks)} elementos ({success_rate:.1f}%)")
            
            # Check if our test client appears in the list
            if 'Juan Pérez García' in content:
                print("✅ Cliente de prueba encontrado en la lista")
            
            return success_rate >= 75
            
        else:
            print(f"❌ Error al acceder a la lista: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder a la lista: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO CREACIÓN REAL DE CLIENTE")
    print("=" * 50)
    print("📋 Datos de prueba:")
    print("   Email: correo@gmail.com")
    print("   Teléfono: 82363829")
    print("=" * 50)
    
    results = []
    
    # Test client creation
    results.append(test_client_creation_form())
    
    # Test client list access
    results.append(test_client_list_access())
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    print("=" * 50)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("\n🎉 CREACIÓN DE CLIENTE FUNCIONANDO CORRECTAMENTE")
        print("✅ Los datos del usuario deberían ser aceptados ahora")
        print("📝 Instrucciones:")
        print("   1. Vaya a /clients/create/")
        print("   2. Use email: correo@gmail.com")
        print("   3. Use teléfono: 82363829")
        print("   4. Complete los demás campos")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS")
        print("❌ Revisar la implementación")
        return 1


if __name__ == '__main__':
    sys.exit(main())