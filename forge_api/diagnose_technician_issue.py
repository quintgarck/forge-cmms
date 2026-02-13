#!/usr/bin/env python
"""
Script de diagnóstico para problemas de creación de técnicos
Analiza el rendimiento y errores en la creación de técnicos
"""

import os
import sys
import time
import logging
from datetime import datetime

# Configurar el entorno Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

# Configurar logging sin caracteres especiales para evitar problemas en Windows
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicianCreationDiagnosis(TestCase):
    """Clase para diagnosticar problemas de creación de técnicos"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.django_client = Client()
        self.django_client.login(username='testuser', password='testpass123')
        
        logger.info("Usuario de prueba creado y logueado")
    
    def test_client_creation_performance(self):
        """Test de rendimiento para creación de clientes"""
        logger.info("=== TEST DE RENDIMIENTO: CREACIÓN DE CLIENTES ===")
        
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
        try:
            response = self.django_client.post(reverse('frontend:client_create'), client_data)
            end_time = time.time()
            
            duration = end_time - start_time
            logger.info(f"Tiempo de creacion de cliente: {duration:.2f} segundos")
            
            if response.status_code == 302:  # Redirección exitosa
                logger.info("[OK] Cliente creado exitosamente")
                if duration > 2:
                    logger.warning("[WARNING] Tiempo de respuesta lento (>2 segundos)")
                return True
            else:
                logger.error(f"[ERROR] Error en creacion de cliente: Status {response.status_code}")
                logger.error(f"Contenido: {response.content[:500]}")
                return False
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"[ERROR] Excepcion en creacion de cliente: {e}")
            logger.error(f"Tiempo transcurrido: {duration:.2f} segundos")
            return False
    
    def test_technician_creation_failure(self):
        """Test específico para fallos en creación de técnicos"""
        logger.info("=== TEST DE DIAGNOSTICO: CREACION DE TECNICOS ===")
        
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
        try:
            response = self.django_client.post(reverse('frontend:technician_create'), technician_data)
            end_time = time.time()
            
            duration = end_time - start_time
            logger.info(f"Tiempo de intento de creacion: {duration:.2f} segundos")
            
            # Analizar la respuesta
            if response.status_code == 302:
                logger.info("[OK] Tecnico creado exitosamente")
                if duration > 3:
                    logger.warning("[WARNING] Tiempo de respuesta muy lento (>3 segundos)")
                return True
            else:
                logger.error(f"[ERROR] Fallo en creacion de tecnico: Status {response.status_code}")
                
                # Obtener mensajes de error
                messages = list(get_messages(response.wsgi_request))
                if messages:
                    logger.error("Mensajes de error:")
                    for message in messages:
                        logger.error(f"  - {message}")
                
                # Mostrar contenido de la respuesta para análisis
                logger.error("Contenido de la respuesta:")
                try:
                    content = response.content.decode('utf-8')
                    logger.error(content[:1000])
                except:
                    logger.error(str(response.content)[:1000])
                
                return False
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"[ERROR] Excepcion en creacion de tecnico: {e}")
            logger.error(f"Tiempo transcurrido: {duration:.2f} segundos")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_api_connectivity(self):
        """Test de conectividad con la API"""
        logger.info("=== TEST DE CONECTIVIDAD API ===")
        
        try:
            from frontend.services.api_client import ForgeAPIClient
            
            # Crear cliente API
            api_client = ForgeAPIClient(request=self.django_client)
            
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
                
            return is_available
            
        except Exception as e:
            logger.error(f"[ERROR] Error en test de conectividad API: {e}")
            return False
    
    def run_complete_diagnosis(self):
        """Ejecutar diagnóstico completo"""
        logger.info("=" * 60)
        logger.info("INICIANDO DIAGNOSTICO COMPLETO DE CREACION DE TECNICOS")
        logger.info("=" * 60)
        
        results = {}
        
        # Test 1: Conectividad API
        results['api_connectivity'] = self.test_api_connectivity()
        
        # Test 2: Creación de cliente (control)
        results['client_creation'] = self.test_client_creation_performance()
        
        # Test 3: Creación de técnico (problema principal)
        results['technician_creation'] = self.test_technician_creation_failure()
        
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
        else:
            logger.info("[OK] Todos los tests pasaron - sistema funcionando correctamente")
        
        return results

if __name__ == '__main__':
    diagnosis = TechnicianCreationDiagnosis()
    diagnosis.run_complete_diagnosis()