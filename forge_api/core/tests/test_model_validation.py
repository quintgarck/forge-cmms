"""
Property-based tests for model validation
**Feature: forge-api-rest, Property 7: Entity creation validation consistency**
**Validates: Requirements 2.2**

This module tests that all model instances are properly validated according to
business rules and constraints.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, datetime

from core.models import (
    Alert, BusinessRule, AuditLog, Technician, Client, Equipment,
    Warehouse, ProductMaster, Stock, Transaction, WorkOrder, Invoice, Document
)


class ModelValidationPropertyTests(TestCase):
    """Property-based tests for model validation consistency"""

    def setUp(self):
        """Set up test data"""
        self.technician = Technician.objects.create(
            employee_code='TECH001',
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            hire_date=date(2023, 1, 1),
            status='active'
        )

    def test_technician_email_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Email addresses must be unique across all technicians
        """
        # Try to create another technician with the same email
        with self.assertRaises(IntegrityError):
            Technician.objects.create(
                employee_code='TECH002',
                first_name='Jane',
                last_name='Smith',
                email='john.doe@test.com',  # Same email as existing technician
                hire_date=date(2023, 1, 1),
                status='active'
            )

    def test_technician_employee_code_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Employee codes must be unique across all technicians
        """
        # Try to create another technician with the same employee code
        with self.assertRaises(IntegrityError):
            Technician.objects.create(
                employee_code='TECH001',  # Same code as existing technician
                first_name='Jane',
                last_name='Smith',
                email='jane.smith@test.com',
                hire_date=date(2023, 1, 1),
                status='active'
            )

    def test_client_code_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Client codes must be unique across all clients
        """
        # Create first client
        Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client 1',
            status='active',
            created_by=self.technician
        )
        
        # Try to create another client with the same code
        with self.assertRaises(IntegrityError):
            Client.objects.create(
                client_code='CLIENT001',  # Same code as existing client
                type='business',
                name='Test Client 2',
                status='active',
                created_by=self.technician
            )

    def test_equipment_vin_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        VIN numbers must be unique across all equipment when provided
        """
        client = Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client',
            status='active',
            created_by=self.technician
        )
        
        # Create first equipment with VIN
        Equipment.objects.create(
            client=client,
            equipment_code='EQ001',
            vin='1HGBH41JXMN109186',
            year=2020,
            make='Honda',
            model='Civic',
            status='active'
        )
        
        # Try to create another equipment with the same VIN
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(
                client=client,
                equipment_code='EQ002',
                vin='1HGBH41JXMN109186',  # Same VIN as existing equipment
                year=2021,
                make='Toyota',
                model='Camry',
                status='active'
            )

    def test_equipment_year_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Equipment year must be within reasonable bounds
        """
        client = Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client',
            status='active',
            created_by=self.technician
        )
        
        # Test invalid year (too old)
        equipment = Equipment(
            client=client,
            equipment_code='EQ001',
            year=1800,  # Invalid year
            make='Honda',
            model='Civic',
            status='active'
        )
        
        with self.assertRaises(ValidationError):
            equipment.full_clean()
        
        # Test invalid year (too new)
        equipment = Equipment(
            client=client,
            equipment_code='EQ002',
            year=2050,  # Invalid year
            make='Honda',
            model='Civic',
            status='active'
        )
        
        with self.assertRaises(ValidationError):
            equipment.full_clean()

    def test_product_code_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Product codes must be unique across all products
        """
        # Create first product
        ProductMaster.objects.create(
            product_code='PROD001',
            type='part',
            name='Test Product 1',
            status='active'
        )
        
        # Try to create another product with the same code
        with self.assertRaises(IntegrityError):
            ProductMaster.objects.create(
                product_code='PROD001',  # Same code as existing product
                type='fluid',
                name='Test Product 2',
                status='active'
            )

    def test_warehouse_code_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Warehouse codes must be unique across all warehouses
        """
        # Create first warehouse
        Warehouse.objects.create(
            warehouse_code='WH001',
            name='Main Warehouse',
            status='active'
        )
        
        # Try to create another warehouse with the same code
        with self.assertRaises(IntegrityError):
            Warehouse.objects.create(
                warehouse_code='WH001',  # Same code as existing warehouse
                name='Secondary Warehouse',
                status='active'
            )

    def test_work_order_number_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Work order numbers must be unique across all work orders
        """
        client = Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client',
            status='active',
            created_by=self.technician
        )
        
        equipment = Equipment.objects.create(
            client=client,
            equipment_code='EQ001',
            year=2020,
            make='Honda',
            model='Civic',
            status='active'
        )
        
        # Create first work order
        WorkOrder.objects.create(
            wo_number='WO001',
            client=client,
            equipment=equipment,
            description='Test work order 1',
            status='draft'
        )
        
        # Try to create another work order with the same number
        with self.assertRaises(IntegrityError):
            WorkOrder.objects.create(
                wo_number='WO001',  # Same number as existing work order
                client=client,
                equipment=equipment,
                description='Test work order 2',
                status='draft'
            )

    def test_invoice_number_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Invoice numbers must be unique across all invoices
        """
        client = Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client',
            status='active',
            created_by=self.technician
        )
        
        # Create first invoice
        Invoice.objects.create(
            invoice_number='INV001',
            client=client,
            due_date=date(2024, 1, 31),
            total_amount=Decimal('100.00')
        )
        
        # Try to create another invoice with the same number
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(
                invoice_number='INV001',  # Same number as existing invoice
                client=client,
                due_date=date(2024, 2, 28),
                total_amount=Decimal('200.00')
            )

    def test_stock_warehouse_product_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Stock records must be unique per warehouse-product combination
        """
        warehouse = Warehouse.objects.create(
            warehouse_code='WH001',
            name='Main Warehouse',
            status='active'
        )
        
        product = ProductMaster.objects.create(
            product_code='PROD001',
            type='part',
            name='Test Product',
            status='active'
        )
        
        # Create first stock record
        Stock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity_on_hand=100
        )
        
        # Try to create another stock record for the same warehouse-product combination
        with self.assertRaises(IntegrityError):
            Stock.objects.create(
                warehouse=warehouse,
                product=product,  # Same warehouse-product combination
                quantity_on_hand=50
            )

    def test_business_rule_code_uniqueness_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Business rule codes must be unique across all business rules
        """
        # Create first business rule
        BusinessRule.objects.create(
            rule_code='BR001',
            rule_name='Test Rule 1',
            condition_text='test condition',
            action_type='alert',
            action_text='test action'
        )
        
        # Try to create another business rule with the same code
        with self.assertRaises(IntegrityError):
            BusinessRule.objects.create(
                rule_code='BR001',  # Same code as existing rule
                rule_name='Test Rule 2',
                condition_text='another condition',
                action_type='warn',
                action_text='another action'
            )

    def test_model_choice_field_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Choice fields must only accept valid choices
        """
        # Test invalid alert type
        alert = Alert(
            alert_type='invalid_type',  # Not in ALERT_TYPES choices
            title='Test Alert',
            message='Test message',
            severity='medium',
            status='new'
        )
        
        with self.assertRaises(ValidationError):
            alert.full_clean()
        
        # Test invalid client type
        client = Client(
            client_code='CLIENT001',
            type='invalid_type',  # Not in TYPE_CHOICES
            name='Test Client',
            status='active',
            created_by=self.technician
        )
        
        with self.assertRaises(ValidationError):
            client.full_clean()

    def test_decimal_field_precision_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Decimal fields must respect precision and scale constraints
        """
        # Test technician hourly rate with too many decimal places
        technician = Technician(
            employee_code='TECH002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@test.com',
            hire_date=date(2023, 1, 1),
            hourly_rate=Decimal('25.123'),  # Too many decimal places (should be 2)
            status='active'
        )
        
        # This should raise a validation error due to too many decimal places
        with self.assertRaises(ValidationError):
            technician.full_clean()
        
        # Test with valid decimal places
        technician_valid = Technician(
            employee_code='TECH003',
            first_name='Bob',
            last_name='Johnson',
            email='bob.johnson@test.com',
            hire_date=date(2023, 1, 1),
            hourly_rate=Decimal('25.12'),  # Valid decimal places
            status='active'
        )
        
        # This should not raise an error
        technician_valid.full_clean()
        technician_valid.save()
        
        # Verify the value was saved correctly
        saved_technician = Technician.objects.get(employee_code='TECH003')
        self.assertEqual(saved_technician.hourly_rate, Decimal('25.12'))

    def test_required_field_validation(self):
        """
        **Feature: forge-api-rest, Property 7: Entity creation validation consistency**
        **Validates: Requirements 2.2**
        
        Required fields must not be empty or null
        """
        # Test missing required fields for Technician
        technician = Technician(
            # Missing employee_code (required)
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@test.com',
            hire_date=date(2023, 1, 1),
            status='active'
        )
        
        with self.assertRaises(ValidationError):
            technician.full_clean()
        
        # Test missing required fields for Client
        client = Client(
            client_code='CLIENT002',
            # Missing type (required)
            name='Test Client',
            status='active',
            created_by=self.technician
        )
        
        with self.assertRaises(ValidationError):
            client.full_clean()