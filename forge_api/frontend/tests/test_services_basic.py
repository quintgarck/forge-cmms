"""
Basic tests for frontend services.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from unittest.mock import Mock, patch

from frontend.services.api_client import ForgeAPIClient, APIException
from frontend.services.auth_service import AuthenticationService


class TestAPIClientBasic(TestCase):
    """Basic tests for API client functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def _create_request_with_session(self):
        """Create a request with session middleware."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        return request
    
    def test_api_client_initialization(self):
        """Test that API client can be initialized."""
        request = self._create_request_with_session()
        client = ForgeAPIClient(request=request)
        
        self.assertIsNotNone(client)
        self.assertIsNotNone(client.base_url)
        self.assertIsNotNone(client.session)
    
    def test_api_client_error_message_extraction(self):
        """Test error message extraction from API responses."""
        request = self._create_request_with_session()
        client = ForgeAPIClient(request=request)
        
        # Test simple error message
        error_data = {'detail': 'Test error message'}
        message = client._extract_error_message(error_data)
        self.assertEqual(message, 'Test error message')
        
        # Test field errors
        error_data = {'name': ['This field is required.']}
        message = client._extract_error_message(error_data)
        self.assertIn('name', message)
        self.assertIn('This field is required', message)


class TestAuthenticationServiceBasic(TestCase):
    """Basic tests for authentication service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def _create_request_with_session(self):
        """Create a request with session middleware."""
        request = self.factory.get('/')
        request.user = self.user
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        return request
    
    def test_auth_service_initialization(self):
        """Test that authentication service can be initialized."""
        request = self._create_request_with_session()
        auth_service = AuthenticationService(request)
        
        self.assertIsNotNone(auth_service)
        self.assertEqual(auth_service.request, request)
    
    def test_get_user_data_unauthenticated(self):
        """Test getting user data when not authenticated."""
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        auth_service = AuthenticationService(request)
        user_data = auth_service.get_user_data()
        
        self.assertIsNone(user_data)
    
    def test_session_info(self):
        """Test getting session information."""
        request = self._create_request_with_session()
        auth_service = AuthenticationService(request)
        
        session_info = auth_service.get_session_info()
        
        self.assertIsInstance(session_info, dict)
        self.assertIn('is_authenticated', session_info)
        self.assertIn('has_jwt_token', session_info)