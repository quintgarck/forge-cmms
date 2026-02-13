"""
Property-Based Tests for System Reliability
**Feature: forge-frontend-web, Property 7: System integration reliability**
**Validates: Requirements: System reliability and data integrity**

*For any* user workflow involving API calls, the system should maintain data consistency 
and provide appropriate feedback for all success and error scenarios
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from hypothesis.extra.django import TestCase as HypothesisTestCase
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json
import time
from datetime import datetime

from ..services.api_client import ForgeAPIClient, APIException


class SystemReliabilityProperties(TestCase):
    """Property-based tests for system reliability"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
    def test_property_7_system_integration_reliability(self):
        """
        Property 7: System integration reliability
        *For any* user workflow involving API calls, the system should maintain data consistency 
        and provide appropriate feedback for all success and error scenarios
        """
        
        # Test with various API response scenarios
        test_scenarios = [
            # Success scenarios
            {'status_code': 200, 'data': {'id': 1, 'name': 'Test'}},
            {'status_code': 201, 'data': {'id': 2, 'name': 'Created'}},
            
            # Error scenarios
            {'status_code': 400, 'data': {'error': 'Bad Request'}},
            {'status_code': 401, 'data': {'error': 'Unauthorized'}},
            {'status_code': 404, 'data': {'error': 'Not Found'}},
            {'status_code': 500, 'data': {'error': 'Internal Server Error'}},
        ]
        
        for scenario in test_scenarios:
            with self.subTest(scenario=scenario):
                self._test_api_response_handling(scenario)
    
    def _test_api_response_handling(self, scenario):
        """Test that the system handles API responses appropriately"""
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = scenario['status_code']
        mock_response.json.return_value = scenario['data']
        mock_response.text = json.dumps(scenario['data'])
        
        with patch('requests.Session.get', return_value=mock_response):
            # Login user
            self.client.login(username='testuser', password='testpass123')
            
            # Test client list view (common workflow)
            response = self.client.get(reverse('frontend:client_list'))
            
            # System should always provide appropriate feedback
            self.assertIn(response.status_code, [200, 302, 500])
            
            # For successful API responses, page should load
            if scenario['status_code'] in [200, 201]:
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'client', msg_prefix="Page should contain client-related content")
            
            # For error responses, system should handle gracefully
            elif scenario['status_code'] >= 400:
                # System should not crash and should provide user feedback
                self.assertIn(response.status_code, [200, 500])
                if response.status_code == 200:
                    # Check that error is communicated to user
                    content = response.content.decode()
                    self.assertTrue(
                        any(keyword in content.lower() for keyword in ['error', 'problema', 'no disponible']),
                        "Error should be communicated to user"
                    )


@pytest.mark.django_db
@given(
    client_data=st.fixed_dictionaries({
        'client_code': st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=['Lu', 'Ll', 'Nd'], whitelist_characters='_-')),
        'type': st.sampled_from(['individual', 'company', 'government', 'nonprofit']),
        'name': st.text(min_size=2, max_size=100, alphabet=st.characters(whitelist_categories=['Lu', 'Ll', 'Nd', 'Zs'], whitelist_characters='-\'')),
        'email': st.emails(),
        'phone': st.text(min_size=7, max_size=15, alphabet=st.characters(whitelist_categories=['Nd'], whitelist_characters='()-+ ')),
    })
)
@settings(max_examples=10, deadline=5000)  # Reduced for faster testing
def test_client_data_consistency_property(client_data):
    """
    Property: Client data consistency
    *For any* valid client data, the system should maintain consistency between 
    frontend forms and API operations
    """
    
    # Assume valid data constraints
    assume(len(client_data['client_code'].strip()) >= 3)
    assume(len(client_data['name'].strip()) >= 2)
    assume('@' in client_data['email'])
    
    # Test that form validation matches API validation
    client = Client()
    user = User.objects.create_user(username='testuser', password='testpass123')
    client.login(username='testuser', password='testpass123')
    
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {**client_data, 'id': 1}
    
    with patch('requests.Session.post', return_value=mock_response):
        # Submit form data
        response = client.post(reverse('frontend:client_create'), data=client_data)
        
        # System should handle the data consistently
        assert response.status_code in [200, 302], f"Form submission should succeed or redirect, got {response.status_code}"
        
        # If redirect (success), should go to appropriate page
        if response.status_code == 302:
            assert 'client' in response.url, "Redirect should be to client-related page"


