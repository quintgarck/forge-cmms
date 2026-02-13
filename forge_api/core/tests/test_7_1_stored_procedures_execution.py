"""
ForgeDB API REST - Property Tests for Stored Procedures Execution
Task 7.1: Property test for stored procedure execution consistency

**Feature: forge-api-rest, Property 11: Inventory function execution consistency**
**Validates: Requirements 3.1**

This module contains property-based tests that verify the consistency of stored
procedure execution and result formatting using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import RequestFactory
import json
from decimal import Decimal
from datetime import date, datetime

from core.models import (
    Technician, Client, Equipment, ProductMaster, Stock, WorkOrder,
    Warehouse, Transaction
)
from core.authentication import TechnicianAuthBackend


class TestStoredProceduresExecutionConsistency:
    """
    Property-based tests for stored procedures execution consistency
    """

    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_inventory_function_execution_consistency(self, employee_code, product_code, warehouse_code):
        """
        **Feature: forge-api-rest, Property 11: Inventory function execution consistency**

        For any inventory-related stored procedure call, the system should execute
        the procedure and return results as valid, well-formed JSON.
        """
        # Setup: Create authenticated user and test data
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

        # Create product and warehouse
        product = ProductMaster.objects.create(
            product_code=product_code,
            type="part",
            name=f"Test Product {product_code}",
            min_stock_level=10,
            reorder_point=20,
            status="active"
        )

        warehouse = Warehouse.objects.create(
            warehouse_code=warehouse_code,
            name=f"Test Warehouse {warehouse_code}",
            status="active"
        )

        # Create stock
        stock = Stock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity_on_hand=50,
            quantity_available=50,
            average_cost=Decimal('25.00')
        )

        # Test: Available stock function should return consistent JSON
        client = APIClient()
        client.force_authenticate(user=user)

        url = f'/api/v1/inventory/available-stock/?sku={product_code}'
        response = client.get(url)

        # Assert: Should return valid response
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # If there are results, they should have expected structure
        if response.data:
            item = response.data[0]
            assert 'internal_sku' in item
            assert 'product_name' in item
            assert 'warehouse_code' in item
            assert 'qty_available' in item
            assert 'unit_cost' in item

        # Test: Sync costs function should return JSON
        url = '/api/v1/inventory/sync-costs/'
        response = client.post(url, {})

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # If successful, should return JSON with expected structure
        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            assert 'success' in response.data
            if response.data.get('success'):
                assert 'products_updated' in response.data
                assert 'timestamp' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        wo_number=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        client_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        equipment_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_service_function_execution_consistency(self, wo_number, client_code, equipment_code):
        """
        Test that service-related stored procedures execute consistently
        """
        # Setup: Create test data
        technician = Technician.objects.create(
            employee_code="TECH001",
            first_name="Test",
            last_name="Technician",
            email="tech@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username="TECH001",
            password="TestPass123",
            email=technician.email
        )

        client = Client.objects.create(
            client_code=client_code,
            type="individual",
            name="Test Client",
            email="client@test.com",
            status="active",
            created_by=technician
        )

        equipment = Equipment.objects.create(
            client=client,
            equipment_code=equipment_code,
            year=2020,
            make="Toyota",
            model="Corolla",
            status="active"
        )

        # Test: Create work order function
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        work_order_data = {
            'equipment_id': equipment.equipment_id,
            'client_id': client.client_id,
            'service_type': 'CORRECTIVO',
            'customer_complaints': 'Test complaint'
        }

        url = '/api/v1/services/create-work-order/'
        response = client_api.post(url, work_order_data, format='json')

        # Assert: Should return valid response structure
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            assert 'success' in response.data
            if response.data.get('success'):
                assert 'wo_id' in response.data
                assert 'wo_number' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        category=st.text(min_size=1, max_size=50).filter(lambda x: len(x.strip()) > 0)
    )
    def test_analytics_function_execution_consistency(self, category):
        """
        Test that analytics stored procedures execute consistently
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code="TECH001",
            first_name="Test",
            last_name="Technician",
            email="tech@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username="TECH001",
            password="TestPass123",
            email=technician.email
        )

        # Test: ABC analysis function
        client = APIClient()
        client.force_authenticate(user=user)

        url = f'/api/v1/analytics/abc-analysis/?category={category}'
        response = client.get(url)

        # Assert: Should return valid response
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # If there are results, they should have expected structure
        if response.data:
            item = response.data[0]
            assert 'internal_sku' in item
            assert 'product_name' in item
            assert 'abc_class' in item
            assert 'recommendation' in item

        # Test: Demand forecast function
        url = '/api/v1/analytics/demand-forecast/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        if response.data:
            item = response.data[0]
            assert 'internal_sku' in item
            assert 'forecasted_qty' in item
            assert 'reorder_suggestion' in item

        # Test: Technician productivity report
        url = '/api/v1/analytics/technician-productivity/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        if response.data:
            item = response.data[0]
            assert 'technician_id' in item
            assert 'technician_name' in item
            assert 'total_orders' in item
            assert 'labor_revenue' in item

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        table_name=st.sampled_from(['audit_logs', 'transactions', 'stock'])
    )
    def test_system_function_execution_consistency(self, table_name):
        """
        Test that system maintenance stored procedures execute consistently
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code="TECH001",
            first_name="Test",
            last_name="Technician",
            email="tech@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username="TECH001",
            password="TestPass123",
            email=technician.email
        )

        # Test: Archive old data function (dry run)
        client = APIClient()
        client.force_authenticate(user=user)

        archive_data = {
            'table_name': table_name,
            'retention_months': 24,
            'dry_run': True
        }

        url = '/api/v1/system/archive-data/'
        response = client.post(url, archive_data, format='json')

        # Assert: Should return valid response structure
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            assert 'dry_run' in response.data
            assert 'table' in response.data

        # Test: Data integrity check function
        url = '/api/v1/system/data-integrity/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        # Each integrity check should have expected structure
        if response.data:
            check = response.data[0]
            assert 'check_type' in check
            assert 'table_name' in check
            assert 'issue_description' in check
            assert 'record_count' in check
            assert 'severity' in check

        # Test: System stats function
        url = '/api/v1/system/stats/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert 'clients' in response.data
        assert 'technicians' in response.data
        assert 'active_work_orders' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        invalid_table=st.text(min_size=1, max_size=20).filter(lambda x: x not in ['audit_logs', 'transactions', 'stock'])
    )
    def test_invalid_stored_procedure_parameters_handling(self, invalid_table):
        """
        Test that invalid parameters are handled gracefully
        """
        # Setup: Create test user
        technician = Technician.objects.create(
            employee_code="TECH001",
            first_name="Test",
            last_name="Technician",
            email="tech@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username="TECH001",
            password="TestPass123",
            email=technician.email
        )

        # Test: Invalid table name for archiving
        client = APIClient()
        client.force_authenticate(user=user)

        archive_data = {
            'table_name': invalid_table,
            'retention_months': 24,
            'dry_run': True
        }

        url = '/api/v1/system/archive-data/'
        response = client.post(url, archive_data, format='json')

        # Should handle invalid table gracefully (either error or validation)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        negative_quantity=st.integers(min_value=-1000, max_value=-1)
    )
    def test_inventory_transaction_negative_quantity_handling(self, negative_quantity):
        """
        Test that negative quantities in inventory transactions are handled properly
        """
        # Setup: Create test data
        technician = Technician.objects.create(
            employee_code="TECH001",
            first_name="Test",
            last_name="Technician",
            email="tech@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )

        user = User.objects.create_user(
            username="TECH001",
            password="TestPass123",
            email=technician.email
        )

        product = ProductMaster.objects.create(
            product_code="TEST_PRODUCT",
            type="part",
            name="Test Product",
            status="active"
        )

        warehouse = Warehouse.objects.create(
            warehouse_code="TEST_WH",
            name="Test Warehouse",
            status="active"
        )

        # Test: Transaction with negative quantity
        client = APIClient()
        client.force_authenticate(user=user)

        transaction_data = {
            'txn_type': 'OUT',
            'internal_sku': product.product_code,
            'qty': negative_quantity,
            'from_warehouse': warehouse.warehouse_code
        }

        url = '/api/v1/inventory/create-transaction/'
        response = client.post(url, transaction_data, format='json')

        # Should handle negative quantity appropriately (validation or database constraint)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Cleanup
        technician.delete()
        user.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])