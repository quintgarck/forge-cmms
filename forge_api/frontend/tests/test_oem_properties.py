"""Property-based tests for OEM interfaces."""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock


class TestOEMInterfaceProperties(TestCase):
    """Property-based tests for OEM interface functionality."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @given(
        search_term=st.text(min_size=1, max_size=50),
        manufacturer_id=st.integers(min_value=1, max_value=100),
        availability_status=st.sampled_from(['IN_STOCK', 'LOW_STOCK', 'OUT_OF_STOCK', 'DISCONTINUED'])
    )
    @settings(max_examples=20)
    @patch('forge_api.frontend.views.oem_views.ForgeAPIClient')
    def test_oem_search_interface_functionality(self, mock_api_client, search_term, manufacturer_id, availability_status):
        """**Feature: forge-frontend-web, Property 27: OEM search interface functionality**
        
        *For any* search parameters (term, manufacturer, availability), 
        the OEM search interface should return properly formatted results 
        with all required fields and maintain consistent structure.
        
        **Validates: Requirements 8.1**
        """
        # Mock API response
        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance
        
        # Generate mock OEM parts data
        mock_parts = [
            {
                'catalog_id': i,
                'part_number': f'OEM-{i:04d}',
                'oem_code': {
                    'oem_code': f'MFG{i}',
                    'name': f'Manufacturer {i}'
                },
                'description_es': f'Descripción de parte {i}',
                'availability_status': availability_status,
                'list_price': 100.00 + i,
                'updated_at': '2024-01-01T00:00:00Z',
                'vin_patterns': [f'VIN{i}*'],
                'cross_ref_count': i % 5
            }
            for i in range(1, 6)
        ]
        
        mock_client_instance.get.return_value = {
            'results': mock_parts,
            'count': len(mock_parts)
        }
        
        # Test the OEM part catalog view
        url = reverse('frontend:oem_part_catalog')
        response = self.client.get(url, {
            'search': search_term,
            'manufacturer': manufacturer_id,
            'availability': availability_status
        })
        
        # Property: Response should be successful
        assert response.status_code == 200
        
        # Property: Context should contain required OEM interface elements
        context = response.context
        assert 'parts' in context
        assert 'pagination' in context
        assert 'filters' in context
        assert 'catalog_stats' in context
        
        # Property: Each part should have required display fields
        parts = context['parts']
        for part in parts:
            # Required fields for OEM interface
            assert 'part_number' in part
            assert 'oem_code' in part
            assert 'availability_status' in part
            assert 'availability_class' in part  # Added by view processing
            assert 'availability_icon' in part   # Added by view processing
            assert 'formatted_price' in part     # Added by view processing
            assert 'compatibility_score' in part # Added by view processing
            
        # Property: Filters should match request parameters
        filters = context['filters']
        assert filters['search'] == search_term
        assert str(filters['manufacturer']) == str(manufacturer_id)
        assert filters['availability'] == availability_status
        
        # Property: Catalog stats should be properly calculated
        stats = context['catalog_stats']
        assert 'total' in stats
        assert 'in_stock' in stats
        assert 'with_cross_refs' in stats
        assert 'avg_compatibility' in stats
        assert stats['total'] >= 0
        assert stats['in_stock'] >= 0
        assert stats['with_cross_refs'] >= 0
        assert 0 <= stats['avg_compatibility'] <= 100
    
    @given(
        part_number=st.text(min_size=3, max_size=30),
        search_type=st.sampled_from(['oem', 'aftermarket']),
        confidence_level=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=20)
    @patch('forge_api.frontend.views.oem_views.ForgeAPIClient')
    def test_part_equivalence_display_accuracy(self, mock_api_client, part_number, search_type, confidence_level):
        """**Feature: forge-frontend-web, Property 29: Part equivalence display accuracy**
        
        *For any* part number and search type, the cross-reference tool should 
        display equivalences with accurate confidence levels, proper formatting,
        and complete cross-reference information.
        
        **Validates: Requirements 8.3**
        """
        # Mock API response
        mock_client_instance = MagicMock()
        mock_api_client.return_value = mock_client_instance
        
        # Generate mock cross-reference data
        mock_cross_refs = [
            {
                'equivalence_id': i,
                'oem_part_number': part_number,
                'oem_code': {
                    'oem_code': f'OEM{i}',
                    'name': f'OEM Brand {i}'
                },
                'aftermarket_sku': f'AM-{i:04d}',
                'equivalence_type': 'DIRECT',
                'confidence_score': confidence_level,
                'notes': f'Cross-reference note {i}',
                'verified_date': '2024-01-01'
            }
            for i in range(1, 4)
        ]
        
        mock_oem_parts = [
            {
                'catalog_id': 1,
                'part_number': part_number,
                'oem_code': {
                    'oem_code': 'OEM1',
                    'name': 'Test OEM Brand'
                },
                'description_es': 'Test part description',
                'availability_status': 'IN_STOCK',
                'list_price': 150.00
            }
        ]
        
        # Configure mock responses based on search type
        if search_type == 'oem':
            mock_client_instance.get.side_effect = [
                {'results': mock_oem_parts},  # OEM parts search
                {'results': mock_cross_refs}   # Cross-references for each part
            ]
        else:
            mock_client_instance.get.side_effect = [
                {'results': mock_cross_refs}   # Aftermarket search
            ]
        
        # Test the cross-reference tool
        url = reverse('frontend:oem_cross_reference_tool')
        response = self.client.get(url, {
            'part_number': part_number,
            'search_type': search_type
        })
        
        # Property: Response should be successful
        assert response.status_code == 200
        
        # Property: Context should contain search results
        context = response.context
        assert 'search_results' in context
        assert 'search_params' in context
        
        # Property: Search parameters should match request
        search_params = context['search_params']
        assert search_params['part_number'] == part_number
        assert search_params['search_type'] == search_type
        
        # Property: Search results should have proper structure
        search_results = context['search_results']
        if search_results:  # Only test if results exist
            assert 'total_matches' in search_results
            assert search_results['total_matches'] >= 0
            
            # Property: Cross-references should have accurate confidence display
            if 'cross_references' in search_results:
                cross_refs = search_results['cross_references']
                for cross_ref in cross_refs:
                    # Required fields for equivalence display
                    assert 'oem_part_number' in cross_ref
                    assert 'aftermarket_sku' in cross_ref
                    assert 'confidence_score' in cross_ref
                    
                    # Processed fields for display
                    assert 'confidence_class' in cross_ref
                    assert 'confidence_icon' in cross_ref
                    assert 'confidence_percent' in cross_ref
                    
                    # Property: Confidence score should be within valid range
                    confidence = cross_ref.get('confidence_score', 0)
                    assert 0 <= confidence <= 100
                    
                    # Property: Confidence class should match score range
                    confidence_class = cross_ref.get('confidence_class')
                    if confidence >= 90:
                        assert confidence_class == 'success'
                    elif confidence >= 70:
                        assert confidence_class == 'info'
                    elif confidence >= 50:
                        assert confidence_class == 'warning'
                    else:
                        assert confidence_class == 'danger'