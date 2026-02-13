#!/usr/bin/env python
"""
Script de diagnóstico detallado para errores de validación en creación de técnicos
"""

import os
import sys
import time
import logging
from io import StringIO

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

def detailed_technician_test():
    """Test detallado con captura de mensajes de error"""
    logger.info("=== TEST DETALLADO DE CREACION DE TECNICO ===")
    
    try:
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario temporal y loguear
        user = User.objects.create_user(
            username='detailtest',
            password='detailpass123',
            email='detail@example.com'
        )
        django_client.login(username='detailtest', password='detailpass123')
        
        # Datos de técnico con errores intencionales para diagnosticar
        technician_data = {
            'employee_code': 'DETAIL-001',
            'first_name': 'Detail',
            'last_name': 'Test',
            'email': 'detail@test.com',
            'hire_date': '2024-01-01',
            'status': 'ACTIVE'
        }
        
        logger.info("Enviando datos de técnico...")
        logger.info(f"Datos enviados: {technician_data}")
        
        # Capturar mensajes de Django
        response = django_client.post(reverse('frontend:technician_create'), technician_data)
        
        logger.info(f"Código de estado: {response.status_code}")
        
        # Obtener mensajes de error
        messages = list(get_messages(response.wsgi_request))
        if messages:
            logger.info("Mensajes del sistema:")
            for i, message in enumerate(messages):
                logger.info(f"  Mensaje {i+1}: {message}")
        else:
            logger.info("No hay mensajes del sistema")
        
        # Analizar la respuesta
        if response.status_code == 302:
            logger.info("[SUCCESS] Redirección exitosa - técnico creado")
            return True
        elif response.status_code == 200:
            logger.info("[FORM_ERROR] Formulario devuelto con errores")
            
            # Buscar errores específicos en el contenido
            try:
                content = response.content.decode('utf-8')
                
                # Buscar patrones comunes de errores
                error_indicators = [
                    'error', 'invalid', 'required', 'Este campo', 
                    'no es válido', 'debe tener', 'no puede estar vacío'
                ]
                
                found_errors = []
                for indicator in error_indicators:
                    if indicator.lower() in content.lower():
                        # Extraer contexto alrededor del error
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if indicator.lower() in line.lower():
                                context_start = max(0, i-2)
                                context_end = min(len(lines), i+3)
                                context = '\n'.join(lines[context_start:context_end])
                                found_errors.append(f"Línea {i}: {context}")
                
                if found_errors:
                    logger.info("Errores encontrados en el formulario:")
                    for error in found_errors[:10]:  # Limitar a 10 errores
                        logger.info(f"  {error}")
                else:
                    logger.info("No se encontraron indicadores claros de error en el contenido")
                
                # Buscar campos específicos con errores
                required_fields = ['employee_code', 'first_name', 'last_name', 'email', 'hire_date', 'status']
                logger.info("Verificando campos requeridos en el formulario devuelto:")
                
                for field in required_fields:
                    if f'name="{field}"' in content:
                        logger.info(f"  ✓ Campo {field} encontrado en el formulario")
                    else:
                        logger.info(f"  ✗ Campo {field} NO encontrado")
                        
            except Exception as decode_error:
                logger.error(f"Error al decodificar contenido: {decode_error}")
            
            return False
        else:
            logger.error(f"[UNEXPECTED] Código de estado inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Excepción durante el test: {e}")
        import traceback
        logger.error("Traceback completo:")
        logger.error(traceback.format_exc())
        return False
    finally:
        # Limpiar usuario temporal
        try:
            if 'user' in locals():
                user.delete()
        except:
            pass

def test_form_validation_specific():
    """Test específico de validación de formulario"""
    logger.info("=== TEST DE VALIDACION ESPECIFICA ===")
    
    try:
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario temporal y loguear
        user = User.objects.create_user(
            username='validationtest',
            password='validationpass123',
            email='validation@example.com'
        )
        django_client.login(username='validationtest', password='validationpass123')
        
        # Probar con datos que sabemos que deberían funcionar
        technician_data = {
            'employee_code': 'VALID-001',
            'first_name': 'Valid',
            'last_name': 'Test',
            'email': 'valid@test.com',
            'phone': '1234567890',
            'hire_date': '2024-01-15',
            'status': 'ACTIVE',
            'hourly_rate': '50.00',
            'daily_rate': '400.00',
            'overtime_multiplier': '1.50',
            'efficiency_avg': '100.00',
            'quality_score': '95.00',
            'is_active': 'on'
        }
        
        logger.info("Probando con datos validados...")
        response = django_client.post(reverse('frontend:technician_create'), technician_data)
        
        logger.info(f"Código de respuesta: {response.status_code}")
        
        if response.status_code == 302:
            logger.info("[SUCCESS] ¡Formulario validado correctamente!")
            return True
        else:
            logger.info("[FAILED] Validación fallida")
            
            # Obtener mensajes específicos
            messages = list(get_messages(response.wsgi_request))
            if messages:
                logger.info("Mensajes de validación:")
                for msg in messages:
                    logger.info(f"  - {msg}")
            
            # Verificar contenido para errores específicos
            try:
                content = response.content.decode('utf-8')
                
                # Buscar errores de campo específicos
                field_errors = {}
                for field in technician_data.keys():
                    if f'id_{field}' in content and 'invalid' in content:
                        field_errors[field] = "Campo marcado como inválido"
                
                if field_errors:
                    logger.info("Errores por campo:")
                    for field, error in field_errors.items():
                        logger.info(f"  {field}: {error}")
                else:
                    logger.info("No se identificaron errores específicos por campo")
                    
            except Exception as e:
                logger.error(f"Error analizando contenido: {e}")
            
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Excepción en validación: {e}")
        return False
    finally:
        try:
            if 'user' in locals():
                user.delete()
        except:
            pass

def main():
    """Función principal"""
    logger.info("=" * 70)
    logger.info("DIAGNOSTICO DETALLADO DE ERRORES EN CREACION DE TECNICOS")
    logger.info("=" * 70)
    
    results = {}
    
    # Test 1: Diagnóstico detallado
    results['detailed_diagnosis'] = detailed_technician_test()
    
    time.sleep(1)
    
    # Test 2: Validación específica
    results['specific_validation'] = test_form_validation_specific()
    
    # Resumen
    logger.info("=" * 70)
    logger.info("RESUMEN DE DIAGNOSTICO")
    logger.info("=" * 70)
    
    for test_name, result in results.items():
        status = "[PASSED]" if result else "[FAILED]"
        logger.info(f"{test_name}: {status}")
    
    successful = sum(results.values())
    total = len(results)
    
    logger.info(f"\nResultado general: {successful}/{total} tests exitosos")
    
    if successful == total:
        logger.info("[EXCELLENT] Todos los tests pasaron")
    elif successful > 0:
        logger.info("[PARTIAL] Algunos tests pasaron")
        logger.info("Recomendación: Revisar los tests fallidos específicamente")
    else:
        logger.error("[CRITICAL] Todos los tests fallaron")
        logger.info("Recomendación: ")
        logger.info("1. Verificar que el servidor backend esté corriendo")
        logger.info("2. Revisar configuración de base de datos")
        logger.info("3. Comprobar permisos de usuario")
        logger.info("4. Validar estructura del formulario")
    
    return results

if __name__ == '__main__':
    main()