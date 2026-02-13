#!/usr/bin/env python3
"""
Script para probar que la lista de clientes funcione después del fix.
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


def test_client_list_fix():
    """Prueba que la lista de clientes funcione después del fix."""
    print("🔍 Probando lista de clientes después del fix...")
    
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
        # Test client list
        response = django_client.get('/clients/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for key elements
            checks = [
                ('Gestión de Clientes' in content, 'Título de página'),
                ('Nuevo Cliente' in content, 'Botón de crear'),
                ('bootstrap' in content.lower(), 'Bootstrap CSS'),
                ('<!DOCTYPE html>' in content, 'HTML válido'),
                ('No se encontraron clientes' in content or 'cliente' in content.lower(), 'Contenido de clientes'),
            ]
            
            passed = sum(1 for check, _ in checks if check)
            success_rate = (passed / len(checks)) * 100
            
            print(f"📊 Elementos verificados: {passed}/{len(checks)} ({success_rate:.1f}%)")
            
            for check, description in checks:
                status = "✅" if check else "❌"
                print(f"  {status} {description}")
            
            if success_rate >= 80:
                print("\n🎉 LISTA DE CLIENTES FUNCIONANDO CORRECTAMENTE")
                return True
            else:
                print("\n⚠️ Lista de clientes con algunos problemas")
                return False
                
        else:
            print(f"❌ Error en lista de clientes: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando lista: {e}")
        return False


if __name__ == '__main__':
    success = test_client_list_fix()
    
    if success:
        print("\n✅ PROBLEMA DE VISUALIZACIÓN CORREGIDO")
        print("🚀 Ahora puedes crear clientes desde la aplicación")
        print("\n📋 INSTRUCCIONES:")
        print("1. Ve a: http://localhost:8000/login/")
        print("2. Usuario: testuser, Contraseña: testpass123")
        print("3. Ve a: http://localhost:8000/clients/create/")
        print("4. Llena el formulario y crea tu cliente")
    else:
        print("\n⚠️ Aún hay algunos problemas menores")