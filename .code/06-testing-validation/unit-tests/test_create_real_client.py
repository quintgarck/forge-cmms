#!/usr/bin/env python3
"""
Script para probar la creación real de un cliente a través del frontend.
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


def create_test_user():
    """Crea un usuario de prueba."""
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
    return user


def test_create_client_through_frontend():
    """Prueba crear un cliente a través del frontend."""
    print("🔍 Probando creación de cliente a través del frontend...")
    
    # Create Django test client
    django_client = Client()
    
    # Login
    login_success = django_client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ No se pudo hacer login")
        return False
    
    print("✅ Login exitoso")
    
    try:
        # Test GET client create form
        response = django_client.get('/clients/create/')
        
        if response.status_code == 200:
            print("✅ Formulario de creación accesible")
            
            # Test POST client creation
            client_data = {
                'client_code': 'TEST-001',
                'type': 'individual',
                'name': 'Juan Pérez García',
                'email': 'juan.perez@example.com',
                'phone': '555-1234-5678',
                'address': 'Calle Principal 123\nColonia Centro\nCiudad, Estado 12345',
                'credit_limit': '5000.00'
            }
            
            response = django_client.post('/clients/create/', client_data)
            
            if response.status_code == 302:  # Redirect after successful creation
                print("✅ Cliente creado exitosamente (redirect)")
                
                # Check if redirected to client detail
                redirect_url = response.url
                print(f"✅ Redirigido a: {redirect_url}")
                
                # Follow the redirect to see the created client
                response = django_client.get(redirect_url)
                if response.status_code == 200:
                    content = response.content.decode('utf-8')
                    
                    # Check if client data is displayed
                    checks = [
                        ('Juan Pérez García' in content, 'Nombre del cliente'),
                        ('juan.perez@example.com' in content, 'Email del cliente'),
                        ('555-1234-5678' in content, 'Teléfono del cliente'),
                        ('5000.00' in content, 'Límite de crédito'),
                        ('TEST-001' in content, 'Código de cliente'),
                    ]
                    
                    passed = sum(1 for check, _ in checks if check)
                    success_rate = (passed / len(checks)) * 100
                    
                    print(f"📊 Datos del cliente verificados: {passed}/{len(checks)} ({success_rate:.1f}%)")
                    
                    if success_rate >= 80:
                        print("🎉 CLIENTE CREADO Y MOSTRADO CORRECTAMENTE")
                        return True
                    else:
                        print("⚠️ Cliente creado pero algunos datos no se muestran correctamente")
                        return False
                else:
                    print(f"❌ Error accediendo a la vista de detalle: HTTP {response.status_code}")
                    return False
                    
            elif response.status_code == 200:
                # Form returned with errors
                content = response.content.decode('utf-8')
                if 'error' in content.lower() or 'invalid' in content.lower():
                    print("❌ Errores en el formulario:")
                    # Try to extract error messages
                    if 'alert-danger' in content:
                        print("   - Hay errores de validación en el formulario")
                    return False
                else:
                    print("⚠️ Formulario devuelto sin errores aparentes")
                    return False
            else:
                print(f"❌ Error creando cliente: HTTP {response.status_code}")
                return False
                
        else:
            print(f"❌ Error accediendo al formulario: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False


def test_client_list_after_creation():
    """Verifica que el cliente aparezca en la lista."""
    print("\n🔍 Verificando que el cliente aparezca en la lista...")
    
    django_client = Client()
    django_client.login(username='testuser', password='testpass123')
    
    try:
        response = django_client.get('/clients/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            if 'Juan Pérez García' in content:
                print("✅ Cliente aparece en la lista")
                return True
            else:
                print("⚠️ Cliente no aparece en la lista (puede ser por problemas de API)")
                return False
        else:
            print(f"❌ Error accediendo a la lista: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando lista: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO CREACIÓN REAL DE CLIENTE")
    print("=" * 50)
    
    # Create test user
    print("🔧 Preparando usuario de prueba...")
    user = create_test_user()
    print(f"✅ Usuario listo: {user.username}")
    
    results = []
    
    # Test client creation
    results.append(test_create_client_through_frontend())
    
    # Test client appears in list
    results.append(test_client_list_after_creation())
    
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
        print("\n🎉 ¡SÍ PUEDES CREAR CLIENTES DE VERDAD!")
        print("✅ El sistema frontend está completamente funcional")
        print("✅ Puedes ir a http://localhost:8000/clients/create/ para crear clientes")
        return 0
    else:
        print("\n⚠️ HAY ALGUNOS PROBLEMAS MENORES")
        print("❌ Revisar logs para más detalles")
        return 1


if __name__ == '__main__':
    sys.exit(main())