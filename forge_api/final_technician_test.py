#!/usr/bin/env python
"""
Test final para crear técnicos después de resolver problemas de base de datos
"""

import os
import sys
import time
import logging

# Configurar el entorno Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def final_technician_test():
    """Test final de creación de técnico"""
    logger.info("=== TEST FINAL DE CREACION DE TECNICO ===")
    
    try:
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario temporal y loguear
        user = User.objects.create_user(
            username='finaltest',
            password='finalpass123',
            email='final@test.com'
        )
        django_client.login(username='finaltest', password='finalpass123')
        
        # Datos de técnico completos y válidos
        technician_data = {
            'employee_code': 'FINAL-001',
            'first_name': 'Final',
            'last_name': 'Test',
            'email': 'final@test.com',
            'phone': '555-0199',
            'hire_date': '2024-01-20',
            'status': 'ACTIVE',
            'hourly_rate': '65.00',
            'daily_rate': '520.00',
            'overtime_multiplier': '1.50',
            'specialization': 'Mecanica, Electricidad',
            'certifications': 'Certificado Profesional',
            'efficiency_avg': '95.00',
            'quality_score': '98.00',
            'is_active': 'on',
            'notes': 'Tecnico de prueba final'
        }
        
        logger.info("Enviando solicitud de creación de técnico...")
        logger.info(f"Datos a enviar: {list(technician_data.keys())}")
        
        start_time = time.time()
        response = django_client.post(reverse('frontend:technician_create'), technician_data)
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Tiempo de respuesta: {duration:.2f} segundos")
        logger.info(f"Código de estado: {response.status_code}")
        
        # Obtener mensajes
        messages = list(get_messages(response.wsgi_request))
        if messages:
            logger.info("Mensajes del sistema:")
            for msg in messages:
                logger.info(f"  - {msg}")
        
        # Analizar resultado
        if response.status_code == 302:
            logger.info("🎉 ¡EXITO! Técnico creado correctamente")
            logger.info("Redirigiendo a la vista de detalle")
            result = True
        elif response.status_code == 200:
            logger.info("📝 Formulario devuelto - posiblemente con errores de validación")
            
            # Buscar errores específicos en el contenido
            try:
                content = response.content.decode('utf-8')
                
                # Buscar mensajes de error comunes
                error_keywords = ['error', 'inválido', 'requerido', 'autenticación', 'sesión']
                found_errors = []
                
                for keyword in error_keywords:
                    if keyword in content.lower():
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if keyword in line.lower():
                                context = lines[max(0, i-1):min(len(lines), i+2)]
                                found_errors.append(' '.join(context))
                
                if found_errors:
                    logger.info("Errores encontrados:")
                    for error in found_errors[:5]:  # Limitar a 5 errores
                        logger.info(f"  {error}")
                else:
                    logger.info("No se encontraron errores específicos visibles")
                    
            except Exception as e:
                logger.error(f"Error analizando contenido: {e}")
                
            result = False
        else:
            logger.error(f"❌ Código de estado inesperado: {response.status_code}")
            result = False
            
        # Limpiar usuario
        user.delete()
        
        return result, duration
        
    except Exception as e:
        logger.error(f"💥 Excepción durante el test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, 0

def test_client_creation_control():
    """Test de control: crear cliente (que ya funciona)"""
    logger.info("=== TEST DE CONTROL: CREACION DE CLIENTE ===")
    
    try:
        django_client = Client()
        user = User.objects.create_user(
            username='controltest',
            password='controlpass123',
            email='control@test.com'
        )
        django_client.login(username='controltest', password='controlpass123')
        
        client_data = {
            'name': 'Cliente Control Test',
            'contact_person': 'Control Person',
            'email': 'control@client.com',
            'phone': '555-0100',
            'address': 'Direccion de control',
            'city': 'Ciudad Control',
            'country': 'MX'
        }
        
        start_time = time.time()
        response = django_client.post(reverse('frontend:client_create'), client_data)
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Tiempo cliente: {duration:.2f} segundos")
        logger.info(f"Código cliente: {response.status_code}")
        
        if response.status_code == 302:
            logger.info("✅ Cliente creado exitosamente (control)")
            result = True
        else:
            logger.info("❌ Cliente falló (control)")
            result = False
            
        user.delete()
        return result, duration
        
    except Exception as e:
        logger.error(f"Error en test de control: {e}")
        return False, 0

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("TEST FINAL - CREACION DE TECNICOS")
    logger.info("Después de resolver problemas de base de datos")
    logger.info("=" * 60)
    
    # Test de control primero
    client_success, client_time = test_client_creation_control()
    
    time.sleep(1)
    
    # Test principal
    tech_success, tech_time = final_technician_test()
    
    # Resumen
    logger.info("=" * 60)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 60)
    
    logger.info(f"Cliente (control): {'✅ EXITO' if client_success else '❌ FALLIDO'} ({client_time:.2f}s)")
    logger.info(f"Técnico (objetivo): {'✅ EXITO' if tech_success else '❌ FALLIDO'} ({tech_time:.2f}s)")
    
    if tech_success:
        logger.info("🎉 ¡OBJETIVO LOGRADO!")
        logger.info("La creación de técnicos ahora funciona correctamente")
    elif client_success and not tech_success:
        logger.info("⚠ Problema específico con técnicos persiste")
        logger.info("Posible causa: autenticación o validaciones específicas")
    else:
        logger.info("❌ Problemas generales persisten")
        logger.info("Requiere investigación adicional")
    
    return tech_success

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)