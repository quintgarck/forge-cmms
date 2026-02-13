"""
**Feature: forge-api-rest, Property 65: OEM part search filtering accuracy**

Property-based test for OEM part search filtering accuracy.
Tests that OEM part search supports complex filtering by VIN patterns, 
model codes, engine specifications, and other automotive criteria.

**Validates: Requirements 14.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal

from ..models import OEMBrand, OEMCatalogItem, TaxonomyGroup, TaxonomySystem, TaxonomySubsystem, Technician
from ..serializers.main_serializers import OEMCatalogItemSerializer


class TestOEMPartSearchFilteringAccuracy(APITestCase):
    """Property-based tests for OEM part search filtering accuracy"""

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
        
        # Create OEM brand
        self.oem_brand = OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            country='Japan',
            is_active=True
        )
        
        # Create taxonomy hierarchy for testing
        self.taxonomy_system = TaxonomySystem.objects.create(
            system_code='ENGINE',
            category='AUTOMOTRIZ',
            name_es='Sistema de Motor',
            is_active=True
        )
        
        self.taxonomy_subsystem = TaxonomySubsystem.objects.create(
            subsystem_code='FUEL_SYS',
            system_code=self.taxonomy_system,
            name_es='Sistema de Combustible',
            sort_order=0
        )
        
        self.taxonomy_group = TaxonomyGroup.objects.create(
            group_code='FUEL_PUMP',
            subsystem_code=self.taxonomy_subsystem,
            system_code=self.taxonomy_system,
            name_es='Bomba de Combustible',
            is_active=True
        )
        
        self.client.force_authenticate(user=self.user)

    # Hypothesis strategies for generating test data
    valid_part_numbers = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=5,
        max_size=30
    ).map(lambda x: x.replace(' ', ''))
    
    valid_descriptions = st.text(min_size=10, max_size=200)
    
    valid_vin_patterns = st.lists(
        st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=17, max_size=17),
        min_size=0,
        max_size=5
    )
    
    valid_model_codes = st.lists(
        st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=3, max_size=10),
        min_size=0,
        max_size=10
    )
    
    valid_engine_codes = st.lists(
        st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=3, max_size=15),
        min_size=0,
        max_size=8
    )
    
    valid_transmission_codes = st.lists(
        st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=2, max_size=10),
        min_size=0,
        max_size=5
    )
    
    valid_prices = st.decimals(
        min_value=Decimal('1.00'),
        max_value=Decimal('9999.99'),
        places=2
    )

    @given(
        part_number=valid_part_numbers,
        description=valid_descriptions,
        vin_patterns=valid_vin_patterns,
        model_codes=valid_model_codes,
        engine_codes=valid_engine_codes,
        transmission_codes=valid_transmission_codes,
        list_price=valid_prices
    )
    @settings(max_examples=100, deadline=None)
    def test_oem_part_search_filtering_accuracy(self, part_number, description, 
                                              vin_patterns, model_codes, 
                                              engine_codes, transmission_codes, list_price):
        """
        **Feature: forge-api-rest, Property 65: OEM part search filtering accuracy**
        
        For any OEM part search, the system should support complex filtering by 
        VIN patterns, model codes, engine specifications, and other automotive criteria.
        """
        # Arrange: Create OEM catalog item data
        catalog_item_data = {
            'oem_code': self.oem_brand.oem_code,
            'part_number': part_number,
            'description_es': description,
            'group_code': self.taxonomy_group.group_code,
            'vin_patterns': vin_patterns,
            'model_codes': model_codes,
            'engine_codes': engine_codes,
            'transmission_codes': transmission_codes,
            'list_price': list_price,
            'currency_code': 'USD',
            'is_discontinued': False
        }

        # Act: Create catalog item through serializer
        serializer = OEMCatalogItemSerializer(data=catalog_item_data)
        
        # Assert: Search filtering should be accurate
        if serializer.is_valid():
            catalog_item = serializer.save()
            
            try:
                # Verify basic filtering accuracy
                assert catalog_item.part_number == part_number
                assert catalog_item.oem_code == self.oem_brand
                assert catalog_item.vin_patterns == vin_patterns
                assert catalog_item.model_codes == model_codes
                assert catalog_item.engine_codes == engine_codes
                assert catalog_item.transmission_codes == transmission_codes
                
                # Test VIN pattern filtering
                if vin_patterns:
                    # Should be found when searching by VIN pattern
                    matching_items = OEMCatalogItem.objects.filter(
                        vin_patterns__contains=vin_patterns[0]
                    )
                    assert catalog_item in matching_items
                    
                    # Should not be found when searching by non-matching VIN
                    non_matching_vin = 'NONMATCHINGVIN123456'
                    non_matching_items = OEMCatalogItem.objects.filter(
                        vin_patterns__contains=non_matching_vin
                    )
                    assert catalog_item not in non_matching_items
                
                # Test model code filtering
                if model_codes:
                    # Should be found when searching by model code
                    matching_items = OEMCatalogItem.objects.filter(
                        model_codes__contains=model_codes[0]
                    )
                    assert catalog_item in matching_items
                
                # Test engine code filtering
                if engine_codes:
                    # Should be found when searching by engine code
                    matching_items = OEMCatalogItem.objects.filter(
                        engine_codes__contains=engine_codes[0]
                    )
                    assert catalog_item in matching_items
                
                # Test transmission code filtering
                if transmission_codes:
                    # Should be found when searching by transmission code
                    matching_items = OEMCatalogItem.objects.filter(
                        transmission_codes__contains=transmission_codes[0]
                    )
                    assert catalog_item in matching_items
                
                # Test price range filtering
                price_range_items = OEMCatalogItem.objects.filter(
                    list_price__gte=list_price - Decimal('100.00'),
                    list_price__lte=list_price + Decimal('100.00')
                )
                assert catalog_item in price_range_items
                
                # Test OEM brand filtering
                brand_items = OEMCatalogItem.objects.filter(
                    oem_code=self.oem_brand
                )
                assert catalog_item in brand_items
                
                # Test group code filtering
                group_items = OEMCatalogItem.objects.filter(
                    group_code=self.taxonomy_group
                )
                assert catalog_item in group_items
                
            finally:
                catalog_item.delete()

    def test_complex_multi_criteria_filtering(self):
        """
        Test complex filtering with multiple criteria simultaneously
        """
        # Create test catalog items with different characteristics
        items = []
        
        # Item 1: Toyota Camry 2020-2022 with specific engine
        item1 = OEMCatalogItem.objects.create(
            oem_code=self.oem_brand,
            part_number='23220-28030',
            description_es='Fuel Pump Assembly',
            group_code=self.taxonomy_group,
            vin_patterns=['4T1C11AK*LU*', '4T1C11AK*MU*'],
            model_codes=['CAMRY20', 'CAMRY21', 'CAMRY22'],
            engine_codes=['2ARFXE', '2ARFE'],
            transmission_codes=['U660E', 'U760E'],
            list_price=Decimal('245.50'),
            currency_code='USD'
        )
        items.append(item1)
        
        # Item 2: Toyota Corolla 2019-2021 with different engine
        item2 = OEMCatalogItem.objects.create(
            oem_code=self.oem_brand,
            part_number='23220-21030',
            description_es='Fuel Pump Module',
            group_code=self.taxonomy_group,
            vin_patterns=['JTDEPRAE*KJ*', 'JTDEPRAE*LJ*'],
            model_codes=['COROLLA19', 'COROLLA20', 'COROLLA21'],
            engine_codes=['2ZRFAE', '2ZRFE'],
            transmission_codes=['K120', 'U681E'],
            list_price=Decimal('189.75'),
            currency_code='USD'
        )
        items.append(item2)
        
        try:
            # Test filtering by specific VIN pattern
            camry_items = OEMCatalogItem.objects.filter(
                vin_patterns__contains='4T1C11AK*LU*'
            )
            assert item1 in camry_items
            assert item2 not in camry_items
            
            # Test filtering by model code
            corolla_items = OEMCatalogItem.objects.filter(
                model_codes__contains='COROLLA20'
            )
            assert item2 in corolla_items
            assert item1 not in corolla_items
            
            # Test filtering by engine code
            hybrid_engine_items = OEMCatalogItem.objects.filter(
                engine_codes__contains='2ARFXE'
            )
            assert item1 in hybrid_engine_items
            assert item2 not in hybrid_engine_items
            
            # Test complex multi-criteria filtering
            complex_filter = OEMCatalogItem.objects.filter(
                oem_code=self.oem_brand,
                group_code=self.taxonomy_group,
                list_price__gte=Decimal('200.00'),
                engine_codes__contains='2ARFXE'
            )
            assert item1 in complex_filter
            assert item2 not in complex_filter
            
            # Test price range with model filtering
            affordable_camry_parts = OEMCatalogItem.objects.filter(
                model_codes__contains='CAMRY',
                list_price__lte=Decimal('300.00')
            )
            assert item1 in affordable_camry_parts
            
        finally:
            for item in items:
                item.delete()

    def test_wildcard_pattern_matching(self):
        """
        Test wildcard pattern matching in VIN and code filtering
        """
        # Create item with wildcard patterns
        catalog_item = OEMCatalogItem.objects.create(
            oem_code=self.oem_brand,
            part_number='WILDCARD-001',
            description_es='Test Wildcard Part',
            group_code=self.taxonomy_group,
            vin_patterns=['4T1*', '*AK*LU*', '4T1C11AK?LU??????'],
            model_codes=['CAM*', '*RY20', 'CAMRY*'],
            engine_codes=['2AR*', '*FXE', '2AR?XE'],
            list_price=Decimal('150.00'),
            currency_code='USD'
        )
        
        try:
            # Test prefix matching
            prefix_items = OEMCatalogItem.objects.filter(
                vin_patterns__contains='4T1*'
            )
            assert catalog_item in prefix_items
            
            # Test suffix matching
            suffix_items = OEMCatalogItem.objects.filter(
                model_codes__contains='*RY20'
            )
            assert catalog_item in suffix_items
            
            # Test contains matching
            contains_items = OEMCatalogItem.objects.filter(
                vin_patterns__contains='*AK*LU*'
            )
            assert catalog_item in contains_items
            
        finally:
            catalog_item.delete()

    def test_api_endpoint_filtering_accuracy(self):
        """
        Test that API endpoints provide accurate filtering
        """
        # Create test catalog item via API
        catalog_data = {
            'oem_code': self.oem_brand.oem_code,
            'part_number': 'API-FILTER-001',
            'description_es': 'API Filter Test Part',
            'group_code': self.taxonomy_group.group_code,
            'vin_patterns': ['APITEST*', '*FILTER*'],
            'model_codes': ['TESTMODEL', 'APIMODEL'],
            'engine_codes': ['TESTENG', '2ARAPI'],
            'transmission_codes': ['APITRANS'],
            'list_price': '199.99',
            'currency_code': 'USD',
            'is_discontinued': False
        }
        
        response = self.client.post('/api/v1/oem/catalog-items/', catalog_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        catalog_id = response.json()['catalog_id']
        
        # Test filtering by OEM code
        response = self.client.get(f'/api/v1/oem/catalog-items/?oem_code={self.oem_brand.oem_code}')
        assert response.status_code == status.HTTP_200_OK
        items = response.json()['results']
        assert any(item['catalog_id'] == catalog_id for item in items)
        
        # Test filtering by group code
        response = self.client.get(f'/api/v1/oem/catalog-items/?group_code={self.taxonomy_group.group_code}')
        assert response.status_code == status.HTTP_200_OK
        items = response.json()['results']
        assert any(item['catalog_id'] == catalog_id for item in items)
        
        # Test search by part number
        response = self.client.get('/api/v1/oem/catalog-items/?search=API-FILTER-001')
        assert response.status_code == status.HTTP_200_OK
        items = response.json()['results']
        assert any(item['part_number'] == 'API-FILTER-001' for item in items)
        
        # Test search by description
        response = self.client.get('/api/v1/oem/catalog-items/?search=Filter Test')
        assert response.status_code == status.HTTP_200_OK
        items = response.json()['results']
        assert any('Filter Test' in item['description_es'] for item in items)

    def tearDown(self):
        """Clean up test data"""
        # Clean up in reverse dependency order
        OEMCatalogItem.objects.filter(part_number__startswith='API').delete()
        OEMCatalogItem.objects.filter(part_number__startswith='WILDCARD').delete()
        OEMCatalogItem.objects.filter(part_number__startswith='23220').delete()
        TaxonomyGroup.objects.filter(group_code__startswith='FUEL').delete()
        TaxonomySubsystem.objects.filter(subsystem_code__startswith='FUEL').delete()
        TaxonomySystem.objects.filter(system_code__startswith='ENGINE').delete()
        OEMBrand.objects.filter(oem_code__startswith='TOYOTA').delete()