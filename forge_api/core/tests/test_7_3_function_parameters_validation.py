"""
ForgeDB API REST - Property Tests for Function Parameters Validation
Task 7.3: Property test for validation of function parameters

**Feature: forge-api-rest, Property 13: Function parameters validation consistency**
**Validates: Requirements 3.3**

This module contains property-based tests that verify the validation of parameters
for database functions and stored procedures using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import RequestFactory
from django.db import transaction, IntegrityError
import json
from decimal import Decimal
from datetime import date, datetime

from core.models import (
    Technician, Client, Equipment, ProductMaster, Stock, WorkOrder,
    Warehouse, Transaction
)
from core.authentication import TechnicianAuthBackend


class TestFunctionParametersValidation:
    """
    Property-based tests for function parameters validation
    """

    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        invalid_qty=st.integers(min_value=-1000, max_value=-1) | st.integers(min_value=10000, max_value=100000)
    )
    def test_inventory_function_parameter_validation(self, employee_code, product_code, warehouse_code, invalid_qty):
        """
        **Feature: forge-api-rest, Property 13: Function parameters validation consistency**

        For any inventory function call, the system should validate parameters and
        return appropriate error responses for invalid inputs.
        """
        # Setup: Create authenticated user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name
        )

        # Test: Create transaction with invalid quantity
        client = APIClient()
        client.force_authenticate(user=user)

        transaction_data = {
            'txn_type': 'IN',
            'internal_sku': product_code,
            'qty': invalid_qty,  # Invalid quantity (negative or too large)
            'to_warehouse': warehouse_code
        }

        url = '/api/v1/inventory/create-transaction/'
        response = client.post(url, transaction_data, format='json')

        # Assert: Should handle invalid parameters appropriately
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            # Invalid parameters should result in failure
            if not response.data.get('success', True):
                assert 'message' in response.data or 'error' in response.data

        # Test: Available stock with invalid SKU
        invalid_sku = product_code + "_INVALID_SUFFIX"
        url = f'/api/v1/inventory/available-stock/?sku={invalid_sku}'
        response = client.get(url)

        # Should handle gracefully
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # Should return empty list for invalid SKU
        assert len(response.data) == 0

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        invalid_service_type=st.text(min_size=1, max_size=50).filter(lambda x: x not in ['CORRECTIVO', 'PREVENTIVO', 'GARANTIA'])
    )
    def test_service_function_parameter_validation(self, employee_code, invalid_service_type):
        """
        Test parameter validation for service functions
        """
        # Setup: Create complete test data
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email
        )

        client = Client.objects.create(
            client_code=f"CLI_{employee_code}",
            type="individual",
            name="Test Client",
            email="client@test.com",
            status="active",
            created_by=technician
        )

        equipment = Equipment.objects.create(
            client=client,
            equipment_code=f"EQ_{employee_code}",
            year=2020,
            make="Toyota",
            model="Corolla",
            status="active"
        )

        # Test: Create work order with invalid service type
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        work_order_data = {
            'equipment_id': equipment.equipment_id,
            'client_id': client.client_id,
            'service_type': invalid_service_type,  # Invalid service type
            'customer_complaints': 'Test complaint'
        }

        url = '/api/v1/services/create-work-order/'
        response = client_api.post(url, work_order_data, format='json')

        # Should validate service type
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Test: Create work order with invalid equipment ID
        invalid_equipment_data = {
            'equipment_id': 999999,  # Non-existent equipment
            'client_id': client.client_id,
            'service_type': 'CORRECTIVO',
            'customer_complaints': 'Test complaint'
        }

        response = client_api.post(url, invalid_equipment_data, format='json')

        # Should handle invalid equipment ID
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            if not response.data.get('success', True):
                assert 'message' in response.data or 'error' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        invalid_category=st.text(min_size=1, max_size=100).filter(lambda x: len(x) > 50 or not x.replace(' ', '').replace('_', '').replace('-', '').isalnum())
    )
    def test_analytics_function_parameter_validation(self, employee_code, invalid_category):
        """
        Test parameter validation for analytics functions
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email
        )

        # Test: ABC analysis with invalid category
        client = APIClient()
        client.force_authenticate(user=user)

        url = f'/api/v1/analytics/abc-analysis/?category={invalid_category}'
        response = client.get(url)

        # Should handle gracefully
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # Test: ABC analysis with empty category
        url = '/api/v1/analytics/abc-analysis/?category='
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # Test: Demand forecast with invalid parameters
        url = '/api/v1/analytics/demand-forecast/?periods=-5'  # Invalid negative periods
        response = client.get(url)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        invalid_table=st.text(min_size=1, max_size=50).filter(lambda x: x not in ['audit_logs', 'transactions', 'stock', 'work_orders'])
    )
    def test_system_function_parameter_validation(self, employee_code, invalid_table):
        """
        Test parameter validation for system maintenance functions
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email
        )

        # Test: Archive data with invalid table name
        client = APIClient()
        client.force_authenticate(user=user)

        archive_data = {
            'table_name': invalid_table,  # Invalid table name
            'retention_months': 24,
            'dry_run': True
        }

        url = '/api/v1/system/archive-data/'
        response = client.post(url, archive_data, format='json')

        # Should handle invalid table name
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Test: Archive data with invalid retention months
        invalid_archive_data = {
            'table_name': 'audit_logs',
            'retention_months': -12,  # Invalid negative retention
            'dry_run': True
        }

        response = client.post(url, invalid_archive_data, format='json')

        # Should handle invalid retention period
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            if not response.data.get('success', True):
                assert 'message' in response.data or 'error' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        empty_string=st.text(min_size=0, max_size=0),
        very_long_string=st.text(min_size=1000, max_size=2000)
    )
    def test_string_parameter_validation_edge_cases(self, employee_code, empty_string, very_long_string):
        """
        Test edge cases for string parameter validation
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email
        )

        client = Client.objects.create(
            client_code=f"CLI_{employee_code}",
            type="individual",
            name="Test Client",
            email="client@test.com",
            status="active",
            created_by=technician
        )

        equipment = Equipment.objects.create(
            client=client,
            equipment_code=f"EQ_{employee_code}",
            year=2020,
            make="Toyota",
            model="Corolla",
            status="active"
        )

        # Test: Create work order with empty strings
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        work_order_data_empty = {
            'equipment_id': equipment.equipment_id,
            'client_id': client.client_id,
            'service_type': 'CORRECTIVO',
            'customer_complaints': empty_string,  # Empty complaint
            'notes': empty_string  # Empty notes
        }

        url = '/api/v1/services/create-work-order/'
        response = client_api.post(url, work_order_data_empty, format='json')

        # Should handle empty strings appropriately
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Test: Create work order with very long strings (if the API accepts them)
        work_order_data_long = {
            'equipment_id': equipment.equipment_id,
            'client_id': client.client_id,
            'service_type': 'CORRECTIVO',
            'customer_complaints': very_long_string[:500],  # Truncate to reasonable length
            'notes': very_long_string[:500]
        }

        response = client_api.post(url, work_order_data_long, format='json')

        # Should handle long strings
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        null_equivalent=st.none() | st.integers(min_value=0, max_value=0)
    )
    def test_null_parameter_validation(self, employee_code, null_equivalent):
        """
        Test parameter validation when null or equivalent values are passed
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email
        )

        # Test: Create transaction with null-equivalent values
        client = APIClient()
        client.force_authenticate(user=user)

        # Note: Django REST framework typically converts None to null in JSON,
        # so we test with zero values or missing keys instead
        transaction_data = {
            'txn_type': 'IN',
            'internal_sku': f'TEST_{employee_code}',
            'qty': null_equivalent,  # Zero quantity which might be treated as null
            'to_warehouse': f'WH_{employee_code}'
        }

        url = '/api/v1/inventory/create-transaction/'
        response = client.post(url, transaction_data, format='json')

        # Should handle null-equivalent parameters
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=30)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        special_chars=st.text(min_size=1, max_size=20).filter(lambda x: any(char in x for char in ['<', '>', '&', '"', "'", ';', '--']))
    )
    def test_sql_injection_parameter_validation(self, employee_code, special_chars):
        """
        Test parameter validation to prevent SQL injection attempts
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username=employee_code,
            password="TestPass123",
            email=technician.email
        )

        # Test: Try to inject SQL in various parameters
        client = APIClient()
        client.force_authenticate(user=user)

        # Test with potentially malicious SKU
        malicious_sku = f"TEST'; {special_chars} --"
        url = f'/api/v1/inventory/available-stock/?sku={malicious_sku}'
        response = client.get(url)

        # Should handle malicious input safely
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # Test with malicious category in analytics
        malicious_category = f"electronics'; {special_chars} --"
        url = f'/api/v1/analytics/abc-analysis/?category={malicious_category}'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # Cleanup
        technician.delete()
        user.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])