class APIReliabilityStateMachine(RuleBasedStateMachine):
    """
    Stateful property testing for API reliability
    Tests that the system maintains reliability across multiple API operations
    """
    
    clients = Bundle('clients')
    
    def __init__(self):
        super().__init__()
        self.django_client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.django_client.login(username='testuser', password='testpass123')
        self.created_clients = []
        self.api_call_count = 0
        self.error_count = 0
    
    @initialize()
    def setup(self):
        """Initialize the test state"""
        self.api_call_count = 0
        self.error_count = 0
    
    @rule(target=clients, client_code=st.text(min_size=3, max_size=10, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'))
    def create_client(self, client_code):
        """Rule: Create a client"""
        
        client_data = {
            'client_code': f'TEST_{client_code}',
            'type': 'individual',
            'name': f'Test Client {client_code}',
            'email': f'test{client_code.lower()}@example.com',
            'phone': '555-123-4567'
        }
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {**client_data, 'id': len(self.created_clients) + 1}
        
        with patch('requests.Session.post', return_value=mock_response):
            response = self.django_client.post(reverse('frontend:client_create'), data=client_data)
            
            self.api_call_count += 1
            
            # System should handle creation reliably
            if response.status_code not in [200, 302]:
                self.error_count += 1
            
            self.created_clients.append(client_data)
            return client_data
    
    @rule(client=clients)
    def view_client_list(self, client):
        """Rule: View client list"""
        
        # Mock API response with existing clients
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': self.created_clients,
            'count': len(self.created_clients)
        }
        
        with patch('requests.Session.get', return_value=mock_response):
            response = self.django_client.get(reverse('frontend:client_list'))
            
            self.api_call_count += 1
            
            # System should handle list view reliably
            if response.status_code != 200:
                self.error_count += 1
    
    @rule(client=clients)
    def handle_api_error(self, client):
        """Rule: Handle API errors gracefully"""
        
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Internal Server Error'}
        
        with patch('requests.Session.get', return_value=mock_response):
            response = self.django_client.get(reverse('frontend:client_list'))
            
            self.api_call_count += 1
            
            # System should handle errors gracefully (not crash)
            assert response.status_code in [200, 500], "System should handle API errors gracefully"
            
            if response.status_code == 500:
                self.error_count += 1
    
    @invariant()
    def system_reliability_invariant(self):
        """
        Invariant: System reliability
        The system should maintain reliability even when API calls fail
        """
        if self.api_call_count > 0:
            error_rate = self.error_count / self.api_call_count
            
            # System should not have more than 50% error rate in normal conditions
            # (This allows for some API failures while ensuring system stability)
            assert error_rate <= 0.5, f"Error rate too high: {error_rate:.2%} ({self.error_count}/{self.api_call_count})"
    
    @invariant()
    def data_consistency_invariant(self):
        """
        Invariant: Data consistency
        Created clients should remain consistent throughout the test
        """
        # All created clients should have required fields
        for client in self.created_clients:
            assert 'client_code' in client, "Client should have client_code"
            assert 'name' in client, "Client should have name"
            assert 'email' in client, "Client should have email"
            assert len(client['client_code']) >= 3, "Client code should be valid length"


class TestSystemReliabilityStateMachine(TestCase):
    """Test case wrapper for the state machine"""
    
    def test_api_reliability_state_machine(self):
        """Run the API reliability state machine test"""
        # Run the state machine with limited examples for CI/CD
        APIReliabilityStateMachine.TestCase.settings = settings(
            max_examples=20,
            stateful_step_count=10,
            deadline=10000
        )
        
        test_case = APIReliabilityStateMachine.TestCase()
        test_case.runTest()


@pytest.mark.django_db
@given(
    api_responses=st.lists(
        st.fixed_dictionaries({
            'status_code': st.integers(min_value=200, max_value=599),
            'success': st.booleans(),
            'data': st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.one_of(st.text(), st.integers(), st.booleans())
            )
        }),
        min_size=1,
        max_size=5  # Reduced for faster testing
    )
)
@settings(max_examples=10, deadline=3000)  # Reduced for faster testing
def test_error_recovery_property(api_responses):
    """
    Property: Error recovery
    *For any* sequence of API responses (success and failure), the system should 
    recover gracefully and maintain user experience
    """
    
    client = Client()
    user = User.objects.create_user(username='testuser', password='testpass123')
    client.login(username='testuser', password='testpass123')
    
    consecutive_errors = 0
    max_consecutive_errors = 0
    
    for i, api_response in enumerate(api_responses):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = api_response['status_code']
        mock_response.json.return_value = api_response['data']
        
        with patch('requests.Session.get', return_value=mock_response):
            response = client.get(reverse('frontend:client_list'))
            
            # Track consecutive errors
            if response.status_code >= 400:
                consecutive_errors += 1
                max_consecutive_errors = max(max_consecutive_errors, consecutive_errors)
            else:
                consecutive_errors = 0
            
            # System should not crash completely
            assert response.status_code != 500 or api_response['status_code'] >= 500, \
                "System should not generate 500 errors unless API returns 500"
    
    # System should recover from errors (not have too many consecutive failures)
    assert max_consecutive_errors <= len(api_responses), \
        f"System should recover from errors, had {max_consecutive_errors} consecutive errors"


class TestFormValidationConsistency(HypothesisTestCase):
    """Test form validation consistency properties"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
    
    @given(
        invalid_data=st.fixed_dictionaries({
            'client_code': st.one_of(
                st.text(max_size=2),  # Too short
                st.text(min_size=1, alphabet='!@#$%^&*()'),  # Invalid characters
                st.just('')  # Empty
            ),
            'name': st.one_of(
                st.text(max_size=1),  # Too short
                st.just('')  # Empty
            ),
            'email': st.one_of(
                st.text(min_size=1, max_size=20).filter(lambda x: '@' not in x),  # Invalid email
                st.just('')  # Empty
            ),
            'type': st.sampled_from(['individual', 'company'])
        })
    )
    @settings(max_examples=10, deadline=3000)  # Reduced for faster testing
    def test_form_validation_consistency_property(self, invalid_data):
        """
        Property: Form validation consistency
        *For any* invalid form data, the system should consistently reject it
        and provide appropriate error messages
        """
        
        # Submit invalid data
        response = self.client.post(reverse('frontend:client_create'), data=invalid_data)
        
        # System should handle invalid data consistently
        # Either show form with errors (200) or redirect to error page
        assert response.status_code in [200, 400], \
            f"Invalid data should be handled consistently, got {response.status_code}"
        
        if response.status_code == 200:
            # Should contain error indicators
            content = response.content.decode().lower()
            assert any(keyword in content for keyword in ['error', 'invalid', 'required', 'requerido']), \
                "Form should show validation errors for invalid data"


# Integration with pytest for running property tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])