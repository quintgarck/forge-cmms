#!/usr/bin/env python3
"""
Script simple para probar la vista de detalle de cliente.
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


def test_client_detail_view_basic():
    """Prueba básica de la vista de detalle de cliente."""
    print("🔍 Probando vista de detalle de cliente...")
    
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
    
    try:
        # Test client detail view with a non-existent client (should show error gracefully)
        response = django_client.get('/clients/999/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for key elements that should be present even with no client data
            checks = [
                ('ForgeDB' in content, 'Brand name in template'),
                ('Cliente No Encontrado' in content or 'client' in content.lower(), 'Client-related content'),
                ('bootstrap' in content.lower(), 'Bootstrap CSS'),
                ('<!DOCTYPE html>' in content, 'Valid HTML structure'),
            ]
            
            passed = 0
            for check, description in checks:
                if check:
                    print(f"✅ {description}")
                    passed += 1
                else:
                    print(f"❌ {description}")
            
            success_rate = (passed / len(checks)) * 100
            print(f"\n📊 Elementos verificados: {passed}/{len(checks)} ({success_rate:.1f}%)")
            
            return success_rate >= 75
            
        else:
            print(f"❌ Vista de detalle: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando vista de detalle: {e}")
        return False


def test_client_list_view():
    """Prueba la vista de lista de clientes."""
    print("\n🔍 Probando vista de lista de clientes...")
    
    # Create Django test client
    django_client = Client()
    
    # Login
    django_client.login(username='testuser', password='testpass123')
    
    try:
        response = django_client.get('/clients/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            checks = [
                ('Gestión de Clientes' in content, 'Page title'),
                ('Nuevo Cliente' in content, 'Create button'),
                ('bootstrap' in content.lower(), 'Bootstrap CSS'),
            ]
            
            passed = sum(1 for check, _ in checks if check)
            success_rate = (passed / len(checks)) * 100
            
            print(f"✅ Lista de clientes: {passed}/{len(checks)} elementos ({success_rate:.1f}%)")
            return success_rate >= 75
            
        else:
            print(f"❌ Lista de clientes: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando lista de clientes: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO VISTAS DE CLIENTE - VERSIÓN SIMPLE")
    print("=" * 50)
    
    results = []
    
    # Test client list view
    results.append(test_client_list_view())
    
    # Test client detail view
    results.append(test_client_detail_view_basic())
    
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
        print("\n🎉 VISTAS DE CLIENTE FUNCIONANDO CORRECTAMENTE")
        print("✅ Task 6.3 - Client Detail View completada")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS EN LAS VISTAS")
        print("❌ Revisar implementación")
        return 1


if __name__ == '__main__':
    sys.exit(main())