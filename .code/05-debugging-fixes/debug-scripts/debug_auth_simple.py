#!/usr/bin/env python
"""
Simple authentication debug script.
This script checks the current authentication state and token handling.
"""
import os
import sys
import django

# Setup Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.contrib.auth.models import User
from frontend.services import AuthenticationService, ForgeAPIClient

def check_user_and_tokens():
    """Check user existence and token handling."""
    print("🔍 Checking User and Token Status")
    print("=" * 50)
    
    # Check if demo user exists
    try:
        user = User.objects.get(username='demo')
        print(f"✅ Demo user exists: {user.username} ({user.email})")
        print(f"   - Is active: {user.is_active}")
        print(f"   - Is staff: {user.is_staff}")
        print(f"   - Last login: {user.last_login}")
    except User.DoesNotExist:
        print("❌ Demo user does not exist")
        print("Creating demo user...")
        user = User.objects.create_user(
            username='demo',
            password='demo123',
            email='demo@example.com'
        )
        print(f"✅ Created demo user: {user.username}")
    
    # Check authentication service
    print(f"\n📡 API Base URL Configuration:")
    auth_service = AuthenticationService()
    print(f"   - API Base URL: {auth_service.api_base_url}")
    
    # Check if we can create API client
    print(f"\n🔧 API Client Configuration:")
    api_client = ForgeAPIClient()
    print(f"   - Base URL: {api_client.base_url}")
    print(f"   - Timeout: {api_client.timeout}")
    print(f"   - Max retries: {api_client.max_retries}")
    
    # Check current session headers
    print(f"   - Current headers: {dict(api_client.session.headers)}")
    
    return True

def check_api_connectivity():
    """Check if we can connect to the API."""
    print(f"\n🌐 Testing API Connectivity")
    print("=" * 30)
    
    api_client = ForgeAPIClient()
    
    # Test health check if available
    try:
        health_status = api_client.health_check()
        print(f"   - Health check: {'✅ OK' if health_status else '❌ Failed'}")
    except Exception as e:
        print(f"   - Health check error: {e}")
    
    # Test a simple GET request without authentication
    try:
        # This might fail due to authentication, but we can see the error
        response = api_client.get('dashboard/')
        print(f"   - Dashboard API: ✅ Success")
    except Exception as e:
        print(f"   - Dashboard API: ❌ {e}")
        if hasattr(e, 'status_code'):
            if e.status_code == 401:
                print("     (This is expected - authentication required)")
            else:
                print(f"     Status code: {e.status_code}")

def main():
    """Run simple authentication debug."""
    print("🔐 ForgeDB Simple Authentication Debug")
    print("Checking basic authentication setup...")
    
    try:
        check_user_and_tokens()
        check_api_connectivity()
        
        print("\n" + "=" * 50)
        print("🎯 Debug completed!")
        print("\n💡 Next steps to fix authentication:")
        print("   1. Make sure you're logged in through the web interface")
        print("   2. Check that JWT tokens are being stored in session")
        print("   3. Verify API endpoints are accessible")
        print("   4. Check CORS and authentication middleware")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)