#!/usr/bin/env python3
"""
Script completo para probar la conectividad del frontend ForgeDB.

Este script prueba:
1. Conectividad API
2. Autenticación JWT
3. Vistas del frontend
4. Templates y archivos estáticos
5. Funcionalidad completa del sistema
"""

import os
import sys
import django
from pathlib import Path
import requests
import json

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from frontend.services.api_client import ForgeAPIClient, APIException


class ConnectivityTester:
    """Prueba completa de conectividad del sistema."""
    
    def __init__(self):
        self.client = Client()
        self.api_base_url = 'http://localhost:8000/api/v1/'
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_success(self, test_name: str):
        """Registra una prueba exitosa."""
        self.test_results['passed'] += 1
        print(f"✅ {test_name}")
    
    def log_failure(self, test_name: str, error: str = ""):
        """Registra una prueba fallida."""
        self.test_results['failed'] += 1
        self.test_results['errors'].append(f"{test_name}: {error}")
        print(f"❌ {test_name}" + (f" - {error}" if error else ""))
    
    def test_api_health_check(self):
        """Prueba el health check de la API."""
        print("\n🔍 PROBANDO API HEALTH CHECK...")
        
        try:
            response = requests.get(f"{self.api_base_url}health/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') in ['healthy', 'degraded']:
                    self.log_success("API Health Check")
                    return True
                else:
                    self.log_failure("API Health Check", f"Status: {data.get('status')}")
            else:
                self.log_failure("API Health Check", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.log_failure("API Health Check", "Connection refused - ¿Está ejecutándose el servidor?")
        except Exception as e:
            self.log_failure("API Health Check", str(e))
        
        return False
    
    def test_api_authentication(self):
        """Prueba la autenticación JWT."""
        print("\n🔍 PROBANDO AUTENTICACIÓN JWT...")
        
        # Create test user if doesn't exist
        try:
            test_user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            test_user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
        
        # Test login
        try:
            login_data = {
                'username': 'testuser',
                'password': 'testpass123'
            }
            
            response = requests.post(
                f"{self.api_base_url}auth/login/",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                if 'access' in token_data:
                    self.log_success("JWT Authentication")
                    return token_data['access']
                else:
                    self.log_failure("JWT Authentication", "No access token in response")
            else:
                self.log_failure("JWT Authentication", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_failure("JWT Authentication", str(e))
        
        return None
    
    def test_api_endpoints_with_auth(self, token: str):
        """Prueba endpoints de la API con autenticación."""
        print("\n🔍 PROBANDO ENDPOINTS API CON AUTENTICACIÓN...")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        endpoints = [
            ('dashboard/', 'Dashboard Data'),
            ('clients/', 'Clients List'),
            ('work-orders/', 'Work Orders List'),
            ('products/', 'Products List'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(
                    f"{self.api_base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_success(f"API Endpoint: {name}")
                else:
                    self.log_failure(f"API Endpoint: {name}", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_failure(f"API Endpoint: {name}", str(e))
    
    def test_frontend_views(self):
        """Prueba las vistas del frontend."""
        print("\n🔍 PROBANDO VISTAS DEL FRONTEND...")
        
        # Test public views
        public_views = [
            ('frontend:login', 'Login Page'),
        ]
        
        for url_name, description in public_views:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                
                if response.status_code == 200:
                    self.log_success(f"Frontend View: {description}")
                else:
                    self.log_failure(f"Frontend View: {description}", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_failure(f"Frontend View: {description}", str(e))
        
        # Test protected views (should redirect to login)
        protected_views = [
            ('frontend:dashboard', 'Dashboard'),
            ('frontend:client_list', 'Client List'),
            ('frontend:client_create', 'Client Create'),
        ]
        
        for url_name, description in protected_views:
            try:
                url = reverse(url_name)
                response = self.client.get(url)
                
                # Should redirect to login (302) or show login form
                if response.status_code in [200, 302]:
                    self.log_success(f"Frontend Protected View: {description}")
                else:
                    self.log_failure(f"Frontend Protected View: {description}", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_failure(f"Frontend Protected View: {description}", str(e))
    
    def test_frontend_authentication(self):
        """Prueba la autenticación del frontend."""
        print("\n🔍 PROBANDO AUTENTICACIÓN DEL FRONTEND...")
        
        # Create test user if doesn't exist
        try:
            test_user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            test_user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
        
        # Test login
        try:
            login_url = reverse('frontend:login')
            response = self.client.post(login_url, {
                'username': 'testuser',
                'password': 'testpass123'
            })
            
            # Should redirect after successful login
            if response.status_code in [200, 302]:
                self.log_success("Frontend Authentication")
                
                # Test accessing protected view after login
                dashboard_url = reverse('frontend:dashboard')
                response = self.client.get(dashboard_url)
                
                if response.status_code == 200:
                    self.log_success("Frontend Protected Access After Login")
                else:
                    self.log_failure("Frontend Protected Access After Login", f"HTTP {response.status_code}")
            else:
                self.log_failure("Frontend Authentication", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_failure("Frontend Authentication", str(e))
    
    def test_api_client_service(self):
        """Prueba el servicio API Client del frontend."""
        print("\n🔍 PROBANDO SERVICIO API CLIENT...")
        
        try:
            # Create a mock request object
            class MockRequest:
                def __init__(self):
                    self.session = {}
                    self.META = {'HTTP_HOST': 'localhost:8000'}
                
                def is_secure(self):
                    return False
                
                def get_host(self):
                    return 'localhost:8000'
            
            mock_request = MockRequest()
            api_client = ForgeAPIClient(request=mock_request)
            
            # Test health check without auth
            try:
                health_data = api_client.get('health/')
                if health_data.get('status'):
                    self.log_success("API Client Health Check")
                else:
                    self.log_failure("API Client Health Check", "No status in response")
            except APIException as e:
                if e.status_code == 401:
                    # Expected for protected endpoints
                    self.log_success("API Client (Auth Required)")
                else:
                    self.log_failure("API Client Health Check", f"API Error: {e.message}")
            
        except Exception as e:
            self.log_failure("API Client Service", str(e))
    
    def test_template_rendering(self):
        """Prueba el renderizado de templates."""
        print("\n🔍 PROBANDO RENDERIZADO DE TEMPLATES...")
        
        try:
            # Test login template
            login_url = reverse('frontend:login')
            response = self.client.get(login_url)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Check for key elements
                if 'ForgeDB' in content:
                    self.log_success("Template Rendering: Brand Name")
                else:
                    self.log_failure("Template Rendering: Brand Name", "ForgeDB not found")
                
                if 'bootstrap' in content.lower():
                    self.log_success("Template Rendering: Bootstrap CSS")
                else:
                    self.log_failure("Template Rendering: Bootstrap CSS", "Bootstrap not found")
                
                if 'login' in content.lower():
                    self.log_success("Template Rendering: Login Form")
                else:
                    self.log_failure("Template Rendering: Login Form", "Login form not found")
            else:
                self.log_failure("Template Rendering", f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_failure("Template Rendering", str(e))
    
    def run_complete_test(self):
        """Ejecuta todas las pruebas de conectividad."""
        print("🚀 INICIANDO PRUEBAS COMPLETAS DE CONECTIVIDAD FORGEDB")
        print("=" * 70)
        
        # Test API connectivity
        api_healthy = self.test_api_health_check()
        
        # Test authentication
        token = None
        if api_healthy:
            token = self.test_api_authentication()
        
        # Test API endpoints with auth
        if token:
            self.test_api_endpoints_with_auth(token)
        
        # Test frontend views
        self.test_frontend_views()
        
        # Test frontend authentication
        self.test_frontend_authentication()
        
        # Test API client service
        self.test_api_client_service()
        
        # Test template rendering
        self.test_template_rendering()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE PRUEBAS DE CONECTIVIDAD")
        print("=" * 70)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Pruebas exitosas: {self.test_results['passed']}")
        print(f"❌ Pruebas fallidas: {self.test_results['failed']}")
        print(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"   {i}. {error}")
        
        print("\n🎯 RECOMENDACIONES:")
        if success_rate >= 90:
            print("   ✅ Sistema funcionando correctamente")
            print("   ✅ Puedes proceder con la implementación de nuevas funcionalidades")
        elif success_rate >= 70:
            print("   ⚠️  Sistema parcialmente funcional")
            print("   ⚠️  Revisar errores antes de continuar")
        else:
            print("   ❌ Sistema con problemas críticos")
            print("   ❌ Corregir errores antes de continuar")
        
        return success_rate >= 70


def main():
    """Función principal."""
    tester = ConnectivityTester()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 PRUEBAS DE CONECTIVIDAD COMPLETADAS EXITOSAMENTE")
        return 0
    else:
        print("\n⚠️  SE ENCONTRARON PROBLEMAS CRÍTICOS DE CONECTIVIDAD")
        return 1


if __name__ == '__main__':
    sys.exit(main())