#!/usr/bin/env python
"""
Simple test script for client form functionality.
This script tests the basic client form validation and functionality.
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

class ClientFormSimpleTestCase(TestCase):
    """Simple test case for client form functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = Client()
    
    def test_client_form_basic_validation(self):
        """Test basic client form validation."""
        print("\n1. Testing Basic Client Form Validation...")
        
        # Test with minimal valid data
        valid_data = {
            'name': 'Juan Pérez',
            'email': 'juan@example.com',
            'phone': '5551234567',
        }
        
        form = ClientForm(data=valid_data)
        if not form.is_valid():
            print(f"   Form errors: {form.errors}")
        self.assertTrue(form.is_valid())
        print("   ✅ Basic valid form data accepted")
        
        # Test with missing required fields
        invalid_data = {
            'name': '',  # Required field empty
            'email': '',  # Required field empty
            'phone': '',  # Required field empty
        }
        
        form = ClientForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        print("   ✅ Form rejects empty required fields")
    
    def test_form_field_validation(self):
        """Test individual field validation."""
        print("\n2. Testing Individual Field Validation...")
        
        # Test name validation
        form_data = {
            'name': 'Valid Name',
            'email': 'valid@email.com',
            'phone': '1234567890',
        }
        
        form = ClientForm(data=form_data)
        self.assertTrue(form.is_valid())
        print("   ✅ Valid field data accepted")
        
        # Test invalid email
        form_data['email'] = 'invalid-email'
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        print("   ✅ Invalid email rejected")
    
    def test_search_form_basic(self):
        """Test basic search form functionality."""
        print("\n3. Testing Search Form...")
        
        # Test empty search form (should be valid)
        form = ClientSearchForm(data={})
        self.assertTrue(form.is_valid())
        print("   ✅ Empty search form is valid")
        
        # Test with search data
        search_data = {
            'search': 'test',
            'status': 'active',
            'sort': 'name',
            'order': 'asc'
        }
        
        form = ClientSearchForm(data=search_data)
        self.assertTrue(form.is_valid())
        print("   ✅ Search form with data is valid")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_client_create_view_basic(self, mock_api_client):
        """Test basic client creation view functionality."""
        print("\n4. Testing Client Create View...")
        
        # Mock API response
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        mock_api_instance.create_client.return_value = {'id': 1}
        
        # Login and test GET request
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Cliente')
        print("   ✅ Client create view loads successfully")
        
        # Test that form is in context
        self.assertIn('form', response.context)
        print("   ✅ Form is available in template context")
    
    @patch('frontend.views.ForgeAPIClient')
    def test_client_update_view_basic(self, mock_api_client):
        """Test basic client update view functionality."""
        print("\n5. Testing Client Update View...")
        
        # Mock API responses
        mock_api_instance = MagicMock()
        mock_api_client.return_value = mock_api_instance
        
        existing_client = {
            'id': 1,
            'name': 'Existing Client',
            'email': 'existing@client.com',
            'phone': '5559876543',
            'address': 'Existing Address',
            'credit_limit': 500.00,
            'credit_used': 100.00
        }
        
        mock_api_instance.get_client.return_value = existing_client
        
        # Login and test GET request
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('frontend:client_update', kwargs={'pk': 1}))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar Cliente')
        print("   ✅ Client update view loads successfully")
        
        # Test that client data is in context
        self.assertIn('client', response.context)
        self.assertEqual(response.context['client']['name'], 'Existing Client')
        print("   ✅ Client data is pre-loaded in context")
    
    def test_form_rendering(self):
        """Test that forms render correctly."""
        print("\n6. Testing Form Rendering...")
        
        # Test form field rendering
        form = ClientForm()
        
        # Check that required fields are present
        self.assertIn('name', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('phone', form.fields)
        self.assertIn('address', form.fields)
        self.assertIn('credit_limit', form.fields)
        print("   ✅ All expected form fields are present")
        
        # Check field properties
        self.assertTrue(form.fields['name'].required)
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['phone'].required)
        self.assertFalse(form.fields['address'].required)
        self.assertFalse(form.fields['credit_limit'].required)
        print("   ✅ Field requirements are correctly set")

def run_simple_form_tests():
    """Run simple form tests."""
    print("🔍 ForgeDB Client Form Simple Test Suite")
    print("Testing basic client form functionality...")
    print("=" * 60)
    
    # Create test suite
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=True)
    
    # Run specific test case
    failures = test_runner.run_tests(['__main__.ClientFormSimpleTestCase'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        print("\n🎯 TASK 6.2 BASIC VALIDATION COMPLETED!")
        print("\n📊 Client Form Features Validated:")
        print("   • Basic form validation and field requirements")
        print("   • Individual field validation (name, email, phone)")
        print("   • Search form functionality")
        print("   • Client create view rendering")
        print("   • Client update view with data pre-loading")
        print("   • Form field rendering and properties")
        print("\n🌟 The basic client forms functionality is working correctly!")
        return True

if __name__ == '__main__':
    success = run_simple_form_tests()
    sys.exit(0 if success else 1)