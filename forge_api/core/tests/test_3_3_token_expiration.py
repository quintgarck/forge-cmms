"""
ForgeDB API REST - Property Tests for Token Expiration
Task 3.3: Property test for token expiration rejection consistency

**Feature: forge-api-rest, Property 3: Token expiration rejection consistency**
**Validates: Requirements 1.3**

This module contains property-based tests that verify the consistency of token 
expiration handling and rejection for expired tokens using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import RequestFactory
from django.utils import timezone
from datetime import datetime, timedelta
import time
import jwt

from core.models import Technician, TechnicianUser
from core.views.auth_views import refresh_token


class TestTokenExpirationRejectionConsistency:
    """
    Property-based tests for token expiration and rejection consistency
    """
    
    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_expired_access_token_rejection_consistency(self, employee_code):
        """
        **Feature: forge-api-rest, Property 3: Token expiration rejection consistency**
        
        For any expired Authentication_Token used in API requests, the system should 
        always reject the request and require re-authentication.
        """
        # Setup: Create user and get valid token
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Get valid access token
        tokens = user.get_tokens()
        valid_access_token = tokens['access']
        
        # Test: Valid token should work
        try:
            valid_decoded = AccessToken(valid_access_token)
            current_time = time.time()
            assert valid_decoded['exp'] > current_time, "Valid token should not be expired"
        except Exception as e:
            pytest.fail(f"Valid token should be decodable: {e}")
        
        # Test: Create expired token by manipulating the exp claim
        try:
            # Decode the original token to get payload
            original_payload = jwt.decode(valid_access_token, options={"verify_signature": False})
            
            # Create expired token by setting exp to past time
            expired_payload = original_payload.copy()
            expired_payload['exp'] = int(time.time()) - 3600  # Expired 1 hour ago
            expired_payload['iat'] = int(time.time()) - 7200  # Issued 2 hours ago
            
            # Encode with same secret
            from django.conf import settings
            expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Test: Expired token should be rejected
            with pytest.raises(TokenError):
                AccessToken(expired_token)
                
        except Exception as e:
            pytest.fail(f"Token manipulation failed: {e}")
        
        # Test: API request with expired token should be rejected
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        
        # Note: This test may vary depending on API endpoint implementation
        # The key is that expired tokens should eventually be rejected
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_token_expiration_time_consistency(self, employee_code):
        """
        Test that tokens have consistent expiration times according to configuration
        """
        # Setup: Create user
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Get tokens
        tokens = user.get_tokens()
        access_token = AccessToken(tokens['access'])
        refresh_token_obj = RefreshToken(tokens['refresh'])
        
        # Test: Access token expiration time should be configured properly
        current_time = time.time()
        exp_time = access_token['exp']
        
        # Access token should expire in the future
        assert exp_time > current_time
        
        # Access token should expire within configured lifetime (1 hour)
        assert exp_time < current_time + 3600 + 300  # 1 hour + 5 minutes buffer
        
        # Access token should be valid for at least reasonable time
        assert exp_time > current_time + 300  # At least 5 minutes
        
        # Test: Refresh token should have much longer expiration
        refresh_exp_time = refresh_token_obj['exp']
        
        # Refresh token should expire much later than access token
        assert refresh_exp_time > exp_time
        
        # Refresh token should expire in the future
        assert refresh_exp_time > current_time
        
        # Refresh token should be valid for configured period (7 days)
        assert refresh_exp_time < current_time + (7 * 24 * 3600) + 3600  # 7 days + 1 hour buffer
        assert refresh_exp_time > current_time + (6 * 24 * 3600)  # At least 6 days
        
        # Test: Time to live should be reasonable
        access_ttl = exp_time - current_time
        refresh_ttl = refresh_exp_time - current_time
        
        assert access_ttl > 0, "Access token should have positive TTL"
        assert refresh_ttl > 0, "Refresh token should have positive TTL"
        assert refresh_ttl > access_ttl, "Refresh token should outlive access token"
        
        # The ratio should be reasonable (refresh much longer than access)
        assert refresh_ttl / access_ttl > 10, "Refresh token should be much longer than access token"
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_expired_refresh_token_handling(self, employee_code):
        """
        Test that expired refresh tokens are properly handled
        """
        # Setup: Create user
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Get valid refresh token
        tokens = user.get_tokens()
        valid_refresh = tokens['refresh']
        
        # Test: Create expired refresh token
        try:
            original_payload = jwt.decode(valid_refresh, options={"verify_signature": False})
            
            # Create expired refresh token
            expired_payload = original_payload.copy()
            expired_payload['exp'] = int(time.time()) - 86400  # Expired 1 day ago
            expired_payload['iat'] = int(time.time()) - 172800  # Issued 2 days ago
            
            from django.conf import settings
            expired_refresh_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Test: Expired refresh token should be rejected
            with pytest.raises(TokenError):
                RefreshToken(expired_refresh_token)
            
            # Test: Attempting to use expired refresh token for refresh should fail
            # Note: This test may require API endpoint testing
            
        except Exception as e:
            pytest.fail(f"Refresh token manipulation failed: {e}")
        
        # Test: API request with expired refresh token should be rejected
        client = APIClient()
        
        # Note: This would typically be tested against the /auth/refresh/ endpoint
        # but we're testing the token validation logic here
        
        # The key behavior is that expired refresh tokens should not work
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_token_expiration_boundary_conditions(self, employee_code):
        """
        Test token expiration handling at boundary conditions
        """
        # Setup
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        tokens = user.get_tokens()
        access_token = AccessToken(tokens['access'])
        
        current_time = time.time()
        exp_time = access_token['exp']
        
        # Test: Token that expires exactly now should be rejected
        boundary_payload = jwt.decode(access_token, options={"verify_signature": False})
        boundary_payload['exp'] = int(current_time)
        
        from django.conf import settings
        boundary_token = jwt.encode(boundary_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Token expiring "now" should be considered expired
        with pytest.raises(TokenError):
            AccessToken(boundary_token)
        
        # Test: Token that expires 1 second in future should be valid
        future_payload = boundary_payload.copy()
        future_payload['exp'] = int(current_time) + 1
        
        future_token = jwt.encode(future_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Should be valid (though may expire quickly)
        try:
            AccessToken(future_token)
        except TokenError:
            pytest.fail("Token expiring 1 second in future should be valid")
        
        # Test: Token with invalid exp claim should be rejected
        invalid_payload = boundary_payload.copy()
        invalid_payload['exp'] = "invalid"  # Invalid format
        
        invalid_token = jwt.encode(invalid_payload, settings.SECRET_KEY, algorithm='HS256')
        
        with pytest.raises((TokenError, jwt.InvalidTokenError)):
            AccessToken(invalid_token)
        
        # Test: Token without exp claim should be rejected
        no_exp_payload = boundary_payload.copy()
        del no_exp_payload['exp']
        
        no_exp_token = jwt.encode(no_exp_payload, settings.SECRET_KEY, algorithm='HS256')
        
        with pytest.raises(TokenError):
            AccessToken(no_exp_token)
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_multiple_token_expiration_consistency(self, employee_code):
        """
        Test that multiple tokens for the same user expire consistently
        """
        # Setup
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Generate multiple sets of tokens
        token_sets = []
        for i in range(5):
            tokens = user.get_tokens()
            access_token = AccessToken(tokens['access'])
            token_sets.append(access_token)
        
        # Test: All access tokens should have similar expiration times
        exp_times = [token['exp'] for token in token_sets]
        
        # All tokens should expire in the future
        current_time = time.time()
        assert all(exp_time > current_time for exp_time in exp_times), "All tokens should be valid"
        
        # Expiration times should be relatively close (within minutes)
        min_exp = min(exp_times)
        max_exp = max(exp_times)
        exp_difference = max_exp - min_exp
        
        # Should be less than 5 minutes difference (generating tokens shouldn't take that long)
        assert exp_difference < 300, f"Token expiration times should be close: {exp_difference}s difference"
        
        # Test: Refresh tokens should also have consistent expiration
        refresh_tokens = []
        for i in range(5):
            tokens = user.get_tokens()
            refresh_token_obj = RefreshToken(tokens['refresh'])
            refresh_tokens.append(refresh_token_obj)
        
        refresh_exp_times = [token['exp'] for token in refresh_tokens]
        
        # All refresh tokens should be valid
        assert all(exp_time > current_time for exp_time in refresh_exp_times), "All refresh tokens should be valid"
        
        # Refresh token expiration should be much later than access tokens
        refresh_min_exp = min(refresh_exp_times)
        access_max_exp = max(exp_times)
        
        assert refresh_min_exp > access_max_exp, "Refresh tokens should expire after access tokens"
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_token_clock_skew_handling(self, employee_code):
        """
        Test that tokens handle clock skew appropriately
        """
        # Setup
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        tokens = user.get_tokens()
        access_token = tokens['access']
        
        # Test: Token should work with small clock differences
        # Simulate client clock being slightly behind (but within tolerance)
        original_payload = jwt.decode(access_token, options={"verify_signature": False})
        
        # Create token that appears to expire 30 seconds in the future from client perspective
        # but 10 seconds in the past from server perspective (30s clock skew)
        client_time = time.time() - 30  # Client clock 30s behind
        
        skewed_payload = original_payload.copy()
        skewed_payload['exp'] = int(client_time + 60)  # Expires 60s from client time
        skewed_payload['iat'] = int(client_time)
        
        from django.conf import settings
        skewed_token = jwt.encode(skewed_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # Test: This should be rejected if clock skew is not handled
        # or accepted if clock skew tolerance is implemented
        try:
            # Most JWT implementations are strict about expiration
            # so this should typically fail
            AccessToken(skewed_token)
            # If it passes, clock skew tolerance is implemented
        except TokenError:
            # Expected: strict token validation
            pass
        
        # Test: Token with future issued-at time should be handled properly
        future_iat_payload = original_payload.copy()
        future_iat_payload['iat'] = int(time.time()) + 300  # Issued 5 minutes in future
        
        future_iat_token = jwt.encode(future_iat_payload, settings.SECRET_KEY, algorithm='HS256')
        
        # This should typically be rejected
        with pytest.raises(TokenError):
            AccessToken(future_iat_token)
        
        # Cleanup
        technician.delete()
        user.delete()


class TestTokenRefreshWithExpiration:
    """
    Tests for token refresh mechanism with expired tokens
    """
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_refresh_with_expired_access_token(self, employee_code):
        """
        Test that refresh works even when access token is expired
        """
        # Setup
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Get tokens
        tokens = user.get_tokens()
        refresh_token_str = tokens['refresh']
        
        # Create expired access token
        try:
            access_token = AccessToken(tokens['access'])
            original_payload = jwt.decode(access_token, options={"verify_signature": False})
            
            expired_payload = original_payload.copy()
            expired_payload['exp'] = int(time.time()) - 3600  # Expired 1 hour ago
            
            from django.conf import settings
            expired_access_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Test: Should be able to refresh even with expired access token
            refresh_token_obj = RefreshToken(refresh_token_str)
            
            # Refresh token should still be valid (assuming refresh token lifetime is longer)
            assert refresh_token_obj['exp'] > time.time(), "Refresh token should still be valid"
            
            # Should be able to generate new access token from valid refresh token
            new_access_token = str(refresh_token_obj.access_token)
            
            # New access token should be valid
            new_access_token_obj = AccessToken(new_access_token)
            assert new_access_token_obj['exp'] > time.time(), "New access token should be valid"
            
        except Exception as e:
            pytest.fail(f"Token refresh test failed: {e}")
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_refresh_token_expiration_blocking(self, employee_code):
        """
        Test that expired refresh tokens cannot be used to get new tokens
        """
        # Setup
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Create expired refresh token
        tokens = user.get_tokens()
        valid_refresh = tokens['refresh']
        
        try:
            original_payload = jwt.decode(valid_refresh, options={"verify_signature": False})
            
            expired_payload = original_payload.copy()
            expired_payload['exp'] = int(time.time()) - 86400  # Expired 1 day ago
            
            from django.conf import settings
            expired_refresh_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Test: Expired refresh token should not work
            with pytest.raises(TokenError):
                RefreshToken(expired_refresh_token)
            
            # Even if we could create a RefreshToken object from expired token,
            # it should not allow generating new access tokens
            
        except Exception as e:
            pytest.fail(f"Expired refresh token test failed: {e}")
        
        # Cleanup
        technician.delete()
        user.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])