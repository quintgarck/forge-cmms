#!/usr/bin/env python
"""
Script de solución para problemas de autenticación en creación de técnicos
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

def diagnose_authentication():
    """Diagnosticar el estado de autenticación"""
    logger.info("=== DIAGNOSTICO DE AUTENTICACION ===")
    
    try:
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario de prueba
        user = User.objects.create_user(
            username='authtest',
            password='authpass123',
            email='auth@test.com'
        )
        
        # Loguear usuario
        login_success = django_client.login(username='authtest', password='authpass123')
        logger.info(f"Inicio de sesión Django: {'Exitoso' if login_success else 'Fallido'}")
        
        if not login_success:
            logger.error("No se pudo iniciar sesión en Django")
            return False
        
        # Verificar estado de sesión
        session = django_client.session
        logger.info(f"Sesión activa: {bool(session)}")
        
        # Verificar tokens en sesión
        auth_token = session.get('auth_token')
        refresh_token = session.get('refresh_token')
        
        logger.info(f"Token de autenticación presente: {auth_token is not None}")
        logger.info(f"Token de refresco presente: {refresh_token is not None}")
        
        if auth_token:
            logger.info(f"Longitud del token: {len(auth_token)} caracteres")
        if refresh_token:
            logger.info(f"Longitud del refresh token: {len(refresh_token)} caracteres")
        
        # Probar endpoint de diagnóstico de autenticación
        try:
            response = django_client.get('/debug/auth/')
            logger.info(f"Endpoint de diagnóstico: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    import json
                    debug_data = json.loads(response.content.decode('utf-8'))
                    logger.info("Información de diagnóstico:")
                    for key, value in debug_data.items():
                        logger.info(f"  {key}: {value}")
                except:
                    logger.info("Contenido del diagnóstico:")
                    logger.info(response.content.decode('utf-8')[:500])
        except Exception as e:
            logger.info(f"Endpoint de diagnóstico no disponible: {e}")
        
        # Limpiar usuario
        user.delete()
        
        return True
        
    except Exception as e:
        logger.error(f"Error en diagnóstico de autenticación: {e}")
        return False

def test_direct_api_authentication():
    """Probar autenticación directa con la API"""
    logger.info("=== PRUEBA DE AUTENTICACION DIRECTA CON API ===")
    
    try:
        from frontend.services import AuthenticationService
        from frontend.services.api_client import ForgeAPIClient
        
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario de prueba
        user = User.objects.create_user(
            username='apitest',
            password='apipass123',
            email='api@test.com'
        )
        
        # Loguear usuario
        django_client.login(username='apitest', password='apipass123')
        
        # Crear servicios
        auth_service = AuthenticationService(django_client)
        api_client = ForgeAPIClient(request=django_client)
        
        # Verificar autenticación
        is_authenticated = auth_service.is_authenticated()
        logger.info(f"Servicio de autenticación reporta: {'Autenticado' if is_authenticated else 'No autenticado'}")
        
        # Probar conectividad con API
        try:
            api_available = api_client.is_api_available()
            logger.info(f"API disponible: {'Sí' if api_available else 'No'}")
        except Exception as e:
            logger.info(f"Error al verificar disponibilidad de API: {e}")
        
        # Limpiar usuario
        user.delete()
        
        return is_authenticated
        
    except Exception as e:
        logger.error(f"Error en prueba de API: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def solution_attempt_1_force_token_refresh():
    """Intento de solución 1: Forzar refresco de tokens"""
    logger.info("=== INTENTO DE SOLUCION 1: FORZAR REFRESCO DE TOKENS ===")
    
    try:
        from frontend.services import AuthenticationService
        
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario de prueba
        user = User.objects.create_user(
            username='solution1',
            password='solutionpass123',
            email='solution1@test.com'
        )
        
        # Loguear usuario
        django_client.login(username='solution1', password='solutionpass123')
        
        # Crear servicio de autenticación
        auth_service = AuthenticationService(django_client)
        
        # Limpiar tokens existentes
        if hasattr(django_client, 'session'):
            session = django_client.session
            session.pop('auth_token', None)
            session.pop('refresh_token', None)
            session.save()
            logger.info("Tokens antiguos eliminados de la sesión")
        
        # Intentar refrescar (debería generar nuevos tokens)
        refresh_result = auth_service.refresh_token()
        logger.info(f"Resultado de refresco de token: {'Exitoso' if refresh_result else 'Fallido'}")
        
        # Verificar autenticación después del refresco
        is_authenticated = auth_service.is_authenticated()
        logger.info(f"Autenticación después del refresco: {'Exitosa' if is_authenticated else 'Fallida'}")
        
        # Limpiar usuario
        user.delete()
        
        return is_authenticated
        
    except Exception as e:
        logger.error(f"Error en solución 1: {e}")
        return False

def solution_attempt_2_manual_token_generation():
    """Intento de solución 2: Generación manual de tokens"""
    logger.info("=== INTENTO DE SOLUCION 2: GENERACION MANUAL DE TOKENS ===")
    
    try:
        import jwt
        from datetime import datetime, timedelta
        from django.conf import settings
        
        # Crear cliente Django
        django_client = Client()
        
        # Crear usuario de prueba
        user = User.objects.create_user(
            username='solution2',
            password='solutionpass123',
            email='solution2@test.com'
        )
        
        # Loguear usuario
        django_client.login(username='solution2', password='solutionpass123')
        
        # Generar token JWT manualmente
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.now() + timedelta(hours=1),
            'iat': datetime.now()
        }
        
        # Usar una clave secreta simple para pruebas
        secret_key = getattr(settings, 'SECRET_KEY', 'test-secret-key')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        # Guardar token en sesión
        if hasattr(django_client, 'session'):
            session = django_client.session
            session['auth_token'] = token
            session.save()
            logger.info("Token JWT generado y guardado en sesión")
        
        # Probar creación de técnico con token manual
        technician_data = {
            'employee_code': 'SOL2-001',
            'first_name': 'Solution2',
            'last_name': 'Test',
            'email': 'sol2@test.com',
            'hire_date': '2024-01-01',
            'status': 'ACTIVE'
        }
        
        response = django_client.post(reverse('frontend:technician_create'), technician_data)
        logger.info(f"Código de respuesta: {response.status_code}")
        
        if response.status_code == 302:
            logger.info("[SUCCESS] ¡Técnico creado con token manual!")
            result = True
        else:
            logger.info("[FAILED] Creación fallida incluso con token manual")
            result = False
            
            # Obtener mensajes de error
            messages = list(get_messages(response.wsgi_request))
            if messages:
                logger.info("Mensajes de error:")
                for msg in messages:
                    logger.info(f"  - {msg}")
        
        # Limpiar usuario
        user.delete()
        
        return result
        
    except Exception as e:
        logger.error(f"Error en solución 2: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Función principal"""
    logger.info("=" * 70)
    logger.info("SOLUCION DE PROBLEMAS DE AUTENTICACION - CREACION DE TECNICOS")
    logger.info("=" * 70)
    
    results = {}
    
    # Diagnóstico inicial
    results['authentication_diagnosis'] = diagnose_authentication()
    
    time.sleep(1)
    
    # Prueba de API
    results['api_test'] = test_direct_api_authentication()
    
    time.sleep(1)
    
    # Solución 1: Refresco de tokens
    results['solution_1'] = solution_attempt_1_force_token_refresh()
    
    time.sleep(1)
    
    # Solución 2: Generación manual
    results['solution_2'] = solution_attempt_2_manual_token_generation()
    
    # Resumen
    logger.info("=" * 70)
    logger.info("RESUMEN DE SOLUCIONES")
    logger.info("=" * 70)
    
    for test_name, result in results.items():
        status = "[IMPLEMENTED]" if result else "[FAILED]"
        logger.info(f"{test_name}: {status}")
    
    successful = sum(results.values())
    total = len(results)
    
    logger.info(f"\nSoluciones implementadas: {successful}/{total}")
    
    if successful >= 3:
        logger.info("[EXCELLENT] Múltiples soluciones funcionan")
        logger.info("Recomendación: La autenticación está resuelta")
    elif successful >= 1:
        logger.info("[GOOD] Al menos una solución funciona")
        logger.info("Recomendación: Implementar la solución que funcionó")
    else:
        logger.error("[CRITICAL] Ninguna solución funcionó")
        logger.info("Recomendación:")
        logger.info("1. Verificar configuración del servidor backend")
        logger.info("2. Revisar SECRET_KEY en settings")
        logger.info("3. Comprobar conectividad con API")
        logger.info("4. Considerar deshabilitar autenticación temporalmente para pruebas")
    
    return results

if __name__ == '__main__':
    main()