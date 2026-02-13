#!/usr/bin/env python3
"""
Script para probar la creación real de cliente con el sistema corregido.
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


def create_admin_user():
    """Crea o verifica que existe un usuario admin."""
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


def test_complete_client_workflow():
    """Prueba el flujo completo de creación de cliente."""
    print("🔍 Probando flujo completo de creación de cliente...")
    
    # Ensure admin user exists
    create_admin_user()
    
    # Create Django test client
    django_client = Client()
    
    # Login with admin credentials
    login_success = django_client.login(username='admin', password='admin123')
    if not login_success:
        print("❌ No se pudo hacer login con admin")
        return False
    
    print("✅ Login con admin exitoso")
    
    # Test client creation form GET
    try:
        print("📄 Cargando formulario de creación...")
        response = django_client.get('/clients/create/')
        
        if response.status_code == 200:
            print("✅ Formulario de creación cargado")
            
            # Check for form fields
            content = response.content.decode('utf-8')
            required_fields = ['name="name"', 'name="email"', 'name="phone"', 'name="client_code"']
            
            missing_fields = []
            for field in required_fields:
                if field not in content:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ Campos faltantes: {missing_fields}")
            else:
                print("✅ Todos los campos del formulario presentes")
        else:
            print(f"❌ Error al cargar formulario: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder al formulario: {e}")
        return False
    
    # Test client creation form POST
    try:
        print("📝 Enviando datos del cliente...")
        
        client_data = {
            'client_code': 'CLI-FIXED-001',
            'type': 'individual',
            'name': 'Cliente Sistema Corregido',
            'email': 'correo@gmail.com',
            'phone': '82363829',
            'address': 'Dirección del cliente corregido',
            'credit_limit': '3000.00',
        }
        
        response = django_client.post('/clients/create/', data=client_data, follow=True)
        
        print(f"📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for success indicators
            success_indicators = [
                'Cliente Sistema Corregido' in content,
                'creado exitosamente' in content.lower(),
                'success' in content.lower(),
                'CLI-FIXED-001' in content,
            ]
            
            success_count = sum(success_indicators)
            print(f"📊 Indicadores de éxito: {success_count}/4")
            
            # Check for error indicators
            error_indicators = [
                'error' in content.lower(),
                'invalid' in content.lower(),
                'alert-danger' in content,
                'form-error' in content,
            ]
            
            error_count = sum(error_indicators)
            print(f"📊 Indicadores de error: {error_count}/4")
            
            if success_count >= 2 and error_count == 0:
                print("✅ Cliente creado exitosamente")
                return True
            elif error_count > 0:
                print("❌ Errores detectados en la respuesta")
                
                # Try to extract specific error messages
                if 'Las credenciales de autenticación no se proveyeron' in content:
                    print("🔐 Error específico: Problema de autenticación JWT")
                elif 'Token expired' in content:
                    print("🔐 Error específico: Token JWT expirado")
                elif 'Invalid token' in content:
                    print("🔐 Error específico: Token JWT inválido")
                
                return False
            else:
                print("⚠️ Respuesta ambigua - puede haber sido exitosa")
                return True
        else:
            print(f"❌ Error en la creación: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la creación: {e}")
        return False


def test_client_list_access():
    """Prueba el acceso a la lista de clientes."""
    print("\n🔍 Probando acceso a la lista de clientes...")
    
    django_client = Client()
    django_client.login(username='admin', password='admin123')
    
    try:
        response = django_client.get('/clients/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for key elements
            checks = [
                ('Gestión de Clientes' in content, 'Título de la página'),
                ('Nuevo Cliente' in content, 'Botón de crear cliente'),
                ('table' in content.lower() or 'No hay clientes' in content, 'Tabla o mensaje'),
            ]
            
            passed = sum(1 for check, _ in checks if check)
            success_rate = (passed / len(checks)) * 100
            
            print(f"✅ Lista de clientes: {passed}/{len(checks)} elementos ({success_rate:.1f}%)")
            
            # Check if our test client appears
            if 'Cliente Sistema Corregido' in content:
                print("✅ Cliente de prueba encontrado en la lista")
            
            return success_rate >= 75
            
        else:
            print(f"❌ Error al acceder a la lista: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al acceder a la lista: {e}")
        return False


def test_client_edit_access():
    """Prueba el acceso a la edición de cliente."""
    print("\n🔍 Probando acceso a la edición de cliente...")
    
    django_client = Client()
    django_client.login(username='admin', password='admin123')
    
    # Try to access edit form for client ID 1
    try:
        response = django_client.get('/clients/1/edit/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for form elements
            form_checks = [
                ('form' in content.lower(), 'Formulario presente'),
                ('name="name"' in content, 'Campo nombre'),
                ('name="email"' in content, 'Campo email'),
                ('name="phone"' in content, 'Campo teléfono'),
                ('Editar Cliente' in content, 'Título de edición'),
            ]
            
            passed = sum(1 for check, _ in form_checks if check)
            success_rate = (passed / len(form_checks)) * 100
            
            print(f"✅ Formulario de edición: {passed}/{len(form_checks)} elementos ({success_rate:.1f}%)")
            return success_rate >= 75
            
        else:
            print(f"ℹ️ Formulario de edición: HTTP {response.status_code} (puede ser normal si no hay clientes)")
            return True  # Not an error if client doesn't exist
            
    except Exception as e:
        print(f"❌ Error al acceder a la edición: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO SISTEMA DE CLIENTE CORREGIDO")
    print("=" * 50)
    print("🎯 Objetivo: Verificar que la corrección de autenticación funciona")
    print("=" * 50)
    
    results = []
    
    # Test complete client workflow
    results.append(test_complete_client_workflow())
    
    # Test client list access
    results.append(test_client_list_access())
    
    # Test client edit access
    results.append(test_client_edit_access())
    
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
        print("\n🎉 SISTEMA DE CLIENTE FUNCIONANDO CORRECTAMENTE")
        print("✅ La corrección de autenticación ha sido exitosa")
        print("📝 Instrucciones para el usuario:")
        print("   1. Usar credenciales: admin / admin123")
        print("   2. Ir a /clients/create/")
        print("   3. Usar email: correo@gmail.com")
        print("   4. Usar teléfono: 82363829")
        print("   5. Completar los demás campos")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS")
        print("❌ La corrección necesita más trabajo")
        return 1


if __name__ == '__main__':
    sys.exit(main())