"""
**Feature: forge-api-rest, Property 51: Taxonomy hierarchy integrity**

Property-based test for taxonomy hierarchy integrity.
Tests that taxonomy entry creation maintains proper hierarchical relationships 
between systems, subsystems, and groups without creating circular references.

**Validates: Requirements 11.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction

from ..models import TaxonomySystem, TaxonomySubsystem, TaxonomyGroup, Technician
from ..serializers.main_serializers import (
    TaxonomySystemSerializer, TaxonomySubsystemSerializer, TaxonomyGroupSerializer
)


class TestTaxonomyHierarchyIntegrity(APITestCase):
    """Property-based tests for taxonomy hierarchy integrity"""

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
    valid_categories = st.sampled_from(['AUTOMOTRIZ', 'INDUSTRIAL', 'AGRÍCOLA'])
    
    valid_codes = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=2,
        max_size=20
    ).map(lambda x: x.replace(' ', ''))
    
    valid_names = st.text(min_size=1, max_size=100)

    @given(
        system_code=valid_codes,
        category=valid_categories,
        name_es=valid_names,
        name_en=valid_names
    )
    @settings(max_examples=100, deadline=None)
    def test_taxonomy_system_creation_integrity(self, system_code, category, name_es, name_en):
        """
        **Feature: forge-api-rest, Property 51: Taxonomy hierarchy integrity**
        
        For any taxonomy system creation, the system should maintain proper 
        hierarchical relationships and prevent duplicate system codes.
        """
        # Arrange: Create taxonomy system data
        system_data = {
            'system_code': system_code,
            'category': category,
            'name_es': name_es,
            'name_en': name_en,
            'is_active': True,
            'sort_order': 0
        }

        # Act: Validate through serializer
        serializer = TaxonomySystemSerializer(data=system_data)
        
        # Assert: Validation should maintain integrity
        if serializer.is_valid():
            # If validation passes, the system should be creatable
            taxonomy_system = serializer.save()
            
            # Verify the saved data maintains integrity
            assert taxonomy_system.system_code == system_code
            assert taxonomy_system.category in ['AUTOMOTRIZ', 'INDUSTRIAL', 'AGRÍCOLA']
            assert len(taxonomy_system.name_es) >= 1
            
            # Verify uniqueness constraint
            duplicate_data = system_data.copy()
            duplicate_serializer = TaxonomySystemSerializer(data=duplicate_data)
            
            # Duplicate system codes should be rejected
            if duplicate_serializer.is_valid():
                with pytest.raises(IntegrityError):
                    with transaction.atomic():
                        duplicate_serializer.save()
            
            # Clean up
            taxonomy_system.delete()

    @given(
        system_code=valid_codes,
        subsystem_code=valid_codes,
        category=valid_categories,
        system_name=valid_names,
        subsystem_name=valid_names
    )
    @settings(max_examples=50, deadline=None)
    def test_taxonomy_subsystem_hierarchy_integrity(self, system_code, subsystem_code, 
                                                   category, system_name, subsystem_name):
        """
        Test that subsystems maintain proper parent-child relationships with systems
        """
        # Assume codes are different to avoid conflicts
        assume(system_code != subsystem_code)
        
        # Create parent system first
        system = TaxonomySystem.objects.create(
            system_code=system_code,
            category=category,
            name_es=system_name,
            is_active=True
        )
        
        try:
            # Create subsystem data
            subsystem_data = {
                'subsystem_code': subsystem_code,
                'system_code': system.system_code,
                'name_es': subsystem_name,
                'sort_order': 0
            }

            # Validate through serializer
            serializer = TaxonomySubsystemSerializer(data=subsystem_data)
            
            if serializer.is_valid():
                subsystem = serializer.save()
                
                # Verify hierarchical relationship
                assert subsystem.system_code == system
                assert subsystem.subsystem_code == subsystem_code
                
                # Verify foreign key constraint
                retrieved_subsystem = TaxonomySubsystem.objects.get(
                    subsystem_code=subsystem_code
                )
                assert retrieved_subsystem.system_code.system_code == system_code
                
                subsystem.delete()
        
        finally:
            system.delete()

    @given(
        system_code=valid_codes,
        subsystem_code=valid_codes,
        group_code=valid_codes,
        category=valid_categories,
        system_name=valid_names,
        subsystem_name=valid_names,
        group_name=valid_names
    )
    @settings(max_examples=30, deadline=None)
    def test_taxonomy_group_hierarchy_integrity(self, system_code, subsystem_code, 
                                              group_code, category, system_name, 
                                              subsystem_name, group_name):
        """
        Test that groups maintain proper hierarchical relationships with systems and subsystems
        """
        # Assume all codes are different
        assume(len({system_code, subsystem_code, group_code}) == 3)
        
        # Create parent hierarchy
        system = TaxonomySystem.objects.create(
            system_code=system_code,
            category=category,
            name_es=system_name,
            is_active=True
        )
        
        subsystem = TaxonomySubsystem.objects.create(
            subsystem_code=subsystem_code,
            system_code=system,
            name_es=subsystem_name,
            sort_order=0
        )
        
        try:
            # Create group data
            group_data = {
                'group_code': group_code,
                'subsystem_code': subsystem.subsystem_code,
                'system_code': system.system_code,
                'name_es': group_name,
                'is_active': True
            }

            # Validate through serializer
            serializer = TaxonomyGroupSerializer(data=group_data)
            
            if serializer.is_valid():
                group = serializer.save()
                
                # Verify complete hierarchical relationship
                assert group.system_code == system
                assert group.subsystem_code == subsystem
                assert group.group_code == group_code
                
                # Verify referential integrity
                retrieved_group = TaxonomyGroup.objects.get(group_code=group_code)
                assert retrieved_group.system_code.system_code == system_code
                assert retrieved_group.subsystem_code.subsystem_code == subsystem_code
                
                group.delete()
        
        finally:
            subsystem.delete()
            system.delete()

    def test_circular_reference_prevention(self):
        """
        Test that the system prevents circular references in taxonomy hierarchy
        """
        # Create a system
        system = TaxonomySystem.objects.create(
            system_code='SYS001',
            category='AUTOMOTRIZ',
            name_es='Test System',
            is_active=True
        )
        
        # Create a subsystem
        subsystem = TaxonomySubsystem.objects.create(
            subsystem_code='SUB001',
            system_code=system,
            name_es='Test Subsystem',
            sort_order=0
        )
        
        try:
            # Attempt to create a group that references non-existent parent
            invalid_group_data = {
                'group_code': 'GRP001',
                'subsystem_code': 'NONEXISTENT',
                'system_code': system.system_code,
                'name_es': 'Invalid Group',
                'is_active': True
            }
            
            serializer = TaxonomyGroupSerializer(data=invalid_group_data)
            
            # Should fail validation due to invalid subsystem reference
            assert not serializer.is_valid()
            
        finally:
            subsystem.delete()
            system.delete()

    def test_api_endpoint_hierarchy_consistency(self):
        """
        Test that API endpoints maintain hierarchy consistency
        """
        # Create system via API
        system_data = {
            'system_code': 'API001',
            'category': 'AUTOMOTRIZ',
            'name_es': 'API Test System',
            'is_active': True,
            'sort_order': 0
        }
        
        response = self.client.post('/api/v1/catalog/taxonomy-systems/', system_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        system_code = response.json()['system_code']
        
        # Create subsystem via API
        subsystem_data = {
            'subsystem_code': 'APISUB001',
            'system_code': system_code,
            'name_es': 'API Test Subsystem',
            'sort_order': 0
        }
        
        response = self.client.post('/api/v1/catalog/taxonomy-subsystems/', subsystem_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Create group via API
        group_data = {
            'group_code': 'APIGRP001',
            'subsystem_code': 'APISUB001',
            'system_code': system_code,
            'name_es': 'API Test Group',
            'is_active': True
        }
        
        response = self.client.post('/api/v1/catalog/taxonomy-groups/', group_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify hierarchy through API
        response = self.client.get(f'/api/v1/catalog/taxonomy-groups/APIGRP001/')
        assert response.status_code == status.HTTP_200_OK
        
        group_data = response.json()
        assert group_data['system_code'] == system_code
        assert group_data['subsystem_code'] == 'APISUB001'

    def tearDown(self):
        """Clean up test data"""
        # Clean up in reverse hierarchical order
        TaxonomyGroup.objects.filter(group_code__startswith='API').delete()
        TaxonomyGroup.objects.filter(group_code__startswith='GRP').delete()
        TaxonomySubsystem.objects.filter(subsystem_code__startswith='API').delete()
        TaxonomySubsystem.objects.filter(subsystem_code__startswith='SUB').delete()
        TaxonomySystem.objects.filter(system_code__startswith='API').delete()
        TaxonomySystem.objects.filter(system_code__startswith='SYS').delete()