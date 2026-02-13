#!/usr/bin/env python
"""
Debug script to test category creation functionality
"""
import os
import sys
import django
from django.test import Client
from django.urls import reverse

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'forge_api'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Category

def test_category_creation():
    print("=== Debugging Category Creation ===")
    
    # Create test user if doesn't exist
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created or not user.check_password('testpass123'):
        user.set_password('testpass123')
        user.save()
        print("Created/Updated test user: testuser / testpass123")
    else:
        print("Using existing test user")
    
    # Create test client
    client = Client()
    
    # Login
    login_success = client.login(username='testuser', password='testpass123')
    print(f"Login successful: {login_success}")
    
    if not login_success:
        print("Login failed!")
        return
    
    # Test accessing category list page
    print("\n--- Testing Category List Page ---")
    response = client.get('/catalog/categories/')
    print(f"Category list status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content.decode()[:500]}")
    
    # Test accessing category create page
    print("\n--- Testing Category Create Page ---")
    response = client.get('/catalog/categories/create/')
    print(f"Category create page status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content.decode()[:500]}")
    
    # Test creating a category via POST
    print("\n--- Testing Category Creation via POST ---")
    import random
    test_code = f'TEST{random.randint(1000, 9999)}'
    category_data = {
        'category_code': test_code,
        'name': 'Test Category',
        'description': 'Test category for debugging',
        'icon': 'bi-test',
        'color': '#ff0000',
        'sort_order': 999,
        'is_active': 'on'
    }
    
    response = client.post('/catalog/categories/create/', category_data)
    print(f"Category creation POST status: {response.status_code}")
    print(f"Redirect URL: {response.get('Location', 'None')}")
    
    if response.status_code == 302:  # Redirect
        print("Category creation redirected - checking if it worked")
        # Check if category was actually created
        try:
            category = Category.objects.get(category_code=test_code)
            print(f"SUCCESS: Category created with ID {category.category_id}")
        except Category.DoesNotExist:
            print("FAILED: Category was not created in database")
    else:
        print(f"Response content: {response.content.decode()[:1000]}")
    
    # Test direct API access
    print("\n--- Testing Direct API Access ---")
    from frontend.services.api_client import ForgeAPIClient
    from django.test import RequestFactory
    from django.contrib.sessions.middleware import SessionMiddleware
    
    # Create a fake request with session
    factory = RequestFactory()
    request = factory.get('/')
    middleware = SessionMiddleware(lambda x: x)
    middleware.process_request(request)
    request.session.save()
    
    # Manually set session data (this simulates login)
    request.session['auth_token'] = 'fake_token_for_testing'
    request.session.save()
    
    api_client = ForgeAPIClient(request=request)
    print(f"API Client base URL: {api_client.base_url}")
    
    try:
        categories = api_client.get('categories/')
        print(f"API Categories response: {categories}")
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == '__main__':
    test_category_creation()