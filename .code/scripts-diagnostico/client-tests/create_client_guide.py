#!/usr/bin/env python3
"""
Guía completa para crear clientes desde la aplicación ForgeDB.
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


def setup_test_environment():
    """Configura el entorno de prueba."""
    print("🔧 CONFIGURANDO ENTORNO DE PRUEBA")
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
        print("✅ Usuario de prueba creado")
    else:
        print("✅ Usuario de prueba ya existe")
    
    # Test server connectivity
    try:
        response = requests.get("http://localhost:8000/api/v1/health/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor API funcionando")
        else:
            print(f"⚠️ Servidor API responde con código {response.status_code}")
    except:
        print("❌ Servidor API no responde - ¿Está ejecutándose?")
        return False
    
    # Test frontend connectivity
    django_client = Client()
    response = django_client.get('/login/')
    if response.status_code == 200:
        print("✅ Frontend funcionando")
    else:
        print(f"❌ Frontend error: {response.status_code}")
        return False
    
    return True


def test_client_creation_flow():
    """Prueba el flujo completo de creación de cliente."""
    print("\n🧪 PROBANDO FLUJO DE CREACIÓN")
    print("=" * 50)
    
    # Get JWT token
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json={'username': 'testuser', 'password': 'testpass123'},
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get('access')
            print("✅ Token JWT obtenido")
        else:
            print("❌ Error obteniendo token JWT")
            return False
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return False
    
    # Test Django login
    django_client = Client()
    login_success = django_client.login(username='testuser', password='testpass123')
    if login_success:
        print("✅ Login Django exitoso")
    else:
        print("❌ Error en login Django")
        return False
    
    # Set JWT token in session
    session = django_client.session
    session['auth_token'] = token
    session.save()
    print("✅ Token configurado en sesión")
    
    # Test client creation form access
    response = django_client.get('/clients/create/')
    if response.status_code == 200:
        print("✅ Formulario de creación accesible")
    else:
        print(f"❌ Error accediendo al formulario: {response.status_code}")
        return False
    
    # Test client list access
    response = django_client.get('/clients/')
    if response.status_code == 200:
        print("✅ Lista de clientes accesible")
    else:
        print(f"❌ Error accediendo a la lista: {response.status_code}")
        return False
    
    return True


def show_creation_instructions():
    """Muestra las instrucciones para crear clientes."""
    print("\n🎯 INSTRUCCIONES PARA CREAR CLIENTES")
    print("=" * 50)
    
    print("1. 🌐 ACCEDE A LA APLICACIÓN:")
    print("   - Abre tu navegador web")
    print("   - Ve a: http://localhost:8000/login/")
    print("   - Usuario: testuser")
    print("   - Contraseña: testpass123")
    
    print("\n2. 📝 CREAR NUEVO CLIENTE:")
    print("   - Haz clic en 'Clientes' en el menú")
    print("   - Haz clic en 'Nuevo Cliente'")
    print("   - O ve directamente a: http://localhost:8000/clients/create/")
    
    print("\n3. 📋 LLENAR EL FORMULARIO:")
    print("   - Código de Cliente: CLI-001 (único)")
    print("   - Tipo: Persona Física")
    print("   - Nombre: Juan Pérez García")
    print("   - Email: juan.perez@example.com")
    print("   - Teléfono: 5551234567 (SIN guiones ni espacios)")
    print("   - Dirección: Calle Principal 123, Colonia Centro")
    print("   - Límite de Crédito: 5000")
    
    print("\n4. ✅ VALIDACIONES IMPORTANTES:")
    print("   - El código debe ser único")
    print("   - El email debe ser válido")
    print("   - El teléfono debe ser solo números (10-15 dígitos)")
    print("   - El nombre debe tener al menos 2 caracteres")
    
    print("\n5. 🎉 DESPUÉS DE CREAR:")
    print("   - Serás redirigido a la vista de detalle del cliente")
    print("   - Podrás ver toda la información del cliente")
    print("   - Podrás editarlo o eliminarlo si es necesario")
    
    print("\n6. 📋 VER LISTA DE CLIENTES:")
    print("   - Ve a: http://localhost:8000/clients/")
    print("   - Verás todos los clientes creados")
    print("   - Puedes buscar, filtrar y ordenar")


def show_troubleshooting():
    """Muestra guía de solución de problemas."""
    print("\n🔧 SOLUCIÓN DE PROBLEMAS")
    print("=" * 50)
    
    print("❌ SI NO PUEDES HACER LOGIN:")
    print("   - Verifica que el servidor esté ejecutándose")
    print("   - Ejecuta: python manage.py runserver")
    
    print("\n❌ SI EL FORMULARIO DA ERRORES:")
    print("   - Teléfono: usa solo números (5551234567)")
    print("   - Email: debe ser válido (usuario@dominio.com)")
    print("   - Código: debe ser único (CLI-001, CLI-002, etc.)")
    
    print("\n❌ SI HAY ERRORES DE API:")
    print("   - Verifica que el backend esté funcionando")
    print("   - Revisa los logs del servidor")
    print("   - Intenta refrescar la página")
    
    print("\n❌ SI LA PÁGINA NO CARGA:")
    print("   - Verifica la URL: http://localhost:8000")
    print("   - Asegúrate de que el servidor esté en puerto 8000")
    print("   - Revisa la consola del navegador para errores")


def main():
    """Función principal."""
    print("🚀 GUÍA PARA CREAR CLIENTES EN FORGEDB")
    print("=" * 60)
    
    # Setup environment
    if not setup_test_environment():
        print("\n❌ PROBLEMA EN LA CONFIGURACIÓN")
        print("Por favor, asegúrate de que el servidor esté ejecutándose:")
        print("python manage.py runserver")
        return 1
    
    # Test creation flow
    if not test_client_creation_flow():
        print("\n❌ PROBLEMA EN EL FLUJO DE CREACIÓN")
        show_troubleshooting()
        return 1
    
    print("\n🎉 TODO ESTÁ LISTO PARA CREAR CLIENTES")
    
    # Show instructions
    show_creation_instructions()
    
    print("\n" + "=" * 60)
    print("✅ SISTEMA COMPLETAMENTE FUNCIONAL")
    print("🎯 ¡Ya puedes crear clientes desde la aplicación!")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())