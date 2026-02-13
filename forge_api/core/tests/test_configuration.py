"""
Property-based tests for Django project configuration.

**Feature: forge-api-rest, Property 1: Authentication token issuance consistency**

This module tests the core configuration properties of the ForgeDB API REST project
to ensure consistent behavior across different configurations and inputs.
"""

import os
import django
from django.test import TestCase, override_settings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from hypothesis import given, strategies as st, settings as hypothesis_settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User


class ProjectConfigurationPropertyTests(TestCase):
    """
    Property-based tests for Django project configuration.
    
    **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
    **Validates: Requirements 1.1**
    
    These tests verify that the Django project configuration behaves consistently
    across different valid configuration scenarios.
    """
    
    def test_required_settings_exist(self):
        """Test that all required Django settings are properly configured."""
        required_settings = [
            'SECRET_KEY',
            'DEBUG',
            'ALLOWED_HOSTS',
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'ROOT_URLCONF',
            'DATABASES',
            'REST_FRAMEWORK',
            'SIMPLE_JWT',
        ]
        
        for setting_name in required_settings:
            with self.subTest(setting=setting_name):
                self.assertTrue(
                    hasattr(settings, setting_name),
                    f"Required setting {setting_name} is missing"
                )
                self.assertIsNotNone(
                    getattr(settings, setting_name),
                    f"Required setting {setting_name} is None"
                )
    
    def test_installed_apps_configuration(self):
        """Test that all required apps are properly installed."""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'rest_framework_simplejwt',
            'drf_yasg',
            'django_filters',
            'corsheaders',
            'core',
        ]
        
        for app in required_apps:
            with self.subTest(app=app):
                self.assertIn(
                    app, 
                    settings.INSTALLED_APPS,
                    f"Required app {app} is not installed"
                )
    
    def test_database_configuration(self):
        """Test that database configuration is valid."""
        db_config = settings.DATABASES['default']
        
        # Test required database settings
        required_db_keys = ['ENGINE', 'NAME', 'USER', 'HOST', 'PORT']
        for key in required_db_keys:
            with self.subTest(db_key=key):
                self.assertIn(key, db_config, f"Database setting {key} is missing")
        
        # Test PostgreSQL engine
        self.assertEqual(
            db_config['ENGINE'],
            'django.db.backends.postgresql',
            "Database engine should be PostgreSQL"
        )
        
        # Test database name (in tests, Django prefixes with 'test_')
        expected_db_name = 'forge_db'
        actual_db_name = db_config['NAME']
        
        # In test environment, Django may prefix with 'test_'
        if actual_db_name.startswith('test_'):
            expected_db_name = 'test_forge_db'
        
        self.assertEqual(
            actual_db_name,
            expected_db_name,
            f"Database name should be '{expected_db_name}'"
        )
    
    def test_rest_framework_configuration(self):
        """Test that Django REST Framework is properly configured."""
        drf_config = settings.REST_FRAMEWORK
        
        # Test authentication classes
        self.assertIn(
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            drf_config['DEFAULT_AUTHENTICATION_CLASSES']
        )
        
        # Test permission classes
        self.assertIn(
            'rest_framework.permissions.IsAuthenticated',
            drf_config['DEFAULT_PERMISSION_CLASSES']
        )
        
        # Test pagination
        self.assertIn('DEFAULT_PAGINATION_CLASS', drf_config)
        self.assertIn('PAGE_SIZE', drf_config)
        self.assertEqual(drf_config['PAGE_SIZE'], 20)
    
    def test_jwt_configuration(self):
        """Test that JWT configuration is valid."""
        jwt_config = settings.SIMPLE_JWT
        
        # Test required JWT settings
        required_jwt_keys = [
            'ACCESS_TOKEN_LIFETIME',
            'REFRESH_TOKEN_LIFETIME',
            'ROTATE_REFRESH_TOKENS',
            'BLACKLIST_AFTER_ROTATION',
        ]
        
        for key in required_jwt_keys:
            with self.subTest(jwt_key=key):
                self.assertIn(key, jwt_config, f"JWT setting {key} is missing")
        
        # Test token lifetimes are reasonable
        self.assertGreater(
            jwt_config['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            0,
            "Access token lifetime should be positive"
        )
        self.assertGreater(
            jwt_config['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            jwt_config['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            "Refresh token should live longer than access token"
        )


class AuthenticationTokenPropertyTests(HypothesisTestCase):
    """
    Property-based tests for JWT authentication token issuance.
    
    **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
    **Validates: Requirements 1.1**
    
    These tests verify that authentication tokens are issued consistently
    for valid credentials across different user scenarios.
    """
    
    def setUp(self):
        """Set up test data."""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        self.test_user = User.objects.create_user(
            username=f'testuser_{unique_suffix}',
            email=f'test_{unique_suffix}@example.com',
            password='testpass123'
        )
    
    @hypothesis_settings(max_examples=10, deadline=None)  # Disable deadline for this test
    @given(
        username=st.text(min_size=1, max_size=150, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), 
            whitelist_characters='_-'
        )),
        password=st.text(min_size=8, max_size=128)
    )
    def test_token_issuance_consistency(self, username, password):
        """
        Property: For any valid user credentials, the system should consistently
        issue JWT tokens with proper structure and claims.
        
        **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
        **Validates: Requirements 1.1**
        """
        # Create a user with the generated credentials
        try:
            user = User.objects.create_user(
                username=username,
                password=password
            )
        except Exception:
            # Skip invalid usernames (Django validation)
            return
        
        # Generate tokens for the user
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Test token properties
        self.assertIsNotNone(refresh, "Refresh token should be generated")
        self.assertIsNotNone(access_token, "Access token should be generated")
        
        # Test token structure
        self.assertIsInstance(str(refresh), str, "Refresh token should be string")
        self.assertIsInstance(str(access_token), str, "Access token should be string")
        
        # Test token claims
        self.assertEqual(
            refresh['user_id'], 
            user.id, 
            "Refresh token should contain correct user_id"
        )
        self.assertEqual(
            access_token['user_id'], 
            user.id, 
            "Access token should contain correct user_id"
        )
        
        # Test token types
        self.assertEqual(
            refresh['token_type'], 
            'refresh', 
            "Refresh token should have correct type"
        )
        self.assertEqual(
            access_token['token_type'], 
            'access', 
            "Access token should have correct type"
        )
        
        # Cleanup
        user.delete()
    
    def test_token_issuance_for_existing_user(self):
        """
        Test that tokens are consistently issued for existing valid users.
        
        **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
        **Validates: Requirements 1.1**
        """
        # Generate tokens multiple times for the same user
        tokens_set1 = RefreshToken.for_user(self.test_user)
        tokens_set2 = RefreshToken.for_user(self.test_user)
        
        # Tokens should be different (new tokens each time)
        self.assertNotEqual(
            str(tokens_set1), 
            str(tokens_set2),
            "Each token generation should produce unique tokens"
        )
        
        # But user_id should be consistent
        self.assertEqual(
            tokens_set1['user_id'],
            tokens_set2['user_id'],
            "User ID should be consistent across token generations"
        )
        self.assertEqual(
            tokens_set1['user_id'],
            self.test_user.id,
            "Token should contain correct user ID"
        )
    
    def test_token_structure_consistency(self):
        """
        Test that all generated tokens have consistent structure.
        
        **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
        **Validates: Requirements 1.1**
        """
        refresh = RefreshToken.for_user(self.test_user)
        access = refresh.access_token
        
        # Test required claims exist
        required_refresh_claims = ['user_id', 'token_type', 'exp', 'iat', 'jti']
        required_access_claims = ['user_id', 'token_type', 'exp', 'iat']
        
        for claim in required_refresh_claims:
            with self.subTest(claim=claim, token_type='refresh'):
                self.assertIn(
                    claim, 
                    refresh, 
                    f"Refresh token should contain {claim} claim"
                )
        
        for claim in required_access_claims:
            with self.subTest(claim=claim, token_type='access'):
                self.assertIn(
                    claim, 
                    access, 
                    f"Access token should contain {claim} claim"
                )
        
        # Test token expiration times are in the future
        import time
        current_time = int(time.time())
        
        self.assertGreater(
            refresh['exp'],
            current_time,
            "Refresh token expiration should be in the future"
        )
        self.assertGreater(
            access['exp'],
            current_time,
            "Access token expiration should be in the future"
        )


