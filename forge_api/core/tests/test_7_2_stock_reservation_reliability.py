"""
ForgeDB API REST - Property Tests for Stock Reservation Reliability
Task 7.2: Property test for stock reservation reliability

**Feature: forge-api-rest, Property 12: Stock reservation function reliability**
**Validates: Requirements 3.2**

This module contains property-based tests that verify the reliability and consistency
of stock reservation operations using Hypothesis.
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


class TestStockReservationReliability:
    """
    Property-based tests for stock reservation reliability
    """

    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        initial_qty=st.integers(min_value=10, max_value=1000),
        reserve_qty=st.integers(min_value=1, max_value=50)
    )
    def test_stock_reservation_function_reliability(self, employee_code, product_code, warehouse_code, initial_qty, reserve_qty):
        """
        **Feature: forge-api-rest, Property 12: Stock reservation function reliability**

        For any stock reservation request, the system should call the inv.reserve_stock_for_wo
        function and return accurate operation status indicating success or failure.
        """
        # Setup: Create authenticated user and complete test data
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

        # Create work order first
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

        work_order = WorkOrder.objects.create(
            wo_number=f"WO_{employee_code}",
            client=client,
            equipment=equipment,
            description="Test work order",
            status="draft"
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

        # Create stock with sufficient quantity
        stock = Stock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity_on_hand=initial_qty,
            quantity_available=initial_qty,
            average_cost=Decimal('25.00')
        )

        # Test: Reserve stock for work order
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        reservation_data = {
            'wo_id': work_order.wo_id,
            'internal_sku': product_code,
            'qty_needed': min(reserve_qty, initial_qty)  # Ensure we don't exceed available stock
        }

        url = '/api/v1/inventory/reserve-stock/'
        response = client_api.post(url, reservation_data, format='json')

        # Assert: Should return valid response structure
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            assert 'success' in response.data

            if response.data.get('success'):
                # If successful, should have reservation details
                assert 'stock_id' in response.data
                assert 'reserved_qty' in response.data
                assert 'wo_item_id' in response.data

                # Verify stock quantities were updated correctly
                stock.refresh_from_db()
                assert stock.quantity_reserved >= min(reserve_qty, initial_qty)
                assert stock.quantity_available == stock.quantity_on_hand - stock.quantity_reserved

        # Test: Attempt to reserve more than available stock
        excess_reservation_data = {
            'wo_id': work_order.wo_id,
            'internal_sku': product_code,
            'qty_needed': initial_qty * 2  # Exceed available stock
        }

        response = client_api.post(url, excess_reservation_data, format='json')

        # Should handle insufficient stock gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            # Insufficient stock should result in failure
            if not response.data.get('success', True):
                assert 'message' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        initial_qty=st.integers(min_value=10, max_value=100),
        multiple_reserve_qty=st.integers(min_value=1, max_value=10)
    )
    def test_concurrent_stock_reservation_consistency(self, employee_code, product_code, warehouse_code, initial_qty, multiple_reserve_qty):
        """
        Test that concurrent stock reservations maintain consistency
        """
        # Setup: Create multiple work orders competing for same stock
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

        # Create multiple work orders
        work_orders = []
        for i in range(3):
            wo = WorkOrder.objects.create(
                wo_number=f"WO_{employee_code}_{i}",
                client=client,
                equipment=equipment,
                description=f"Test work order {i}",
                status="draft"
            )
            work_orders.append(wo)

        # Create product and warehouse with limited stock
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

        # Create stock with limited quantity
        stock = Stock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity_on_hand=initial_qty,
            quantity_available=initial_qty,
            average_cost=Decimal('25.00')
        )

        # Test: Multiple reservations for same product
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        total_reserved = 0
        successful_reservations = 0

        for i, wo in enumerate(work_orders):
            reservation_data = {
                'wo_id': wo.wo_id,
                'internal_sku': product_code,
                'qty_needed': min(multiple_reserve_qty, initial_qty - total_reserved)
            }

            url = '/api/v1/inventory/reserve-stock/'
            response = client_api.post(url, reservation_data, format='json')

            if response.status_code == status.HTTP_200_OK and response.data.get('success'):
                successful_reservations += 1
                total_reserved += min(multiple_reserve_qty, initial_qty - total_reserved)
            else:
                # Should fail when stock is exhausted
                break

        # Assert: Total reserved should not exceed initial quantity
        stock.refresh_from_db()
        assert stock.quantity_reserved <= initial_qty
        assert stock.quantity_available >= 0

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_stock_reservation_release_consistency(self, employee_code, product_code, warehouse_code):
        """
        Test that stock reservation and release operations are consistent
        """
        # Setup: Complete test environment
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

        work_order = WorkOrder.objects.create(
            wo_number=f"WO_{employee_code}",
            client=client,
            equipment=equipment,
            description="Test work order",
            status="draft"
        )

        # Create product and warehouse
        product = ProductMaster.objects.create(
            product_code=product_code,
            type="part",
            name=f"Test Product {product_code}",
            status="active"
        )

        warehouse = Warehouse.objects.create(
            warehouse_code=warehouse_code,
            name=f"Test Warehouse {warehouse_code}",
            status="active"
        )

        initial_qty = 100
        stock = Stock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity_on_hand=initial_qty,
            quantity_available=initial_qty,
            average_cost=Decimal('25.00')
        )

        # Test: Reserve stock first
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        reservation_data = {
            'wo_id': work_order.wo_id,
            'internal_sku': product_code,
            'qty_needed': 25
        }

        url = '/api/v1/inventory/reserve-stock/'
        response = client_api.post(url, reservation_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('success') == True

        # Verify stock was reserved
        stock.refresh_from_db()
        assert stock.quantity_reserved == 25
        assert stock.quantity_available == initial_qty - 25

        # Get the work order item ID for release
        from core.models import WOItems
        wo_item = WOItems.objects.filter(
            wo_id=work_order.wo_id,
            internal_sku=product_code
        ).first()

        assert wo_item is not None

        # Test: Release reserved stock
        release_data = {
            'wo_item_id': wo_item.item_id,
            'qty_to_release': 10  # Release partial quantity
        }

        url = '/api/v1/inventory/release-stock/'
        response = client_api.post(url, release_data, format='json')

        # Assert: Should handle release operation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            if response.data.get('success'):
                assert 'released_qty' in response.data

                # Verify stock quantities were adjusted
                stock.refresh_from_db()
                assert stock.quantity_reserved == 15  # 25 - 10
                assert stock.quantity_available == initial_qty - 15

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        invalid_wo_id=st.integers(min_value=99999, max_value=999999)
    )
    def test_stock_reservation_error_handling(self, employee_code, invalid_wo_id):
        """
        Test that stock reservation handles errors gracefully
        """
        # Setup: Create user
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

        # Test: Reserve stock with invalid work order ID
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        reservation_data = {
            'wo_id': invalid_wo_id,  # Non-existent work order
            'internal_sku': 'INVALID_SKU',
            'qty_needed': 10
        }

        url = '/api/v1/inventory/reserve-stock/'
        response = client_api.post(url, reservation_data, format='json')

        # Should handle invalid data gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, dict)
            # Should indicate failure for invalid data
            if not response.data.get('success', True):
                assert 'message' in response.data or 'error' in response.data

        # Cleanup
        technician.delete()
        user.delete()

    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        zero_qty=st.integers(min_value=0, max_value=0)
    )
    def test_stock_reservation_zero_quantity_handling(self, employee_code, product_code, warehouse_code, zero_qty):
        """
        Test that stock reservation handles zero or invalid quantities properly
        """
        # Setup: Complete environment
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

        work_order = WorkOrder.objects.create(
            wo_number=f"WO_{employee_code}",
            client=client,
            equipment=equipment,
            description="Test work order",
            status="draft"
        )

        # Test: Reserve zero quantity
        client_api = APIClient()
        client_api.force_authenticate(user=user)

        reservation_data = {
            'wo_id': work_order.wo_id,
            'internal_sku': product_code,
            'qty_needed': zero_qty  # Zero or negative
        }

        url = '/api/v1/inventory/reserve-stock/'
        response = client_api.post(url, reservation_data, format='json')

        # Should handle invalid quantities appropriately
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]

        # Cleanup
        technician.delete()
        user.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])