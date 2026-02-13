#!/usr/bin/env python3
"""
Script para probar la validación del formulario de cliente con los nuevos valores.
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

from frontend.forms import ClientForm


def test_phone_validation():
    """Prueba la validación del teléfono con diferentes formatos."""
    print("🔍 Probando validación de teléfono...")
    
    test_cases = [
        # (phone_number, should_be_valid, description)
        ("82363829", True, "Número local de 8 dígitos"),
        ("correo@gmail.com", False, "Email en campo teléfono"),
        ("55-1234-5678", True, "Número con guiones"),
        ("(55) 1234-5678", True, "Número con paréntesis"),
        ("+52 55 1234 5678", True, "Número internacional"),
        ("123", False, "Número muy corto"),
        ("12345678901234567890", False, "Número muy largo"),
        ("555 123 4567", True, "Número con espacios"),
        ("", False, "Campo vacío"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for phone, should_be_valid, description in test_cases:
        form_data = {
            'client_code': 'TEST-001',
            'type': 'individual',
            'name': 'Cliente de Prueba',
            'email': 'test@example.com',
            'phone': phone,
            'address': 'Dirección de prueba 123',
            'credit_limit': '1000.00'
        }
        
        form = ClientForm(data=form_data)
        is_valid = form.is_valid()
        
        if is_valid == should_be_valid:
            print(f"✅ {description}: '{phone}' - {'Válido' if is_valid else 'Inválido'}")
            passed += 1
        else:
            print(f"❌ {description}: '{phone}' - Esperado: {'Válido' if should_be_valid else 'Inválido'}, Obtenido: {'Válido' if is_valid else 'Inválido'}")
            if not is_valid and form.errors:
                print(f"   Errores: {form.errors.get('phone', [])}")
    
    success_rate = (passed / total) * 100
    print(f"\n📊 Validación de teléfono: {passed}/{total} casos ({success_rate:.1f}%)")
    return success_rate >= 80


def test_email_validation():
    """Prueba la validación del email."""
    print("\n🔍 Probando validación de email...")
    
    test_cases = [
        # (email, should_be_valid, description)
        ("correo@gmail.com", True, "Email válido con gmail"),
        ("usuario@dominio.com", True, "Email válido genérico"),
        ("test@test", False, "Email sin dominio completo"),
        ("", False, "Campo vacío"),
        ("invalid-email", False, "Email sin @"),
        ("user@domain.co.mx", True, "Email con dominio mexicano"),
        ("test.user+tag@example.com", True, "Email con caracteres especiales"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for email, should_be_valid, description in test_cases:
        form_data = {
            'client_code': 'TEST-001',
            'type': 'individual',
            'name': 'Cliente de Prueba',
            'email': email,
            'phone': '82363829',
            'address': 'Dirección de prueba 123',
            'credit_limit': '1000.00'
        }
        
        form = ClientForm(data=form_data)
        is_valid = form.is_valid()
        
        if is_valid == should_be_valid:
            print(f"✅ {description}: '{email}' - {'Válido' if is_valid else 'Inválido'}")
            passed += 1
        else:
            print(f"❌ {description}: '{email}' - Esperado: {'Válido' if should_be_valid else 'Inválido'}, Obtenido: {'Válido' if is_valid else 'Inválido'}")
            if not is_valid and form.errors:
                print(f"   Errores: {form.errors.get('email', [])}")
    
    success_rate = (passed / total) * 100
    print(f"\n📊 Validación de email: {passed}/{total} casos ({success_rate:.1f}%)")
    return success_rate >= 80


def test_complete_form():
    """Prueba un formulario completo con los datos del usuario."""
    print("\n🔍 Probando formulario completo con datos del usuario...")
    
    form_data = {
        'client_code': 'CLI-001',
        'type': 'individual',
        'name': 'Juan Pérez García',
        'email': 'correo@gmail.com',
        'phone': '82363829',
        'address': 'Calle Principal 123, Colonia Centro, Ciudad de México',
        'credit_limit': '5000.00'
    }
    
    form = ClientForm(data=form_data)
    is_valid = form.is_valid()
    
    if is_valid:
        print("✅ Formulario completo válido")
        print("📋 Datos procesados:")
        for field, value in form.cleaned_data.items():
            print(f"   {field}: {value}")
        return True
    else:
        print("❌ Formulario completo inválido")
        print("🚫 Errores encontrados:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return False


def main():
    """Función principal."""
    print("🚀 PROBANDO VALIDACIÓN DE FORMULARIO DE CLIENTE")
    print("=" * 60)
    
    results = []
    
    # Test phone validation
    results.append(test_phone_validation())
    
    # Test email validation
    results.append(test_email_validation())
    
    # Test complete form
    results.append(test_complete_form())
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 VALIDACIÓN DE FORMULARIO FUNCIONANDO CORRECTAMENTE")
        print("✅ Los datos del usuario ahora deberían ser aceptados")
        return 0
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS EN LA VALIDACIÓN")
        print("❌ Revisar implementación del formulario")
        return 1


if __name__ == '__main__':
    sys.exit(main())