"""
Test helpers for ForgeDB API REST tests
Provides utilities for creating unique test data
"""
import uuid
from datetime import date
from decimal import Decimal
from core.models import Technician, Client, Equipment, Warehouse, ProductMaster


class TestDataFactory:
    """Factory for creating unique test data"""
    
    @staticmethod
    def get_unique_id():
        """Generate a unique ID for test data"""
        return str(uuid.uuid4())[:8].upper()
    
    @staticmethod
    def create_technician(**kwargs):
        """Create a technician with unique data"""
        unique_id = TestDataFactory.get_unique_id()
        defaults = {
            'employee_code': f'TECH{unique_id}',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': f'john.doe.{unique_id.lower()}@test.com',
            'hire_date': date(2023, 1, 1),
            'status': 'active'
        }
        defaults.update(kwargs)
        return Technician.objects.create(**defaults)
    
    @staticmethod
    def create_client(created_by=None, **kwargs):
        """Create a client with unique data"""
        unique_id = TestDataFactory.get_unique_id()
        defaults = {
            'client_code': f'CLI{unique_id}',
            'type': 'individual',
            'name': f'Test Client {unique_id}',
            'email': f'client.{unique_id.lower()}@test.com',
            'status': 'active'
        }
        if created_by:
            defaults['created_by'] = created_by
        defaults.update(kwargs)
        return Client.objects.create(**defaults)
    
    @staticmethod
    def create_equipment(client=None, **kwargs):
        """Create equipment with unique data"""
        unique_id = TestDataFactory.get_unique_id()
        defaults = {
            'equipment_code': f'EQ{unique_id}',
            'year': 2020,
            'make': 'Honda',
            'model': 'Civic',
            'status': 'active'
        }
        if client:
            defaults['client'] = client
        defaults.update(kwargs)
        return Equipment.objects.create(**defaults)
    
    @staticmethod
    def create_warehouse(**kwargs):
        """Create a warehouse with unique data"""
        unique_id = TestDataFactory.get_unique_id()
        defaults = {
            'warehouse_code': f'WH{unique_id}',
            'name': f'Warehouse {unique_id}',
            'status': 'active'
        }
        defaults.update(kwargs)
        return Warehouse.objects.create(**defaults)
    
    @staticmethod
    def create_product(**kwargs):
        """Create a product with unique data"""
        unique_id = TestDataFactory.get_unique_id()
        defaults = {
            'product_code': f'PROD{unique_id}',
            'type': 'part',
            'name': f'Test Product {unique_id}',
            'min_stock_level': 10,
            'max_stock_level': 100,
            'reorder_point': 20,
            'reorder_quantity': 50,
            'status': 'active'
        }
        defaults.update(kwargs)
        return ProductMaster.objects.create(**defaults)