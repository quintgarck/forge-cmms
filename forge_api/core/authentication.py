"""
ForgeDB API REST - Authentication System
Custom authentication backend and user model integration

This module provides custom authentication that integrates with the existing
cat.technicians table in ForgeDB.
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)


class TechnicianAuthBackend(BaseBackend):
    """
    Custom authentication backend that authenticates against the technicians table
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user using employee_code and password, or fallback to Django users
        """
        if username is None or password is None:
            return None
            
        try:
            # Import here to avoid circular imports
            from .models import Technician, TechnicianUser
            
            # First, try to find technician by employee_code
            try:
                technician = Technician.objects.get(
                    employee_code=username,
                    status='active'
                )
                
                # Try to get or create the corresponding user account
                user, created = TechnicianUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'technician': technician,
                        'email': technician.email,
                        'first_name': technician.first_name,
                        'last_name': technician.last_name,
                        'is_active': True,
                    }
                )
                
                # If user was just created, set a default password
                if created:
                    # For new users, use a default password pattern
                    # In production, this should be changed on first login
                    default_password = f"{username}@forge2024"
                    user.set_password(default_password)
                    user.save()
                    logger.info(f"Created new user account for technician {username}")
                
                # Check password
                if user.check_password(password):
                    # Update user info from technician if needed
                    if user.email != technician.email:
                        user.email = technician.email
                        user.save()
                    
                    logger.info(f"Successful authentication for technician user {username}")
                    return user
                else:
                    logger.warning(f"Failed password check for technician user {username}")
                    
            except Technician.DoesNotExist:
                # If no technician found, this backend doesn't handle this user
                # Let Django's ModelBackend handle it
                logger.debug(f"No technician found for username {username}, letting Django backend handle it")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error for {username}: {str(e)}")
            
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            from .models import TechnicianUser
            return TechnicianUser.objects.get(pk=user_id)
        except:
            return None


# Custom Permission Classes for DRF

class IsWorkshopAdmin(BasePermission):
    """
    Permission class for workshop administrators
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff)
        )


class CanManageInventory(BasePermission):
    """
    Permission class for inventory management
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff or
             request.user.has_perm('core.manage_inventory'))
        )


class CanManageClients(BasePermission):
    """
    Permission class for client management
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff or
             request.user.has_perm('core.manage_clients'))
        )


class CanViewReports(BasePermission):
    """
    Permission class for viewing reports
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.is_staff or
             request.user.has_perm('core.view_reports'))
        )


class IsTechnicianOrReadOnly(BasePermission):
    """
    Permission class that allows technicians to modify their own work orders
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only for the assigned technician or admins
        if hasattr(obj, 'assigned_technician'):
            return (
                request.user.is_superuser or request.user.is_staff or
                (obj.assigned_technician and
                 obj.assigned_technician.technician_id == getattr(request.user.technician, 'technician_id', None))
            )

        # For objects created by technicians
        if hasattr(obj, 'created_by'):
            return (
                request.user.is_superuser or request.user.is_staff or
                (obj.created_by and
                 obj.created_by.technician_id == getattr(request.user.technician, 'technician_id', None))
            )

        return request.user.is_superuser or request.user.is_staff


def create_user_for_technician(technician, password=None):
    """
    Utility function to create a user account for an existing technician
    """
    from .models import TechnicianUser
    
    if password is None:
        password = f"{technician.employee_code}@forge2024"
    
    user = TechnicianUser.objects.create_user(
        username=technician.employee_code,
        email=technician.email,
        password=password,
        first_name=technician.first_name,
        last_name=technician.last_name,
        technician=technician
    )
    
    return user


def setup_default_permissions():
    """
    Setup default permissions and groups for the workshop system
    """
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Create groups
    admin_group, _ = Group.objects.get_or_create(name='Workshop Administrators')
    manager_group, _ = Group.objects.get_or_create(name='Workshop Managers')
    technician_group, _ = Group.objects.get_or_create(name='Technicians')
    viewer_group, _ = Group.objects.get_or_create(name='Viewers')
    
    # Get content types for our models
    from . import models
    
    content_types = {
        'technician': ContentType.objects.get_for_model(models.Technician),
        'client': ContentType.objects.get_for_model(models.Client),
        'equipment': ContentType.objects.get_for_model(models.Equipment),
        'workorder': ContentType.objects.get_for_model(models.WorkOrder),
        'invoice': ContentType.objects.get_for_model(models.Invoice),
        'product': ContentType.objects.get_for_model(models.ProductMaster),
        'stock': ContentType.objects.get_for_model(models.Stock),
    }
    
    # Create custom permissions
    permissions = [
        ('manage_workshop', 'Can manage workshop operations'),
        ('manage_inventory', 'Can manage inventory'),
        ('manage_clients', 'Can manage clients'),
        ('view_reports', 'Can view reports'),
        ('manage_technicians', 'Can manage technicians'),
    ]
    
    for codename, name in permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_types['technician']
        )
    
    logger.info("Default permissions and groups created successfully")