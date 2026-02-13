"""
**Feature: forge-api-rest, Property 54: Warehouse bin location accuracy**

Property-based test for warehouse bin location accuracy.
Tests that warehouse operations maintain accurate bin-level location tracking 
with proper zone, aisle, rack, and position identification.

**Validates: Requirements 12.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from ..models import Warehouse, Bin, Technician
from ..serializers.main_serializers import WarehouseSerializer, BinSerializer


class TestWarehouseBinLocationAccuracy(APITestCase):
    """Property-based tests for warehouse bin location accuracy"""

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
    valid_warehouse_codes = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=2,
        max_size=10
    ).map(lambda x: x.replace(' ', ''))
    
    valid_bin_codes = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd', 'Pd')),
        min_size=1,
        max_size=30
    )
    
    valid_zones = st.one_of(
        st.just(None),
        st.text(min_size=1, max_size=30)
    )
    
    valid_aisles = st.one_of(
        st.just(None),
        st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=10)
    )
    
    valid_racks = st.one_of(
        st.just(None),
        st.text(alphabet='0123456789', min_size=1, max_size=10)
    )
    
    valid_levels = st.one_of(
        st.just(None),
        st.text(alphabet='0123456789', min_size=1, max_size=10)
    )
    
    valid_positions = st.one_of(
        st.just(None),
        st.text(alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=10)
    )

    @given(
        warehouse_code=valid_warehouse_codes,
        bin_code=valid_bin_codes,
        zone=valid_zones,
        aisle=valid_aisles,
        rack=valid_racks,
        level=valid_levels,
        position=valid_positions
    )
    @settings(max_examples=100, deadline=None)
    def test_warehouse_bin_location_accuracy(self, warehouse_code, bin_code, zone, 
                                           aisle, rack, level, position):
        """
        **Feature: forge-api-rest, Property 54: Warehouse bin location accuracy**
        
        For any warehouse operation, the system should maintain accurate bin-level 
        location tracking with proper zone, aisle, rack, and position identification.
        """
        # Create warehouse first
        warehouse = Warehouse.objects.create(
            warehouse_code=warehouse_code,
            name=f'Test Warehouse {warehouse_code}',
            status='active'
        )
        
        try:
            # Arrange: Create bin data with location details
            bin_data = {
                'warehouse_code': warehouse.warehouse_code,
                'bin_code': bin_code,
                'zone': zone,
                'aisle': aisle,
                'rack': rack,
                'level': level,
                'position': position,
                'is_active': True,
                'current_occupancy': 0
            }

            # Act: Validate through serializer
            serializer = BinSerializer(data=bin_data)
            
            # Assert: Location tracking should be accurate
            if serializer.is_valid():
                bin_obj = serializer.save()
                
                # Verify location accuracy
                assert bin_obj.warehouse_code.warehouse_code == warehouse_code
                assert bin_obj.bin_code == bin_code
                
                # Verify location components are preserved accurately
                if zone is not None:
                    assert bin_obj.zone == zone
                if aisle is not None:
                    assert bin_obj.aisle == aisle
                if rack is not None:
                    assert bin_obj.rack == rack
                if level is not None:
                    assert bin_obj.level == level
                if position is not None:
                    assert bin_obj.position == position
                
                # Verify location uniqueness within warehouse
                duplicate_data = bin_data.copy()
                duplicate_serializer = BinSerializer(data=duplicate_data)
                
                if duplicate_serializer.is_valid():
                    with pytest.raises(IntegrityError):
                        with transaction.atomic():
                            duplicate_serializer.save()
                
                # Verify location can be retrieved accurately
                retrieved_bin = Bin.objects.get(
                    warehouse_code=warehouse,
                    bin_code=bin_code
                )
                assert retrieved_bin.zone == zone
                assert retrieved_bin.aisle == aisle
                assert retrieved_bin.rack == rack
                assert retrieved_bin.level == level
                assert retrieved_bin.position == position
                
                bin_obj.delete()
            
        finally:
            warehouse.delete()

    @given(
        warehouse_code=valid_warehouse_codes,
        bin_codes=st.lists(valid_bin_codes, min_size=2, max_size=5, unique=True),
        zone=st.text(min_size=1, max_size=30),
        aisle=st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=1, max_size=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_bins_location_consistency(self, warehouse_code, bin_codes, zone, aisle):
        """
        Test that multiple bins in the same location area maintain consistent tracking
        """
        # Create warehouse
        warehouse = Warehouse.objects.create(
            warehouse_code=warehouse_code,
            name=f'Test Warehouse {warehouse_code}',
            status='active'
        )
        
        created_bins = []
        
        try:
            # Create multiple bins in the same zone/aisle
            for i, bin_code in enumerate(bin_codes):
                bin_data = {
                    'warehouse_code': warehouse.warehouse_code,
                    'bin_code': bin_code,
                    'zone': zone,
                    'aisle': aisle,
                    'rack': str(i + 1),  # Different racks
                    'level': '1',
                    'position': str(i + 1),
                    'is_active': True,
                    'current_occupancy': 0
                }
                
                serializer = BinSerializer(data=bin_data)
                if serializer.is_valid():
                    bin_obj = serializer.save()
                    created_bins.append(bin_obj)
            
            # Verify all bins have consistent location tracking
            for bin_obj in created_bins:
                assert bin_obj.warehouse_code.warehouse_code == warehouse_code
                assert bin_obj.zone == zone
                assert bin_obj.aisle == aisle
                assert bin_obj.is_active == True
            
            # Verify bins can be filtered by location
            zone_bins = Bin.objects.filter(
                warehouse_code=warehouse,
                zone=zone
            )
            assert zone_bins.count() == len(created_bins)
            
            aisle_bins = Bin.objects.filter(
                warehouse_code=warehouse,
                zone=zone,
                aisle=aisle
            )
            assert aisle_bins.count() == len(created_bins)
            
        finally:
            for bin_obj in created_bins:
                bin_obj.delete()
            warehouse.delete()

    def test_bin_location_hierarchy_validation(self):
        """
        Test that bin location hierarchy is properly validated
        """
        # Create warehouse
        warehouse = Warehouse.objects.create(
            warehouse_code='WH001',
            name='Test Warehouse',
            status='active'
        )
        
        try:
            # Test valid hierarchical location
            valid_bin_data = {
                'warehouse_code': warehouse.warehouse_code,
                'bin_code': 'A01-01-01',
                'zone': 'A',
                'aisle': '01',
                'rack': '01',
                'level': '01',
                'position': '01',
                'is_active': True
            }
            
            serializer = BinSerializer(data=valid_bin_data)
            assert serializer.is_valid()
            
            bin_obj = serializer.save()
            
            # Verify hierarchical structure
            assert bin_obj.zone == 'A'
            assert bin_obj.aisle == '01'
            assert bin_obj.rack == '01'
            assert bin_obj.level == '01'
            assert bin_obj.position == '01'
            
            # Test location path construction
            location_path = f"{bin_obj.zone}/{bin_obj.aisle}/{bin_obj.rack}/{bin_obj.level}/{bin_obj.position}"
            expected_path = "A/01/01/01/01"
            assert location_path == expected_path
            
            bin_obj.delete()
            
        finally:
            warehouse.delete()

    def test_api_endpoint_location_accuracy(self):
        """
        Test that API endpoints maintain location accuracy
        """
        # Create warehouse via API
        warehouse_data = {
            'warehouse_code': 'API001',
            'name': 'API Test Warehouse',
            'status': 'active'
        }
        
        response = self.client.post('/api/v1/inventory/warehouses/', warehouse_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Create bin with detailed location via API
        bin_data = {
            'warehouse_code': 'API001',
            'bin_code': 'A01-R01-L01-P01',
            'description': 'Test bin with full location',
            'zone': 'A01',
            'aisle': 'R01',
            'rack': 'L01',
            'level': '01',
            'position': 'P01',
            'capacity': 100,
            'is_active': True
        }
        
        response = self.client.post('/api/v1/inventory/bins/', bin_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify location accuracy through API
        bin_id = response.json()['bin_id']
        response = self.client.get(f'/api/v1/inventory/bins/{bin_id}/')
        assert response.status_code == status.HTTP_200_OK
        
        retrieved_bin = response.json()
        assert retrieved_bin['warehouse_code'] == 'API001'
        assert retrieved_bin['zone'] == 'A01'
        assert retrieved_bin['aisle'] == 'R01'
        assert retrieved_bin['rack'] == 'L01'
        assert retrieved_bin['level'] == '01'
        assert retrieved_bin['position'] == 'P01'
        
        # Test location-based filtering
        response = self.client.get('/api/v1/inventory/bins/?zone=A01')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) >= 1

    def tearDown(self):
        """Clean up test data"""
        # Clean up bins first (due to foreign key)
        Bin.objects.filter(warehouse_code__warehouse_code__startswith='API').delete()
        Bin.objects.filter(warehouse_code__warehouse_code__startswith='WH').delete()
        Bin.objects.filter(warehouse_code__warehouse_code__startswith='TEST').delete()
        
        # Clean up warehouses
        Warehouse.objects.filter(warehouse_code__startswith='API').delete()
        Warehouse.objects.filter(warehouse_code__startswith='WH').delete()
        Warehouse.objects.filter(warehouse_code__startswith='TEST').delete()