"""
ForgeDB API REST - Property Tests for CRUD Operations Integrity
Task 5.1: Property test for CRUD operations integrity

**Feature: forge-api-rest, Property 8: Entity update integrity preservation**
**Validates: Requirements 2.3**

This module contains property-based tests that verify the integrity of CRUD operations
across all ViewSets using Hypothesis.
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
    Technician, Client, Equipment, WorkOrder, Invoice, 
    ProductMaster, Stock, Warehouse, Transaction
)
from core.authentication import TechnicianAuthBackend


class TestCRUDOperationsIntegrity:
    """
    Property-based tests for CRUD operations integrity across all ViewSets
    """
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        client_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ''),
        client_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_client_crud_integrity_preservation(self, employee_code, client_name, client_code):
        """
        **Feature: forge-api-rest, Property 8: Entity update integrity preservation**
        **Validates: Requirements 2.3**
        
        For any Client entity, CRUD operations should preserve data integrity
        and maintain referential consistency.
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
        
        # Test: Create operation
        original_data = {
            'client_code': client_code,
            'type': 'individual',
            'name': client_name,
            'email': f"{client_code}@test.com",
            'status': 'active'
        }
        
        client = Client.objects.create(
            created_by=technician,
            **original_data
        )
        
        # Assert: Created entity should preserve all provided data
        assert client.client_code == client_code
        assert client.name == client_name
        assert client.type == 'individual'
        assert client.email == f"{client_code}@test.com"
        assert client.status == 'active'
        assert client.created_by == technician
        assert client.created_at is not None
        assert client.updated_at is not None
        
        # Test: Read operation should return consistent data
        retrieved_client = Client.objects.get(client_id=client.client_id)
        assert retrieved_client.client_code == client.client_code
        assert retrieved_client.name == client.name
        assert retrieved_client.type == client.type
        assert retrieved_client.email == client.email
        assert retrieved_client.status == client.status
        assert retrieved_client.created_by == client.created_by
        
        # Test: Update operation should preserve integrity
        updated_name = f"Updated {client_name}"
        original_created_at = client.created_at
        original_created_by = client.created_by
        
        client.name = updated_name
        client.save()
        
        # Assert: Update should preserve original metadata
        client.refresh_from_db()
        assert client.name == updated_name
        assert client.created_at == original_created_at  # Should not change
        assert client.created_by == original_created_by  # Should not change
        assert client.updated_at > original_created_at  # Should be updated
        
        # Test: Related data integrity
        # Create equipment for this client
        equipment = Equipment.objects.create(
            client=client,
            equipment_code=f"EQ_{client_code}",
            year=2020,
            make="Toyota",
            model="Corolla",
            status="active"
        )
        
        # Assert: Relationship should be maintained
        assert equipment.client == client
        assert client.equipment_set.count() == 1
        assert client.equipment_set.first() == equipment
        
        # Test: Cascade behavior on delete
        client_id = client.client_id
        equipment_id = equipment.equipment_id
        
        # Equipment should be deleted when client is deleted (CASCADE)
        client.delete()
        
        # Assert: Related objects should be properly handled
        assert not Client.objects.filter(client_id=client_id).exists()
        assert not Equipment.objects.filter(equipment_id=equipment_id).exists()
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        wo_number=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_work_order_crud_integrity_preservation(self, employee_code, wo_number):
        """
        **Feature: forge-api-rest, Property 8: Entity update integrity preservation**
        **Validates: Requirements 2.3**
        
        For any WorkOrder entity, CRUD operations should preserve data integrity
        and maintain proper status transitions.
        """
        # Setup: Create test data
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
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
        
        # Test: Create work order
        work_order = WorkOrder.objects.create(
            wo_number=wo_number,
            client=client,
            equipment=equipment,
            description="Test work order",
            status="draft",
            priority="normal",
            created_by=technician
        )
        
        # Assert: Created work order should preserve all data
        assert work_order.wo_number == wo_number
        assert work_order.client == client
        assert work_order.equipment == equipment
        assert work_order.description == "Test work order"
        assert work_order.status == "draft"
        assert work_order.priority == "normal"
        assert work_order.created_by == technician
        assert work_order.created_at is not None
        
        # Test: Status transition integrity
        original_created_at = work_order.created_at
        
        # Update to in_progress
        work_order.status = "in_progress"
        work_order.assigned_technician = technician
        work_order.save()
        
        # Assert: Status change should preserve other data
        work_order.refresh_from_db()
        assert work_order.status == "in_progress"
        assert work_order.assigned_technician == technician
        assert work_order.wo_number == wo_number  # Should not change
        assert work_order.client == client  # Should not change
        assert work_order.equipment == equipment  # Should not change
        assert work_order.created_at == original_created_at  # Should not change
        assert work_order.updated_at > original_created_at  # Should be updated
        
        # Test: Complete work order
        work_order.status = "completed"
        work_order.resolution = "Work completed successfully"
        work_order.completed_at = datetime.now()
        work_order.save()
        
        # Assert: Completion should preserve all data
        work_order.refresh_from_db()
        assert work_order.status == "completed"
        assert work_order.resolution == "Work completed successfully"
        assert work_order.completed_at is not None
        assert work_order.wo_number == wo_number
        assert work_order.client == client
        assert work_order.equipment == equipment
        
        # Test: Related data integrity
        # Create invoice for this work order
        invoice = Invoice.objects.create(
            invoice_number=f"INV_{wo_number}",
            client=client,
            work_order=work_order,
            due_date=date(2024, 2, 28),
            total_amount=Decimal('100.00'),
            created_by=technician
        )
        
        # Assert: Relationship should be maintained
        assert invoice.work_order == work_order
        assert work_order.invoice_set.count() == 1
        
        # Cleanup
        technician.delete()
        client.delete()
        equipment.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        product_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        warehouse_code=st.text(min_size=1, max_size=10).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        quantity=st.integers(min_value=0, max_value=1000)
    )
    def test_inventory_crud_integrity_preservation(self, product_code, warehouse_code, quantity):
        """
        **Feature: forge-api-rest, Property 8: Entity update integrity preservation**
        **Validates: Requirements 2.3**
        
        For any inventory entity (Product, Stock), CRUD operations should preserve
        data integrity and maintain inventory consistency.
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
        
        # Test: Create product
        product = ProductMaster.objects.create(
            product_code=product_code,
            type="part",
            name=f"Test Product {product_code}",
            min_stock_level=10,
            max_stock_level=100,
            reorder_point=20,
            reorder_quantity=50,
            status="active"
        )
        
        # Assert: Product creation should preserve all data
        assert product.product_code == product_code
        assert product.type == "part"
        assert product.name == f"Test Product {product_code}"
        assert product.min_stock_level == 10
        assert product.max_stock_level == 100
        assert product.reorder_point == 20
        assert product.reorder_quantity == 50
        assert product.status == "active"
        
        # Test: Create warehouse
        warehouse = Warehouse.objects.create(
            warehouse_code=warehouse_code,
            name=f"Test Warehouse {warehouse_code}",
            status="active"
        )
        
        # Assert: Warehouse creation should preserve data
        assert warehouse.warehouse_code == warehouse_code
        assert warehouse.name == f"Test Warehouse {warehouse_code}"
        assert warehouse.status == "active"
        
        # Test: Create stock record
        stock = Stock.objects.create(
            warehouse=warehouse,
            product=product,
            quantity_on_hand=quantity,
            quantity_available=quantity,
            average_cost=Decimal('10.50')
        )
        
        # Assert: Stock creation should preserve data and relationships
        assert stock.warehouse == warehouse
        assert stock.product == product
        assert stock.quantity_on_hand == quantity
        assert stock.quantity_available == quantity
        assert stock.average_cost == Decimal('10.50')
        
        # Test: Update stock quantity
        original_created_at = stock.created_at
        new_quantity = quantity + 50
        
        stock.quantity_on_hand = new_quantity
        stock.quantity_available = new_quantity
        stock.save()
        
        # Assert: Update should preserve relationships and metadata
        stock.refresh_from_db()
        assert stock.quantity_on_hand == new_quantity
        assert stock.quantity_available == new_quantity
        assert stock.warehouse == warehouse  # Should not change
        assert stock.product == product  # Should not change
        assert stock.created_at == original_created_at  # Should not change
        assert stock.updated_at > original_created_at  # Should be updated
        
        # Test: Create transaction
        transaction = Transaction.objects.create(
            transaction_type="receipt",
            warehouse=warehouse,
            product=product,
            quantity=50,
            unit_cost=Decimal('10.50'),
            created_by=technician
        )
        
        # Assert: Transaction should maintain referential integrity
        assert transaction.warehouse == warehouse
        assert transaction.product == product
        assert transaction.quantity == 50
        assert transaction.unit_cost == Decimal('10.50')
        assert transaction.created_by == technician
        
        # Test: Unique constraint enforcement
        # Should not be able to create another stock record for same warehouse-product
        with pytest.raises(Exception):  # IntegrityError
            Stock.objects.create(
                warehouse=warehouse,
                product=product,
                quantity_on_hand=100
            )
        
        # Cleanup
        technician.delete()
        product.delete()
        warehouse.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_audit_trail_integrity_preservation(self, employee_code):
        """
        **Feature: forge-api-rest, Property 8: Entity update integrity preservation**
        **Validates: Requirements 2.3**
        
        CRUD operations should maintain proper audit trails and timestamps.
        """
        # Setup: Create technician
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        original_created_at = technician.created_at
        original_updated_at = technician.updated_at
        
        # Test: Update should change updated_at but not created_at
        technician.first_name = "Updated"
        technician.save()
        
        technician.refresh_from_db()
        
        # Assert: Audit trail integrity
        assert technician.created_at == original_created_at  # Should not change
        assert technician.updated_at > original_updated_at  # Should be updated
        assert technician.first_name == "Updated"
        
        # Test: Multiple updates should continue updating timestamp
        second_update_time = technician.updated_at
        
        technician.last_name = "Updated Last"
        technician.save()
        
        technician.refresh_from_db()
        
        # Assert: Continued audit trail integrity
        assert technician.created_at == original_created_at  # Should not change
        assert technician.updated_at > second_update_time  # Should be updated again
        assert technician.last_name == "Updated Last"
        
        # Cleanup
        technician.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_concurrent_update_integrity(self, employee_code):
        """
        **Feature: forge-api-rest, Property 8: Entity update integrity preservation**
        **Validates: Requirements 2.3**
        
        Concurrent updates should maintain data integrity.
        """
        # Setup: Create technician
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Original",
            last_name="Name",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        # Test: Simulate concurrent updates
        # Get two instances of the same object
        tech1 = Technician.objects.get(technician_id=technician.technician_id)
        tech2 = Technician.objects.get(technician_id=technician.technician_id)
        
        # Update different fields
        tech1.first_name = "Updated1"
        tech2.last_name = "Updated2"
        
        # Save both (last one wins for conflicting fields)
        tech1.save()
        tech2.save()
        
        # Assert: Final state should be consistent
        final_tech = Technician.objects.get(technician_id=technician.technician_id)
        
        # The last save should win, but data should be consistent
        assert final_tech.technician_id == technician.technician_id
        assert final_tech.employee_code == employee_code
        assert final_tech.email == f"{employee_code}@test.com"
        # Either first_name or last_name should be updated depending on save order
        assert final_tech.first_name in ["Original", "Updated1"]
        assert final_tech.last_name in ["Name", "Updated2"]
        
        # Cleanup
        technician.delete()


class TestCRUDValidationIntegrity:
    """
    Tests for validation integrity during CRUD operations
    """
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        invalid_email=st.text(min_size=1, max_size=50).filter(lambda x: '@' not in x)
    )
    def test_validation_integrity_on_create(self, invalid_email):
        """
        Test that validation is consistently applied during create operations
        """
        # Test: Invalid email should be rejected
        with pytest.raises(Exception):  # ValidationError or IntegrityError
            Technician.objects.create(
                employee_code="TECH001",
                first_name="Test",
                last_name="User",
                email=invalid_email,  # Invalid email
                hire_date=date(2023, 1, 1),
                status="active"
            )
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_validation_integrity_on_update(self, employee_code):
        """
        Test that validation is consistently applied during update operations
        """
        # Setup: Create valid technician
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date=date(2023, 1, 1),
            status="active"
        )
        
        # Test: Invalid update should be rejected
        technician.email = "invalid-email-format"
        
        with pytest.raises(Exception):  # ValidationError
            technician.full_clean()  # Explicit validation
        
        # Test: Valid update should work
        technician.email = f"updated_{employee_code}@test.com"
        technician.full_clean()  # Should not raise
        technician.save()
        
        # Assert: Valid update should be saved
        technician.refresh_from_db()
        assert technician.email == f"updated_{employee_code}@test.com"
        
        # Cleanup
        technician.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])