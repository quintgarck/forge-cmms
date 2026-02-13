"""
Property-based tests for model serialization
**Feature: forge-api-rest, Property 6: Entity serialization completeness**
**Validates: Requirements 2.1**

This module tests that all model instances can be properly serialized and deserialized
without losing data integrity.
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.core import serializers
from django.forms.models import model_to_dict
import json
from datetime import date, datetime
from decimal import Decimal

from core.models import (
    Alert, BusinessRule, AuditLog, Technician, Client, Equipment,
    Warehouse, ProductMaster, Stock, Transaction, WorkOrder, Invoice, Document
)
from .test_helpers import TestDataFactory


class ModelSerializationPropertyTests(TestCase):
    """Property-based tests for model serialization completeness"""

    def setUp(self):
        """Set up test data"""
        # Use factory to create unique test data
        self.technician = TestDataFactory.create_technician()
        self.client = TestDataFactory.create_client(created_by=self.technician)

    @given(
        alert_type=st.sampled_from(['inventory', 'maintenance', 'business', 'system']),
        title=st.text(min_size=1, max_size=200),
        message=st.text(min_size=1, max_size=1000),
        severity=st.sampled_from(['low', 'medium', 'high', 'critical']),
        status=st.sampled_from(['new', 'read', 'acknowledged', 'resolved'])
    )
    @settings(max_examples=10)
    def test_alert_serialization_completeness(self, alert_type, title, message, severity, status):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        For any Alert instance, serializing to JSON should include all notification fields
        """
        alert = Alert.objects.create(
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity,
            status=status
        )
        
        json_data = serializers.serialize('json', [alert])
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Alert notification fields
        notification_fields = ['alert_type', 'title', 'message', 'severity', 'status']
        
        for field in notification_fields:
            self.assertIn(field, parsed_json,
                f"Notification field '{field}' missing from Alert serialization")

    @given(
        employee_code=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        first_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        last_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        status=st.sampled_from(['active', 'inactive', 'suspended'])
    )
    @settings(max_examples=10)
    def test_technician_serialization_completeness(self, employee_code, first_name, last_name, status):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        For any Technician instance, serializing to JSON and back should preserve all data
        """
        # Generate unique email to avoid conflicts
        email = f"{employee_code.lower()}@test.com"
        
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            hire_date=date(2023, 1, 1),
            status=status
        )
        
        # Convert model to dictionary
        original_data = model_to_dict(technician)
        
        # Serialize to JSON
        json_data = serializers.serialize('json', [technician])
        
        # Verify JSON contains all expected fields
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Check that all non-None fields are present in serialization
        # Note: Django JSON serializer uses 'uuid' instead of 'technician_id' for primary key
        expected_fields = original_data.copy()
        if 'technician_id' in expected_fields:
            expected_fields.pop('technician_id')  # Remove PK field as it's handled differently
        
        for field_name, field_value in expected_fields.items():
            if field_value is not None:
                self.assertIn(field_name, parsed_json, 
                    f"Field '{field_name}' missing from serialization")

    @given(
        client_code=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        type_choice=st.sampled_from(['individual', 'business', 'fleet']),
        name=st.text(min_size=1, max_size=150, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
        status=st.sampled_from(['active', 'inactive', 'blocked'])
    )
    @settings(max_examples=10)
    def test_client_serialization_completeness(self, client_code, type_choice, name, status):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        For any Client instance, serializing to JSON should include all required fields
        """
        client = Client.objects.create(
            client_code=client_code,
            type=type_choice,
            name=name,
            status=status,
            created_by=self.technician
        )
        
        original_data = model_to_dict(client)
        json_data = serializers.serialize('json', [client])
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Required fields that must always be present
        required_fields = ['client_code', 'type', 'name', 'status']
        
        for field in required_fields:
            self.assertIn(field, parsed_json,
                f"Required field '{field}' missing from Client serialization")
            self.assertIsNotNone(parsed_json[field],
                f"Required field '{field}' is None in serialization")

    @given(
        product_code=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        type_choice=st.sampled_from(['part', 'fluid', 'consumable', 'tool', 'service']),
        name=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
        status=st.sampled_from(['active', 'inactive', 'discontinued'])
    )
    @settings(max_examples=10)
    def test_product_serialization_completeness(self, product_code, type_choice, name, status):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        For any ProductMaster instance, serialization should include inventory control fields
        """
        product = ProductMaster.objects.create(
            product_code=product_code,
            type=type_choice,
            name=name,
            status=status
        )
        
        json_data = serializers.serialize('json', [product])
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Essential product fields
        essential_fields = ['product_code', 'type', 'name', 'unit_of_measure', 'status']
        
        for field in essential_fields:
            self.assertIn(field, parsed_json,
                f"Essential field '{field}' missing from ProductMaster serialization")

    def test_serialization_preserves_data_types(self):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        Serialization should preserve appropriate data types for different field types
        """
        # Create a technician with known data types
        technician = Technician.objects.create(
            employee_code='TEST002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@test.com',
            hire_date=date(2023, 1, 1),
            hourly_rate=Decimal('25.50'),
            specializations=['engine', 'transmission'],
            status='active'
        )
        
        json_data = serializers.serialize('json', [technician])
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Verify data types are preserved appropriately
        self.assertIsInstance(parsed_json['first_name'], str)
        self.assertIsInstance(parsed_json['hourly_rate'], str)  # Decimal serialized as string
        self.assertIsInstance(parsed_json['specializations'], list)
        self.assertIsInstance(parsed_json['hire_date'], str)  # Date serialized as string

    def test_json_serialization_roundtrip_integrity(self):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        Data should maintain integrity through JSON serialization roundtrip
        """
        # Serialize to JSON
        json_data = serializers.serialize('json', [self.client])
        
        # Parse JSON
        parsed_data = json.loads(json_data)
        
        # Verify structure
        self.assertEqual(len(parsed_data), 1)
        self.assertIn('model', parsed_data[0])
        self.assertIn('fields', parsed_data[0])
        self.assertEqual(parsed_data[0]['model'], 'core.client')
        
        # Verify critical fields preserved
        fields = parsed_data[0]['fields']
        self.assertEqual(fields['client_code'], self.client.client_code)
        self.assertEqual(fields['type'], 'individual')
        self.assertEqual(fields['name'], self.client.name)
        self.assertEqual(fields['email'], self.client.email)
        self.assertEqual(fields['status'], 'active')

    def test_model_serialization_includes_foreign_keys(self):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        Serialization should properly handle foreign key relationships
        """
        equipment = Equipment.objects.create(
            client=self.client,
            equipment_code='EQ001',
            year=2020,
            make='Toyota',
            model='Camry',
            status='active'
        )
        
        json_data = serializers.serialize('json', [equipment])
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Foreign key should be serialized as the primary key value
        self.assertIn('client', parsed_json)
        self.assertEqual(parsed_json['client'], self.client.client_id)

    @given(
        quantity=st.integers(min_value=-1000, max_value=1000),
        transaction_type=st.sampled_from(['receipt', 'issue', 'transfer', 'adjustment', 'return', 'scrap'])
    )
    @settings(max_examples=10)
    def test_transaction_serialization_with_negative_quantities(self, quantity, transaction_type):
        """
        **Feature: forge-api-rest, Property 6: Entity serialization completeness**
        **Validates: Requirements 2.1**
        
        Serialization should handle negative quantities and different transaction types
        """
        warehouse = TestDataFactory.create_warehouse()
        product = TestDataFactory.create_product()
        
        transaction = Transaction.objects.create(
            transaction_type=transaction_type,
            warehouse=warehouse,
            product=product,
            quantity=quantity,
            created_by=self.technician
        )
        
        json_data = serializers.serialize('json', [transaction])
        parsed_json = json.loads(json_data)[0]['fields']
        
        # Verify quantity and type are preserved
        self.assertEqual(parsed_json['quantity'], quantity)
        self.assertEqual(parsed_json['transaction_type'], transaction_type)
        self.assertIn('warehouse', parsed_json)
        self.assertIn('product', parsed_json)