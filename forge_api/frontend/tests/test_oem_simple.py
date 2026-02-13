"""Simple tests for OEM interfaces."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock


class TestOEMInterfaceSimple(TestCase):
    """Simple tests for OEM interface functionality."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_oem_manufacturer_management_view(self):
        """Test OEM manufacturer management view loads correctly."""
        url = reverse('frontend:oem_manufacturer_management')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should contain required context elements
        self.assertIn('manufacturers', response.context)
        self.assertIn('pagination', response.context)
        self.assertIn('filters', response.context)
        self.assertIn('dashboard_stats', response.context)
        
        # Should have manufacturers data
        manufacturers = response.context['manufacturers']
        self.assertIsInstance(manufacturers, list)
        
        # Each manufacturer should have required fields
        if manufacturers:
            manufacturer = manufacturers[0]
            self.assertIn('name', manufacturer)
            self.assertIn('status', manufacturer)
            self.assertIn('status_class', manufacturer)
            self.assertIn('status_icon', manufacturer)
            self.assertIn('quality_score', manufacturer)
            self.assertIn('quality_class', manufacturer)
    
    def test_oem_part_catalog_view(self):
        """Test OEM part catalog view loads correctly."""
        url = reverse('frontend:oem_part_catalog')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should contain required context elements
        self.assertIn('parts', response.context)
        self.assertIn('pagination', response.context)
        self.assertIn('filters', response.context)
        self.assertIn('catalog_stats', response.context)
        
        # Should have parts data
        parts = response.context['parts']
        self.assertIsInstance(parts, list)
        
        # Each part should have required fields
        if parts:
            part = parts[0]
            self.assertIn('part_number', part)
            self.assertIn('oem_code', part)
            self.assertIn('availability_status', part)
            self.assertIn('availability_class', part)
            self.assertIn('availability_icon', part)
            self.assertIn('formatted_price', part)
            self.assertIn('compatibility_score', part)
    
    def test_cross_reference_tool_view(self):
        """Test cross-reference tool view loads correctly."""
        url = reverse('frontend:oem_cross_reference_tool')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should contain required context elements
        self.assertIn('search_params', response.context)
        self.assertIn('popular_parts', response.context)
        
        # Search params should have default values
        search_params = response.context['search_params']
        self.assertIn('part_number', search_params)
        self.assertIn('search_type', search_params)
        self.assertEqual(search_params['search_type'], 'oem')
    
    def test_cross_reference_tool_with_search(self):
        """Test cross-reference tool with search parameters."""
        url = reverse('frontend:oem_cross_reference_tool')
        response = self.client.get(url, {
            'part_number': 'TEST-1234',
            'search_type': 'oem'
        })
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Should contain search results
        self.assertIn('search_results', response.context)
        
        # Search results should have proper structure
        search_results = response.context['search_results']
        if search_results:
            self.assertIn('total_matches', search_results)
            self.assertIn('oem_parts', search_results)
            self.assertIn('cross_references', search_results)
    
    def test_oem_manufacturer_filters(self):
        """Test OEM manufacturer management with filters."""
        url = reverse('frontend:oem_manufacturer_management')
        response = self.client.get(url, {
            'search': 'test',
            'status': 'ACTIVE',
            'country': 'US'
        })
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Filters should be preserved in context
        filters = response.context['filters']
        self.assertEqual(filters['search'], 'test')
        self.assertEqual(filters['status'], 'ACTIVE')
        self.assertEqual(filters['country'], 'US')
    
    def test_oem_part_catalog_filters(self):
        """Test OEM part catalog with filters."""
        url = reverse('frontend:oem_part_catalog')
        response = self.client.get(url, {
            'search': 'OEM-1234',
            'manufacturer': '1',
            'availability': 'IN_STOCK'
        })
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Filters should be preserved in context
        filters = response.context['filters']
        self.assertEqual(filters['search'], 'OEM-1234')
        self.assertEqual(filters['manufacturer'], '1')
        self.assertEqual(filters['availability'], 'IN_STOCK')
    
    def test_oem_dashboard_stats_calculation(self):
        """Test that dashboard statistics are calculated correctly."""
        url = reverse('frontend:oem_manufacturer_management')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Dashboard stats should be present and valid
        stats = response.context['dashboard_stats']
        self.assertIn('total', stats)
        self.assertIn('active', stats)
        self.assertIn('certified', stats)
        self.assertIn('avg_quality', stats)
        self.assertIn('total_parts', stats)
        self.assertIn('active_rate', stats)
        
        # Stats should have valid values
        self.assertGreaterEqual(stats['total'], 0)
        self.assertGreaterEqual(stats['active'], 0)
        self.assertGreaterEqual(stats['certified'], 0)
        self.assertGreaterEqual(stats['avg_quality'], 0)
        self.assertLessEqual(stats['avg_quality'], 100)
        self.assertGreaterEqual(stats['total_parts'], 0)
        self.assertGreaterEqual(stats['active_rate'], 0)
        self.assertLessEqual(stats['active_rate'], 100)
    
    def test_oem_catalog_stats_calculation(self):
        """Test that catalog statistics are calculated correctly."""
        url = reverse('frontend:oem_part_catalog')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Catalog stats should be present and valid
        stats = response.context['catalog_stats']
        self.assertIn('total', stats)
        self.assertIn('in_stock', stats)
        self.assertIn('with_cross_refs', stats)
        self.assertIn('avg_compatibility', stats)
        self.assertIn('total_cross_refs', stats)
        self.assertIn('availability_rate', stats)
        
        # Stats should have valid values
        self.assertGreaterEqual(stats['total'], 0)
        self.assertGreaterEqual(stats['in_stock'], 0)
        self.assertGreaterEqual(stats['with_cross_refs'], 0)
        self.assertGreaterEqual(stats['avg_compatibility'], 0)
        self.assertLessEqual(stats['avg_compatibility'], 100)
        self.assertGreaterEqual(stats['total_cross_refs'], 0)
        self.assertGreaterEqual(stats['availability_rate'], 0)
        self.assertLessEqual(stats['availability_rate'], 100)