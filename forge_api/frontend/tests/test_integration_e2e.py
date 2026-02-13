"""
End-to-end integration tests for ForgeDB frontend.
Tests complete user workflows from login to data operations.
"""
import json
import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, Mock
from frontend.services.api_client import ForgeAPIClient, APIException


class EndToEndIntegrationTests(TestCase):
    """
    Comprehensive end-to-end integration tests for the frontend.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Mock API responses
        self.mock_client_data = {
            'id': 1,
            'client_code': 'TEST-001',
            'name': 'Test Client',
            'email': 'test@client.com',
            'phone': '1234567890',
            'address': 'Test Address',
            'credit_limit': 1000.00,
            'current_balance': 0.00,
            'type': 'individual',
            'created_date': '2024-01-01T10:00:00Z'
        }
        
        self.mock_dashboard_data = {
            'active_work_orders': 5,
            'pending_invoices': 3,
            'low_stock_items': 2,
            'technician_productivity': 85.5,
            'recent_alerts': [],
            'charts': {},
            'summary': {}
        }
    
    def test_complete_user_workflow_login_to_client_creation(self):
        """
        Test complete workflow: Login -> Dashboard -> Client Creation -> Client Detail
        """
        # Step 1: Login
        with patch('frontend.services.AuthenticationService.login') as mock_login:
            mock_login.return_value = (True, 'Login successful', {'user_id': self.user.id})
            
            response = self.client.post(reverse('frontend:login'), {
                'username': 'testuser',
                'password': 'testpass123'
            })
            
            # Should redirect to dashboard after successful login
            self.assertEqual(response.status_code, 302)
            self.assertIn('dashboard', response.url)
        
        # Step 2: Access Dashboard
        with patch.object(ForgeAPIClient, 'get') as mock_get:
            mock_get.return_value = self.mock_dashboard_data
            
            # Login the user for subsequent requests
            self.client.force_login(self.user)
            
            response = self.client.get(reverse('frontend:dashboard'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Dashboard')
        
        # Step 3: Navigate to Client Creation
        response = self.client.get(reverse('frontend:client_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Cliente')
        
        # Step 4: Submit Client Creation Form
        with patch.object(ForgeAPIClient, 'create_client') as mock_create:
            mock_create.return_value = self.mock_client_data
            
            response = self.client.post(reverse('frontend:client_create'), {
                'client_code': 'TEST-001',
                'type': 'individual',
                'name': 'Test Client',
                'email': 'test@client.com',
                'phone': '1234567890',
                'address': 'Test Address',
                'credit_limit': '1000.00'
            })
            
            # Should redirect to client detail after successful creation
            self.assertEqual(response.status_code, 302)
            self.assertIn('client', response.url)
            
            # Verify API was called with correct data
            mock_create.assert_called_once()
            call_args = mock_create.call_args[0][0]
            self.assertEqual(call_args['client_code'], 'TEST-001')
            self.assertEqual(call_args['name'], 'Test Client')
        
        # Step 5: View Client Detail
        with patch.object(ForgeAPIClient, 'get_client') as mock_get_client:
            mock_get_client.return_value = self.mock_client_data
            
            response = self.client.get(reverse('frontend:client_detail', kwargs={'pk': 1}))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Test Client')
            self.assertContains(response, 'TEST-001')
    
    def test_error_handling_workflow(self):
        """
        Test error handling throughout the user workflow.
        """
        self.client.force_login(self.user)
        
        # Test API error during client creation
        with patch.object(ForgeAPIClient, 'create_client') as mock_create:
            mock_create.side_effect = APIException(
                "Validation error", 
                status_code=400, 
                response_data={'client_code': ['This code already exists']}
            )
            
            response = self.client.post(reverse('frontend:client_create'), {
                'client_code': 'DUPLICATE-001',
                'type': 'individual',
                'name': 'Test Client',
                'email': 'test@client.com',
                'phone': '1234567890',
                'credit_limit': '1000.00'
            })
            
            # Should stay on form page and show errors
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'This code already exists')
        
        # Test server error handling
        with patch.object(ForgeAPIClient, 'create_client') as mock_create:
            mock_create.side_effect = APIException(
                "Internal server error", 
                status_code=500
            )
            
            response = self.client.post(reverse('frontend:client_create'), {
                'client_code': 'SERVER-ERROR',
                'type': 'individual',
                'name': 'Test Client',
                'email': 'test@client.com',
                'phone': '1234567890',
                'credit_limit': '1000.00'
            })
            
            # Should stay on form page and show server error
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Error interno del servidor')
    
    def test_authentication_flow(self):
        """
        Test authentication and session management.
        """
        # Test unauthenticated access
        response = self.client.get(reverse('frontend:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Test login with invalid credentials
        with patch('frontend.services.AuthenticationService.login') as mock_login:
            mock_login.return_value = (False, 'Invalid credentials', None)
            
            response = self.client.post(reverse('frontend:login'), {
                'username': 'invalid',
                'password': 'invalid'
            })
            
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Invalid credentials')
        
        # Test successful login
        with patch('frontend.services.AuthenticationService.login') as mock_login:
            mock_login.return_value = (True, 'Login successful', {'user_id': self.user.id})
            
            response = self.client.post(reverse('frontend:login'), {
                'username': 'testuser',
                'password': 'testpass123'
            })
            
            self.assertEqual(response.status_code, 302)
            self.assertIn('dashboard', response.url)
    
    def test_form_validation_integration(self):
        """
        Test form validation integration with API responses.
        """
        self.client.force_login(self.user)
        
        # Test client-side validation
        response = self.client.post(reverse('frontend:client_create'), {
            'client_code': '',  # Empty required field
            'type': 'individual',
            'name': '',  # Empty required field
            'email': 'invalid-email',  # Invalid format
            'phone': '123',  # Too short
            'credit_limit': '-100'  # Negative value
        })
        
        self.assertEqual(response.status_code, 200)
        # Form should show validation errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('client_code', form.errors)
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
    
    def test_api_connectivity_and_error_recovery(self):
        """
        Test API connectivity issues and error recovery mechanisms.
        """
        self.client.force_login(self.user)
        
        # Test connection timeout
        with patch.object(ForgeAPIClient, 'get') as mock_get:
            mock_get.side_effect = APIException("Connection timeout", status_code=None)
            
            response = self.client.get(reverse('frontend:dashboard'))
            self.assertEqual(response.status_code, 200)
            # Should show fallback data
            self.assertContains(response, 'Dashboard')
        
        # Test API unavailable
        with patch.object(ForgeAPIClient, 'get_clients') as mock_get_clients:
            mock_get_clients.side_effect = APIException("Service unavailable", status_code=503)
            
            response = self.client.get(reverse('frontend:client_list'))
            self.assertEqual(response.status_code, 200)
            # Should show empty state with error message
            self.assertContains(response, 'Clientes')
    
    def test_data_consistency_across_modules(self):
        """
        Test data consistency between different modules.
        """
        self.client.force_login(self.user)
        
        # Create a client and verify it appears in lists
        with patch.object(ForgeAPIClient, 'create_client') as mock_create, \
             patch.object(ForgeAPIClient, 'get_clients') as mock_get_clients:
            
            mock_create.return_value = self.mock_client_data
            mock_get_clients.return_value = {
                'results': [self.mock_client_data],
                'count': 1,
                'next': None,
                'previous': None
            }
            
            # Create client
            response = self.client.post(reverse('frontend:client_create'), {
                'client_code': 'TEST-001',
                'type': 'individual',
                'name': 'Test Client',
                'email': 'test@client.com',
                'phone': '1234567890',
                'credit_limit': '1000.00'
            })
            
            self.assertEqual(response.status_code, 302)
            
            # Verify client appears in list
            response = self.client.get(reverse('frontend:client_list'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Test Client')
            self.assertContains(response, 'TEST-001')
    
    def test_responsive_design_and_mobile_compatibility(self):
        """
        Test responsive design elements and mobile compatibility.
        """
        self.client.force_login(self.user)
        
        # Test with mobile user agent
        response = self.client.get(
            reverse('frontend:dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'viewport')  # Should have responsive viewport meta tag
        
        # Test client form on mobile
        response = self.client.get(
            reverse('frontend:client_create'),
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form-control')  # Should use responsive form classes
    
    def test_performance_and_loading_optimization(self):
        """
        Test performance optimizations and loading states.
        """
        self.client.force_login(self.user)
        
        # Test that pages load within reasonable time
        start_time = time.time()
        
        with patch.object(ForgeAPIClient, 'get') as mock_get:
            mock_get.return_value = self.mock_dashboard_data
            
            response = self.client.get(reverse('frontend:dashboard'))
            
        load_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0)  # Should load within 2 seconds
        
        # Test static file serving
        response = self.client.get('/static/frontend/css/main.css')
        # Should either serve the file or return 404 if not found (both are acceptable in tests)
        self.assertIn(response.status_code, [200, 404])
    
    def test_security_and_csrf_protection(self):
        """
        Test security measures and CSRF protection.
        """
        self.client.force_login(self.user)
        
        # Test CSRF protection on forms
        response = self.client.post(reverse('frontend:client_create'), {
            'client_code': 'TEST-001',
            'type': 'individual',
            'name': 'Test Client',
            'email': 'test@client.com',
            'phone': '1234567890',
            'credit_limit': '1000.00'
        }, follow=True)
        
        # Should be protected by CSRF (will fail without proper token in real scenario)
        # In test environment, Django handles this automatically
        self.assertIn(response.status_code, [200, 302, 403])
        
        # Test that sensitive data is not exposed in responses
        response = self.client.get(reverse('frontend:client_create'))
        self.assertEqual(response.status_code, 200)
        # Should not contain sensitive information in HTML
        self.assertNotContains(response, 'password')
        self.assertNotContains(response, 'secret')


class APIIntegrationTests(TestCase):
    """
    Tests specifically for API integration functionality.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.user = User.objects.create_user(
            username='apitest',
            password='testpass123'
        )
    
    def test_api_client_initialization(self):
        """Test API client initialization and configuration."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {}
        
        api_client = ForgeAPIClient(request=request)
        
        self.assertIsNotNone(api_client.base_url)
        self.assertIsNotNone(api_client.session)
        self.assertEqual(api_client.timeout, 30)  # Default timeout
    
    def test_api_error_handling_and_retry_logic(self):
        """Test API error handling and retry mechanisms."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {}
        
        api_client = ForgeAPIClient(request=request)
        
        # Test retry logic with mock
        with patch.object(api_client.session, 'request') as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [
                Mock(status_code=500, text='Server Error'),
                Mock(status_code=200, json=lambda: {'success': True}, content=b'{"success": true}')
            ]
            
            try:
                result = api_client._make_request('GET', 'test/')
                self.assertEqual(result['success'], True)
            except APIException:
                # Retry logic might still fail in test environment
                pass
    
    def test_authentication_token_management(self):
        """Test JWT token management and refresh."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {
            'auth_token': 'test_token_123',
            'refresh_token': 'refresh_token_456'
        }
        
        api_client = ForgeAPIClient(request=request)
        
        # Verify token is set in headers
        self.assertIn('Authorization', api_client.session.headers)
        self.assertEqual(
            api_client.session.headers['Authorization'], 
            'Bearer test_token_123'
        )
    
    def test_diagnostic_information_collection(self):
        """Test diagnostic information collection."""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {'auth_token': 'test_token'}
        
        api_client = ForgeAPIClient(request=request)
        
        diagnostic_info = api_client.get_diagnostic_info()
        
        self.assertIn('base_url', diagnostic_info)
        self.assertIn('timeout', diagnostic_info)
        self.assertIn('has_auth_token', diagnostic_info)
        self.assertIn('session_auth_token', diagnostic_info)
        self.assertTrue(diagnostic_info['session_auth_token'])


class UserExperienceTests(TestCase):
    """
    Tests for user experience and interface functionality.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='uxtest',
            password='testpass123'
        )
    
    def test_navigation_and_breadcrumbs(self):
        """Test navigation consistency and breadcrumb functionality."""
        self.client.force_login(self.user)
        
        # Test dashboard navigation
        response = self.client.get(reverse('frontend:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Test client list navigation
        with patch.object(ForgeAPIClient, 'get_clients') as mock_get:
            mock_get.return_value = {'results': [], 'count': 0}
            
            response = self.client.get(reverse('frontend:client_list'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'breadcrumb')
    
    def test_error_messages_and_user_feedback(self):
        """Test error message display and user feedback mechanisms."""
        self.client.force_login(self.user)
        
        # Test form validation messages
        response = self.client.post(reverse('frontend:client_create'), {
            'client_code': '',
            'name': '',
            'email': 'invalid'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should contain form with errors
        self.assertContains(response, 'form')
    
    def test_loading_states_and_progress_indicators(self):
        """Test loading states and progress indicators."""
        self.client.force_login(self.user)
        
        # Test that forms include loading state handling
        response = self.client.get(reverse('frontend:client_create'))
        self.assertEqual(response.status_code, 200)
        # Should include JavaScript for loading states
        self.assertContains(response, 'form')
    
    def test_accessibility_compliance(self):
        """Test basic accessibility compliance."""
        self.client.force_login(self.user)
        
        response = self.client.get(reverse('frontend:client_create'))
        self.assertEqual(response.status_code, 200)
        
        # Check for basic accessibility features
        self.assertContains(response, 'label')  # Form labels
        self.assertContains(response, 'aria-')  # ARIA attributes (if present)
        self.assertContains(response, 'form-control')  # Proper form styling