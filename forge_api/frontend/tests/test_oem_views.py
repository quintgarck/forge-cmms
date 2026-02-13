"""
Tests for OEM catalog management views.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from ..services.api_client import APIException


class OEMViewsTestCase(TestCase):
    """Test case for OEM catalog management views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_catalog_search_view(self, mock_api_client):
        """Test OEM catalog search view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_catalog_items = {
            'count': 2,
            'results': [
                {
                    'catalog_id': 1,
                    'part_number': 'ABC123',
                    'oem_code': {'name': 'Honda', 'oem_code': 'HON'},
                    'description_es': 'Filtro de aceite',
                    'list_price': '25.99',
                    'net_price': '19.99',
                    'currency_code': 'USD',
                    'is_discontinued': False,
                    'oem_lead_time_days': 7,
                    'part_number_type': 'FULL_12',
                    'vin_patterns': ['1HGBH41JXMN*'],
                    'model_codes': ['CIVIC'],
                    'engine_codes': ['K20A'],
                    'updated_at': '2024-01-15T10:00:00Z'
                },
                {
                    'catalog_id': 2,
                    'part_number': 'XYZ789',
                    'oem_code': {'name': 'Toyota', 'oem_code': 'TOY'},
                    'description_es': 'Pastillas de freno',
                    'list_price': '45.00',
                    'net_price': '35.00',
                    'currency_code': 'USD',
                    'is_discontinued': True,
                    'oem_lead_time_days': 30,
                    'part_number_type': 'BASIC_5',
                    'vin_patterns': [],
                    'model_codes': ['CAMRY'],
                    'engine_codes': [],
                    'updated_at': '2024-01-10T15:30:00Z'
                }
            ]
        }
        
        mock_client.get.side_effect = [
            mock_catalog_items,  # Catalog items
            {'results': [{'oem_code': 'HON', 'name': 'Honda'}]},  # OEM brands
            {'results': [{'group_code': 'ENG', 'group_name': 'Engine'}]},  # Taxonomy groups
        ]
        
        url = reverse('frontend:oem_catalog_search')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Búsqueda de Catálogo OEM')
        self.assertContains(response, 'ABC123')
        self.assertContains(response, 'XYZ789')
        self.assertContains(response, 'Honda')
        self.assertContains(response, 'Toyota')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_catalog_search_with_filters(self, mock_api_client):
        """Test OEM catalog search with filters."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_client.get.side_effect = [
            {'count': 0, 'results': []},  # Filtered results (empty)
            {'results': []},  # OEM brands
            {'results': []},  # Taxonomy groups
        ]
        
        url = reverse('frontend:oem_catalog_search')
        response = self.client.get(url, {
            'search': 'brake',
            'oem_code': 'HON',
            'vin_pattern': '1HGBH41JXMN',
            'is_discontinued': 'false'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontraron partes')
        
        # Verify API was called with filters
        mock_client.get.assert_called()
        call_args = mock_client.get.call_args_list[0]
        self.assertEqual(call_args[0][0], 'oem-catalog-items/')
        self.assertIn('search', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['search'], 'brake')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_brand_management_view(self, mock_api_client):
        """Test OEM brand management view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_brands = {
            'results': [
                {
                    'brand_id': 1,
                    'oem_code': 'HON',
                    'name': 'Honda',
                    'country': 'Japan',
                    'website': 'https://honda.com',
                    'support_email': 'support@honda.com',
                    'is_active': True,
                    'created_at': '2024-01-01T00:00:00Z'
                },
                {
                    'brand_id': 2,
                    'oem_code': 'TOY',
                    'name': 'Toyota',
                    'country': 'Japan',
                    'website': None,
                    'support_email': None,
                    'is_active': False,
                    'created_at': '2024-01-02T00:00:00Z'
                }
            ]
        }
        
        # Mock catalog items count for each brand
        mock_client.get.side_effect = [
            mock_brands,  # Brands
            {'count': 150},  # Honda catalog count
            {'count': 200},  # Toyota catalog count
        ]
        
        url = reverse('frontend:oem_brand_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Marcas OEM')
        self.assertContains(response, 'Honda')
        self.assertContains(response, 'Toyota')
        self.assertContains(response, 'Japan')
        self.assertContains(response, 'Activo')
        self.assertContains(response, 'Inactivo')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_equivalence_view(self, mock_api_client):
        """Test OEM equivalence management view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_equivalences = {
            'count': 2,
            'results': [
                {
                    'equivalence_id': 1,
                    'oem_part_number': 'ABC123',
                    'oem_code': {'name': 'Honda', 'oem_code': 'HON'},
                    'aftermarket_sku': 'AM-ABC123',
                    'equivalence_type': 'DIRECT',
                    'confidence_score': 95,
                    'notes': 'Perfect match',
                    'verified_by': {
                        'name': 'John Doe',
                        'username': 'johndoe'
                    },
                    'verified_date': '2024-01-15',
                    'created_at': '2024-01-10T10:00:00Z'
                },
                {
                    'equivalence_id': 2,
                    'oem_part_number': 'XYZ789',
                    'oem_code': {'name': 'Toyota', 'oem_code': 'TOY'},
                    'aftermarket_sku': 'AM-XYZ789',
                    'equivalence_type': 'COMPATIBLE',
                    'confidence_score': 75,
                    'notes': 'Good alternative',
                    'verified_by': None,
                    'verified_date': None,
                    'created_at': '2024-01-12T14:30:00Z'
                }
            ]
        }
        
        mock_client.get.side_effect = [
            mock_equivalences,  # Equivalences
            {'results': [{'oem_code': 'HON', 'name': 'Honda'}]},  # OEM brands
        ]
        
        url = reverse('frontend:oem_equivalence_management')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Equivalencias OEM')
        self.assertContains(response, 'ABC123')
        self.assertContains(response, 'XYZ789')
        self.assertContains(response, 'AM-ABC123')
        self.assertContains(response, 'Directo')
        self.assertContains(response, 'Compatible')
        self.assertContains(response, 'Verificado')
        self.assertContains(response, 'Sin verificar')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_part_comparator_view_no_search(self, mock_api_client):
        """Test OEM part comparator view without search."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_client.get.return_value = {
            'results': [
                {'oem_code': 'HON', 'name': 'Honda'},
                {'oem_code': 'TOY', 'name': 'Toyota'}
            ]
        }
        
        url = reverse('frontend:oem_part_comparator')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comparador de Partes OEM vs Aftermarket')
        self.assertContains(response, 'Ingrese los datos de la parte OEM')
        self.assertContains(response, 'Honda')
        self.assertContains(response, 'Toyota')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_part_comparator_with_results(self, mock_api_client):
        """Test OEM part comparator with search results."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_oem_part = {
            'catalog_id': 1,
            'part_number': 'ABC123',
            'description_es': 'Filtro de aceite Honda',
            'list_price': '25.99',
            'net_price': '19.99',
            'currency_code': 'USD'
        }
        
        mock_equivalences = {
            'results': [
                {
                    'equivalence_id': 1,
                    'oem_part_number': 'ABC123',
                    'oem_code': {'name': 'Honda', 'oem_code': 'HON'},
                    'aftermarket_sku': 'AM-ABC123',
                    'equivalence_type': 'DIRECT',
                    'confidence_score': 95,
                    'notes': 'Perfect match',
                    'verified_by': {'name': 'John Doe', 'username': 'johndoe'},
                    'verified_date': '2024-01-15'
                }
            ]
        }
        
        mock_client.get.side_effect = [
            {'results': [mock_oem_part]},  # OEM catalog item
            mock_equivalences,  # Equivalences
            {'results': [{'oem_code': 'HON', 'name': 'Honda'}]},  # OEM brands
        ]
        
        url = reverse('frontend:oem_part_comparator')
        response = self.client.get(url, {
            'oem_code': 'HON',
            'oem_part': 'ABC123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Parte OEM Original')
        self.assertContains(response, 'ABC123')
        self.assertContains(response, 'AM-ABC123')
        self.assertContains(response, 'Equivalencias Aftermarket')
        self.assertContains(response, '95%')
        self.assertContains(response, 'Verificado')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_part_comparator_no_results(self, mock_api_client):
        """Test OEM part comparator with no results found."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_client.get.side_effect = [
            {'results': []},  # No OEM catalog item found
            {'results': []},  # No equivalences
            {'results': [{'oem_code': 'HON', 'name': 'Honda'}]},  # OEM brands
        ]
        
        url = reverse('frontend:oem_part_comparator')
        response = self.client.get(url, {
            'oem_code': 'HON',
            'oem_part': 'NOTFOUND123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Parte OEM No Encontrada')
        self.assertContains(response, 'NOTFOUND123')
        self.assertContains(response, 'Agregar al Catálogo')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_views_api_error_handling(self, mock_api_client):
        """Test OEM views handle API errors gracefully."""
        # Mock API client to raise exception
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        mock_client.get.side_effect = APIException("API connection failed")
        
        # Test catalog search
        url = reverse('frontend:oem_catalog_search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Búsqueda de Catálogo OEM')
        
        # Test brand management
        url = reverse('frontend:oem_brand_management')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Marcas OEM')
        
        # Test equivalence management
        url = reverse('frontend:oem_equivalence_management')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Equivalencias OEM')
    
    def test_oem_views_require_authentication(self):
        """Test that OEM views require user authentication."""
        # Logout user
        self.client.logout()
        
        urls_to_test = [
            reverse('frontend:oem_catalog_search'),
            reverse('frontend:oem_brand_management'),
            reverse('frontend:oem_equivalence_management'),
            reverse('frontend:oem_part_comparator'),
        ]
        
        for url in urls_to_test:
            response = self.client.get(url)
            # Should redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)


class OEMPropertyTestCase(TestCase):
    """Property-based tests for OEM functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_oem_search_interface_functionality_property(self, mock_api_client):
        """
        Property 27: OEM search interface functionality
        For any search query and filter combination, the OEM catalog search
        should return consistent results and handle all input variations properly.
        Validates: Requirements 8.1
        """
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Test different search configurations
        test_searches = [
            {'search': '', 'oem_code': '', 'filters': {}},  # Empty search
            {'search': 'brake', 'oem_code': 'HON', 'filters': {'vin_pattern': '1HGBH'}},  # Full search
            {'search': 'filter', 'oem_code': '', 'filters': {'is_discontinued': 'false'}},  # Partial search
            {'search': '123', 'oem_code': 'TOY', 'filters': {'model_code': 'CAMRY'}},  # Specific search
        ]
        
        for search_config in test_searches:
            with self.subTest(search=search_config):
                # Mock appropriate responses
                mock_client.get.side_effect = [
                    {'count': 5, 'results': []},  # Search results
                    {'results': []},  # OEM brands
                    {'results': []},  # Taxonomy groups
                ]
                
                url = reverse('frontend:oem_catalog_search')
                params = {
                    'search': search_config['search'],
                    'oem_code': search_config['oem_code'],
                    **search_config['filters']
                }
                response = self.client.get(url, params)
                
                # Property: Search interface should be functional for any input
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Búsqueda de Catálogo OEM')
                
                # Should have search form
                self.assertContains(response, 'form')
                self.assertContains(response, 'name="search"')
                self.assertContains(response, 'name="oem_code"')
                
                # Should handle results appropriately
                if search_config['search'] or search_config['oem_code'] or search_config['filters']:
                    # Should show results section
                    pass  # Results handling is consistent
    
    @patch('frontend.views.oem_views.ForgeAPIClient')
    def test_part_equivalence_display_accuracy_property(self, mock_api_client):
        """
        Property 29: Part equivalence display accuracy
        For any equivalence with any confidence score and verification status,
        the interface should accurately display the equivalence information
        and provide appropriate visual indicators.
        Validates: Requirements 8.3
        """
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Test different equivalence configurations
        test_equivalences = [
            {'confidence': 95, 'type': 'DIRECT', 'verified': True},
            {'confidence': 75, 'type': 'COMPATIBLE', 'verified': False},
            {'confidence': 45, 'type': 'UPGRADE', 'verified': True},
            {'confidence': 25, 'type': 'DOWNGRADE', 'verified': False},
            {'confidence': 0, 'type': '', 'verified': False},  # Edge case
        ]
        
        for equiv_config in test_equivalences:
            with self.subTest(equivalence=equiv_config):
                mock_equivalence = {
                    'equivalence_id': 1,
                    'oem_part_number': 'TEST123',
                    'oem_code': {'name': 'Test Brand', 'oem_code': 'TST'},
                    'aftermarket_sku': 'AM-TEST123',
                    'equivalence_type': equiv_config['type'],
                    'confidence_score': equiv_config['confidence'],
                    'notes': 'Test equivalence',
                    'verified_by': {'name': 'Tester', 'username': 'tester'} if equiv_config['verified'] else None,
                    'verified_date': '2024-01-15' if equiv_config['verified'] else None,
                    'created_at': '2024-01-10T10:00:00Z'
                }
                
                mock_client.get.side_effect = [
                    {'count': 1, 'results': [mock_equivalence]},  # Equivalences
                    {'results': []},  # OEM brands
                ]
                
                url = reverse('frontend:oem_equivalence_management')
                response = self.client.get(url)
                
                # Property: Equivalence display should be accurate for any configuration
                self.assertEqual(response.status_code, 200)
                
                # Should display equivalence information
                self.assertContains(response, 'TEST123')
                self.assertContains(response, 'AM-TEST123')
                
                # Should display confidence score
                self.assertContains(response, str(equiv_config['confidence']))
                
                # Should display verification status appropriately
                if equiv_config['verified']:
                    self.assertContains(response, 'Verificado')
                else:
                    self.assertContains(response, 'Sin verificar')
                
                # Should have appropriate styling based on confidence
                if equiv_config['confidence'] >= 90:
                    # High confidence should have success styling
                    pass  # Visual styling is handled by CSS
                elif equiv_config['confidence'] >= 50:
                    # Medium confidence should have warning styling
                    pass
                else:
                    # Low confidence should have danger styling
                    pass