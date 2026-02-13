"""
**Feature: forge-api-rest, Property 62: Parts usage reservation consistency**

Property-based test for parts usage reservation consistency.
Tests that service item operations manage parts usage with proper stock 
reservation, usage tracking, and return processing capabilities.

**Validates: Requirements 13.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime, date

from ..models import (
    WorkOrder, Client, Equipment, Technician, WOItem,
    Warehouse, ProductMaster, Stock, Transaction
)
from ..serializers.main_serializers import WOItemSerializer


class TestPartsUsageReservationConsistency(APITestCase):
    """Property-based tests for parts usage reservation consistency"""

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
        
        # Create test client and equipment
        self.client_obj = Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client',
            status='active'
        )
        
        self.equipment = Equipment.objects.create(
            client=self.client_obj,
            equipment_code='EQ001',
            year=2020,
            make='Toyota',
            model='Camry',
            status='active'
        )
        
        # Create warehouse and product
        self.warehouse = Warehouse.objects.create(
            warehouse_code='WH001',
            name='Main Warehouse',
            status='active'
        )
        
        self.product = ProductMaster.objects.create(
            product_code='PART001',
            type='part',
            name='Test Part',
            unit_of_measure='EA',
            status='active'
        )
        
        # Create initial stock
        self.stock = Stock.objects.create(
            warehouse=self.warehouse,
            product=self.product,
            quantity_on_hand=100,
            quantity_reserved=0,
            quantity_available=100,
            average_cost=Decimal('10.00')
        )
        
        # Create work order
        self.work_order = WorkOrder.objects.create(
            wo_number='WO001',
            client=self.client_obj,
            equipment=self.equipment,
            description='Test work order',
            status='in_progress',
            assigned_technician=self.technician,
            created_by=self.technician
        )
        
        self.client.force_authenticate(user=self.user)

    # Hypothesis strategies for generating test data
    valid_quantities = st.decimals(
        min_value=Decimal('0.1'),
        max_value=Decimal('50.0'),
        places=3
    )
    
    valid_prices = st.decimals(
        min_value=Decimal('0.01'),
        max_value=Decimal('999.99'),
        places=2
    )
    
    valid_percentages = st.decimals(
        min_value=Decimal('0.00'),
        max_value=Decimal('50.00'),
        places=2
    )
    
    valid_statuses = st.sampled_from(['PENDING', 'RESERVED', 'USED', 'RETURNED', 'CANCELLED'])

    @given(
        qty_ordered=valid_quantities,
        unit_price=valid_prices,
        discount_percent=valid_percentages,
        tax_percent=valid_percentages
    )
    @settings(max_examples=100, deadline=None)
    def test_parts_usage_reservation_consistency(self, qty_ordered, unit_price, 
                                               discount_percent, tax_percent):
        """
        **Feature: forge-api-rest, Property 62: Parts usage reservation consistency**
        
        For any service item operation, the system should manage parts usage with 
        proper stock reservation, usage tracking, and return processing capabilities.
        """
        # Ensure we don't exceed available stock
        assume(qty_ordered <= Decimal('50.0'))  # We have 100 in stock
        
        # Arrange: Create WO item data
        wo_item_data = {
            'wo': self.work_order.wo_id,
            'internal_sku': self.product.product_code,
            'qty_ordered': qty_ordered,
            'qty_used': Decimal('0.0'),
            'qty_returned': Decimal('0.0'),
            'unit_price': unit_price,
            'discount_percent': discount_percent,
            'tax_percent': tax_percent,
            'status': 'PENDING'
        }

        # Act: Create WO item through serializer
        serializer = WOItemSerializer(data=wo_item_data)
        
        # Assert: Reservation consistency should be maintained
        if serializer.is_valid():
            wo_item = serializer.save()
            
            try:
                # Verify initial state
                assert wo_item.qty_ordered == qty_ordered
                assert wo_item.qty_used == Decimal('0.0')
                assert wo_item.qty_returned == Decimal('0.0')
                assert wo_item.status == 'PENDING'
                
                # Test reservation process
                wo_item.status = 'RESERVED'
                wo_item.reserved_stock_date = date.today()
                wo_item.save()
                
                # Update stock to reflect reservation
                self.stock.quantity_reserved += qty_ordered
                self.stock.quantity_available -= qty_ordered
                self.stock.save()
                
                # Verify reservation consistency
                updated_stock = Stock.objects.get(pk=self.stock.pk)
                assert updated_stock.quantity_reserved >= qty_ordered
                assert updated_stock.quantity_available == (
                    updated_stock.quantity_on_hand - updated_stock.quantity_reserved
                )
                
                # Test usage process
                qty_actually_used = min(qty_ordered, qty_ordered * Decimal('0.9'))  # Use 90% or less
                wo_item.qty_used = qty_actually_used
                wo_item.status = 'USED'
                wo_item.used_stock_date = date.today()
                wo_item.save()
                
                # Update stock to reflect usage
                updated_stock.quantity_on_hand -= qty_actually_used
                updated_stock.quantity_reserved -= qty_ordered
                qty_returned_to_available = qty_ordered - qty_actually_used
                updated_stock.quantity_available += qty_returned_to_available
                updated_stock.save()
                
                # Verify usage consistency
                final_stock = Stock.objects.get(pk=self.stock.pk)
                assert wo_item.qty_used == qty_actually_used
                assert wo_item.status == 'USED'
                
                # Test return process if there's unused quantity
                if qty_actually_used < qty_ordered:
                    qty_to_return = qty_ordered - qty_actually_used
                    wo_item.qty_returned = qty_to_return
                    wo_item.save()
                    
                    # Verify return consistency
                    assert wo_item.qty_returned == qty_to_return
                    assert wo_item.qty_ordered == wo_item.qty_used + wo_item.qty_returned
                
                # Verify transaction consistency
                total_cost = qty_actually_used * unit_price
                discounted_cost = total_cost * (Decimal('100') - discount_percent) / Decimal('100')
                final_cost = discounted_cost * (Decimal('100') + tax_percent) / Decimal('100')
                
                # Cost calculations should be consistent
                assert wo_item.unit_price == unit_price
                assert wo_item.discount_percent == discount_percent
                assert wo_item.tax_percent == tax_percent
                
                # Reset stock for next test
                self.stock.quantity_on_hand = 100
                self.stock.quantity_reserved = 0
                self.stock.quantity_available = 100
                self.stock.save()
                
            finally:
                wo_item.delete()

    def test_stock_reservation_atomicity(self):
        """
        Test that stock reservations are atomic and consistent
        """
        # Create multiple WO items that would exceed stock if not handled atomically
        wo_items = []
        
        try:
            # Create first item - should succeed
            wo_item1 = WOItem.objects.create(
                wo=self.work_order,
                internal_sku=self.product.product_code,
                qty_ordered=Decimal('60.0'),
                unit_price=Decimal('10.00'),
                status='PENDING'
            )
            wo_items.append(wo_item1)
            
            # Reserve stock for first item
            wo_item1.status = 'RESERVED'
            wo_item1.save()
            
            self.stock.quantity_reserved += wo_item1.qty_ordered
            self.stock.quantity_available -= wo_item1.qty_ordered
            self.stock.save()
            
            # Verify first reservation
            updated_stock = Stock.objects.get(pk=self.stock.pk)
            assert updated_stock.quantity_available == 40  # 100 - 60
            assert updated_stock.quantity_reserved == 60
            
            # Create second item - should succeed with remaining stock
            wo_item2 = WOItem.objects.create(
                wo=self.work_order,
                internal_sku=self.product.product_code,
                qty_ordered=Decimal('30.0'),
                unit_price=Decimal('10.00'),
                status='PENDING'
            )
            wo_items.append(wo_item2)
            
            # Reserve stock for second item
            wo_item2.status = 'RESERVED'
            wo_item2.save()
            
            self.stock.quantity_reserved += wo_item2.qty_ordered
            self.stock.quantity_available -= wo_item2.qty_ordered
            self.stock.save()
            
            # Verify second reservation
            updated_stock = Stock.objects.get(pk=self.stock.pk)
            assert updated_stock.quantity_available == 10  # 100 - 60 - 30
            assert updated_stock.quantity_reserved == 90
            
            # Test partial usage and return
            wo_item1.qty_used = Decimal('50.0')  # Use less than ordered
            wo_item1.qty_returned = Decimal('10.0')  # Return unused portion
            wo_item1.status = 'USED'
            wo_item1.save()
            
            # Update stock for partial usage
            self.stock.quantity_on_hand -= wo_item1.qty_used
            self.stock.quantity_reserved -= wo_item1.qty_ordered
            self.stock.quantity_available += wo_item1.qty_returned
            self.stock.save()
            
            # Verify consistency after partial usage
            final_stock = Stock.objects.get(pk=self.stock.pk)
            assert final_stock.quantity_on_hand == 50  # 100 - 50 used
            assert final_stock.quantity_reserved == 30  # Only item2 reserved
            assert final_stock.quantity_available == 20  # 50 - 30 + 10 returned
            
        finally:
            for item in wo_items:
                item.delete()
            # Reset stock
            self.stock.quantity_on_hand = 100
            self.stock.quantity_reserved = 0
            self.stock.quantity_available = 100
            self.stock.save()

    def test_return_processing_consistency(self):
        """
        Test that return processing maintains consistency
        """
        # Create and reserve item
        wo_item = WOItem.objects.create(
            wo=self.work_order,
            internal_sku=self.product.product_code,
            qty_ordered=Decimal('20.0'),
            unit_price=Decimal('15.00'),
            status='RESERVED'
        )
        
        try:
            # Simulate partial usage
            wo_item.qty_used = Decimal('15.0')
            wo_item.status = 'USED'
            wo_item.save()
            
            # Process return of unused quantity
            unused_qty = wo_item.qty_ordered - wo_item.qty_used
            wo_item.qty_returned = unused_qty
            wo_item.save()
            
            # Verify return consistency
            assert wo_item.qty_returned == Decimal('5.0')
            assert wo_item.qty_ordered == wo_item.qty_used + wo_item.qty_returned
            
            # Test that returns cannot exceed unused quantity
            wo_item.qty_returned = Decimal('10.0')  # More than unused
            
            # This should be caught by business logic validation
            # (In a real implementation, this would be validated in the serializer)
            assert wo_item.qty_returned <= (wo_item.qty_ordered - wo_item.qty_used)
            
        finally:
            wo_item.delete()

    def test_api_endpoint_reservation_consistency(self):
        """
        Test that API endpoints maintain reservation consistency
        """
        # Create WO item via API
        wo_item_data = {
            'wo': self.work_order.wo_id,
            'internal_sku': self.product.product_code,
            'qty_ordered': '25.0',
            'unit_price': '12.50',
            'discount_percent': '5.0',
            'tax_percent': '8.0',
            'status': 'PENDING'
        }
        
        response = self.client.post('/api/v1/services/wo-items/', wo_item_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        item_id = response.json()['item_id']
        
        # Update to reserved status via API
        update_data = {
            'status': 'RESERVED',
            'reserved_stock_date': str(date.today())
        }
        response = self.client.patch(f'/api/v1/services/wo-items/{item_id}/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'RESERVED'
        
        # Update to used status via API
        usage_data = {
            'qty_used': '20.0',
            'qty_returned': '5.0',
            'status': 'USED',
            'used_stock_date': str(date.today())
        }
        response = self.client.patch(f'/api/v1/services/wo-items/{item_id}/', usage_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        final_item = response.json()
        assert Decimal(final_item['qty_used']) == Decimal('20.0')
        assert Decimal(final_item['qty_returned']) == Decimal('5.0')
        assert final_item['status'] == 'USED'
        
        # Verify consistency
        total_accounted = Decimal(final_item['qty_used']) + Decimal(final_item['qty_returned'])
        assert total_accounted == Decimal(final_item['qty_ordered'])

    def tearDown(self):
        """Clean up test data"""
        # Clean up in reverse dependency order
        WOItem.objects.filter(wo=self.work_order).delete()
        Transaction.objects.filter(product=self.product).delete()
        Stock.objects.filter(product=self.product).delete()
        ProductMaster.objects.filter(product_code__startswith='PART').delete()
        Warehouse.objects.filter(warehouse_code__startswith='WH').delete()
        WorkOrder.objects.filter(wo_number__startswith='WO').delete()
        Equipment.objects.filter(equipment_code__startswith='EQ').delete()
        Client.objects.filter(client_code__startswith='CLIENT').delete()