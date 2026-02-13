"""
**Feature: forge-api-rest, Property 50: Equipment type validation consistency**

Property-based test for equipment type validation consistency.
Tests that equipment type creation and updates validate category assignments 
and attribute schema compliance according to predefined automotive standards.

**Validates: Requirements 11.1**
"""

import pytest
from hypothesis import given, strategies as st, settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal

from ..models import EquipmentType, Technician
from ..serializers.main_serializers import EquipmentTypeSerializer


class TestEquipmentTypeValidationConsistency(APITestCase):
    """Property-based tests for equipment type validation consistency"""

    def setUp(self):
        """Set up test data"""
        # Create test user and technician
        self.user = User.objects.create_user(
            username='testtech',
            password='testpass123',
            email='test@example.com'
        )
        self.technician = Technician.objects.create(
            employee_code='TECH001',
            first_name='Test',
            last_name='Technician',
            email='test@example.com',
            hire_date='2023-01-01',
            status='active'
        )
        self.client.force_authenticate(user=self.user)

    # Hypothesis strategies for generating test data
    valid_categories = st.sampled_from([
        'AUTOMOTRIZ', 'INDUSTRIAL', 'AGRÍCOLA', 
        'CONSTRUCCIÓN', 'ELECTRÓNICO', 'OTRO'
    ])
    
    valid_type_codes = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=3,
        max_size=20
    ).map(lambda x: x.replace(' ', ''))
    
    valid_names = st.text(min_size=1, max_size=100)
    
    valid_attr_schemas = st.one_of(
        st.just({}),
        st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.booleans(),
                st.lists(st.text(max_size=50), max_size=10)
            ),
            max_size=10
        )
    )

    @given(
        category=valid_categories,
        type_code=valid_type_codes,
        name=valid_names,
        attr_schema=valid_attr_schemas
    )
    @settings(max_examples=100, deadline=None)
    def test_equipment_type_validation_consistency(self, category, type_code, name, attr_schema):
        """
        **Feature: forge-api-rest, Property 50: Equipment type validation consistency**
        
        For any equipment type creation or update, the system should validate 
        category assignments and attribute schema compliance according to 
        predefined automotive standards.
        """
        # Arrange: Create equipment type data
        equipment_type_data = {
            'type_code': type_code,
            'category': category,
            'name': name,
            'attr_schema': attr_schema,
            'is_active': True
        }

        # Act: Validate through serializer
        serializer = EquipmentTypeSerializer(data=equipment_type_data)
        
        # Assert: Validation should be consistent
        if serializer.is_valid():
            # If validation passes, the equipment type should be creatable
            equipment_type = serializer.save()
            
            # Verify the saved data matches expected standards
            assert equipment_type.category in [
                'AUTOMOTRIZ', 'INDUSTRIAL', 'AGRÍCOLA', 
                'CONSTRUCCIÓN', 'ELECTRÓNICO', 'OTRO'
            ]
            assert len(equipment_type.type_code) >= 3
            assert len(equipment_type.type_code) <= 20
            assert len(equipment_type.name) >= 1
            assert len(equipment_type.name) <= 100
            assert isinstance(equipment_type.attr_schema, dict)
            
            # Clean up
            equipment_type.delete()
        else:
            # If validation fails, it should be for valid reasons
            errors = serializer.errors
            
            # Check that errors are related to expected validation rules
            if 'type_code' in errors:
                # Type code validation should be consistent
                assert any(
                    'required' in str(error).lower() or
                    'blank' in str(error).lower() or
                    'length' in str(error).lower()
                    for error in errors['type_code']
                )
            
            if 'category' in errors:
                # Category validation should be consistent
                assert any(
                    'invalid choice' in str(error).lower() or
                    'required' in str(error).lower()
                    for error in errors['category']
                )

    @given(
        category=st.text(min_size=1, max_size=50).filter(
            lambda x: x not in ['AUTOMOTRIZ', 'INDUSTRIAL', 'AGRÍCOLA', 
                               'CONSTRUCCIÓN', 'ELECTRÓNICO', 'OTRO']
        ),
        type_code=valid_type_codes,
        name=valid_names
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_category_rejection(self, category, type_code, name):
        """
        Test that invalid categories are consistently rejected
        """
        equipment_type_data = {
            'type_code': type_code,
            'category': category,
            'name': name,
            'is_active': True
        }

        serializer = EquipmentTypeSerializer(data=equipment_type_data)
        
        # Invalid categories should always be rejected
        assert not serializer.is_valid()
        assert 'category' in serializer.errors

    @given(
        category=valid_categories,
        name=valid_names
    )
    @settings(max_examples=50, deadline=None)
    def test_missing_type_code_rejection(self, category, name):
        """
        Test that missing type codes are consistently rejected
        """
        equipment_type_data = {
            'category': category,
            'name': name,
            'is_active': True
            # Missing type_code
        }

        serializer = EquipmentTypeSerializer(data=equipment_type_data)
        
        # Missing type code should always be rejected
        assert not serializer.is_valid()
        assert 'type_code' in serializer.errors

    def test_api_endpoint_validation_consistency(self):
        """
        Test that API endpoint validation is consistent with serializer validation
        """
        # Test valid equipment type creation via API
        valid_data = {
            'type_code': 'AUTO001',
            'category': 'AUTOMOTRIZ',
            'name': 'Passenger Vehicle',
            'description': 'Standard passenger vehicle type',
            'is_active': True,
            'attr_schema': {
                'engine_types': ['gasoline', 'diesel', 'hybrid'],
                'max_passengers': 8
            }
        }

        response = self.client.post('/api/v1/catalog/equipment-types/', valid_data, format='json')
        
        # Should create successfully
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify response data
        response_data = response.json()
        assert response_data['type_code'] == 'AUTO001'
        assert response_data['category'] == 'AUTOMOTRIZ'
        assert response_data['name'] == 'Passenger Vehicle'
        
        # Test invalid category via API
        invalid_data = valid_data.copy()
        invalid_data['category'] = 'INVALID_CATEGORY'
        invalid_data['type_code'] = 'AUTO002'
        
        response = self.client.post('/api/v1/catalog/equipment-types/', invalid_data, format='json')
        
        # Should reject invalid category
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'category' in response.json()

    def tearDown(self):
        """Clean up test data"""
        # Clean up any remaining equipment types
        EquipmentType.objects.filter(type_code__startswith='AUTO').delete()
        EquipmentType.objects.filter(type_code__startswith='TEST').delete()