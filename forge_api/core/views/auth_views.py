"""
ForgeDB API REST - Authentication Views
JWT-based authentication endpoints for the workshop management system
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from ..authentication import create_user_for_technician
from ..models import Technician, TechnicianUser
from ..serializers.auth_serializers import (
    LoginSerializer, 
    UserProfileSerializer, 
    ChangePasswordSerializer,
    TokenResponseSerializer
)

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view that works with our technician authentication
    """
    serializer_class = LoginSerializer
    
    @swagger_auto_schema(
        operation_description="Obtain JWT tokens using employee code and password",
        request_body=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            401: 'Invalid credentials',
            400: 'Bad request'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.warning(f"Login validation failed: {str(e)}")
            return Response(
                {'error': 'Invalid credentials provided'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        # Log successful login
        logger.info(f"Successful login for user {user.username}")
        
        # Build response data - handle both TechnicianUser and regular User
        response_data = {
            'access': str(access),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name() if hasattr(user, 'get_full_name') else f"{user.first_name} {user.last_name}".strip(),
            }
        }
        
        # Add role and permissions if it's a TechnicianUser
        if hasattr(user, 'role'):
            response_data['user'].update({
                'role': user.role,
                'permissions': {
                    'is_workshop_admin': getattr(user, 'is_workshop_admin', user.is_superuser),
                    'can_manage_inventory': getattr(user, 'can_manage_inventory', user.is_staff),
                    'can_manage_clients': getattr(user, 'can_manage_clients', user.is_staff),
                    'can_view_reports': getattr(user, 'can_view_reports', True),
                }
            })
        else:
            # For regular Django users (like admin)
            response_data['user'].update({
                'role': 'admin' if user.is_superuser else 'staff' if user.is_staff else 'user',
                'permissions': {
                    'is_workshop_admin': user.is_superuser,
                    'can_manage_inventory': user.is_staff or user.is_superuser,
                    'can_manage_clients': user.is_staff or user.is_superuser,
                    'can_view_reports': True,
                }
            })
        
        return Response(response_data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Refresh JWT access token",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access': openapi.Schema(type=openapi.TYPE_STRING, description='New access token')
            }
        ),
        401: 'Invalid or expired refresh token'
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh JWT access token using refresh token
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        return Response({
            'access': access_token
        }, status=status.HTTP_200_OK)
        
    except TokenError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        return Response(
            {'error': 'Invalid or expired refresh token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


@swagger_auto_schema(
    method='post',
    operation_description="Logout user by blacklisting refresh token",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist')
        }
    ),
    responses={
        200: 'Successfully logged out',
        400: 'Bad request'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting the refresh token
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        logger.info(f"User {request.user.username} logged out successfully")
        return Response(
            {'message': 'Successfully logged out'}, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Logout error for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Logout failed'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@swagger_auto_schema(
    method='get',
    operation_description="Get current user profile information",
    responses={
        200: UserProfileSerializer,
        401: 'Authentication required'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile information
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='put',
    operation_description="Update user profile information",
    request_body=UserProfileSerializer,
    responses={
        200: UserProfileSerializer,
        400: 'Validation error',
        401: 'Authentication required'
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile information
    """
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Profile updated for user {request.user.username}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Change user password",
    request_body=ChangePasswordSerializer,
    responses={
        200: 'Password changed successfully',
        400: 'Validation error',
        401: 'Authentication required'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        user = request.user
        
        # Check current password
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password
        try:
            validate_password(serializer.validated_data['new_password'], user)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(f"Password changed for user {user.username}")
        return Response(
            {'message': 'Password changed successfully'}, 
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_description="Check if user has specific permission",
    manual_parameters=[
        openapi.Parameter(
            'permission',
            openapi.IN_QUERY,
            description="Permission to check (manage_inventory, manage_clients, view_reports)",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'has_permission': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        ),
        400: 'Permission parameter required',
        401: 'Authentication required'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_permission(request):
    """
    Check if current user has a specific permission
    """
    permission = request.query_params.get('permission')
    
    if not permission:
        return Response(
            {'error': 'Permission parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    has_permission = request.user.has_workshop_permission(permission)
    
    return Response({
        'permission': permission,
        'has_permission': has_permission
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Get all user permissions",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'permissions': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'is_workshop_admin': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'can_manage_inventory': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'can_manage_clients': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'can_view_reports': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    }
                )
            }
        ),
        401: 'Authentication required'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions(request):
    """
    Get all permissions for the current user
    """
    permissions = {
        'is_workshop_admin': request.user.is_workshop_admin,
        'can_manage_inventory': request.user.can_manage_inventory,
        'can_manage_clients': request.user.can_manage_clients,
        'can_view_reports': request.user.can_view_reports,
        'role': request.user.role,
    }
    
    return Response({
        'permissions': permissions
    }, status=status.HTTP_200_OK)