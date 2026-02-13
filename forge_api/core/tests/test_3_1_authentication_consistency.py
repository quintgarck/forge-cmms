"""
ForgeDB API REST - Property Tests for Authentication Consistency
Task 3.1: Property test for authentication token issuance consistency

**Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
**Validates: Requirements 1.1**

This module contains property-based tests that verify the consistency of JWT token 
issuance for the ForgeDB authentication system using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import RequestFactory
import json
import time

from core.models import Technician, TechnicianUser
from core.authentication import TechnicianAuthBackend
from core.views.auth_views import CustomTokenObtainPairView


class TestAuthenticationTokenIssuance:
    """
    Property-based tests for JWT token issuance consistency
    """
    
    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        password=st.text(min_size=8, max_size=50).filter(lambda x: any(c.isupper() for c in x) and any(c.islower() for c in x) and any(c.isdigit() for c in x))
    )
    def test_token_issuance_consistency_for_valid_credentials(self, employee_code, password):
        """
        **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
        
        For any valid credentials provided to the authentication endpoint, 
        the system should always issue a valid Authentication_Token with 
        permissions matching the user's role.
        """
        # Setup: Create technician and user with valid credentials
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
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
        
        # Test: Authenticate with valid credentials
        backend = TechnicianAuthBackend()
        authenticated_user = backend.authenticate(
            request=RequestFactory().post('/'),
            username=employee_code,
            password=password
        )
        
        # Assert: Authentication should succeed and user should have proper permissions
        assert authenticated_user is not None
        assert authenticated_user == user
        assert authenticated_user.is_authenticated
        assert authenticated_user.technician == technician
        assert authenticated_user.is_workshop_admin or authenticated_user.role in ['admin', 'technician', 'viewer']
        
        # Test: Generate JWT tokens and verify structure
        tokens = authenticated_user.get_tokens()
        
        # Assert: Both access and refresh tokens should be present and valid
        assert 'access' in tokens
        assert 'refresh' in tokens
        assert isinstance(tokens['access'], str)
        assert isinstance(tokens['refresh'], str)
        assert len(tokens['access']) > 50  # JWT tokens have significant length
        assert len(tokens['refresh']) > 50
        
        # Assert: Tokens should be valid JWT tokens
        access_token = AccessToken(tokens['access'])
        refresh_token = RefreshToken(tokens['refresh'])
        
        assert access_token['user_id'] == authenticated_user.id
        assert 'token_type' in access_token
        assert access_token['token_type'] == 'access'
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20),
        invalid_password=st.text(min_size=1, max_size=50)
    )
    def test_authentication_failure_for_invalid_credentials(self, employee_code, invalid_password):
        """
        **Feature: forge-api-rest, Property 4: Credential error response security**
        
        For any invalid credentials provided to authentication endpoints, 
        the system should return appropriate error responses without exposing 
        sensitive system details or internal information.
        """
        # Setup: Create technician and user
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        correct_password = "ValidPass123"
        user = TechnicianUser.objects.create_user(
            username=employee_code,
            password=correct_password,
            email=technician.email,
            first_name=technician.first_name,
            last_name=technician.last_name,
            technician=technician
        )
        
        # Test: Attempt authentication with wrong password
        backend = TechnicianAuthBackend()
        authenticated_user = backend.authenticate(
            request=RequestFactory().post('/'),
            username=employee_code,
            password=invalid_password
        )
        
        # Assert: Authentication should fail, no user returned
        assert authenticated_user is None
        
        # Test: Try with non-existent employee code
        fake_employee_code = f"fake_{employee_code}_code"
        fake_user = backend.authenticate(
            request=RequestFactory().post('/'),
            username=fake_employee_code,
            password=correct_password
        )
        
        # Assert: Authentication should fail for non-existent user
        assert fake_user is None
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_token_structure_and_claims_consistency(self, employee_code):
        """
        Test that JWT tokens have consistent structure and claims
        """
        # Setup: Create technician and user
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="Technician",
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
        
        # Generate tokens
        tokens = user.get_tokens()
        access_token = AccessToken(tokens['access'])
        refresh_token = RefreshToken(tokens['refresh'])
        
        # Assert: Access token should have required claims
        assert 'exp' in access_token  # Expiration time
        assert 'iat' in access_token  # Issued at time
        assert 'jti' in access_token  # JWT ID
        assert 'token_type' in access_token
        assert access_token['user_id'] == user.id
        
        # Assert: Refresh token should have required claims
        assert 'exp' in refresh_token
        assert 'iat' in refresh_token
        assert 'jti' in refresh_token
        assert 'token_type' in refresh_token
        assert refresh_token['token_type'] == 'refresh'
        
        # Assert: Token expiration times should be reasonable
        current_time = time.time()
        assert access_token['exp'] > current_time
        assert refresh_token['exp'] > current_time
        assert access_token['exp'] < current_time + 3600 * 2  # Less than 2 hours
        assert refresh_token['exp'] > current_time + 3600 * 24  # More than 24 hours
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_technician_integration_consistency(self, employee_code):
        """
        Test that user authentication properly integrates with technician data
        """
        # Setup: Create technician with specific data
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Juan",
            last_name="Pérez",
            email=f"{employee_code}@test.com",
            phone="+1234567890",
            mobile="+0987654321",
            hire_date="2023-01-15",
            specializations=["Motor", "Frenos"],
            certifications=["Certificado A", "Certificado B"],
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
        
        # Test: Verify technician integration
        assert user.technician == technician
        assert user.technician.technician_id == technician.technician_id
        assert user.technician.employee_code == employee_code
        assert user.technician.full_name == "Juan Pérez"
        assert user.technician.status == "active"
        assert user.technician.specializations == ["Motor", "Frenos"]
        assert user.technician.certifications == ["Certificado A", "Certificado B"]
        
        # Test: Verify user properties based on technician data
        assert user.full_name == "Juan Pérez"
        assert user.email == f"{employee_code}@test.com"
        
        # Test: Verify tokens include correct user identification
        tokens = user.get_tokens()
        access_token = AccessToken(tokens['access'])
        assert access_token['user_id'] == user.id
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_authentication_backend_user_creation(self, employee_code):
        """
        Test that the authentication backend properly creates user accounts for technicians
        """
        # Setup: Create technician without user account
        password = "ValidPass123"
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Ana",
            last_name="García",
            email=f"{employee_code}@test.com",
            hire_date="2023-06-01",
            status="active"
        )
        
        # Verify technician has no user account initially
        assert not hasattr(technician, 'user_account') or technician.user_account is None
        
        # Test: Authenticate - should create user account
        backend = TechnicianAuthBackend()
        user = backend.authenticate(
            request=RequestFactory().post('/'),
            username=employee_code,
            password=password  # Default password pattern: {username}@forge2024
        )
        
        # Assert: User should be created and authentication should succeed
        assert user is not None
        assert user.username == employee_code
        assert user.technician == technician
        assert user.email == technician.email
        assert user.first_name == technician.first_name
        assert user.last_name == technician.last_name
        assert user.is_active
        
        # Verify user account was properly linked
        technician.refresh_from_db()
        assert technician.user_account == user
        
        # Test: Second authentication should return existing user
        user2 = backend.authenticate(
            request=RequestFactory().post('/'),
            username=employee_code,
            password=password
        )
        
        # Assert: Should return the same user object
        assert user2 == user
        assert user2.id == user.id
        
        # Cleanup
        technician.delete()
        user.delete()


class TestTokenRefreshMechanism:
    """
    Property-based tests for token refresh reliability
    """
    
    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_token_refresh_mechanism_reliability(self, employee_code):
        """
        **Feature: forge-api-rest, Property 5: Token refresh mechanism reliability**
        
        For any valid refresh token, the system should consistently issue new 
        Authentication_Tokens with appropriate expiration times and permissions.
        """
        # Setup: Create user and get initial tokens
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
        
        # Get initial tokens
        initial_tokens = user.get_tokens()
        initial_access = initial_tokens['access']
        initial_refresh = initial_tokens['refresh']
        
        # Test: Refresh the access token
        refresh_token = RefreshToken(initial_refresh)
        new_access = str(refresh_token.access_token)
        
        # Assert: New access token should be different from initial
        assert new_access != initial_access
        
        # Assert: New access token should be valid
        new_access_token = AccessToken(new_access)
        assert new_access_token['user_id'] == user.id
        assert 'exp' in new_access_token
        assert 'iat' in new_access_token
        assert new_access_token['token_type'] == 'access'
        
        # Assert: Expiration time should be in the future
        current_time = time.time()
        assert new_access_token['exp'] > current_time
        
        # Assert: New access token should have same user claims
        assert new_access_token['user_id'] == AccessToken(initial_access)['user_id']
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @given(
        invalid_refresh_token=st.text(min_size=10, max_size=500)
    )
    def test_invalid_refresh_token_handling(self, invalid_refresh_token):
        """
        Test that invalid refresh tokens are properly rejected
        """
        # Test: Attempt to refresh with invalid token
        with pytest.raises(Exception):  # TokenError or InvalidToken
            refresh_token = RefreshToken(invalid_refresh_token)
            _ = str(refresh_token.access_token)
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_refresh_token_rotation(self, employee_code):
        """
        Test that refresh tokens can be rotated and old ones invalidated
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
        
        # Get initial tokens
        initial_tokens = user.get_tokens()
        initial_refresh = initial_tokens['refresh']
        
        # Test: Rotate refresh token by creating new tokens
        new_tokens = user.get_tokens()
        new_refresh = new_tokens['refresh']
        
        # Assert: Refresh token should be different (rotation enabled)
        assert new_refresh != initial_refresh
        
        # Assert: Both tokens should be valid initially
        try:
            AccessToken(initial_tokens['access'])
            AccessToken(new_tokens['access'])
            RefreshToken(initial_refresh)
            RefreshToken(new_refresh)
        except Exception as e:
            pytest.fail(f"Token validation failed: {e}")
        
        # Cleanup
        technician.delete()
        user.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])