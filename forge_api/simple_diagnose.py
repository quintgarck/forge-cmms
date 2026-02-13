#!/usr/bin/env python
"""
Script simple de diagnóstico para problemas de creación de técnicos
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

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_connectivity():
    """Test de conectividad con la API"""
    logger.info("=== TEST DE CONECTIVIDAD API ===")
    
    try:
        from frontend.services.api_client import ForgeAPIClient
        
        # Crear cliente Django para obtener sesión
        django_client = Client()
        
        # Crear usuario temporal y loguear
        user = User.objects.create_user(
            username='tempuser',
            password='temppass123',
            email='temp@example.com'
        )
        django_client.login(username='tempuser', password='temppass123')
        
        # Crear cliente API
        api_client = ForgeAPIClient(request=django_client)
        
        # Test básico de conectividad
        start_time = time.time()
        is_available = api_client.is_api_available()
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Tiempo de verificacion API: {duration:.2f} segundos")
        
        if is_available:
            logger.info("[OK] API disponible y respondiendo")
            if duration > 1:
                logger.warning("[WARNING] Conectividad lenta con API (>1 segundo)")
        else:
            logger.error("[ERROR] API no disponible")
            
        # Limpiar usuario temporal
        user.delete()
        
        return is_available
        
    except Exception as e:
        logger.error(f"[ERROR] Error en test de conectividad API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_client_creation():
    """Test de creación de cliente"""
    logger.info("=== TEST DE CREACION DE CLIENTES ===")
    
    try:
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario temporal y loguear
        user = User.objects.create_user(
            username='tempuser2',
            password='temppass123',
            email='temp2@example.com'
        )
        django_client.login(username='tempuser2', password='temppass123')
        
        client_data = {
            'name': 'Cliente Test Performance',
            'contact_person': 'Juan Perez',
            'email': 'cliente@test.com',
            'phone': '1234567890',
            'address': 'Direccion de prueba',
            'city': 'Ciudad de Prueba',
            'country': 'MX'
        }
        
        start_time = time.time()
        response = django_client.post(reverse('frontend:client_create'), client_data)
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Tiempo de creacion de cliente: {duration:.2f} segundos")
        
        if response.status_code == 302:  # Redirección exitosa
            logger.info("[OK] Cliente creado exitosamente")
            if duration > 2:
                logger.warning("[WARNING] Tiempo de respuesta lento (>2 segundos)")
            result = True
        else:
            logger.error(f"[ERROR] Error en creacion de cliente: Status {response.status_code}")
            logger.error(f"Contenido: {response.content[:500]}")
            result = False
            
        # Limpiar usuario temporal
        user.delete()
        
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] Excepcion en creacion de cliente: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_technician_creation():
    """Test de creación de técnico"""
    logger.info("=== TEST DE CREACION DE TECNICOS ===")
    
    try:
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario temporal y loguear
        user = User.objects.create_user(
            username='tempuser3',
            password='temppass123',
            email='temp3@example.com'
        )
        django_client.login(username='tempuser3', password='temppass123')
        
        technician_data = {
            'employee_code': 'TECH-TEST-001',
            'first_name': 'Tecnico',
            'last_name': 'Prueba',
            'email': 'tecnico@test.com',
            'phone': '1234567890',
            'hire_date': '2024-01-01',
            'status': 'ACTIVE',
            'hourly_rate': '50.00',
            'daily_rate': '400.00',
            'overtime_multiplier': '1.50',
            'specialization': 'Mecanica, Electricidad',
            'certifications': 'Certificado A, Certificado B',
            'efficiency_avg': '100.00',
            'quality_score': '95.00',
            'is_active': 'on',
            'notes': 'Tecnico de prueba para diagnostico'
        }
        
        start_time = time.time()
        response = django_client.post(reverse('frontend:technician_create'), technician_data)
        end_time = time.time()
        
        duration = end_time - start_time
        logger.info(f"Tiempo de intento de creacion: {duration:.2f} segundos")
        
        # Analizar la respuesta
        if response.status_code == 302:
            logger.info("[OK] Tecnico creado exitosamente")
            if duration > 3:
                logger.warning("[WARNING] Tiempo de respuesta muy lento (>3 segundos)")
            result = True
        else:
            logger.error(f"[ERROR] Fallo en creacion de tecnico: Status {response.status_code}")
            
            # Mostrar contenido de la respuesta para análisis
            logger.error("Contenido de la respuesta:")
            try:
                content = response.content.decode('utf-8')
                logger.error(content[:1000])
            except:
                logger.error(str(response.content)[:1000])
                
            result = False
            
        # Limpiar usuario temporal
        user.delete()
        
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] Excepcion en creacion de tecnico: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("INICIANDO DIAGNOSTICO DE CREACION DE TECNICOS")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: Conectividad API
    results['api_connectivity'] = test_api_connectivity()
    
    # Test 2: Creación de cliente (control)
    results['client_creation'] = test_client_creation()
    
    # Test 3: Creación de técnico (problema principal)
    results['technician_creation'] = test_technician_creation()
    
    # Resumen
    logger.info("=" * 60)
    logger.info("RESUMEN DE DIAGNOSTICO")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "[OK] PASSED" if result else "[ERROR] FAILED"
        logger.info(f"{test_name}: {status}")
    
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        logger.error(f"Tests fallidos: {', '.join(failed_tests)}")
        logger.info("Recomendaciones:")
        if not results['api_connectivity']:
            logger.info("- Verificar que el servidor backend este corriendo")
            logger.info("- Revisar configuracion de conexion API")
        if not results['technician_creation']:
            logger.info("- Revisar logs del servidor backend")
            logger.info("- Verificar permisos de base de datos")
            logger.info("- Comprobar validaciones del formulario")
            logger.info("- Probar crear un técnico manualmente para ver errores específicos")
    else:
        logger.info("[OK] Todos los tests pasaron - sistema funcionando correctamente")
    
    return results

if __name__ == '__main__':
    main()