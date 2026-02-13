#!/usr/bin/env python3
"""
Script para probar la funcionalidad de edición de cliente.
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


def test_client_detail_edit_button():
    """Prueba que el botón de editar esté presente en la vista de detalle."""
    print("🔍 Probando botón de editar en vista de detalle...")
    
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
    
    # Test client detail view (using a test client ID)
    try:
        # Try with a few different client IDs to find one that exists
        test_client_ids = [1, 2, 3, 999]  # 999 should show "not found" gracefully
        
        for client_id in test_client_ids:
            response = django_client.get(f'/clients/{client_id}/')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Check if this is a valid client detail page (not "not found")
                if 'Cliente No Encontrado' not in content and 'client' in content.lower():
                    print(f"✅ Vista de detalle cargada para cliente ID {client_id}")
                    
                    # Check for edit button
                    edit_checks = [
                        ('btn btn-primary' in content and 'Editar' in content, 'Botón de editar presente'),
                        (f'/clients/{client_id}/edit/' in content, 'URL de edición correcta'),
                        ('bi-pencil' in content, 'Icono de editar presente'),
                    ]
                    
                    passed = 0
                    for check, description in edit_checks:
                        if check:
                            print(f"✅ {description}")
                            passed += 1
                        else:
                            print(f"❌ {description}")
                    
                    success_rate = (passed / len(edit_checks)) * 100
                    print(f"📊 Elementos de edición: {passed}/{len(edit_checks)} ({success_rate:.1f}%)")
                    
                    return success_rate >= 75
                
                elif 'Cliente No Encontrado' in content:
                    print(f"ℹ️ Cliente ID {client_id} no encontrado (esperado)")
                    
                    # Even for "not found", check that the page structure is correct
                    structure_checks = [
                        ('ForgeDB' in content, 'Título de la aplicación'),
                        ('Volver a la Lista' in content, 'Enlace de regreso'),
                        ('bootstrap' in content.lower(), 'Bootstrap CSS'),
                    ]
                    
                    passed = sum(1 for check, _ in structure_checks if check)
                    if passed >= 2:
                        print("✅ Página 'no encontrado' bien estructurada")
                        continue  # Try next client ID
                    
        print("⚠️ No se encontró ningún cliente existente para probar")
        return False
        
    except Exception as e:
        print(f"❌ Error al acceder a la vista de detalle: {e}")
        return False


def test_client_edit_form_access():
    """Prueba el acceso directo al formulario de edición."""
    print("\n🔍 Probando acceso al formulario de edición...")
    
    # Create Django test client
    django_client = Client()
    
    # Login
    django_client.login(username='testuser', password='testpass123')
    
    # Test edit form access
    try:
        # Try with a few different client IDs
        test_client_ids = [1, 2, 3]
        
        for client_id in test_client_ids:
            response = django_client.get(f'/clients/{client_id}/edit/')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Check for form elements
                form_checks = [
                    ('form' in content.lower(), 'Formulario presente'),
                    ('name="name"' in content, 'Campo nombre'),
                    ('name="email"' in content, 'Campo email'),
                    ('name="phone"' in content, 'Campo teléfono'),
                    ('Editar Cliente' in content or 'Actualizar' in content, 'Título de edición'),
                    ('btn' in content and ('Guardar' in content or 'Actualizar' in content), 'Botón de guardar'),
                ]
                
                passed = sum(1 for check, _ in form_checks if check)
                success_rate = (passed / len(form_checks)) * 100
                
                print(f"✅ Formulario de edición cargado para cliente ID {client_id}")
                print(f"📊 Elementos del formulario: {passed}/{len(form_checks)} ({success_rate:.1f}%)")
                
                return success_rate >= 75
        
        print("⚠️ No se pudo acceder a ningún formulario de edición")
        return False
        
    except Exception as e:
        print(f"❌ Error al acceder al formulario de edición: {e}")
        return False


def test_navigation_flow():
    """Prueba el flujo de navegación completo."""
    print("\n🔍 Probando flujo de navegación...")
    
    # Create Django test client
    django_client = Client()
    
    # Login
    django_client.login(username='testuser', password='testpass123')
    
    try:
        # 1. Access client list
        response = django_client.get('/clients/')
        if response.status_code != 200:
            print("❌ No se pudo acceder a la lista de clientes")
            return False
        
        print("✅ Lista de clientes accesible")
        
        # 2. Access client creation form
        response = django_client.get('/clients/create/')
        if response.status_code != 200:
            print("❌ No se pudo acceder al formulario de creación")
            return False
        
        print("✅ Formulario de creación accesible")
        
        # 3. Check that URLs are properly configured
        url_checks = [
            ('/clients/', 'Lista de clientes'),
            ('/clients/create/', 'Crear cliente'),
            ('/clients/1/', 'Detalle de cliente'),
            ('/clients/1/edit/', 'Editar cliente'),
        ]
        
        accessible_urls = 0
        for url, description in url_checks:
            try:
                response = django_client.get(url)
                if response.status_code in [200, 404]:  # 404 is OK for non-existent clients
                    print(f"✅ {description}: {url}")
                    accessible_urls += 1
                else:
                    print(f"❌ {description}: {url} - HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {description}: {url} - Error: {e}")
        
        success_rate = (accessible_urls / len(url_checks)) * 100
        print(f"📊 URLs accesibles: {accessible_urls}/{len(url_checks)} ({success_rate:.1f}%)")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"❌ Error en el flujo de navegación: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO FUNCIONALIDAD DE EDICIÓN DE CLIENTE")
    print("=" * 55)
    
    results = []
    
    # Test edit button in detail view
    results.append(test_client_detail_edit_button())
    
    # Test edit form access
    results.append(test_client_edit_form_access())
    
    # Test navigation flow
    results.append(test_navigation_flow())
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 55)
    print("📊 RESUMEN")
    print("=" * 55)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("\n🎉 FUNCIONALIDAD DE EDICIÓN DISPONIBLE")
        print("✅ El botón de editar debería estar visible")
        print("📝 Instrucciones:")
        print("   1. Vaya a la lista de clientes: /clients/")
        print("   2. Haga clic en un cliente para ver detalles")
        print("   3. Busque el botón 'Editar' en la parte superior derecha")
        print("   4. O acceda directamente: /clients/[ID]/edit/")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS EN LA EDICIÓN")
        print("❌ Revisar la implementación de edición")
        return 1


if __name__ == '__main__':
    sys.exit(main())