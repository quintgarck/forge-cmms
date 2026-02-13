#!/usr/bin/env python
"""
Simple test script for client list functionality.
This script tests the client list view template and basic functionality.
"""
import os
import sys
import django

# Setup Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock

class ClientListSimpleTestCase(TestCase):
    """Simple test case for client list functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = Client()
    
    @patch('frontend.views.ForgeAPIClient')
    def test_client_list_template_rendering(self, mock_api_client):
        """Test that the client list template renders correctly."""
        print("\n1. Testing Client List Template Rendering...")
        
        # Mock API response
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        mock_api_instance.get_clients.return_value = {
            'results': [
                {
                    'id': 1,
                    'name': 'Cliente Test',
                    'email': 'test@cliente.com',
                    'phone': '123456789',
                    'credit_limit': 1000.00,
                    'credit_used': 250.00
                }
            ],
            'count': 1,
            'next': None,
            'previous': None
        }
        
        # Login and test
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_list'))
        
        self.assertEqual(response.status_code, 200)
        print("   ✅ Template renders successfully")
        
        # Check content
        content = response.content.decode()
        self.assertIn('Gestión de Clientes', content)
        self.assertIn('search-filter-bar', content)
        self.assertIn('Cliente Test', content)
        print("   ✅ Client data displayed correctly")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_search_parameters(self, mock_api_client):
        """Test search parameters are passed correctly."""
        print("\n2. Testing Search Parameters...")
        
        # Mock API response
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        mock_api_instance.get_clients.return_value = {
            'results': [],
            'count': 0,
            'next': None,
            'previous': None
        }
        
        # Login and test search
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_list'), {
            'search': 'test query',
            'status': 'active',
            'sort': 'name',
            'order': 'desc'
        })
        
        self.assertEqual(response.status_code, 200)
        print("   ✅ Search parameters accepted")
        
        # Verify API was called with correct parameters
        mock_api_instance.get_clients.assert_called_once()
        call_args = mock_api_instance.get_clients.call_args
        self.assertIn('search', call_args[1])
        self.assertEqual(call_args[1]['search'], 'test query')
        print("   ✅ Search parameters passed to API correctly")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_pagination_logic(self, mock_api_client):
        """Test pagination logic."""
        print("\n3. Testing Pagination Logic...")
        
        # Mock API response with pagination
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        mock_api_instance.get_clients.return_value = {
            'results': [],
            'count': 100,  # Total items
            'next': 'http://example.com/api/clients/?page=2',
            'previous': None
        }
        
        # Login and test pagination
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_list'), {'page': '1'})
        
        self.assertEqual(response.status_code, 200)
        print("   ✅ Pagination page parameter accepted")
        
        # Check pagination context
        self.assertIn('pagination', response.context)
        pagination = response.context['pagination']
        self.assertEqual(pagination['count'], 100)
        self.assertEqual(pagination['current_page'], 1)
        self.assertEqual(pagination['total_pages'], 5)  # 100 items / 20 per page
        print("   ✅ Pagination context calculated correctly")
    
    def test_template_elements_present(self):
        """Test that all required template elements are present."""
        print("\n4. Testing Template Elements...")
        
        # Mock the API client to avoid network calls
        with patch('frontend.views.ForgeAPIClient') as mock_api_client:
            mock_api_instance = MagicMock()
            mock_api_client.return_value = mock_api_instance
            mock_api_instance.get_clients.return_value = {
                'results': [],
                'count': 0,
                'next': None,
                'previous': None
            }
            
            # Login and get response
            self.client.login(username='testuser', password='testpass123')
            response = self.client.get(reverse('frontend:client_list'))
            content = response.content.decode()
            
            # Check for essential elements
            essential_elements = [
                'search-filter-bar',
                'form-select',
                'search-input',
                'Nuevo Cliente',
                'confirmDelete',
                'changePageSize',
                'client-list.css'
            ]
            
            for element in essential_elements:
                self.assertIn(element, content)
                print(f"   ✅ {element} present")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_error_handling(self, mock_api_client):
        """Test error handling when API fails."""
        print("\n5. Testing Error Handling...")
        
        # Mock API to raise exception
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        from frontend.services.api_client import APIException
        mock_api_instance.get_clients.side_effect = APIException("API Error", 500)
        
        # Login and test
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_list'))
        
        self.assertEqual(response.status_code, 200)  # Should still render
        print("   ✅ Page renders even when API fails")
        
        # Check that empty state is shown
        content = response.content.decode()
        self.assertIn('No se encontraron clientes', content)
        print("   ✅ Empty state displayed correctly")
    
    def test_invalid_page_handling(self):
        """Test handling of invalid page numbers."""
        print("\n6. Testing Invalid Page Handling...")
        
        with patch('frontend.views.ForgeAPIClient') as mock_api_client:
            mock_api_instance = MagicMock()
            mock_api_client.return_value = mock_api_instance
            mock_api_instance.get_clients.return_value = {
                'results': [],
                'count': 0,
                'next': None,
                'previous': None
            }
            
            # Login and test invalid page
            self.client.login(username='testuser', password='testpass123')
            
            # Test invalid page number
            response = self.client.get(reverse('frontend:client_list'), {'page': 'invalid'})
            self.assertEqual(response.status_code, 200)
            print("   ✅ Invalid page number handled gracefully")
            
            # Test negative page number
            response = self.client.get(reverse('frontend:client_list'), {'page': '-1'})
            self.assertEqual(response.status_code, 200)
            print("   ✅ Negative page number handled gracefully")

def run_simple_tests():
    """Run simple tests."""
    print("🔍 ForgeDB Client List Simple Test Suite")
    print("Testing client list template and basic functionality...")
    print("=" * 60)
    
    # Create test suite
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
    
    # Run specific test case
    failures = test_runner.run_tests(['__main__.ClientListSimpleTestCase'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        print("\n🎯 TASK 6.1 VALIDATION COMPLETED!")
        print("\n📊 Client List Features Validated:")
        print("   • Template rendering with mock data")
        print("   • Search parameter handling")
        print("   • Pagination logic and calculations")
        print("   • Template elements presence")
        print("   • Error handling and fallbacks")
        print("   • Invalid input handling")
        print("\n🌟 The client list implementation is working correctly!")
        return True

if __name__ == '__main__':
    success = run_simple_tests()
    sys.exit(0 if success else 1)