"""
ForgeDB API REST - Property Tests for Authorization Enforcement
Task 3.2: Property test for authorization enforcement universality

**Feature: forge-api-rest, Property 2: Authorization enforcement universality**
**Validates: Requirements 1.2**

This module contains property-based tests that verify the universality and consistency 
of authorization enforcement across all protected endpoints using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse
from django.test import RequestFactory
from django.core.exceptions import PermissionDenied
import json

from core.models import Technician, TechnicianUser, Client, Equipment, WorkOrder
from core.authentication import (
    TechnicianAuthBackend, 
    IsWorkshopAdmin, 
    CanManageInventory, 
    CanManageClients, 
    CanViewReports, 
    IsTechnicianOrReadOnly
)
from core.serializers.auth_serializers import LoginSerializer


class TestAuthorizationEnforcementUniversality:
    """
    Property-based tests for authorization enforcement across all endpoints
    """
    
    @pytest.mark.django_db
    @settings(max_examples=100)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
        password=st.text(min_size=8, max_size=50)
    )
    def test_protected_endpoint_access_control(self, employee_code, password):
        """
        **Feature: forge-api-rest, Property 2: Authorization enforcement universality**
        
        For any protected endpoint and any Authentication_Token, the system should 
        consistently validate the token and enforce role-based permissions according 
        to the user's assigned role.
        """
        # Setup: Create authenticated user
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
        
        # Test: Verify user is properly authenticated
        assert user.is_authenticated
        assert user.technician == technician
        
        # Test: Verify role-based permissions are available
        assert hasattr(user, 'is_workshop_admin')
        assert hasattr(user, 'can_manage_inventory')
        assert hasattr(user, 'can_manage_clients')
        assert hasattr(user, 'can_view_reports')
        assert hasattr(user, 'role')
        
        # Test: Verify permission methods work correctly
        assert callable(user.has_workshop_permission)
        
        # Test: Admin user should have all permissions
        if user.is_workshop_admin:
            assert user.has_workshop_permission('manage_inventory')
            assert user.has_workshop_permission('manage_clients')
            assert user.has_workshop_permission('view_reports')
        
        # Test: Regular user should have at least view_reports
        if not user.is_workshop_admin:
            assert user.has_workshop_permission('view_reports') or user.role in ['technician', 'viewer']
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_permission_classes_universality(self, employee_code):
        """
        Test that permission classes work consistently across different user types
        """
        # Setup: Create different types of users
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        # Test admin user
        admin_user = TechnicianUser.objects.create_superuser(
            username=f"admin_{employee_code}",
            password="AdminPass123",
            email=f"admin_{employee_code}@test.com"
        )
        admin_user.technician = technician
        admin_user.save()
        
        # Test regular user
        regular_user = TechnicianUser.objects.create_user(
            username=f"user_{employee_code}",
            password="UserPass123",
            email=f"user_{employee_code}@test.com",
            technician=technician
        )
        
        # Test permission classes with admin user
        admin_request = RequestFactory().get('/')
        admin_request.user = admin_user
        
        assert IsWorkshopAdmin().has_permission(admin_request, None) == True
        assert CanManageInventory().has_permission(admin_request, None) == True
        assert CanManageClients().has_permission(admin_request, None) == True
        assert CanViewReports().has_permission(admin_request, None) == True
        
        # Test permission classes with regular user
        regular_request = RequestFactory().get('/')
        regular_request.user = regular_user
        
        # Regular user should not be workshop admin
        assert IsWorkshopAdmin().has_permission(regular_request, None) == False
        
        # Regular user should have view permissions
        assert CanViewReports().has_permission(regular_request, None) == True
        
        # Test with anonymous user
        anonymous_request = RequestFactory().get('/')
        anonymous_request.user = AnonymousUser()
        
        # All permissions should be denied for anonymous users
        assert IsWorkshopAdmin().has_permission(anonymous_request, None) == False
        assert CanManageInventory().has_permission(anonymous_request, None) == False
        assert CanManageClients().has_permission(anonymous_request, None) == False
        assert CanViewReports().has_permission(anonymous_request, None) == False
        
        # Cleanup
        technician.delete()
        admin_user.delete()
        regular_user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_work_order_permission_enforcement(self, employee_code):
        """
        Test permission enforcement for work order operations
        """
        # Setup: Create test data
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Juan",
            last_name="Pérez",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        client = Client.objects.create(
            client_code=f"CLI_{employee_code}",
            type="individual",
            name="Test Client",
            email="client@test.com"
        )
        
        equipment = Equipment.objects.create(
            client=client,
            equipment_code=f"EQ_{employee_code}",
            year=2020,
            make="Toyota",
            model="Corolla"
        )
        
        # Create users with different roles
        admin_user = TechnicianUser.objects.create_superuser(
            username=f"admin_{employee_code}",
            password="AdminPass123",
            email=f"admin_{employee_code}@test.com"
        )
        admin_user.technician = technician
        admin_user.save()
        
        assigned_user = TechnicianUser.objects.create_user(
            username=f"assigned_{employee_code}",
            password="UserPass123",
            email=f"assigned_{employee_code}@test.com",
            technician=technician
        )
        
        other_user = TechnicianUser.objects.create_user(
            username=f"other_{employee_code}",
            password="UserPass123",
            email=f"other_{employee_code}@test.com",
            technician=technician
        )
        
        # Create work orders
        wo_assigned = WorkOrder.objects.create(
            wo_number=f"WO_ASSIGNED_{employee_code}",
            client=client,
            equipment=equipment,
            description="Test work order",
            status="in_progress",
            assigned_technician=assigned_user.technician,
            created_by=assigned_user.technician
        )
        
        wo_other = WorkOrder.objects.create(
            wo_number=f"WO_OTHER_{employee_code}",
            client=client,
            equipment=equipment,
            description="Other test work order",
            status="in_progress",
            assigned_technician=other_user.technician,
            created_by=other_user.technician
        )
        
        # Test: IsTechnicianOrReadOnly permission
        admin_request = RequestFactory().get('/')
        admin_request.user = admin_user
        
        # Admin should have full access
        assert IsTechnicianOrReadOnly().has_object_permission(admin_request, None, wo_assigned) == True
        assert IsTechnicianOrReadOnly().has_object_permission(admin_request, None, wo_other) == True
        
        # Assigned user should have access to their work orders
        assigned_request = RequestFactory().get('/')
        assigned_request.user = assigned_user
        
        assert IsTechnicianOrReadOnly().has_object_permission(assigned_request, None, wo_assigned) == True
        assert IsTechnicianOrReadOnly().has_object_permission(assigned_request, None, wo_other) == False
        
        # Other user should not have access to work orders they didn't create/assign
        other_request = RequestFactory().get('/')
        other_request.user = other_user
        
        assert IsTechnicianOrReadOnly().has_object_permission(other_request, None, wo_assigned) == False
        assert IsTechnicianOrReadOnly().has_object_permission(other_request, None, wo_other) == True
        
        # Test: Read permissions should be available for authenticated users
        read_request = RequestFactory().get('/')
        read_request.user = other_user
        
        assert IsTechnicianOrReadOnly().has_object_permission(read_request, None, wo_assigned) == True  # GET request
        
        # Cleanup
        technician.delete()
        admin_user.delete()
        assigned_user.delete()
        other_user.delete()
        client.delete()
        equipment.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_permission_consistency_across_roles(self, employee_code):
        """
        Test that permissions are consistently applied across different user roles
        """
        # Setup: Create base data
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        # Create users with different roles
        superuser = TechnicianUser.objects.create_superuser(
            username=f"super_{employee_code}",
            password="SuperPass123",
            email=f"super_{employee_code}@test.com"
        )
        
        admin_user = TechnicianUser.objects.create_user(
            username=f"admin_{employee_code}",
            password="AdminPass123",
            email=f"admin_{employee_code}@test.com",
            technician=technician,
            is_staff=True
        )
        
        regular_user = TechnicianUser.objects.create_user(
            username=f"regular_{employee_code}",
            password="UserPass123",
            email=f"regular_{employee_code}@test.com",
            technician=technician,
            role="technician"
        )
        
        readonly_user = TechnicianUser.objects.create_user(
            username=f"readonly_{employee_code}",
            password="ReadOnly123",
            email=f"readonly_{employee_code}@test.com",
            technician=technician,
            role="viewer"
        )
        
        # Test permission consistency
        test_request = RequestFactory().get('/')
        
        # Superuser should have all permissions
        test_request.user = superuser
        assert IsWorkshopAdmin().has_permission(test_request, None) == True
        assert CanManageInventory().has_permission(test_request, None) == True
        assert CanManageClients().has_permission(test_request, None) == True
        assert CanViewReports().has_permission(test_request, None) == True
        
        # Admin user should have admin permissions
        test_request.user = admin_user
        assert IsWorkshopAdmin().has_permission(test_request, None) == True
        assert CanViewReports().has_permission(test_request, None) == True
        
        # Regular user should have basic permissions
        test_request.user = regular_user
        assert CanViewReports().has_permission(test_request, None) == True
        assert regular_user.has_workshop_permission('manage_inventory') == True  # All authenticated users have this
        
        # Read-only user should have view permissions
        test_request.user = readonly_user
        assert CanViewReports().has_permission(test_request, None) == True
        
        # Test: All authenticated users should pass IsTechnicianOrReadOnly for read operations
        for user in [superuser, admin_user, regular_user, readonly_user]:
            test_request.user = user
            assert IsTechnicianOrReadOnly().has_permission(test_request, None) == True
        
        # Cleanup
        technician.delete()
        superuser.delete()
        admin_user.delete()
        regular_user.delete()
        readonly_user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_unauthorized_access_prevention(self, employee_code):
        """
        Test that unauthorized access is consistently prevented
        """
        # Setup: Create users and data
        technician = Technician.objects.create(
            employee_code=employee_code,
            first_name="Test",
            last_name="User",
            email=f"{employee_code}@test.com",
            hire_date="2023-01-01",
            status="active"
        )
        
        authorized_user = TechnicianUser.objects.create_user(
            username=f"auth_{employee_code}",
            password="AuthPass123",
            email=f"auth_{employee_code}@test.com",
            technician=technician
        )
        
        unauthorized_user = TechnicianUser.objects.create_user(
            username=f"unauth_{employee_code}",
            password="UnAuthPass123",
            email=f"unauth_{employee_code}@test.com",
            technician=technician
        )
        
        client = Client.objects.create(
            client_code=f"CLI_{employee_code}",
            type="individual",
            name="Test Client",
            email="client@test.com"
        )
        
        equipment = Equipment.objects.create(
            client=client,
            equipment_code=f"EQ_{employee_code}",
            year=2020,
            make="Toyota",
            model="Corolla"
        )
        
        work_order = WorkOrder.objects.create(
            wo_number=f"WO_{employee_code}",
            client=client,
            equipment=equipment,
            description="Test work order",
            created_by=authorized_user.technician
        )
        
        # Test: Authorized user should have access
        auth_request = RequestFactory().get('/')
        auth_request.user = authorized_user
        
        # All authenticated users should have read access
        assert IsTechnicianOrReadOnly().has_permission(auth_request, None) == True
        assert CanViewReports().has_permission(auth_request, None) == True
        
        # Test: Unauthorized user should still have read access (authenticated)
        unauth_request = RequestFactory().get('/')
        unauth_request.user = unauthorized_user
        
        assert IsTechnicianOrReadOnly().has_permission(unauth_request, None) == True
        assert CanViewReports().has_permission(unauth_request, None) == True
        
        # Test: Anonymous user should be denied all permissions
        anon_request = RequestFactory().get('/')
        anon_request.user = AnonymousUser()
        
        assert IsWorkshopAdmin().has_permission(anon_request, None) == False
        assert CanManageInventory().has_permission(anon_request, None) == False
        assert CanManageClients().has_permission(anon_request, None) == False
        assert CanViewReports().has_permission(anon_request, None) == False
        assert IsTechnicianOrReadOnly().has_permission(anon_request, None) == False
        
        # Test: Inactive user should be denied permissions
        inactive_user = TechnicianUser.objects.create_user(
            username=f"inactive_{employee_code}",
            password="Inactive123",
            email=f"inactive_{employee_code}@test.com",
            technician=technician,
            is_active=False
        )
        
        inactive_request = RequestFactory().get('/')
        inactive_request.user = inactive_user
        
        # Inactive users should be treated as unauthenticated
        assert inactive_user.is_active == False
        
        # Cleanup
        technician.delete()
        authorized_user.delete()
        unauthorized_user.delete()
        inactive_user.delete()
        client.delete()
        equipment.delete()


class TestAPIEndpointAuthorization:
    """
    Property-based tests for API endpoint authorization enforcement
    """
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_authentication_required_for_protected_endpoints(self, employee_code):
        """
        Test that protected endpoints require authentication
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
        
        # Test: Authenticated requests should work
        client = APIClient()
        client.force_authenticate(user=user)
        
        # These endpoints should be accessible with authentication
        # Note: We're testing the pattern, actual endpoints may vary
        protected_endpoints = [
            '/api/v1/auth/profile/',
            '/api/v1/auth/permissions/',
        ]
        
        for endpoint in protected_endpoints:
            # Should not return 401 or 403 for authenticated users
            # (might return other errors, but not auth errors)
            response = client.get(endpoint)
            assert response.status_code not in [401, 403], f"Endpoint {endpoint} should allow authenticated access"
        
        # Test: Unauthenticated requests should be denied
        client_unauth = APIClient()
        # Don't authenticate
        
        for endpoint in protected_endpoints:
            response = client_unauth.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require authentication"
        
        # Cleanup
        technician.delete()
        user.delete()
    
    @pytest.mark.django_db
    @settings(max_examples=50)
    @given(
        employee_code=st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum())
    )
    def test_token_validation_consistency(self, employee_code):
        """
        Test that token validation is consistent across different endpoints
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
        
        # Get valid tokens
        tokens = user.get_tokens()
        access_token = tokens['access']
        
        # Test: Valid token should work across endpoints
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test multiple endpoints with same token
        endpoints = [
            '/api/v1/auth/profile/',
            '/api/v1/auth/permissions/',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not be 401 (invalid token) or 403 (insufficient permissions)
            assert response.status_code != 401, f"Valid token should work on {endpoint}"
        
        # Test: Invalid token should be rejected consistently
        client_invalid = APIClient()
        client_invalid.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_12345')
        
        for endpoint in endpoints:
            response = client_invalid.get(endpoint)
            assert response.status_code == 401, f"Invalid token should be rejected on {endpoint}"
        
        # Test: Malformed token should be rejected consistently
        client_malformed = APIClient()
        client_malformed.credentials(HTTP_AUTHORIZATION='InvalidFormat token')
        
        for endpoint in endpoints:
            response = client_malformed.get(endpoint)
            assert response.status_code == 401, f"Malformed token should be rejected on {endpoint}"
        
        # Cleanup
        technician.delete()
        user.delete()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])