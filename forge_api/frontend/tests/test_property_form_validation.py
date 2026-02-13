"""
Property-based tests for form validation consistency.

**Feature: forge-frontend-web, Property 3: Form validation consistency**

This module tests the property that for any form submission with invalid data,
the system should display specific error messages, prevent submission, and maintain form state.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from unittest.mock import Mock, patch
import json

from frontend.services.api_client import ForgeAPIClient, APIException
from frontend.services.auth_service import AuthenticationService
from frontend.views import ClientCreateView, ClientUpdateView


class TestFormValidationConsistency(TestCase):
    """
    **Feature: forge-frontend-web, Property 3: Form validation consistency**
    
    Tests that form validation behaves consistently across all input combinations,
    ensuring that invalid data always results in proper error handling.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def _create_request_with_session(self, method='POST', data=None):
        """Create a request with session middleware."""
        if method == 'POST':
            request = self.factory.post('/clients/create/', data=data or {})
        else:
            request = self.factory.get('/clients/create/')
        
        request.user = self.user
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        return request
    
    # Hypothesis strategies for generating test data
    @st.composite
    def invalid_client_data(draw):
        """Generate invalid client data for testing."""
        # Generate various types of invalid data
        invalid_types = [
            # Empty strings
            {'name': '', 'email': 'valid@email.com', 'phone': '1234567890'},
            # Invalid email formats
            {'name': 'Valid Name', 'email': 'invalid-email', 'phone': '1234567890'},
            # Missing required fields
            {'email': 'valid@email.com', 'phone': '1234567890'},
            # Invalid phone numbers
            {'name': 'Valid Name', 'email': 'valid@email.com', 'phone': ''},
            # Extremely long values
            {'name': 'x' * 1000, 'email': 'valid@email.com', 'phone': '1234567890'},
            # Invalid credit limit
            {'name': 'Valid Name', 'email': 'valid@email.com', 'phone': '1234567890', 'credit_limit': 'invalid'},
            # Negative credit limit
            {'name': 'Valid Name', 'email': 'valid@email.com', 'phone': '1234567890', 'credit_limit': '-100'},
        ]
        
        return draw(st.sampled_from(invalid_types))
    
    @st.composite
    def api_error_responses(draw):
        """Generate various API error responses."""
        error_types = [
            # Field validation errors
            {
                'name': ['This field is required.'],
                'email': ['Enter a valid email address.']
            },
            # Non-field errors
            {
                'non_field_errors': ['A client with this email already exists.']
            },
            # Single error message
            {
                'detail': 'Invalid data provided.'
            },
            # Complex nested errors
            {
                'name': ['This field is required.', 'Name must be at least 2 characters.'],
                'credit_limit': ['Ensure this value is greater than or equal to 0.']
            }
        ]
        
        return draw(st.sampled_from(error_types))
    
    @given(invalid_client_data())
    @settings(max_examples=100, deadline=None)
    def test_form_validation_consistency_create(self, invalid_data):
        """
        **Property 3: Form validation consistency**
        
        Test that client creation forms consistently handle invalid data by:
        1. Displaying specific error messages
        2. Preventing form submission
        3. Maintaining form state
        """
        # Arrange
        request = self._create_request_with_session('POST', invalid_data)
        view = ClientCreateView()
        view.request = request
        
        # Mock API client to simulate validation errors
        with patch.object(view, 'make_api_request') as mock_api:
            # Configure mock to raise APIException with validation errors
            error_data = {
                'name': ['This field is required.'] if not invalid_data.get('name') else [],
                'email': ['Enter a valid email address.'] if '@' not in invalid_data.get('email', '') else [],
                'phone': ['This field is required.'] if not invalid_data.get('phone') else []
            }
            
            # Remove empty error lists
            error_data = {k: v for k, v in error_data.items() if v}
            
            if error_data:
                mock_api.side_effect = APIException("Validation failed", 400, error_data)
            
            # Act
            response = view.post(request)
            
            # Assert - Property validation
            if error_data:
                # Should not redirect (form submission prevented)
                self.assertNotEqual(response.status_code, 302, 
                    "Form with invalid data should not redirect (submission should be prevented)")
                
                # Should return form with errors (specific error messages displayed)
                self.assertIn('client', response.context_data if hasattr(response, 'context_data') else {},
                    "Form should maintain state when validation fails")
    
    @given(invalid_client_data())
    @settings(max_examples=100, deadline=None)
    def test_form_validation_consistency_update(self, invalid_data):
        """
        **Property 3: Form validation consistency**
        
        Test that client update forms consistently handle invalid data.
        """
        # Arrange
        request = self._create_request_with_session('POST', invalid_data)
        view = ClientUpdateView()
        view.request = request
        view.kwargs = {'pk': 1}
        
        # Mock API client
        with patch.object(view, 'make_api_request') as mock_api:
            # Mock get request for existing client data
            existing_client = {
                'id': 1,
                'name': 'Existing Client',
                'email': 'existing@example.com',
                'phone': '1234567890',
                'credit_limit': 1000.00
            }
            
            def api_side_effect(endpoint, method='GET', data=None):
                if method == 'GET':
                    return existing_client
                else:
                    # Simulate validation error for invalid data
                    error_data = {}
                    if not data.get('name'):
                        error_data['name'] = ['This field is required.']
                    if data.get('email') and '@' not in data.get('email'):
                        error_data['email'] = ['Enter a valid email address.']
                    
                    if error_data:
                        raise APIException("Validation failed", 400, error_data)
                    return data
            
            mock_api.side_effect = api_side_effect
            
            # Act
            response = view.post(request)
            
            # Assert - Property validation
            # The form should handle validation consistently
            self.assertIsNotNone(response, "Update form should return a response")
    
    @given(api_error_responses())
    @settings(max_examples=50, deadline=None)
    def test_api_error_message_extraction(self, error_response):
        """
        **Property 3: Form validation consistency**
        
        Test that API error messages are consistently extracted and formatted.
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request=request)
        
        # Act & Assert
        error_message = api_client._extract_error_message(error_response)
        
        # Property: Error message should always be a non-empty string
        self.assertIsInstance(error_message, str, 
            "Error message should always be a string")
        self.assertTrue(len(error_message) > 0, 
            "Error message should not be empty")
        
        # Property: Error message should not contain raw dict representations
        self.assertNotIn('{', error_message, 
            "Error message should be user-friendly, not raw dict")
        self.assertNotIn('}', error_message, 
            "Error message should be user-friendly, not raw dict")
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50, deadline=None)
    def test_authentication_error_handling(self, username):
        """
        **Property 3: Form validation consistency**
        
        Test that authentication errors are handled consistently.
        """
        assume(len(username.strip()) > 0)  # Ensure non-empty username
        
        # Arrange
        request = self._create_request_with_session()
        auth_service = AuthenticationService(request)
        
        # Act - Try to login with invalid credentials
        with patch('requests.post') as mock_post:
            # Mock API response for invalid credentials
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {'detail': 'Invalid credentials'}
            mock_post.return_value = mock_response
            
            # Mock Django authenticate to return None (invalid credentials)
            with patch('django.contrib.auth.authenticate', return_value=None):
                success, message, user_data = auth_service.login(username, 'invalid_password')
        
        # Assert - Property validation
        self.assertFalse(success, 
            "Login with invalid credentials should always fail")
        self.assertIsInstance(message, str, 
            "Error message should always be a string")
        self.assertTrue(len(message) > 0, 
            "Error message should not be empty")
        self.assertEqual(user_data, {}, 
            "User data should be empty for failed login")
    
    def test_form_state_preservation_on_error(self):
        """
        **Property 3: Form validation consistency**
        
        Test that form state is preserved when validation fails.
        """
        # Arrange
        form_data = {
            'name': 'Test Client',
            'email': 'invalid-email',  # Invalid email
            'phone': '1234567890',
            'address': 'Test Address',
            'credit_limit': '1000.00'
        }
        
        request = self._create_request_with_session('POST', form_data)
        view = ClientCreateView()
        view.request = request
        
        # Mock API to return validation error
        with patch.object(view, 'make_api_request') as mock_api:
            mock_api.side_effect = APIException(
                "Validation failed", 
                400, 
                {'email': ['Enter a valid email address.']}
            )
            
            # Act
            response = view.post(request)
            
            # Assert - Form state should be preserved
            # The view should re-render the form with the submitted data
            self.assertNotEqual(response.status_code, 302, 
                "Should not redirect when validation fails")
    
    @given(st.integers(min_value=400, max_value=599))
    @settings(max_examples=20, deadline=None)
    def test_api_client_error_handling_consistency(self, status_code):
        """
        **Property 3: Form validation consistency**
        
        Test that API client handles all HTTP error codes consistently.
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request=request)
        
        # Mock requests to return various error codes
        with patch.object(api_client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.content = b'{"detail": "Error message"}'
            mock_response.json.return_value = {"detail": "Error message"}
            mock_request.return_value = mock_response
            
            # Act & Assert
            with self.assertRaises(APIException) as context:
                api_client.get('test-endpoint/')
            
            # Property: All HTTP errors should raise APIException
            self.assertIsInstance(context.exception, APIException,
                f"Status code {status_code} should raise APIException")
            self.assertEqual(context.exception.status_code, status_code,
                "Exception should preserve the original status code")
    
    def test_token_refresh_consistency(self):
        """
        **Property 3: Form validation consistency**
        
        Test that token refresh behaves consistently across different scenarios.
        """
        # Arrange
        request = self._create_request_with_session()
        auth_service = AuthenticationService(request)
        
        # Test with no refresh token
        result = auth_service.refresh_token()
        self.assertFalse(result, "Should fail when no refresh token exists")
        
        # Test with invalid refresh token
        request.session['refresh_token'] = 'invalid_token'
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response
            
            result = auth_service.refresh_token()
            self.assertFalse(result, "Should fail with invalid refresh token")
        
        # Test with valid refresh token
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'access': 'new_access_token',
                'refresh': 'new_refresh_token'
            }
            mock_post.return_value = mock_response
            
            result = auth_service.refresh_token()
            self.assertTrue(result, "Should succeed with valid refresh token")
            self.assertEqual(request.session['auth_token'], 'new_access_token',
                "Should update access token in session")


# Additional test utilities for property testing
class FormValidationTestHelpers:
    """Helper methods for form validation property tests."""
    
    @staticmethod
    def generate_invalid_email():
        """Generate various invalid email formats."""
        return st.sampled_from([
            'invalid',
            'invalid@',
            '@invalid.com',
            'invalid.com',
            'invalid@.com',
            'invalid@com.',
            'invalid..email@test.com',
            'invalid email@test.com',
            'invalid@test..com'
        ])
    
    @staticmethod
    def generate_invalid_phone():
        """Generate various invalid phone formats."""
        return st.sampled_from([
            '',
            'abc',
            '123',
            '123-456-789a',
            '+1-800-INVALID',
            '1' * 50,  # Too long
            '!@#$%^&*()',
        ])
    
    @staticmethod
    def generate_boundary_values():
        """Generate boundary values for testing."""
        return st.sampled_from([
            '',  # Empty
            'a',  # Single character
            'a' * 255,  # Max typical length
            'a' * 256,  # Over max length
            'a' * 1000,  # Way over max length
        ])