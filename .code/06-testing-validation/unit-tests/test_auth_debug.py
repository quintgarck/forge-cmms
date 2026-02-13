#!/usr/bin/env python
"""
Debug script for authentication issues.
This script helps debug JWT token and authentication problems.
"""
import os
import sys
import django

# Setup Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from frontend.services import AuthenticationService, ForgeAPIClient

def test_authentication_flow():
    """Test the complete authentication flow."""
    print("🔍 Testing Authentication Flow")
    print("=" * 50)
    
    client = Client()
    
    # Step 1: Create or get test user
    print("\n1. Setting up test user...")
    try:
        user = User.objects.get(username='demo')
        print(f"   ✅ Found existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='demo',
            password='demo123',
            email='demo@example.com'
        )
        print(f"   ✅ Created new user: {user.username}")
    
    # Step 2: Test login
    print("\n2. Testing login...")
    login_response = client.post(reverse('frontend:login'), {
        'username': 'demo',
        'password': 'demo123'
    })
    
    if login_response.status_code == 302:  # Redirect after successful login
        print("   ✅ Login successful (redirected)")
    else:
        print(f"   ❌ Login failed with status {login_response.status_code}")
        return False
    
    # Step 3: Check session data
    print("\n3. Checking session data...")
    session = client.session
    
    auth_token = session.get('auth_token')
    refresh_token = session.get('refresh_token')
    user_data = session.get('user_data')
    
    print(f"   Auth token present: {'✅' if auth_token else '❌'}")
    print(f"   Refresh token present: {'✅' if refresh_token else '❌'}")
    print(f"   User data present: {'✅' if user_data else '❌'}")
    
    if auth_token:
        print(f"   Auth token (first 20 chars): {auth_token[:20]}...")
    
    # Step 4: Test API client with session
    print("\n4. Testing API client...")
    
    # Create a mock request object with session
    class MockRequest:
        def __init__(self, session):
            self.session = session
            self.user = user
        
        def is_secure(self):
            return False
        
        def get_host(self):
            return 'localhost:8000'
    
    mock_request = MockRequest(session)
    api_client = ForgeAPIClient(request=mock_request)
    
    # Check if auth headers are set
    auth_header = api_client.session.headers.get('Authorization')
    print(f"   API client auth header: {'✅' if auth_header else '❌'}")
    
    if auth_header:
        print(f"   Auth header: {auth_header[:30]}...")
    
    # Step 5: Test API call
    print("\n5. Testing API call...")
    try:
        # This should work if authentication is properly set up
        dashboard_data = api_client.get('dashboard/')
        print("   ✅ API call successful")
        print(f"   Response keys: {list(dashboard_data.keys())}")
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        
        # Try to get more details about the error
        if hasattr(e, 'status_code'):
            print(f"   Status code: {e.status_code}")
        if hasattr(e, 'response_data'):
            print(f"   Response data: {e.response_data}")
    
    # Step 6: Test client creation (the failing operation)
    print("\n6. Testing client creation...")
    try:
        test_client_data = {
            'name': 'Test Client Debug',
            'email': 'test@debug.com',
            'phone': '5551234567',
            'address': 'Test Address',
            'credit_limit': 1000.00
        }
        
        result = api_client.create_client(test_client_data)
        print("   ✅ Client creation successful")
        print(f"   Created client ID: {result.get('id')}")
        
    except Exception as e:
        print(f"   ❌ Client creation failed: {e}")
        
        # Try to get more details about the error
        if hasattr(e, 'status_code'):
            print(f"   Status code: {e.status_code}")
        if hasattr(e, 'response_data'):
            print(f"   Response data: {e.response_data}")
    
    return True

def test_manual_token_refresh():
    """Test manual token refresh."""
    print("\n🔄 Testing Manual Token Refresh")
    print("=" * 50)
    
    client = Client()
    
    # Login first
    client.post(reverse('frontend:login'), {
        'username': 'demo',
        'password': 'demo123'
    })
    
    session = client.session
    
    # Create mock request and auth service
    class MockRequest:
        def __init__(self, session):
            self.session = session
        
        def is_secure(self):
            return False
        
        def get_host(self):
            return 'localhost:8000'
    
    mock_request = MockRequest(session)
    auth_service = AuthenticationService(mock_request)
    
    print(f"Initial auth token: {'✅' if session.get('auth_token') else '❌'}")
    
    # Try to refresh token
    refresh_success = auth_service.refresh_token()
    print(f"Token refresh result: {'✅' if refresh_success else '❌'}")
    
    if refresh_success:
        new_token = session.get('auth_token')
        print(f"New auth token: {'✅' if new_token else '❌'}")

def main():
    """Run authentication debug tests."""
    print("🔐 ForgeDB Authentication Debug Suite")
    print("Debugging JWT token and authentication issues...")
    
    try:
        success = test_authentication_flow()
        
        if success:
            test_manual_token_refresh()
        
        print("\n" + "=" * 50)
        print("🎯 Debug session completed!")
        print("\nIf you're still seeing authentication errors, check:")
        print("   • API server is running and accessible")
        print("   • JWT tokens are being generated correctly")
        print("   • Session middleware is properly configured")
        print("   • CORS settings allow credentials")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Debug session failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)