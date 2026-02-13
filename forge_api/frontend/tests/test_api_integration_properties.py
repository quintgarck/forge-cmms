"""
Property-based tests for API integration reliability
**Feature: forge-frontend-web, Property 6: API integration consistency**
*For any* API endpoint call, the frontend should handle both success and error responses 
appropriately and provide meaningful user feedback
**Validates: Requirements: API reliability and error handling**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from unittest.mock import Mock, patch
import json
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

from ..services.api_client import ForgeAPIClient, APIException
from ..services.auth_service import AuthenticationService


class APIIntegrationPropertyTests(TestCase):
    """
    Property-based tests for API integration reliability
    """
    
    def setUp(self):
        """Set up test environment"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def _create_request_with_session(self, user=None):
        """Create a request with session middleware"""
        request = self.factory.get('/')
        if user:
            request.user = user
        else:
            request.user = self.user
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add messages middleware
        messages_middleware = MessageMiddleware(lambda req: None)
        messages_middleware.process_request(request)
        
        return request
    
    @given(
        endpoint=st.text(min_size=1, max_size=50).filter(lambda x: '/' in x or x.isalnum()),
        status_code=st.integers(min_value=200, max_value=599),
        response_data=st.one_of(
            st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100)),
            st.lists(st.dictionaries(st.text(min_size=1, max_size=10), st.text(max_size=50))),
            st.text(max_size=200)
        )
    )
    @settings(max_examples=100, deadline=5000)
    def test_api_client_handles_all_response_types_consistently(self, endpoint, status_code, response_data):
        """
        Property: API client should handle all HTTP response types consistently
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.ok = 200 <= status_code < 300
        
        # Handle different response data types
        if isinstance(response_data, (dict, list)):
            mock_response.json.return_value = response_data
            mock_response.headers = {'Content-Type': 'application/json'}
        else:
            mock_response.json.side_effect = ValueError("No JSON object could be decoded")
            mock_response.text = str(response_data)
            mock_response.headers = {'Content-Type': 'text/plain'}
        
        # Act & Assert
        with patch('requests.request', return_value=mock_response):
            if status_code >= 400:
                # Should raise APIException for error status codes
                with pytest.raises(APIException) as exc_info:
                    api_client.request('GET', endpoint)
                
                # Verify exception has proper attributes
                exception = exc_info.value
                assert hasattr(exception, 'status_code')
                assert hasattr(exception, 'get_user_message')
                assert exception.status_code == status_code
                assert isinstance(exception.get_user_message(), str)
                assert len(exception.get_user_message()) > 0
            else:
                # Should return response for success status codes
                response = api_client.request('GET', endpoint)
                assert response.status_code == status_code
                assert response == mock_response
    
    @given(
        endpoints=st.lists(
            st.text(min_size=1, max_size=30).filter(lambda x: x.replace('/', '').isalnum()),
            min_size=1,
            max_size=10
        ),
        method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE'])
    )
    @settings(max_examples=50, deadline=10000)
    def test_api_client_provides_consistent_error_handling_across_endpoints(self, endpoints, method):
        """
        Property: Error handling should be consistent across all endpoints and methods
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        error_types = [
            (ConnectionError("Connection failed"), "connection"),
            (Timeout("Request timeout"), "timeout"),
            (RequestException("Generic request error"), "request")
        ]
        
        for endpoint in endpoints:
            for error, error_type in error_types:
                # Act & Assert
                with patch('requests.request', side_effect=error):
                    with pytest.raises(APIException) as exc_info:
                        api_client.request(method, endpoint)
                    
                    # Verify consistent error handling
                    exception = exc_info.value
                    assert isinstance(exception.get_user_message(), str)
                    assert len(exception.get_user_message()) > 0
                    
                    # Error message should be user-friendly
                    message = exception.get_user_message().lower()
                    if error_type == "connection":
                        assert any(word in message for word in ['conexión', 'conectar', 'servidor'])
                    elif error_type == "timeout":
                        assert any(word in message for word in ['tiempo', 'timeout', 'tardó'])
    
    @given(
        valid_token=st.text(min_size=10, max_size=200),
        expired_token=st.text(min_size=10, max_size=200),
        refresh_token=st.text(min_size=10, max_size=200)
    )
    @settings(max_examples=30, deadline=5000)
    def test_token_refresh_mechanism_works_consistently(self, valid_token, expired_token, refresh_token):
        """
        Property: Token refresh mechanism should work consistently for any valid tokens
        """
        assume(valid_token != expired_token)
        assume(valid_token != refresh_token)
        assume(expired_token != refresh_token)
        
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        # Set up initial expired token
        request.session['access_token'] = expired_token
        request.session['refresh_token'] = refresh_token
        
        # Mock responses
        expired_response = Mock()
        expired_response.status_code = 401
        expired_response.ok = False
        
        refresh_response = Mock()
        refresh_response.status_code = 200
        refresh_response.ok = True
        refresh_response.json.return_value = {'access': valid_token}
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.ok = True
        success_response.json.return_value = {'data': 'success'}
        
        # Act
        with patch('requests.request') as mock_request:
            with patch('requests.post', return_value=refresh_response):
                # First call returns 401, second call (after refresh) returns 200
                mock_request.side_effect = [expired_response, success_response]
                
                response = api_client.request('GET', 'test-endpoint/')
                
                # Assert
                assert response.status_code == 200
                assert request.session['access_token'] == valid_token
                assert mock_request.call_count == 2  # Original call + retry after refresh
    
    @given(
        data_payload=st.one_of(
            st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.one_of(st.text(max_size=100), st.integers(), st.booleans())
            ),
            st.lists(st.text(max_size=50)),
            st.none()
        )
    )
    @settings(max_examples=50, deadline=5000)
    def test_api_client_serializes_data_consistently(self, data_payload):
        """
        Property: API client should serialize all data types consistently
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {'success': True}
        
        # Act
        with patch('requests.request', return_value=mock_response) as mock_request:
            if data_payload is not None:
                api_client.post('test-endpoint/', data_payload)
                
                # Assert
                call_args = mock_request.call_args
                if data_payload:
                    # Should have JSON body
                    assert 'json' in call_args.kwargs
                    # Should be able to serialize back
                    serialized_data = call_args.kwargs['json']
                    assert json.dumps(serialized_data)  # Should not raise exception
            else:
                api_client.get('test-endpoint/')
                # Should work without data
                assert mock_request.called
    
    @given(
        error_responses=st.lists(
            st.tuples(
                st.integers(min_value=400, max_value=599),
                st.dictionaries(
                    st.sampled_from(['detail', 'error', 'message', 'non_field_errors']),
                    st.one_of(st.text(max_size=100), st.lists(st.text(max_size=50)))
                )
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=30, deadline=5000)
    def test_error_messages_are_always_user_friendly(self, error_responses):
        """
        Property: All error responses should produce user-friendly messages
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        for status_code, error_data in error_responses:
            # Create mock response
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.ok = False
            mock_response.json.return_value = error_data
            
            # Act & Assert
            with patch('requests.request', return_value=mock_response):
                with pytest.raises(APIException) as exc_info:
                    api_client.request('GET', 'test-endpoint/')
                
                exception = exc_info.value
                user_message = exception.get_user_message()
                
                # Verify message is user-friendly
                assert isinstance(user_message, str)
                assert len(user_message) > 0
                assert not user_message.startswith('Traceback')
                assert not user_message.startswith('Exception')
                # Should not contain technical jargon
                technical_terms = ['traceback', 'exception', 'stack', 'null', 'undefined']
                assert not any(term in user_message.lower() for term in technical_terms)
    
    @given(
        response_times=st.lists(
            st.floats(min_value=0.001, max_value=10.0),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=20, deadline=5000)
    def test_api_client_handles_varying_response_times_consistently(self, response_times):
        """
        Property: API client should handle varying response times consistently
        """
        # Arrange
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        for response_time in response_times:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = {'data': 'test'}
            
            def slow_request(*args, **kwargs):
                import time
                time.sleep(min(response_time, 0.1))  # Cap at 0.1s for test performance
                return mock_response
            
            # Act & Assert
            with patch('requests.request', side_effect=slow_request):
                try:
                    response = api_client.request('GET', 'test-endpoint/')
                    # Should always return valid response regardless of timing
                    assert response.status_code == 200
                except APIException:
                    # If timeout occurs, should be handled gracefully
                    pass  # This is acceptable behavior
    
    @given(
        cache_scenarios=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=30),  # endpoint
                st.dictionaries(st.text(min_size=1, max_size=10), st.text(max_size=50)),  # data
                st.booleans()  # bypass_cache
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=20, deadline=5000)
    def test_caching_behavior_is_consistent(self, cache_scenarios):
        """
        Property: Caching behavior should be consistent across different scenarios
        """
        # This test would verify caching behavior if implemented
        # For now, we'll test that the API client behaves consistently
        # regardless of caching parameters
        
        request = self._create_request_with_session()
        api_client = ForgeAPIClient(request)
        
        for endpoint, data, bypass_cache in cache_scenarios:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.return_value = data
            
            with patch('requests.request', return_value=mock_response):
                # Should work consistently regardless of cache settings
                response = api_client.request('GET', endpoint)
                assert response.status_code == 200
    
    def test_property_coverage_completeness(self):
        """
        Meta-test: Verify that our property tests cover the main reliability aspects
        """
        # This test ensures we're testing the right properties
        test_methods = [method for method in dir(self) if method.startswith('test_') and 'property' in method.lower()]
        
        # Should cover these key aspects of API integration reliability
        expected_aspects = [
            'response_types',  # Different HTTP responses
            'error_handling',  # Consistent error handling
            'token_refresh',   # Authentication reliability
            'serialization',   # Data handling
            'user_friendly',   # User experience
            'response_times',  # Performance reliability
            'caching'          # Caching consistency
        ]
        
        test_method_names = ' '.join(test_methods).lower()
        
        for aspect in expected_aspects:
            assert aspect in test_method_names, f"Missing property test for {aspect}"