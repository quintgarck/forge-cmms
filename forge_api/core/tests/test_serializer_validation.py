"""
Property-based tests for DRF serializer validation
**Feature: forge-api-rest, Property 10: Validation error detail completeness**
**Validates: Requirements 2.5**

This module tests that all DRF serializers properly validate data and
provide complete error details for invalid inputs.
"""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone

from core.models import (
    Alert, BusinessRule, Technician, Client, Equipment,
    Warehouse, ProductMaster, Stock, Transaction, WorkOrder, Invoice, Document
)
from core.serializers import (
    AlertSerializer, BusinessRuleSerializer, TechnicianSerializer,
    ClientSerializer, EquipmentSerializer, WarehouseSerializer,
    ProductMasterSerializer, StockSerializer, TransactionSerializer,
    WorkOrderSerializer, InvoiceSerializer, DocumentSerializer
)


from .test_helpers import TestDataFactory


class SerializerValidationPropertyTests(TestCase):
    """
    Property-based tests for serializer validation consistency
    **Feature: forge-api-rest, Property 10: Validation error detail completeness**
    **Validates: Requirements 2.5**
    """

    def setUp(self):
        """Set up test data"""
        self.technician = TestDataFactory.create_technician()
        self.client = TestDataFactory.create_client(created_by=self.technician)

    def test_property_code_validation_consistency(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        For any entity with a code field, invalid characters should be rejected consistently
        """
        # Test cases with invalid characters
        invalid_codes = ['CODE@123', 'CODE#456', 'CODE$789', 'CODE%000']
        
        # Test technician employee_code validation
        for invalid_code in invalid_codes:
            data = {
                'employee_code': invalid_code,
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'hire_date': date(2023, 1, 1),
                'status': 'active'
            }
            serializer = TechnicianSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('employee_code', serializer.errors)
            
        # Test client client_code validation
        for invalid_code in invalid_codes:
            data = {
                'client_code': invalid_code,
                'type': 'individual',
                'name': 'Test Client',
                'email': 'client@test.com',
                'status': 'active',
                'created_by': self.technician.technician_id
            }
            serializer = ClientSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('client_code', serializer.errors)

    def test_property_negative_amount_validation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        For any entity with amount fields, negative values should be rejected where inappropriate
        """
        # Test technician hourly_rate
        data = {
            'employee_code': 'TECH002',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'hire_date': date(2023, 1, 1),
            'hourly_rate': Decimal('-10.00'),  # Negative rate
            'status': 'active'
        }
        serializer = TechnicianSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('hourly_rate', serializer.errors)
        
        # Test client credit_limit
        data = {
            'client_code': 'CLIENT002',
            'type': 'business',
            'name': 'Test Business',
            'email': 'business@test.com',
            'credit_limit': Decimal('-1000.00'),  # Negative credit
            'status': 'active',
            'created_by': self.technician.technician_id
        }
        serializer = ClientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('credit_limit', serializer.errors)

    def test_property_future_date_validation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        For any entity with historical date fields, future dates should be rejected
        """
        future_date = date.today() + timedelta(days=30)
        
        # Test technician hire_date
        data = {
            'employee_code': 'TECH003',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'hire_date': future_date,  # Future date
            'status': 'active'
        }
        serializer = TechnicianSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('hire_date', serializer.errors)
        
        # Test equipment purchase_date
        equipment_data = {
            'client': self.client.client_id,
            'equipment_code': 'EQ001',
            'year': 2020,
            'make': 'Honda',
            'model': 'Civic',
            'purchase_date': future_date,  # Future date
            'status': 'active'
        }
        serializer = EquipmentSerializer(data=equipment_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('purchase_date', serializer.errors)

    def test_property_vin_format_validation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        VIN validation should consistently reject invalid formats
        """
        invalid_vins = [
            '1HGBH41JXMN10918',  # Too short (16 chars)
            '1HGBH41JXMN1091866',  # Too long (18 chars)
            '1HGBH41JXMN10918@',  # Invalid character
            ''  # Empty string should be allowed (nullable field)
        ]
        
        for i, invalid_vin in enumerate(invalid_vins):
            data = {
                'client': self.client.client_id,
                'equipment_code': f'EQ00{i}',
                'vin': invalid_vin,
                'year': 2020,
                'make': 'Honda',
                'model': 'Civic',
                'status': 'active'
            }
            serializer = EquipmentSerializer(data=data)
            
            # Empty string should be valid (nullable field)
            if invalid_vin == '':
                self.assertTrue(serializer.is_valid())
            else:
                self.assertFalse(serializer.is_valid())
                self.assertIn('vin', serializer.errors)

    def test_property_stock_level_validation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Stock level validation should enforce business rules consistently
        """
        # Test max stock less than min stock
        data = {
            'product_code': TestDataFactory.get_unique_id(),
            'type': 'part',
            'name': 'Test Product',
            'min_stock_level': 100,
            'max_stock_level': 50,  # Less than min
            'reorder_point': 25,
            'reorder_quantity': 50,
            'status': 'active'
        }
        serializer = ProductMasterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # Test reorder point greater than min stock
        data = {
            'product_code': 'PROD002',
            'type': 'part',
            'name': 'Test Product 2',
            'min_stock_level': 50,
            'max_stock_level': 200,
            'reorder_point': 75,  # Greater than min stock
            'reorder_quantity': 50,
            'status': 'active'
        }
        serializer = ProductMasterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_property_invoice_amount_calculation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Invoice amount calculations should be consistent and validated
        """
        # Test paid amount exceeding total
        data = {
            'invoice_number': 'INV001',
            'client': self.client.client_id,
            'due_date': date.today() + timedelta(days=30),
            'subtotal': Decimal('100.00'),
            'tax_amount': Decimal('10.00'),
            'discount_amount': Decimal('5.00'),
            'paid_amount': Decimal('200.00')  # More than total (105.00)
        }
        serializer = InvoiceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # Test valid calculation
        valid_data = data.copy()
        valid_data['paid_amount'] = Decimal('50.00')
        serializer = InvoiceSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Verify calculated fields
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['total_amount'], Decimal('105.00'))
        self.assertEqual(validated_data['balance_due'], Decimal('55.00'))

    def test_property_transaction_quantity_sign_correction(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Transaction quantities should be automatically corrected based on type
        """
        warehouse = TestDataFactory.create_warehouse()
        product = TestDataFactory.create_product()
        
        # Test receipt transaction with negative quantity (should be corrected to positive)
        receipt_data = {
            'transaction_type': 'receipt',
            'warehouse': warehouse.warehouse_id,
            'product': product.product_id,
            'quantity': -50,  # Negative input
            'unit_cost': Decimal('10.00'),
            'created_by': self.technician.technician_id
        }
        serializer = TransactionSerializer(data=receipt_data)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['quantity'], 50)  # Should be positive
        
        # Test issue transaction with positive quantity (should be corrected to negative)
        issue_data = {
            'transaction_type': 'issue',
            'warehouse': warehouse.warehouse_id,
            'product': product.product_id,
            'quantity': 25,  # Positive input
            'created_by': self.technician.technician_id
        }
        serializer = TransactionSerializer(data=issue_data)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['quantity'], -25)  # Should be negative

    def test_property_work_order_status_validation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Work order status transitions should enforce business rules
        """
        equipment = Equipment.objects.create(
            client=self.client,
            equipment_code='EQ001',
            year=2020,
            make='Honda',
            model='Civic',
            status='active'
        )
        
        # Test completed status without resolution
        data = {
            'wo_number': 'WO001',
            'client': self.client.client_id,
            'equipment': equipment.equipment_id,
            'description': 'Test work order',
            'status': 'completed',  # Completed status
            'priority': 'normal'
            # Missing resolution field
        }
        serializer = WorkOrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # Test with resolution provided
        valid_data = data.copy()
        valid_data['resolution'] = 'Work completed successfully'
        serializer = WorkOrderSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Verify completed_at timestamp is set
        validated_data = serializer.validated_data
        self.assertIsNotNone(validated_data.get('completed_at'))

    def test_property_alert_timestamp_setting(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Alert status changes should automatically set appropriate timestamps
        """
        # Test resolved status sets resolved_at
        resolved_data = {
            'alert_type': 'system',
            'title': 'Test Alert',
            'message': 'Test message',
            'severity': 'medium',
            'status': 'resolved'
        }
        serializer = AlertSerializer(data=resolved_data)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertIsNotNone(validated_data.get('resolved_at'))
        self.assertIsNotNone(validated_data.get('read_at'))
        
        # Test acknowledged status sets acknowledged_at
        ack_data = resolved_data.copy()
        ack_data['status'] = 'acknowledged'
        serializer = AlertSerializer(data=ack_data)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertIsNotNone(validated_data.get('acknowledged_at'))
        self.assertIsNotNone(validated_data.get('read_at'))

    def test_property_warehouse_main_uniqueness(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Only one main warehouse should be allowed in the system
        """
        # Create first main warehouse
        TestDataFactory.create_warehouse(
            is_main=True,
            status='active'
        )
        
        # Try to create another main warehouse
        data = {
            'warehouse_code': 'WH002',
            'name': 'Another Main Warehouse',
            'is_main': True,
            'status': 'active'
        }
        serializer = WarehouseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # Test creating non-main warehouse (should work)
        valid_data = data.copy()
        valid_data['is_main'] = False
        serializer = WarehouseSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_property_document_file_validation(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Document file validation should enforce size and type restrictions
        """
        # Test file too large
        data = {
            'document_type': 'invoice',
            'title': 'Test Document',
            'file_name': 'test.pdf',
            'file_path': '/documents/test.pdf',
            'file_size': 60 * 1024 * 1024,  # 60MB (exceeds 50MB limit)
            'mime_type': 'application/pdf',
            'uploaded_by': self.technician.technician_id
        }
        serializer = DocumentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('file_size', serializer.errors)
        
        # Test invalid MIME type
        valid_data = data.copy()
        valid_data['file_size'] = 1024000  # 1MB
        valid_data['mime_type'] = 'application/x-executable'  # Not allowed
        serializer = DocumentSerializer(data=valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('mime_type', serializer.errors)
        
        # Test valid document
        valid_data['mime_type'] = 'application/pdf'
        serializer = DocumentSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_property_business_rule_code_formatting(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        Business rule codes should be formatted consistently
        """
        # Test lowercase code gets uppercased
        data = {
            'rule_code': 'br001',  # lowercase
            'rule_name': 'Test Rule',
            'condition_text': 'test condition',
            'action_type': 'alert',
            'action_text': 'test action',
            'execution_order': 100
        }
        serializer = BusinessRuleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['rule_code'], 'BR001')
        
        # Test invalid characters in rule code
        invalid_data = data.copy()
        invalid_data['rule_code'] = 'BR@001'  # Contains invalid character
        serializer = BusinessRuleSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rule_code', serializer.errors)

    def test_property_validation_error_completeness(self):
        """
        **Feature: forge-api-rest, Property 10: Validation error detail completeness**
        **Validates: Requirements 2.5**
        
        All validation errors should provide complete and helpful error messages
        """
        # Test multiple validation errors on a single serializer
        data = {
            'employee_code': 'TECH@001',  # Invalid character
            'first_name': '',  # Required field empty
            'last_name': '',  # Required field empty
            'email': 'invalid-email',  # Invalid email format
            'hire_date': date.today() + timedelta(days=30),  # Future date
            'hourly_rate': Decimal('-10.00'),  # Negative rate
            'status': 'invalid_status'  # Invalid choice
        }
        
        serializer = TechnicianSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Verify that all invalid fields have error messages
        expected_error_fields = [
            'employee_code', 'first_name', 'last_name', 
            'email', 'hire_date', 'hourly_rate', 'status'
        ]
        
        for field in expected_error_fields:
            self.assertIn(field, serializer.errors, 
                         f"Expected validation error for field: {field}")
            self.assertTrue(len(serializer.errors[field]) > 0,
                          f"Expected non-empty error message for field: {field}")
            
        # Verify error messages are descriptive
        for field, errors in serializer.errors.items():
            for error in errors:
                self.assertIsInstance(error, str)
                self.assertTrue(len(error) > 10,  # Reasonable minimum length
                              f"Error message too short for field {field}: {error}")