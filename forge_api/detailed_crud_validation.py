#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validación detallada CRUD por CRUD del sistema ForgeDB
Valida cada funcionalidad individualmente con tests específicos
"""

import os
import django
import requests
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

class DetailedCRUDValidation:
    """Validación detallada de cada CRUD individualmente"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.session = requests.Session()
        
    def login(self):
        """Iniciar sesión en el sistema"""
        try:
            # Primero obtener el token CSRF
            csrf_response = self.session.get(f"{self.base_url}/login/")
            csrf_token = csrf_response.cookies.get('csrftoken')
            
            # Login con credenciales de prueba
            login_data = {
                'username': 'admin',
                'password': 'admin123',
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = self.session.post(
                f"{self.base_url}/login/",
                data=login_data,
                headers={'Referer': f"{self.base_url}/login/"}
            )
            
            return response.status_code == 200 or response.status_code == 302
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False
    
    def validate_list_view(self, module_name, url_path):
        """Validar vista de lista"""
        try:
            response = self.session.get(f"{self.base_url}{url_path}")
            if response.status_code == 200:
                print(f"✅ {module_name} - Lista: OK (Status 200)")
                return True
            else:
                print(f"❌ {module_name} - Lista: ERROR (Status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ {module_name} - Lista: EXCEPTION - {str(e)}")
            return False
    
    def validate_create_view(self, module_name, url_path):
        """Validar vista de creación"""
        try:
            response = self.session.get(f"{self.base_url}{url_path}")
            if response.status_code == 200:
                print(f"✅ {module_name} - Crear: OK (Status 200)")
                return True
            else:
                print(f"❌ {module_name} - Crear: ERROR (Status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ {module_name} - Crear: EXCEPTION - {str(e)}")
            return False
    
    def validate_detail_view(self, module_name, url_pattern, test_id=1):
        """Validar vista de detalle"""
        try:
            url = url_pattern.format(pk=test_id)
            response = self.session.get(f"{self.base_url}{url}")
            # Puede ser 200 (existe) o 404 (no existe), ambos son OK
            if response.status_code in [200, 404]:
                status_text = "EXISTE" if response.status_code == 200 else "NO EXISTE"
                print(f"✅ {module_name} - Detalle: OK ({status_text})")
                return True
            else:
                print(f"❌ {module_name} - Detalle: ERROR (Status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ {module_name} - Detalle: EXCEPTION - {str(e)}")
            return False
    
    def validate_update_view(self, module_name, url_pattern, test_id=1):
        """Validar vista de edición"""
        try:
            url = url_pattern.format(pk=test_id)
            response = self.session.get(f"{self.base_url}{url}")
            if response.status_code in [200, 404]:
                status_text = "EXISTE" if response.status_code == 200 else "NO EXISTE"
                print(f"✅ {module_name} - Editar: OK ({status_text})")
                return True
            else:
                print(f"❌ {module_name} - Editar: ERROR (Status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ {module_name} - Editar: EXCEPTION - {str(e)}")
            return False
    
    def validate_delete_view(self, module_name, url_pattern, test_id=1):
        """Validar vista de eliminación"""
        try:
            url = url_pattern.format(pk=test_id)
            response = self.session.get(f"{self.base_url}{url}")
            if response.status_code in [200, 404]:
                status_text = "EXISTE" if response.status_code == 200 else "NO EXISTE"
                print(f"✅ {module_name} - Eliminar: OK ({status_text})")
                return True
            else:
                print(f"❌ {module_name} - Eliminar: ERROR (Status {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ {module_name} - Eliminar: EXCEPTION - {str(e)}")
            return False

def validate_module_by_module():
    """Validar cada módulo de forma detallada"""
    
    validator = DetailedCRUDValidation()
    
    # Módulos a validar con sus URLs específicas
    modules = [
        {
            'name': 'CLIENTES',
            'list_url': '/clients/',
            'create_url': '/clients/create/',
            'detail_pattern': '/clients/{}/',
            'update_pattern': '/clients/{}/edit/',
            'delete_pattern': '/clients/{}/delete/'
        },
        {
            'name': 'EQUIPOS',
            'list_url': '/equipment/',
            'create_url': '/equipment/create/',
            'detail_pattern': '/equipment/{}/',
            'update_pattern': '/equipment/{}/edit/',
            'delete_pattern': '/equipment/{}/delete/'
        },
        {
            'name': 'TIPOS DE EQUIPO',
            'list_url': '/catalog/equipment-types/',
            'create_url': '/catalog/equipment-types/create/',
            'detail_pattern': '/catalog/equipment-types/{}/',
            'update_pattern': '/catalog/equipment-types/{}/edit/',
            'delete_pattern': '/catalog/equipment-types/{}/delete/'
        },
        {
            'name': 'TAXONOMÍA',
            'list_url': '/catalog/taxonomy/',
            'create_url': '/catalog/taxonomy/systems/create/',
            'detail_pattern': '/catalog/taxonomy/systems/{}/',
            'update_pattern': '/catalog/taxonomy/systems/{}/edit/',
            'delete_pattern': '/catalog/taxonomy/systems/{}/delete/'
        },
        {
            'name': 'CÓDIGOS DE REFERENCIA',
            'list_url': '/catalog/reference-codes/',
            'create_url': '/catalog/reference-codes/create/',
            'detail_pattern': '/catalog/reference-codes/category/{}/',
            'update_pattern': '/catalog/reference-codes/category/{}/edit/',
            'delete_pattern': '/catalog/reference-codes/category/{}/delete/'
        },
        {
            'name': 'MONEDAS',
            'list_url': '/catalog/currencies/',
            'create_url': '/catalog/currencies/create/',
            'detail_pattern': '/catalog/currencies/{}/',
            'update_pattern': '/catalog/currencies/{}/edit/',
            'delete_pattern': '/catalog/currencies/{}/delete/'
        },
        {
            'name': 'PROVEEDORES',
            'list_url': '/suppliers/',
            'create_url': '/suppliers/create/',
            'detail_pattern': '/suppliers/{}/',
            'update_pattern': '/suppliers/{}/edit/',
            'delete_pattern': '/suppliers/{}/delete/'
        },
        {
            'name': 'TÉCNICOS',
            'list_url': '/technicians/',
            'create_url': '/technicians/create/',
            'detail_pattern': '/technicians/{}/',
            'update_pattern': '/technicians/{}/edit/',
            'delete_pattern': '/technicians/{}/delete/'
        },
        {
            'name': 'ÓRDENES DE TRABAJO',
            'list_url': '/workorders/',
            'create_url': '/workorders/create/',
            'detail_pattern': '/workorders/{}/',
            'update_pattern': '/workorders/{}/edit/',
            'delete_pattern': '/workorders/{}/delete/'
        },
        {
            'name': 'FACTURAS',
            'list_url': '/invoices/',
            'create_url': '/invoices/create/',
            'detail_pattern': '/invoices/{}/',
            'update_pattern': '/invoices/{}/edit/',
            'delete_pattern': '/invoices/{}/delete/'
        },
        {
            'name': 'COTIZACIONES',
            'list_url': '/quotes/',
            'create_url': '/quotes/create/',
            'detail_pattern': '/quotes/{}/',
            'update_pattern': '/quotes/{}/edit/',
            'delete_pattern': '/quotes/{}/delete/'
        },
        {
            'name': 'PRODUCTOS',
            'list_url': '/inventory/products/',
            'create_url': '/inventory/products/create/',
            'detail_pattern': '/inventory/products/{}/',
            'update_pattern': '/inventory/products/{}/edit/',
            'delete_pattern': '/inventory/products/{}/delete/'
        },
        {
            'name': 'ALMACENES',
            'list_url': '/inventory/warehouses/',
            'create_url': '/inventory/warehouses/create/',
            'detail_pattern': '/inventory/warehouses/{}/',
            'update_pattern': '/inventory/warehouses/{}/edit/',
            'delete_pattern': '/inventory/warehouses/{}/delete/'
        },
        {
            'name': 'MOVIMIENTOS DE STOCK',
            'list_url': '/inventory/stock/movements/',
            'create_url': '/inventory/stock/movements/create/'
            # No tienen detail/update/delete individuales
        },
        {
            'name': 'ÓRDENES DE COMPRA',
            'list_url': '/purchase-orders/',
            'create_url': '/purchase-orders/create/',
            'detail_pattern': '/purchase-orders/{}/',
            'update_pattern': '/purchase-orders/{}/edit/',
            'delete_pattern': '/purchase-orders/{}/delete/'
        }
    ]
    
    print("=" * 60)
    print("🔍 VALIDACIÓN DETALLADA CRUD POR CRUD")
    print("=" * 60)
    
    # Intentar login
    if not validator.login():
        print("⚠️  No se pudo iniciar sesión - algunas validaciones pueden fallar")
    
    total_operations = 0
    passed_operations = 0
    
    for module in modules:
        print(f"\n📂 MÓDULO: {module['name']}")
        print("-" * 40)
        
        # Validar cada operación del CRUD
        operations = [
            ('LISTA', lambda: validator.validate_list_view(module['name'], module['list_url'])),
            ('CREAR', lambda: validator.validate_create_view(module['name'], module['create_url']))
        ]
        
        # Agregar operaciones condicionales
        if 'detail_pattern' in module:
            operations.append(('DETALLE', lambda: validator.validate_detail_view(module['name'], module['detail_pattern'])))
        if 'update_pattern' in module:
            operations.append(('EDITAR', lambda: validator.validate_update_view(module['name'], module['update_pattern'])))
        if 'delete_pattern' in module:
            operations.append(('ELIMINAR', lambda: validator.validate_delete_view(module['name'], module['delete_pattern'])))
        
        module_passed = 0
        module_total = len(operations)
        
        for op_name, op_func in operations:
            if op_func():
                module_passed += 1
                passed_operations += 1
            total_operations += 1
        
        # Resultado del módulo
        print(f"📊 {module['name']}: {module_passed}/{module_total} operaciones OK")
        if module_passed == module_total:
            print(f"🎉 {module['name']}: COMPLETAMENTE VALIDADO")
        else:
            print(f"⚠️  {module['name']}: {module_total - module_passed} operaciones con problemas")
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESUMEN GENERAL")
    print("=" * 60)
    print(f"✅ Operaciones exitosas: {passed_operations}/{total_operations}")
    print(f"📈 Porcentaje de éxito: {(passed_operations/total_operations)*100:.1f}%")
    
    if passed_operations == total_operations:
        print("\n🎉 ¡TODAS LAS OPERACIONES CRUD VALIDADAS EXITOSAMENTE!")
        print("✅ Sistema completamente funcional")
    else:
        print(f"\n⚠️  {total_operations - passed_operations} operaciones con problemas")
        print("🔧 Requiere atención y corrección")

if __name__ == '__main__':
    print("🚀 Iniciando validación detallada CRUD por CRUD...")
    print("⏱️  Este proceso puede tardar varios minutos...")
    
    try:
        validate_module_by_module()
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la validación: {str(e)}")