class ConfigurationValidationTests(TestCase):
    """
    Tests for configuration validation and error handling.
    
    **Feature: forge-api-rest, Property 1: Authentication token issuance consistency**
    **Validates: Requirements 1.1**
    """
    
    def test_secret_key_validation(self):
        """Test that SECRET_KEY is properly configured."""
        self.assertIsNotNone(settings.SECRET_KEY, "SECRET_KEY should not be None")
        self.assertNotEqual(
            settings.SECRET_KEY, 
            '', 
            "SECRET_KEY should not be empty"
        )
        self.assertGreater(
            len(settings.SECRET_KEY), 
            20, 
            "SECRET_KEY should be reasonably long"
        )
    
    def test_debug_setting_type(self):
        """Test that DEBUG setting is boolean."""
        self.assertIsInstance(
            settings.DEBUG, 
            bool, 
            "DEBUG setting should be boolean"
        )
    
    def test_allowed_hosts_configuration(self):
        """Test that ALLOWED_HOSTS is properly configured."""
        self.assertIsInstance(
            settings.ALLOWED_HOSTS, 
            list, 
            "ALLOWED_HOSTS should be a list"
        )
        
        if not settings.DEBUG:
            self.assertGreater(
                len(settings.ALLOWED_HOSTS), 
                0, 
                "ALLOWED_HOSTS should not be empty in production"
            )