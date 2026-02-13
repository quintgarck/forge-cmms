#!/usr/bin/env python
"""
Debug admin authentication specifically.
This script helps debug the admin authentication flow.
"""
import os
import sys
import django

# Setup Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import requests
import json

def test_admin_authentication():
    """Test admin authentication flow."""
    print("🔐 Testing Admin Authentication Flow")
    print("=" * 50)
    
    # Step 1: Test Django authentication
    print("\n1. Testing Django Authentication...")
    admin_user = authenticate(username='admin', password='admin123')
    if admin_user:
        print(f"   ✅ Django auth successful: {admin_user.username}")
        print(f"   - Is active: {admin_user.is_active}")
        print(f"   - Is staff: {admin_user.is_staff}")
        print(f"   - Is superuser: {admin_user.is_superuser}")
    else:
        print("   ❌ Django authentication failed")
        return False
    
    # Step 2: Test API authentication
    print("\n2. Testing API Authentication...")
    try:
        api_url = "http://localhost:8000/api/v1/auth/login/"
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = requests.post(api_url, json=login_data, timeout=10)
        print(f"   API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access')
            refresh_token = token_data.get('refresh')
            
            print(f"   ✅ API authentication successful")
            print(f"   - Access token: {'✅' if access_token else '❌'}")
            print(f"   - Refresh token: {'✅' if refresh_token else '❌'}")
            
            if access_token:
                print(f"   - Token preview: {access_token[:30]}...")
                
                # Step 3: Test API call with token
                print("\n3. Testing API Call with Token...")
                headers = {'Authorization': f'Bearer {access_token}'}
                
                try:
                    dashboard_response = requests.get(
                        "http://localhost:8000/api/v1/dashboard/",
                        headers=headers,
                        timeout=10
                    )
                    print(f"   Dashboard API Status: {dashboard_response.status_code}")
                    
                    if dashboard_response.status_code == 200:
                        print("   ✅ Dashboard API call successful")
                        dashboard_data = dashboard_response.json()
                        print(f"   - Response keys: {list(dashboard_data.keys())}")
                    else:
                        print(f"   ❌ Dashboard API call failed")
                        print(f"   - Response: {dashboard_response.text[:200]}")
                        
                except requests.RequestException as e:
                    print(f"   ❌ Dashboard API request failed: {e}")
                
                # Step 4: Test client creation with token
                print("\n4. Testing Client Creation with Token...")
                client_data = {
                    'name': 'Test Client API',
                    'email': 'testapi@client.com',
                    'phone': '5551234567',
                    'address': 'Test API Address',
                    'credit_limit': 1000.00
                }
                
                try:
                    client_response = requests.post(
                        "http://localhost:8000/api/v1/clients/",
                        headers=headers,
                        json=client_data,
                        timeout=10
                    )
                    print(f"   Client Creation Status: {client_response.status_code}")
                    
                    if client_response.status_code in [200, 201]:
                        print("   ✅ Client creation successful")
                        client_result = client_response.json()
                        print(f"   - Created client ID: {client_result.get('id')}")
                    else:
                        print(f"   ❌ Client creation failed")
                        print(f"   - Response: {client_response.text[:200]}")
                        
                except requests.RequestException as e:
                    print(f"   ❌ Client creation request failed: {e}")
            
        elif response.status_code == 401:
            print("   ❌ API authentication failed - Invalid credentials")
        elif response.status_code == 404:
            print("   ❌ API authentication endpoint not found")
            print("   - Check if the API server is running")
        else:
            print(f"   ❌ API authentication failed with status {response.status_code}")
            print(f"   - Response: {response.text[:200]}")
            
    except requests.RequestException as e:
        print(f"   ❌ API request failed: {e}")
        print("   - Make sure the server is running on http://localhost:8000")
        return False
    
    return True

def check_api_endpoints():
    """Check if API endpoints are accessible."""
    print("\n🌐 Checking API Endpoints")
    print("=" * 30)
    
    endpoints = [
        "http://localhost:8000/api/v1/",
        "http://localhost:8000/api/v1/auth/login/",
        "http://localhost:8000/api/v1/clients/",
        "http://localhost:8000/api/v1/dashboard/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            status = "✅" if response.status_code in [200, 401, 403] else "❌"
            print(f"   {status} {endpoint} - Status: {response.status_code}")
        except requests.RequestException as e:
            print(f"   ❌ {endpoint} - Error: {e}")

def main():
    """Run admin authentication debug."""
    print("🔐 ForgeDB Admin Authentication Debug")
    print("Debugging admin authentication and API access...")
    
    try:
        success = test_admin_authentication()
        check_api_endpoints()
        
        print("\n" + "=" * 50)
        print("🎯 Admin Authentication Debug Completed!")
        
        if success:
            print("\n✅ Authentication appears to be working correctly")
            print("\n💡 If you're still having issues in the web interface:")
            print("   1. Clear your browser cache and cookies")
            print("   2. Try logging out and logging back in")
            print("   3. Check the browser's developer console for errors")
            print("   4. Verify the session is being maintained")
        else:
            print("\n❌ Authentication issues detected")
            print("\n🔧 Troubleshooting steps:")
            print("   1. Ensure the API server is running")
            print("   2. Check database connectivity")
            print("   3. Verify JWT settings in Django settings")
            print("   4. Check CORS configuration")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)