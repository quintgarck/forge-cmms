#!/usr/bin/env python3
"""
Simple script to test the login flow without emoji characters.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User


def create_admin_user():
    """Create admin user."""
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@forgedb.com',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("Created admin user")
    else:
        print("Admin user already exists")
    
    return admin_user


def test_login_flow():
    """Test the login flow."""
    print("Testing login flow")
    print("-" * 40)
    
    create_admin_user()
    django_client = Client()
    
    # Step 1: GET login form
    print("Step 1: Loading login form...")
    try:
        response = django_client.get('/login/')
        print(f"GET /login/: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to load login form")
            return False
            
    except Exception as e:
        print(f"Error loading login form: {e}")
        return False
    
    # Step 2: POST login credentials
    print("\nStep 2: Sending login credentials...")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = django_client.post('/login/', data=login_data, follow=True)
        print(f"POST /login/: {response.status_code}")
        
        # Check if redirected to dashboard (successful login)
        if response.status_code == 200:
            final_url = response.request['PATH_INFO']
            print(f"Final URL: {final_url}")
            
            if '/dashboard/' in final_url or final_url == '/':
                print("Login successful - redirected to dashboard")
            else:
                print("Login processed but not redirected to dashboard")
        
        # Step 3: Check session for JWT tokens
        print("\nStep 3: Checking tokens in session...")
        session = django_client.session
        
        auth_token = session.get('auth_token')
        refresh_token = session.get('refresh_token')
        user_data = session.get('user_data')
        token_timestamp = session.get('token_timestamp')
        
        print(f"Auth token: {'Present' if auth_token else 'Missing'}")
        print(f"Refresh token: {'Present' if refresh_token else 'Missing'}")
        print(f"User data: {'Present' if user_data else 'Missing'}")
        print(f"Token timestamp: {'Present' if token_timestamp else 'Missing'}")
        
        if auth_token:
            print(f"Token preview: {auth_token[:50]}...")
            
        if user_data:
            print(f"User: {user_data.get('username')} ({user_data.get('email')})")
        
        # Success if we have tokens
        has_tokens = bool(auth_token and refresh_token)
        return has_tokens
        
    except Exception as e:
        print(f"Error during login: {e}")
        return False


def main():
    """Main function."""
    print("Testing complete login flow")
    print("=" * 60)
    print("Objective: Use real frontend login views to get JWT tokens")
    print("=" * 60)
    
    login_success = test_login_flow()
    
    print("\n" + "=" * 60)
    if login_success:
        print("SUCCESS: Login flow working correctly")
        return 0
    else:
        print("FAILURE: Login flow has issues")
        return 1


if __name__ == '__main__':
    sys.exit(main())