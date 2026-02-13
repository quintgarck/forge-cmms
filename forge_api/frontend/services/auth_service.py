"""
Authentication Service for ForgeDB Frontend

This service handles user authentication, JWT token management,
session management, and user authorization.
"""
import requests
import logging
from typing import Dict, Any, Optional, Tuple, List
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import jwt
from .api_client import APIException

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class AuthenticationService:
    """
    Comprehensive authentication service for ForgeDB frontend.
    
    Features:
    - JWT token management with automatic refresh
    - Session management and persistence
    - User profile caching
    - Permission checking
    - Multi-factor authentication support (future)
    """
    
    def __init__(self, request=None):
        """
        Initialize the authentication service.
        
        Args:
            request: Django request object for session management.
        """
        self.request = request
        self.api_base_url = self._get_api_base_url()
        self.session_timeout = getattr(settings, 'SESSION_TIMEOUT', 3600)  # 1 hour
        
    def _get_api_base_url(self) -> str:
        """Get the base URL for API requests."""
        if self.request:
            scheme = 'https' if self.request.is_secure() else 'http'
            host = self.request.get_host()
            
            # Handle testserver in testing environment
            if host == 'testserver':
                host = 'localhost:8000'
            
            return f"{scheme}://{host}/api/v1/"
        return getattr(settings, 'API_BASE_URL', 'http://localhost:8000/api/v1/')
    
    def _get_user_cache_key(self, user_id: int) -> str:
        """Generate cache key for user data."""
        return f"forge_user:{user_id}"
    
    def _decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Decode JWT token to extract user information.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict containing token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            # Note: In production, you should verify the signature
            # For now, we'll decode without verification for development
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def _is_token_expired(self, token: str) -> bool:
        """
        Check if a JWT token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            bool: True if token is expired
        """
        try:
            payload = self._decode_jwt_token(token)
            exp_timestamp = payload.get('exp')
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                return datetime.now() >= exp_datetime
            
            return False
        except AuthenticationError:
            return True
    
    def _should_refresh_token(self, token: str, buffer_minutes: int = 5) -> bool:
        """
        Check if a token should be refreshed (is close to expiring).
        
        Args:
            token: JWT token string
            buffer_minutes: Minutes before expiration to trigger refresh
            
        Returns:
            bool: True if token should be refreshed
        """
        try:
            payload = self._decode_jwt_token(token)
            exp_timestamp = payload.get('exp')
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                buffer_time = timedelta(minutes=buffer_minutes)
                return datetime.now() >= (exp_datetime - buffer_time)
            
            return False
        except AuthenticationError:
            return True
    
    def _store_tokens(self, access_token: str, refresh_token: str, user_data: Dict = None):
        """
        Store authentication tokens in session.
        
        Args:
            access_token: JWT access token
            refresh_token: JWT refresh token
            user_data: Optional user data to cache
        """
        if not self.request or not hasattr(self.request, 'session'):
            logger.warning("No request or session available for token storage")
            return
        
        try:
            # Store tokens in session
            self.request.session['auth_token'] = access_token
            self.request.session['refresh_token'] = refresh_token
            self.request.session['token_timestamp'] = datetime.now().isoformat()
            
            # Store user data if provided
            if user_data:
                self.request.session['user_data'] = user_data
                
                # Cache user data
                user_id = user_data.get('user_id') or user_data.get('id')
                if user_id:
                    cache_key = self._get_user_cache_key(user_id)
                    cache.set(cache_key, user_data, self.session_timeout)
            
            # Set session expiry - only if session supports it
            if hasattr(self.request.session, 'set_expiry'):
                self.request.session.set_expiry(self.session_timeout)
            
            # Force session save to ensure persistence
            if hasattr(self.request.session, 'save'):
                self.request.session.save()
                
            logger.debug(f"Tokens stored successfully in session {self.request.session.session_key}")
                
        except Exception as e:
            logger.error(f"Could not store tokens in session: {e}")
            # Continue without session storage
    
    def _clear_tokens(self):
        """Clear authentication tokens from session."""
        if not self.request or not hasattr(self.request, 'session'):
            return
        
        try:
            # Clear session data
            session_keys = ['auth_token', 'refresh_token', 'token_timestamp', 'user_data']
            for key in session_keys:
                self.request.session.pop(key, None)
            
            # Clear user cache if we have user data
            user_data = self.request.session.get('user_data')
            if user_data:
                user_id = user_data.get('user_id') or user_data.get('id')
                if user_id:
                    cache_key = self._get_user_cache_key(user_id)
                    cache.delete(cache_key)
                    
        except Exception as e:
            logger.warning(f"Could not clear tokens from session: {e}")
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Dict]:
        """
        Authenticate user and establish session.
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            Tuple of (success, message, user_data)
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # First, authenticate with Django's auth system
            django_user = authenticate(self.request, username=username, password=password)
            
            if django_user is None:
                return False, "Credenciales inválidas", {}
            
            # Login the user in Django
            if self.request:
                login(self.request, django_user)
            
            
            # Get JWT tokens from the API
            try:
                logger.info(f"Attempting to get JWT tokens from {self.api_base_url}auth/login/")
                api_response = requests.post(
                    f"{self.api_base_url}auth/login/",
                    json={
                        'username': username,
                        'password': password
                    },
                    timeout=30
                )
                logger.info(f"JWT token request response: {api_response.status_code}")
                if api_response.status_code == 200:
                    token_data = api_response.json()
                    access_token = token_data.get('access')
                    refresh_token = token_data.get('refresh')
                    
                    if access_token and refresh_token:
                        # Decode token to get user info
                        try:
                            token_payload = self._decode_jwt_token(access_token)
                            user_data = {
                                'user_id': token_payload.get('user_id'),
                                'username': django_user.username,
                                'email': django_user.email,
                                'first_name': django_user.first_name,
                                'last_name': django_user.last_name,
                                'is_staff': django_user.is_staff,
                                'is_superuser': django_user.is_superuser,
                                'groups': [group.name for group in django_user.groups.all()],
                                'permissions': list(django_user.get_all_permissions()),
                                'token_exp': token_payload.get('exp'),
                            }
                        except AuthenticationError:
                            # If we can't decode the token, use basic user data
                            user_data = {
                                'username': django_user.username,
                                'email': django_user.email,
                                'first_name': django_user.first_name,
                                'last_name': django_user.last_name,
                                'is_staff': django_user.is_staff,
                                'is_superuser': django_user.is_superuser,
                            }
                        
                        # Store tokens and user data
                        self._store_tokens(access_token, refresh_token, user_data)
                        
                        logger.info(f"User {username} logged in successfully")
                        return True, f"Bienvenido, {django_user.get_full_name() or django_user.username}!", user_data
                    
                elif api_response.status_code == 401:
                    return False, "Credenciales inválidas para la API", {}
                else:
                    logger.warning(f"API login failed with status {api_response.status_code}")
                    # Continue with Django-only authentication
                    
            except requests.RequestException as e:
                logger.warning(f"API login request failed: {e}")
                # Continue with Django-only authentication
            
            # Fallback: Django authentication without API tokens
            user_data = {
                'username': django_user.username,
                'email': django_user.email,
                'first_name': django_user.first_name,
                'last_name': django_user.last_name,
                'is_staff': django_user.is_staff,
                'is_superuser': django_user.is_superuser,
            }
            
            if self.request:
                self.request.session['user_data'] = user_data
            
            logger.info(f"User {username} logged in (Django only)")
            return True, f"Bienvenido, {django_user.get_full_name() or django_user.username}!", user_data
            
        except Exception as e:
            logger.error(f"Login error for user {username}: {e}")
            raise AuthenticationError(f"Error durante el login: {str(e)}")
    
    def logout(self) -> bool:
        """
        Logout user and clear session.
        
        Returns:
            bool: True if logout was successful
        """
        try:
            # Attempt to invalidate JWT token on the server
            refresh_token = self.request.session.get('refresh_token') if self.request else None
            
            if refresh_token:
                try:
                    requests.post(
                        f"{self.api_base_url}auth/logout/",
                        json={'refresh': refresh_token},
                        timeout=10
                    )
                except requests.RequestException:
                    # Ignore API logout errors
                    pass
            
            # Clear tokens and session data
            self._clear_tokens()
            
            # Django logout
            if self.request:
                logout(self.request)
            
            logger.info("User logged out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def refresh_token(self) -> bool:
        """
        Refresh the JWT access token using the refresh token.
        
        Returns:
            bool: True if token was refreshed successfully
        """
        if not self.request:
            logger.warning("No request available for token refresh")
            return False
        
        refresh_token = self.request.session.get('refresh_token')
        if not refresh_token:
            logger.warning("No refresh token available in session")
            return False
        
        try:
            logger.debug(f"Attempting to refresh token using refresh token: {refresh_token[:30]}...")
            
            response = requests.post(
                f"{self.api_base_url}auth/refresh/",
                json={'refresh': refresh_token},
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            logger.debug(f"Token refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get('access')
                new_refresh_token = token_data.get('refresh', refresh_token)
                
                if new_access_token:
                    # Update tokens in session
                    self.request.session['auth_token'] = new_access_token
                    self.request.session['refresh_token'] = new_refresh_token
                    self.request.session['token_timestamp'] = datetime.now().isoformat()
                    
                    # Force session save
                    if hasattr(self.request.session, 'save'):
                        self.request.session.save()
                    
                    logger.info("JWT token refreshed successfully")
                    return True
                else:
                    logger.error("No access token in refresh response")
                    return False
            elif response.status_code == 401:
                logger.warning("Refresh token is invalid or expired")
                # Clear invalid tokens
                self._clear_tokens()
                return False
            else:
                logger.warning(f"Token refresh failed with status {response.status_code}: {response.text}")
                return False
            
        except requests.RequestException as e:
            logger.error(f"Token refresh network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Token refresh unexpected error: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if the user is currently authenticated.
        
        Returns:
            bool: True if user is authenticated
        """
        if not self.request:
            return False
        
        # Check Django authentication
        if not self.request.user.is_authenticated:
            return False
        
        # Check JWT token if available
        token = self.request.session.get('auth_token')
        if token:
            # Check if token is expired
            if self._is_token_expired(token):
                logger.debug("Token is expired, attempting refresh")
                # Token expired, try to refresh
                if self.refresh_token():
                    return True
                else:
                    # Refresh failed, clear tokens
                    logger.warning("Token refresh failed, clearing session")
                    self._clear_tokens()
                    return False
            
            # Check if token should be refreshed proactively
            elif self._should_refresh_token(token):
                logger.debug("Token is close to expiring, proactively refreshing")
                # Token is close to expiring, refresh proactively
                self.refresh_token()  # Don't fail if this doesn't work
            
            return True
        
        # Django authentication without JWT is still valid
        return True
    
    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current user data.
        
        Returns:
            Dict containing user data or None if not authenticated
        """
        if not self.is_authenticated():
            return None
        
        # Try to get from session first
        if self.request:
            user_data = self.request.session.get('user_data')
            if user_data:
                return user_data
        
        # Fallback to Django user
        if self.request and self.request.user.is_authenticated:
            django_user = self.request.user
            return {
                'username': django_user.username,
                'email': django_user.email,
                'first_name': django_user.first_name,
                'last_name': django_user.last_name,
                'is_staff': django_user.is_staff,
                'is_superuser': django_user.is_superuser,
            }
        
        return None
    
    def get_auth_token(self) -> Optional[str]:
        """
        Get the current JWT access token.
        
        Returns:
            str: JWT access token or None if not available
        """
        if not self.request:
            return None
        
        return self.request.session.get('auth_token')
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if the current user has a specific permission.
        
        Args:
            permission: Permission string (e.g., 'core.add_client')
            
        Returns:
            bool: True if user has the permission
        """
        if not self.is_authenticated():
            return False
        
        if self.request and self.request.user.is_authenticated:
            return self.request.user.has_perm(permission)
        
        return False
    
    def is_staff(self) -> bool:
        """
        Check if the current user is staff.
        
        Returns:
            bool: True if user is staff
        """
        user_data = self.get_user_data()
        return user_data.get('is_staff', False) if user_data else False
    
    def is_superuser(self) -> bool:
        """
        Check if the current user is a superuser.
        
        Returns:
            bool: True if user is superuser
        """
        user_data = self.get_user_data()
        return user_data.get('is_superuser', False) if user_data else False
    
    def get_user_groups(self) -> List[str]:
        """
        Get the current user's groups.
        
        Returns:
            List of group names
        """
        user_data = self.get_user_data()
        return user_data.get('groups', []) if user_data else []
    
    def in_group(self, group_name: str) -> bool:
        """
        Check if the current user is in a specific group.
        
        Args:
            group_name: Name of the group
            
        Returns:
            bool: True if user is in the group
        """
        return group_name in self.get_user_groups()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            Dict containing session information
        """
        if not self.request:
            return {}
        
        token_timestamp = self.request.session.get('token_timestamp')
        token_age = None
        
        if token_timestamp:
            try:
                token_time = datetime.fromisoformat(token_timestamp)
                token_age = (datetime.now() - token_time).total_seconds()
            except ValueError:
                pass
        
        return {
            'is_authenticated': self.is_authenticated(),
            'has_jwt_token': bool(self.get_auth_token()),
            'token_age_seconds': token_age,
            'session_key': self.request.session.session_key,
            'user_data': self.get_user_data(),
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired user sessions from cache."""
        # This would typically be called by a management command or celery task
        # For now, it's a placeholder for future implementation
        pass