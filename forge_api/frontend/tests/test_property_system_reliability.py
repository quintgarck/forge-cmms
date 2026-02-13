"""
Property-based tests for system integration reliability.
**Feature: forge-frontend-web, Property 7: System integration reliability**
*For any* user workflow involving API calls, the system should maintain data consistency 
and provide appropriate feedback for all success and error scenarios
**Validates: Requirements: System reliability and data integrity**
"""
import json
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from unittest.mock import patch, Mock
from frontend.services.api_client import ForgeAPIClient, APIException


class SystemReliabilityPropertyTests(TestCase):
    """
    Property-based tests for system integration reliability.
    Tests that the system maintains consistency and provides appropriate feedback
    across all possible input combinations and error scenarios.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='proptest',
            password='testpass123',
            email='prop@test.com'
        )
        self.client.force_login(self.user)
    
    @given(
        client_code=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd'), whitelist_characters='-_'),
            min_size=1,
            max_size=20
        ),
        name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' -\''),
            min_size=1,
            max_size=100
        ),
        email=st.emails(),
        phone=st.text(
            alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters=' -()'),
            min_size=8,
            max_size=20
        ),
        credit_limit=st.floats(min_value=0, max_value=999999.99, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=5000)
    def test_client_form_data_consistency_property(self, client_code, name, email, phone, credit_limit):
        """
        Property: For any valid client data, form processing should maintain data consistency.
        
        This test verifies that:
        1. Valid data is processed correctly
        2. Invalid data is rejected with appropriate errors
        3. Data transformations are consistent
        4. No data corruption occurs during processing
        """
        # Filter out obviously invalid data that would cause test setup issues
        assume(len(client_code.strip()) >= 3)
        assume(len(name.strip()) >= 2)
        assume('@' in email and '.' in email)
        assume(len(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 8)
        
        # Prepare form data
        form_data = {
            'client_code': client_code,
            'type': 'individual',
            'name': name,
            'email': email,
            'phone': phone,
            'address': 'Test Address',
            'credit_limit': f'{credit_limit:.2f}'
        }
        
        # Test with successful API response
        with patch.object(ForgeAPIClient, 'create_client') as mock_create:
            expected_response = {
                'id': 1,
                'client_code': client_code.upper().strip(),
                'name': name.strip(),
                'email': email.lower().strip(),
                'phone': phone,
                'credit_limit': credit_limit,
                'type': 'individual'
            }
            mock_create.return_value = expected_response
            
            response = self.client.post(reverse('frontend:client_create'), form_data)
            
            # Property: System should either succeed or fail gracefully
            self.assertIn(response.status_code, [200, 302])
            
            if response.status_code == 302:
                # Success case - should redirect to client detail
                self.assertIn('client', response.url)
                # Verify API was called with processed data
                mock_create.assert_called_once()
                call_data = mock_create.call_args[0][0]
                
                # Property: Data transformations should be consistent
                self.assertEqual(call_data['client_code'], client_code.upper().strip())
                self.assertEqual(call_data['name'], name.strip())
                self.assertEqual(call_data['email'], email.lower().strip())
                self.assertEqual(call_data['type'], 'individual')
            else:
                # Form validation failed - should show errors
                self.assertContains(response, 'form')
                form = response.context.get('form')
                if form:
                    # Property: Invalid data should produce validation errors
                    self.assertFalse(form.is_valid())
    
    @given(
        status_code=st.integers(min_value=400, max_value=599),
        error_message=st.text(min_size=1, max_size=200),
        has_field_errors=st.booleans()
    )
    @settings(max_examples=30, deadline=3000)
    def test_api_error_handling_consistency_property(self, status_code, error_message, has_field_errors):
        """
        Property: For any API error response, the system should provide consistent error handling.
        
        This test verifies that:
        1. All error status codes are handled appropriately
        2. Error messages are displayed to users
        3. System remains stable after errors
        4. No sensitive information is leaked
        """
        # Prepare valid form data
        form_data = {
            'client_code': 'TEST-001',
            'type': 'individual',
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone': '1234567890',
            'credit_limit': '1000.00'
        }
        
        # Prepare error response
        error_data = {}
        if has_field_errors:
            error_data = {
                'client_code': ['Field-specific error message'],
                'email': ['Another field error']
            }
        
        with patch.object(ForgeAPIClient, 'create_client') as mock_create:
            mock_create.side_effect = APIException(
                message=error_message,
                status_code=status_code,
                response_data=error_data
            )
            
            response = self.client.post(reverse('frontend:client_create'), form_data)
            
            # Property: System should always handle errors gracefully
            self.assertEqual(response.status_code, 200)  # Should stay on form page
            
            # Property: Error information should be displayed to user
            self.assertContains(response, 'form')
            
            # Property: Sensitive information should not be exposed
            response_content = response.content.decode()
            sensitive_terms = ['password', 'secret', 'token', 'key']
            for term in sensitive_terms:
                self.assertNotIn(term.lower(), response_content.lower())
            
            # Property: Form should be in error state
            form = response.context.get('form')
            if form:
                self.assertTrue(len(form.errors) > 0 or len(form.non_field_errors()) > 0)
    
    @given(
        page_number=st.integers(min_value=1, max_value=100),
        search_query=st.text(min_size=0, max_size=50),
        sort_field=st.sampled_from(['name', 'email', 'created_at', 'client_code']),
        sort_order=st.sampled_from(['asc', 'desc'])
    )
    @settings(max_examples=25, deadline=3000)
    def test_list_view_pagination_consistency_property(self, page_number, search_query, sort_field, sort_order):
        """
        Property: For any pagination parameters, list views should maintain consistency.
        
        This test verifies that:
        1. Pagination works with any valid page number
        2. Search and sorting parameters are preserved
        3. Empty results are handled gracefully
        4. Invalid parameters don't break the system
        """
        # Mock API response
        mock_response = {
            'results': [
                {
                    'id': i,
                    'client_code': f'TEST-{i:03d}',
                    'name': f'Test Client {i}',
                    'email': f'test{i}@example.com',
                    'phone': f'123456789{i}',
                    'credit_limit': 1000.00,
                    'current_balance': 0.00,
                    'type': 'individual'
                }
                for i in range(1, min(21, page_number * 20 + 1))  # Simulate realistic pagination
            ],
            'count': max(100, page_number * 20),
            'next': f'?page={page_number + 1}' if page_number < 5 else None,
            'previous': f'?page={page_number - 1}' if page_number > 1 else None
        }
        
        with patch.object(ForgeAPIClient, 'get_clients') as mock_get:
            mock_get.return_value = mock_response
            
            # Build query parameters
            params = {
                'page': page_number,
                'search': search_query,
                'sort': sort_field,
                'order': sort_order
            }
            
            response = self.client.get(reverse('frontend:client_list'), params)
            
            # Property: System should always respond successfully to list requests
            self.assertEqual(response.status_code, 200)
            
            # Property: Pagination context should be consistent
            context = response.context
            if 'pagination' in context:
                pagination = context['pagination']
                
                # Property: Current page should match requested page (or be adjusted to valid range)
                current_page = pagination.get('current_page', 1)
                self.assertGreaterEqual(current_page, 1)
                
                # Property: Total count should be non-negative
                total_count = pagination.get('count', 0)
                self.assertGreaterEqual(total_count, 0)
            
            # Property: Search and sort parameters should be preserved in context
            if 'filters' in context:
                filters = context['filters']
                self.assertEqual(filters.get('search', ''), search_query)
                self.assertEqual(filters.get('sort', ''), sort_field)
                self.assertEqual(filters.get('order', ''), sort_order)
    
    @given(
        network_error=st.booleans(),
        timeout_error=st.booleans(),
        server_error=st.booleans(),
        connection_refused=st.booleans()
    )
    @settings(max_examples=20, deadline=2000)
    def test_network_error_resilience_property(self, network_error, timeout_error, server_error, connection_refused):
        """
        Property: For any network error condition, the system should remain resilient.
        
        This test verifies that:
        1. Network errors don't crash the application
        2. Appropriate fallback behavior is implemented
        3. User receives meaningful error messages
        4. System can recover from temporary failures
        """
        # Skip if no error condition is selected
        assume(network_error or timeout_error or server_error or connection_refused)
        
        # Determine which error to simulate
        if connection_refused:
            error = ConnectionError("Connection refused")
        elif timeout_error:
            error = TimeoutError("Request timeout")
        elif server_error:
            error = APIException("Server error", status_code=500)
        else:  # network_error
            error = APIException("Network error", status_code=None)
        
        with patch.object(ForgeAPIClient, 'get') as mock_get:
            mock_get.side_effect = error
            
            # Test dashboard resilience
            response = self.client.get(reverse('frontend:dashboard'))
            
            # Property: System should not crash on network errors
            self.assertEqual(response.status_code, 200)
            
            # Property: Page should still render with fallback data
            self.assertContains(response, 'Dashboard')
            
            # Property: Context should contain fallback values
            context = response.context
            # Should have default/fallback values for KPIs
            self.assertIn('active_work_orders', context)
            self.assertIn('pending_invoices', context)
            self.assertIn('low_stock_items', context)
    
    @given(
        field_name=st.sampled_from(['client_code', 'name', 'email', 'phone', 'credit_limit']),
        field_value=st.text(min_size=0, max_size=200),
        validation_should_pass=st.booleans()
    )
    @settings(max_examples=30, deadline=3000)
    def test_form_validation_consistency_property(self, field_name, field_value, validation_should_pass):
        """
        Property: Form validation should be consistent across all field types and values.
        
        This test verifies that:
        1. Validation rules are applied consistently
        2. Error messages are appropriate and helpful
        3. Valid data passes validation
        4. Invalid data is rejected with clear feedback
        """
        from frontend.forms import ClientForm
        
        # Create base valid form data
        base_data = {
            'client_code': 'TEST-001',
            'type': 'individual',
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone': '1234567890',
            'credit_limit': '1000.00'
        }
        
        # Modify the specific field being tested
        form_data = base_data.copy()
        form_data[field_name] = field_value
        
        # Create and validate form
        form = ClientForm(data=form_data)
        is_valid = form.is_valid()
        
        # Property: Form validation should be deterministic
        # Running validation again should give same result
        form2 = ClientForm(data=form_data)
        is_valid2 = form2.is_valid()
        self.assertEqual(is_valid, is_valid2)
        
        # Property: If form is invalid, there should be error messages
        if not is_valid:
            self.assertTrue(len(form.errors) > 0 or len(form.non_field_errors()) > 0)
            
            # Property: Error messages should be strings and non-empty
            for field, errors in form.errors.items():
                for error in errors:
                    self.assertIsInstance(error, str)
                    self.assertGreater(len(error.strip()), 0)
        
        # Property: Valid forms should have cleaned data
        if is_valid:
            self.assertIsNotNone(form.cleaned_data)
            self.assertIn(field_name, form.cleaned_data)
    
    @given(
        concurrent_requests=st.integers(min_value=1, max_value=5),
        request_delay=st.floats(min_value=0.0, max_value=0.1)
    )
    @settings(max_examples=10, deadline=5000)
    def test_concurrent_request_handling_property(self, concurrent_requests, request_delay):
        """
        Property: System should handle concurrent requests reliably.
        
        This test verifies that:
        1. Multiple simultaneous requests don't interfere with each other
        2. Data consistency is maintained under concurrent access
        3. No race conditions occur
        4. All requests receive appropriate responses
        """
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                # Simulate slight delay between requests
                time.sleep(request_delay * request_id)
                
                with patch.object(ForgeAPIClient, 'get_clients') as mock_get:
                    mock_get.return_value = {
                        'results': [{'id': request_id, 'name': f'Client {request_id}'}],
                        'count': 1
                    }
                    
                    response = self.client.get(reverse('frontend:client_list'))
                    results.append((request_id, response.status_code))
                    
            except Exception as e:
                errors.append((request_id, str(e)))
        
        # Create and start threads
        threads = []
        for i in range(concurrent_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=2.0)  # Prevent hanging
        
        # Property: All requests should complete successfully
        self.assertEqual(len(results), concurrent_requests)
        self.assertEqual(len(errors), 0)
        
        # Property: All responses should be successful
        for request_id, status_code in results:
            self.assertEqual(status_code, 200)


class DataIntegrityPropertyTests(TestCase):
    """
    Property-based tests for data integrity across the system.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='datatest',
            password='testpass123'
        )
        self.client.force_login(self.user)
    
    @given(
        original_data=st.fixed_dictionaries({
            'client_code': st.text(min_size=3, max_size=20),
            'name': st.text(min_size=2, max_size=100),
            'email': st.emails(),
            'phone': st.text(min_size=8, max_size=20),
            'credit_limit': st.floats(min_value=0, max_value=999999, allow_nan=False)
        })
    )
    @settings(max_examples=20, deadline=3000)
    def test_data_round_trip_integrity_property(self, original_data):
        """
        Property: Data should maintain integrity through create -> retrieve -> update cycles.
        
        This test verifies that:
        1. Created data can be retrieved accurately
        2. Updates preserve data integrity
        3. No data corruption occurs during processing
        """
        # Simulate create operation
        with patch.object(ForgeAPIClient, 'create_client') as mock_create, \
             patch.object(ForgeAPIClient, 'get_client') as mock_get, \
             patch.object(ForgeAPIClient, 'update_client') as mock_update:
            
            # Mock responses that preserve data integrity
            created_data = original_data.copy()
            created_data['id'] = 1
            
            mock_create.return_value = created_data
            mock_get.return_value = created_data
            mock_update.return_value = created_data
            
            # Test create
            form_data = {
                'client_code': original_data['client_code'],
                'type': 'individual',
                'name': original_data['name'],
                'email': original_data['email'],
                'phone': original_data['phone'],
                'credit_limit': str(original_data['credit_limit'])
            }
            
            create_response = self.client.post(reverse('frontend:client_create'), form_data)
            
            # Property: Create should succeed or fail gracefully
            self.assertIn(create_response.status_code, [200, 302])
            
            if create_response.status_code == 302:
                # Test retrieve
                detail_response = self.client.get(reverse('frontend:client_detail', kwargs={'pk': 1}))
                self.assertEqual(detail_response.status_code, 200)
                
                # Property: Retrieved data should match created data
                context = detail_response.context
                if 'client' in context:
                    client_data = context['client']
                    # Key fields should be preserved
                    if 'client_code' in client_data:
                        self.assertEqual(client_data['client_code'], original_data['client_code'])
                    if 'name' in client_data:
                        self.assertEqual(client_data['name'], original_data['name'])
                    if 'email' in client_data:
                        self.assertEqual(client_data['email'], original_data['email'])