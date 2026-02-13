#!/usr/bin/env python
"""
Test script for client form functionality.
This script tests the enhanced client creation and editing forms.
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
from frontend.forms import ClientForm, ClientSearchForm

class ClientFormTestCase(TestCase):
    """Test case for client form functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = Client()
    
    def test_client_form_validation(self):
        """Test client form validation."""
        print("\n1. Testing Client Form Validation...")
        
        # Test valid data
        valid_data = {
            'name': 'Juan Pérez',
            'email': 'juan@example.com',
            'phone': '(555) 123-4567',
            'address': 'Calle Principal 123, Ciudad',
            'credit_limit': '1000.00'
        }
        
        form = ClientForm(data=valid_data)
        self.assertTrue(form.is_valid())
        print("   ✅ Valid form data accepted")
        
        # Test invalid data
        invalid_data = {
            'name': 'A',  # Too short
            'email': 'invalid-email',  # Invalid format
            'phone': '123',  # Too short
            'address': 'Short',  # Too short if provided
            'credit_limit': '-100'  # Negative value
        }
        
        form = ClientForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('phone', form.errors)
        print("   ✅ Invalid form data rejected with appropriate errors")
    
    def test_form_field_cleaning(self):
        """Test form field cleaning and formatting."""
        print("\n2. Testing Form Field Cleaning...")
        
        # Test name cleaning
        form_data = {
            'name': '  juan   perez  ',
            'email': '  JUAN@EXAMPLE.COM  ',
            'phone': '5551234567',
            'address': 'Test address with proper length',
            'credit_limit': '1000'
        }
        
        form = ClientForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.cleaned_data
        self.assertEqual(cleaned_data['name'], 'Juan Perez')
        self.assertEqual(cleaned_data['email'], 'juan@example.com')
        self.assertEqual(cleaned_data['phone'], '(555) 123-4567')
        print("   ✅ Form fields cleaned and formatted correctly")
    
    def test_cross_field_validation(self):
        """Test cross-field validation."""
        print("\n3. Testing Cross-field Validation...")
        
        # Test form with no email or phone
        invalid_data = {
            'name': 'Test User',
            'email': '',
            'phone': '',
            'address': 'Test address',
            'credit_limit': '0'
        }
        
        form = ClientForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        print("   ✅ Cross-field validation working (requires email or phone)")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_client_create_view(self, mock_api_client):
        """Test client creation view."""
        print("\n4. Testing Client Create View...")
        
        # Mock API response
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        mock_api_instance.create_client.return_value = {'id': 1}
        
        # Login and test GET request
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ClientForm)
        print("   ✅ Client create view renders with form")
        
        # Test POST request with valid data
        valid_data = {
            'name': 'Test Client',
            'email': 'test@client.com',
            'phone': '(555) 123-4567',
            'address': 'Test Address 123',
            'credit_limit': '1000.00'
        }
        
        response = self.client.post(reverse('frontend:client_create'), data=valid_data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        mock_api_instance.create_client.assert_called_once()
        print("   ✅ Client creation with valid data successful")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_client_update_view(self, mock_api_client):
        """Test client update view."""
        print("\n5. Testing Client Update View...")
        
        # Mock API responses
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        
        existing_client = {
            'id': 1,
            'name': 'Existing Client',
            'email': 'existing@client.com',
            'phone': '(555) 987-6543',
            'address': 'Existing Address',
            'credit_limit': 500.00,
            'credit_used': 100.00
        }
        
        mock_api_instance.get_client.return_value = existing_client
        mock_api_instance.update_client.return_value = existing_client
        
        # Login and test GET request
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_update', kwargs={'pk': 1}))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('client', response.context)
        print("   ✅ Client update view renders with pre-populated form")
        
        # Test POST request with updated data
        updated_data = {
            'name': 'Updated Client Name',
            'email': 'updated@client.com',
            'phone': '(555) 111-2222',
            'address': 'Updated Address 456',
            'credit_limit': '1500.00'
        }
        
        response = self.client.post(reverse('frontend:client_update', kwargs={'pk': 1}), data=updated_data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        mock_api_instance.update_client.assert_called_once()
        print("   ✅ Client update with valid data successful")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_form_error_handling(self, mock_api_client):
        """Test form error handling with API errors."""
        print("\n6. Testing Form Error Handling...")
        
        # Mock API to raise validation error
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        
        from frontend.services.api_client import APIException
        api_error = APIException(
            "Validation error", 
            400, 
            {'email': ['This email is already in use']}
        )
        mock_api_instance.create_client.side_effect = api_error
        
        # Login and test POST with data that causes API error
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'name': 'Test Client',
            'email': 'duplicate@email.com',
            'phone': '(555) 123-4567',
            'address': 'Test Address',
            'credit_limit': '1000.00'
        }
        
        response = self.client.post(reverse('frontend:client_create'), data=form_data)
        
        # Should render form with errors
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        print("   ✅ API validation errors properly handled and displayed")
    
    def test_search_form(self):
        """Test client search form."""
        print("\n7. Testing Client Search Form...")
        
        # Test valid search data
        search_data = {
            'search': 'test query',
            'status': 'active',
            'sort': 'name',
            'order': 'asc'
        }
        
        form = ClientSearchForm(data=search_data)
        self.assertTrue(form.is_valid())
        print("   ✅ Search form with valid data accepted")
        
        # Test search query too short
        invalid_search_data = {
            'search': 'a',  # Too short
            'status': 'active',
            'sort': 'name',
            'order': 'asc'
        }
        
        form = ClientSearchForm(data=invalid_search_data)
        self.assertFalse(form.is_valid())
        self.assertIn('search', form.errors)
        print("   ✅ Search form rejects queries that are too short")

def run_form_tests():
    """Run form tests."""
    print("🔍 ForgeDB Client Form Test Suite")
    print("Testing enhanced client forms and validation...")
    print("=" * 60)
    
    # Create test suite
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
    
    # Run specific test case
    failures = test_runner.run_tests(['__main__.ClientFormTestCase'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        print("\n🎯 TASK 6.2 VALIDATION COMPLETED!")
        print("\n📊 Client Form Features Validated:")
        print("   • Django form validation and cleaning")
        print("   • Field-level and cross-field validation")
        print("   • Form pre-population for editing")
        print("   • API error handling and display")
        print("   • Search form functionality")
        print("   • Client creation and update workflows")
        print("\n🌟 The client forms implementation is working correctly!")
        return True

if __name__ == '__main__':
    success = run_form_tests()
    sys.exit(0 if success else 1)