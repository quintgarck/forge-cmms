"""
ForgeDB API REST - Custom Permissions
Custom permission classes for the workshop management system
"""

from rest_framework.permissions import BasePermission
from .authentication import (
    IsWorkshopAdmin,
    CanManageInventory,
    CanManageClients,
    CanViewReports,
    IsTechnicianOrReadOnly
)

# Re-export permissions from authentication module for convenience
__all__ = [
    'IsWorkshopAdmin',
    'CanManageInventory', 
    'CanManageClients',
    'CanViewReports',
    'IsTechnicianOrReadOnly'
]