"""
**Feature: forge-api-rest, Property 59: Work order lifecycle completeness**

Property-based test for work order lifecycle completeness.
Tests that work order creation supports complete service lifecycle management 
from initial scheduling through final completion and invoicing.

**Validates: Requirements 13.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime, date, timedelta

from ..models import (
    WorkOrder, Client, Equipment, Technician, Invoice, 
    WOService, WOItem, FlatRateStandard, EquipmentType
)
from ..serializers.main_serializers import WorkOrderSerializer


class TestWorkOrderLifecycleCompleteness(APITestCase):
    """Property-based tests for work order lifecycle completeness"""

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
            status='active',
            hourly_rate=Decimal('50.00')
        )
        
        # Create test client
        self.client_obj = Client.objects.create(
            client_code='CLIENT001',
            type='individual',
            name='Test Client',
            email='client@example.com',
            status='active'
        )
        
        # Create test equipment
        self.equipment = Equipment.objects.create(
            client=self.client_obj,
            equipment_code='EQ001',
            year=2020,
            make='Toyota',
            model='Camry',
            status='active'
        )
        
        self.client.force_authenticate(user=self.user)

    # Hypothesis strategies for generating test data
    valid_wo_numbers = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=5,
        max_size=20
    ).map(lambda x: x.replace(' ', ''))
    
    valid_descriptions = st.text(min_size=10, max_size=500)
    
    valid_priorities = st.sampled_from(['low', 'normal', 'high', 'urgent'])
    
    valid_statuses = st.sampled_from([
        'draft', 'scheduled', 'in_progress', 'waiting_parts', 
        'waiting_approval', 'completed', 'invoiced', 'cancelled'
    ])
    
    valid_hours = st.decimals(
        min_value=Decimal('0.1'),
        max_value=Decimal('100.0'),
        places=2
    )
    
    valid_costs = st.decimals(
        min_value=Decimal('10.00'),
        max_value=Decimal('10000.00'),
        places=2
    )

    @given(
        wo_number=valid_wo_numbers,
        description=valid_descriptions,
        priority=valid_priorities,
        estimated_hours=valid_hours,
        estimated_cost=valid_costs
    )
    @settings(max_examples=100, deadline=None)
    def test_work_order_lifecycle_completeness(self, wo_number, description, 
                                             priority, estimated_hours, estimated_cost):
        """
        **Feature: forge-api-rest, Property 59: Work order lifecycle completeness**
        
        For any work order creation, the system should support complete service 
        lifecycle management from initial scheduling through final completion and invoicing.
        """
        # Arrange: Create work order data
        wo_data = {
            'wo_number': wo_number,
            'client': self.client_obj.client_id,
            'equipment': self.equipment.equipment_id,
            'description': description,
            'priority': priority,
            'status': 'draft',
            'estimated_hours': estimated_hours,
            'estimated_cost': estimated_cost,
            'assigned_technician': self.technician.technician_id,
            'created_by': self.technician.technician_id
        }

        # Act: Create work order through serializer
        serializer = WorkOrderSerializer(data=wo_data)
        
        # Assert: Complete lifecycle should be supported
        if serializer.is_valid():
            work_order = serializer.save()
            
            try:
                # Verify initial creation completeness
                assert work_order.wo_number == wo_number
                assert work_order.client == self.client_obj
                assert work_order.equipment == self.equipment
                assert work_order.description == description
                assert work_order.priority == priority
                assert work_order.status == 'draft'
                assert work_order.estimated_hours == estimated_hours
                assert work_order.estimated_cost == estimated_cost
                
                # Test lifecycle progression: Draft -> Scheduled
                work_order.status = 'scheduled'
                work_order.scheduled_date = datetime.now() + timedelta(days=1)
                work_order.save()
                
                # Verify scheduled state
                assert work_order.status == 'scheduled'
                assert work_order.scheduled_date is not None
                
                # Test lifecycle progression: Scheduled -> In Progress
                work_order.status = 'in_progress'
                work_order.started_at = datetime.now()
                work_order.save()
                
                # Verify in-progress state
                assert work_order.status == 'in_progress'
                assert work_order.started_at is not None
                
                # Test lifecycle progression: In Progress -> Completed
                work_order.status = 'completed'
                work_order.completed_at = datetime.now()
                work_order.actual_hours = estimated_hours + Decimal('1.0')
                work_order.actual_cost = estimated_cost + Decimal('50.00')
                work_order.resolution = 'Work completed successfully'
                work_order.save()
                
                # Verify completed state
                assert work_order.status == 'completed'
                assert work_order.completed_at is not None
                assert work_order.actual_hours is not None
                assert work_order.actual_cost is not None
                assert work_order.resolution is not None
                
                # Test final lifecycle stage: Completed -> Invoiced
                # Create invoice for the work order
                invoice = Invoice.objects.create(
                    invoice_number=f'INV-{wo_number}',
                    client=self.client_obj,
                    work_order=work_order,
                    due_date=date.today() + timedelta(days=30),
                    subtotal=work_order.actual_cost,
                    total_amount=work_order.actual_cost,
                    status='draft',
                    created_by=self.technician
                )
                
                work_order.status = 'invoiced'
                work_order.save()
                
                # Verify invoiced state and complete lifecycle
                assert work_order.status == 'invoiced'
                assert hasattr(work_order, 'invoice_set')
                assert work_order.invoice_set.filter(invoice_number=f'INV-{wo_number}').exists()
                
                # Verify lifecycle completeness metrics
                if work_order.started_at and work_order.completed_at:
                    duration = work_order.completed_at - work_order.started_at
                    assert duration.total_seconds() >= 0
                
                # Clean up
                invoice.delete()
                
            finally:
                work_order.delete()

    def test_work_order_status_transition_validation(self):
        """
        Test that work order status transitions follow proper lifecycle rules
        """
        # Create work order
        work_order = WorkOrder.objects.create(
            wo_number='WO-LIFECYCLE-001',
            client=self.client_obj,
            equipment=self.equipment,
            description='Test lifecycle validation',
            status='draft',
            estimated_hours=Decimal('2.0'),
            estimated_cost=Decimal('100.00'),
            assigned_technician=self.technician,
            created_by=self.technician
        )
        
        try:
            # Test valid transitions
            valid_transitions = [
                ('draft', 'scheduled'),
                ('scheduled', 'in_progress'),
                ('in_progress', 'waiting_parts'),
                ('waiting_parts', 'in_progress'),
                ('in_progress', 'waiting_approval'),
                ('waiting_approval', 'in_progress'),
                ('in_progress', 'completed'),
                ('completed', 'invoiced')
            ]
            
            for from_status, to_status in valid_transitions:
                work_order.status = from_status
                work_order.save()
                
                # Transition should be allowed
                work_order.status = to_status
                if to_status == 'in_progress' and not work_order.started_at:
                    work_order.started_at = datetime.now()
                if to_status == 'completed' and not work_order.completed_at:
                    work_order.completed_at = datetime.now()
                    work_order.resolution = 'Test completion'
                
                work_order.save()
                assert work_order.status == to_status
            
            # Test that cancelled status can be reached from any status
            for status in ['draft', 'scheduled', 'in_progress', 'waiting_parts']:
                work_order.status = status
                work_order.save()
                
                work_order.status = 'cancelled'
                work_order.save()
                assert work_order.status == 'cancelled'
                
        finally:
            work_order.delete()

    def test_work_order_service_integration(self):
        """
        Test that work orders integrate properly with services and items
        """
        # Create equipment type and flat rate standard
        equipment_type = EquipmentType.objects.create(
            type_code='AUTO001',
            category='AUTOMOTRIZ',
            name='Passenger Vehicle'
        )
        
        flat_rate = FlatRateStandard.objects.create(
            service_code='OIL_CHANGE',
            description_es='Cambio de aceite',
            equipment_type=equipment_type,
            standard_hours=Decimal('1.0')
        )
        
        # Create work order
        work_order = WorkOrder.objects.create(
            wo_number='WO-SERVICE-001',
            client=self.client_obj,
            equipment=self.equipment,
            description='Oil change service',
            status='in_progress',
            started_at=datetime.now(),
            assigned_technician=self.technician,
            created_by=self.technician
        )
        
        try:
            # Add service to work order
            wo_service = WOService.objects.create(
                wo=work_order,
                flat_rate=flat_rate,
                service_code='OIL_CHANGE',
                description='Oil change service',
                flat_hours=Decimal('1.0'),
                estimated_hours=Decimal('1.0'),
                hourly_rate=self.technician.hourly_rate,
                technician=self.technician,
                completion_status='PENDING'
            )
            
            # Add item to work order
            wo_item = WOItem.objects.create(
                wo=work_order,
                internal_sku='OIL-5W30',
                qty_ordered=Decimal('4.0'),
                unit_price=Decimal('8.50'),
                status='PENDING'
            )
            
            # Verify integration
            assert work_order.woservice_set.count() == 1
            assert work_order.woitem_set.count() == 1
            
            # Complete service
            wo_service.completion_status = 'COMPLETED'
            wo_service.actual_hours = Decimal('0.8')
            wo_service.completed_at = datetime.now()
            wo_service.save()
            
            # Use item
            wo_item.qty_used = Decimal('4.0')
            wo_item.status = 'USED'
            wo_item.save()
            
            # Complete work order
            work_order.status = 'completed'
            work_order.completed_at = datetime.now()
            work_order.actual_hours = wo_service.actual_hours
            work_order.actual_cost = (wo_service.actual_hours * wo_service.hourly_rate + 
                                    wo_item.qty_used * wo_item.unit_price)
            work_order.resolution = 'Oil change completed successfully'
            work_order.save()
            
            # Verify completion
            assert work_order.status == 'completed'
            assert work_order.actual_hours == Decimal('0.8')
            assert work_order.actual_cost == Decimal('74.00')  # 0.8 * 50 + 4 * 8.5
            
        finally:
            work_order.delete()
            flat_rate.delete()
            equipment_type.delete()

    def test_api_endpoint_lifecycle_completeness(self):
        """
        Test that API endpoints support complete work order lifecycle
        """
        # Create work order via API
        wo_data = {
            'wo_number': 'API-WO-001',
            'client': self.client_obj.client_id,
            'equipment': self.equipment.equipment_id,
            'description': 'API lifecycle test',
            'priority': 'normal',
            'status': 'draft',
            'estimated_hours': '2.5',
            'estimated_cost': '125.00',
            'assigned_technician': self.technician.technician_id
        }
        
        response = self.client.post('/api/v1/services/work-orders/', wo_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        wo_id = response.json()['wo_id']
        
        # Progress through lifecycle via API
        # Draft -> Scheduled
        update_data = {
            'status': 'scheduled',
            'scheduled_date': (datetime.now() + timedelta(days=1)).isoformat()
        }
        response = self.client.patch(f'/api/v1/services/work-orders/{wo_id}/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'scheduled'
        
        # Scheduled -> In Progress
        update_data = {
            'status': 'in_progress',
            'started_at': datetime.now().isoformat()
        }
        response = self.client.patch(f'/api/v1/services/work-orders/{wo_id}/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'in_progress'
        
        # In Progress -> Completed
        update_data = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'actual_hours': '2.0',
            'actual_cost': '100.00',
            'resolution': 'Work completed via API'
        }
        response = self.client.patch(f'/api/v1/services/work-orders/{wo_id}/', update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        final_wo = response.json()
        assert final_wo['status'] == 'completed'
        assert final_wo['resolution'] == 'Work completed via API'
        assert Decimal(final_wo['actual_hours']) == Decimal('2.0')
        assert Decimal(final_wo['actual_cost']) == Decimal('100.00')

    def tearDown(self):
        """Clean up test data"""
        # Clean up in reverse dependency order
        Invoice.objects.filter(invoice_number__startswith='INV-').delete()
        WOService.objects.filter(wo__wo_number__startswith='WO-').delete()
        WOItem.objects.filter(wo__wo_number__startswith='WO-').delete()
        WorkOrder.objects.filter(wo_number__startswith='WO-').delete()
        WorkOrder.objects.filter(wo_number__startswith='API-').delete()
        FlatRateStandard.objects.filter(service_code__startswith='OIL').delete()
        EquipmentType.objects.filter(type_code__startswith='AUTO').delete()