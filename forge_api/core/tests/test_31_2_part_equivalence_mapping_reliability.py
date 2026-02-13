"""
**Feature: forge-api-rest, Property 66: Part equivalence mapping reliability**

Property-based test for part equivalence mapping reliability.
Tests that equivalence requests provide accurate OEM to aftermarket part 
mapping with confidence scores and compatibility verification.

**Validates: Requirements 14.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal

from ..models import OEMBrand, OEMEquivalence, Technician
from ..serializers.main_serializers import OEMEquivalenceSerializer


class TestPartEquivalenceMappingReliability(APITestCase):
    """Property-based tests for part equivalence mapping reliability"""

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
        
        # Create OEM brands for testing
        self.oem_brands = [
            OEMBrand.objects.create(
                oem_code='TOYOTA',
                name='Toyota Motor Corporation',
                country='Japan',
                is_active=True
            ),
            OEMBrand.objects.create(
                oem_code='HONDA',
                name='Honda Motor Co.',
                country='Japan',
                is_active=True
            ),
            OEMBrand.objects.create(
                oem_code='FORD',
                name='Ford Motor Company',
                country='USA',
                is_active=True
            )
        ]
        
        self.client.force_authenticate(user=self.user)

    # Hypothesis strategies for generating test data
    valid_oem_part_numbers = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=5,
        max_size=30
    ).map(lambda x: x.replace(' ', ''))
    
    valid_aftermarket_skus = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=3,
        max_size=20
    ).map(lambda x: x.replace(' ', ''))
    
    valid_equivalence_types = st.sampled_from(['DIRECT', 'COMPATIBLE', 'UPGRADE', 'DOWNGRADE'])
    
    valid_confidence_scores = st.integers(min_value=1, max_value=100)
    
    valid_notes = st.text(min_size=0, max_size=500)

    @given(
        oem_part_number=valid_oem_part_numbers,
        aftermarket_sku=valid_aftermarket_skus,
        equivalence_type=valid_equivalence_types,
        confidence_score=valid_confidence_scores,
        notes=valid_notes
    )
    @settings(max_examples=100, deadline=None)
    def test_part_equivalence_mapping_reliability(self, oem_part_number, aftermarket_sku, 
                                                equivalence_type, confidence_score, notes):
        """
        **Feature: forge-api-rest, Property 66: Part equivalence mapping reliability**
        
        For any equivalence request, the system should provide accurate OEM to 
        aftermarket part mapping with confidence scores and compatibility verification.
        """
        # Select random OEM brand
        oem_brand = st.sampled_from(self.oem_brands).example()
        
        # Arrange: Create equivalence data
        equivalence_data = {
            'oem_part_number': oem_part_number,
            'oem_code': oem_brand.oem_code,
            'aftermarket_sku': aftermarket_sku,
            'equivalence_type': equivalence_type,
            'confidence_score': confidence_score,
            'notes': notes,
            'verified_by': self.technician.technician_id
        }

        # Act: Create equivalence through serializer
        serializer = OEMEquivalenceSerializer(data=equivalence_data)
        
        # Assert: Mapping reliability should be maintained
        if serializer.is_valid():
            equivalence = serializer.save()
            
            try:
                # Verify mapping accuracy
                assert equivalence.oem_part_number == oem_part_number
                assert equivalence.oem_code == oem_brand
                assert equivalence.aftermarket_sku == aftermarket_sku
                assert equivalence.equivalence_type == equivalence_type
                assert equivalence.confidence_score == confidence_score
                assert equivalence.notes == notes
                
                # Test reliability of mapping retrieval
                # Should be found when searching by OEM part number
                oem_equivalences = OEMEquivalence.objects.filter(
                    oem_part_number=oem_part_number,
                    oem_code=oem_brand
                )
                assert equivalence in oem_equivalences
                
                # Should be found when searching by aftermarket SKU
                aftermarket_equivalences = OEMEquivalence.objects.filter(
                    aftermarket_sku=aftermarket_sku
                )
                assert equivalence in aftermarket_equivalences
                
                # Test confidence score reliability
                if confidence_score >= 80:
                    # High confidence equivalences should be easily retrievable
                    high_confidence = OEMEquivalence.objects.filter(
                        confidence_score__gte=80
                    )
                    assert equivalence in high_confidence
                
                # Test equivalence type reliability
                type_equivalences = OEMEquivalence.objects.filter(
                    equivalence_type=equivalence_type
                )
                assert equivalence in type_equivalences
                
                # Test brand-specific reliability
                brand_equivalences = OEMEquivalence.objects.filter(
                    oem_code=oem_brand
                )
                assert equivalence in brand_equivalences
                
                # Verify mapping consistency
                retrieved_equivalence = OEMEquivalence.objects.get(
                    oem_part_number=oem_part_number,
                    oem_code=oem_brand,
                    aftermarket_sku=aftermarket_sku
                )
                assert retrieved_equivalence.equivalence_type == equivalence_type
                assert retrieved_equivalence.confidence_score == confidence_score
                
            finally:
                equivalence.delete()

    def test_multiple_equivalences_reliability(self):
        """
        Test reliability when multiple equivalences exist for the same OEM part
        """
        oem_brand = self.oem_brands[0]  # Toyota
        oem_part = '90915-YZZD4'  # Oil filter
        
        equivalences = []
        
        try:
            # Create multiple aftermarket equivalences for same OEM part
            equivalence_data = [
                {
                    'aftermarket_sku': 'FRAM-PH3593A',
                    'equivalence_type': 'DIRECT',
                    'confidence_score': 95,
                    'notes': 'Direct OEM replacement'
                },
                {
                    'aftermarket_sku': 'MOBIL1-M1-110A',
                    'equivalence_type': 'COMPATIBLE',
                    'confidence_score': 88,
                    'notes': 'Compatible premium filter'
                },
                {
                    'aftermarket_sku': 'BOSCH-3323',
                    'equivalence_type': 'UPGRADE',
                    'confidence_score': 92,
                    'notes': 'Enhanced filtration upgrade'
                },
                {
                    'aftermarket_sku': 'GENERIC-OF001',
                    'equivalence_type': 'COMPATIBLE',
                    'confidence_score': 65,
                    'notes': 'Budget compatible option'
                }
            ]
            
            for data in equivalence_data:
                equivalence = OEMEquivalence.objects.create(
                    oem_part_number=oem_part,
                    oem_code=oem_brand,
                    aftermarket_sku=data['aftermarket_sku'],
                    equivalence_type=data['equivalence_type'],
                    confidence_score=data['confidence_score'],
                    notes=data['notes'],
                    verified_by=self.technician
                )
                equivalences.append(equivalence)
            
            # Test reliability of multiple mappings
            all_equivalences = OEMEquivalence.objects.filter(
                oem_part_number=oem_part,
                oem_code=oem_brand
            )
            assert all_equivalences.count() == 4
            
            # Test confidence-based filtering reliability
            high_confidence = all_equivalences.filter(confidence_score__gte=90)
            assert high_confidence.count() == 2  # FRAM and BOSCH
            
            medium_confidence = all_equivalences.filter(
                confidence_score__gte=80,
                confidence_score__lt=90
            )
            assert medium_confidence.count() == 1  # MOBIL1
            
            # Test type-based filtering reliability
            direct_equivalences = all_equivalences.filter(equivalence_type='DIRECT')
            assert direct_equivalences.count() == 1
            assert direct_equivalences.first().aftermarket_sku == 'FRAM-PH3593A'
            
            compatible_equivalences = all_equivalences.filter(equivalence_type='COMPATIBLE')
            assert compatible_equivalences.count() == 2
            
            # Test ordering by confidence score reliability
            ordered_equivalences = all_equivalences.order_by('-confidence_score')
            confidence_scores = [eq.confidence_score for eq in ordered_equivalences]
            assert confidence_scores == [95, 92, 88, 65]
            
        finally:
            for equivalence in equivalences:
                equivalence.delete()

    def test_cross_brand_equivalence_reliability(self):
        """
        Test reliability of equivalences across different OEM brands
        """
        # Same aftermarket part fits multiple OEM brands
        aftermarket_sku = 'UNIVERSAL-BRAKE-PAD-001'
        
        equivalences = []
        
        try:
            # Create equivalences for same aftermarket part across brands
            cross_brand_data = [
                {
                    'oem_brand': self.oem_brands[0],  # Toyota
                    'oem_part': '04465-02140',
                    'confidence_score': 90
                },
                {
                    'oem_brand': self.oem_brands[1],  # Honda
                    'oem_part': '45022-S9A-A00',
                    'confidence_score': 88
                },
                {
                    'oem_brand': self.oem_brands[2],  # Ford
                    'oem_part': 'F1TZ-2001-A',
                    'confidence_score': 85
                }
            ]
            
            for data in cross_brand_data:
                equivalence = OEMEquivalence.objects.create(
                    oem_part_number=data['oem_part'],
                    oem_code=data['oem_brand'],
                    aftermarket_sku=aftermarket_sku,
                    equivalence_type='COMPATIBLE',
                    confidence_score=data['confidence_score'],
                    notes=f'Compatible brake pad for {data["oem_brand"].name}',
                    verified_by=self.technician
                )
                equivalences.append(equivalence)
            
            # Test cross-brand reliability
            aftermarket_equivalences = OEMEquivalence.objects.filter(
                aftermarket_sku=aftermarket_sku
            )
            assert aftermarket_equivalences.count() == 3
            
            # Verify each brand mapping is reliable
            for data in cross_brand_data:
                brand_equivalence = aftermarket_equivalences.filter(
                    oem_code=data['oem_brand']
                ).first()
                assert brand_equivalence is not None
                assert brand_equivalence.oem_part_number == data['oem_part']
                assert brand_equivalence.confidence_score == data['confidence_score']
            
            # Test brand-specific filtering reliability
            toyota_equivalences = aftermarket_equivalences.filter(
                oem_code=self.oem_brands[0]
            )
            assert toyota_equivalences.count() == 1
            assert toyota_equivalences.first().oem_part_number == '04465-02140'
            
        finally:
            for equivalence in equivalences:
                equivalence.delete()

    def test_equivalence_verification_reliability(self):
        """
        Test reliability of equivalence verification process
        """
        equivalence = OEMEquivalence.objects.create(
            oem_part_number='TEST-PART-001',
            oem_code=self.oem_brands[0],
            aftermarket_sku='TEST-SKU-001',
            equivalence_type='DIRECT',
            confidence_score=75,
            notes='Pending verification',
            verified_by=None,  # Not yet verified
            verified_date=None
        )
        
        try:
            # Test unverified state reliability
            unverified = OEMEquivalence.objects.filter(
                verified_by__isnull=True
            )
            assert equivalence in unverified
            
            # Verify the equivalence
            equivalence.verified_by = self.technician
            equivalence.verified_date = '2024-01-15'
            equivalence.confidence_score = 95  # Increase confidence after verification
            equivalence.notes = 'Verified by technician testing'
            equivalence.save()
            
            # Test verified state reliability
            verified = OEMEquivalence.objects.filter(
                verified_by__isnull=False
            )
            assert equivalence in verified
            
            # Test verification impact on confidence
            high_confidence_verified = OEMEquivalence.objects.filter(
                verified_by__isnull=False,
                confidence_score__gte=90
            )
            assert equivalence in high_confidence_verified
            
        finally:
            equivalence.delete()

    def test_api_endpoint_equivalence_reliability(self):
        """
        Test that API endpoints provide reliable equivalence mapping
        """
        # Create equivalence via API
        equivalence_data = {
            'oem_part_number': 'API-TEST-001',
            'oem_code': self.oem_brands[0].oem_code,
            'aftermarket_sku': 'API-SKU-001',
            'equivalence_type': 'DIRECT',
            'confidence_score': 92,
            'notes': 'API test equivalence'
        }
        
        response = self.client.post('/api/v1/oem/equivalences/', equivalence_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        equivalence_id = response.json()['equivalence_id']
        
        # Test retrieval reliability via API
        response = self.client.get(f'/api/v1/oem/equivalences/{equivalence_id}/')
        assert response.status_code == status.HTTP_200_OK
        
        retrieved_data = response.json()
        assert retrieved_data['oem_part_number'] == 'API-TEST-001'
        assert retrieved_data['aftermarket_sku'] == 'API-SKU-001'
        assert retrieved_data['confidence_score'] == 92
        
        # Test filtering reliability via API
        response = self.client.get(f'/api/v1/oem/equivalences/?oem_code={self.oem_brands[0].oem_code}')
        assert response.status_code == status.HTTP_200_OK
        equivalences = response.json()['results']
        assert any(eq['equivalence_id'] == equivalence_id for eq in equivalences)
        
        # Test search reliability via API
        response = self.client.get('/api/v1/oem/equivalences/?search=API-TEST-001')
        assert response.status_code == status.HTTP_200_OK
        equivalences = response.json()['results']
        assert any(eq['oem_part_number'] == 'API-TEST-001' for eq in equivalences)

    def tearDown(self):
        """Clean up test data"""
        # Clean up equivalences
        OEMEquivalence.objects.filter(oem_part_number__startswith='API').delete()
        OEMEquivalence.objects.filter(oem_part_number__startswith='TEST').delete()
        OEMEquivalence.objects.filter(oem_part_number__startswith='90915').delete()
        OEMEquivalence.objects.filter(oem_part_number__startswith='04465').delete()
        OEMEquivalence.objects.filter(oem_part_number__startswith='45022').delete()
        OEMEquivalence.objects.filter(oem_part_number__startswith='F1TZ').delete()
        
        # Clean up OEM brands
        for brand in self.oem_brands:
            brand.delete()