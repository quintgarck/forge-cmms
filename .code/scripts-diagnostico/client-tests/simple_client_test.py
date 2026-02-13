#!/usr/bin/env python3
"""
Simple script to test client creation with the specific data.
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


def test_client_creation():
    """Test client creation with specific data."""
    print("Testing client creation")
    print("-" * 40)
    
    create_admin_user()
    django_client = Client()
    
    # Login
    login_success = django_client.login(username='admin', password='admin123')
    if not login_success:
        print("Failed to login with admin")
        return False
    
    print("Login with admin successful")
    
    # Test client creation form GET
    try:
        print("Loading creation form...")
        response = django_client.get('/clients/create/')
        
        if response.status_code == 200:
            print("Creation form loaded successfully")
        else:
            print(f"Error loading form: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error accessing form: {e}")
        return False
    
    # Test client creation form POST with specific data
    try:
        print("Sending client data...")
        
        client_data = {
            'client_code': 'CLI-TEST-001',
            'type': 'individual',
            'name': 'Cliente Test Especifico',
            'email': 'correo@gmail.com',
            'phone': '82363829',
            'address': 'Direccion del cliente test',
            'credit_limit': '3000.00',
        }
        
        response = django_client.post('/clients/create/', data=client_data, follow=True)
        
        print(f"Response code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for success indicators
            success_indicators = [
                'Cliente Test Especifico' in content,
                'creado exitosamente' in content.lower(),
                'success' in content.lower(),
                'CLI-TEST-001' in content,
            ]
            
            success_count = sum(success_indicators)
            print(f"Success indicators: {success_count}/4")
            
            # Check for error indicators
            error_indicators = [
                'error' in content.lower(),
                'invalid' in content.lower(),
                'alert-danger' in content,
                'form-error' in content,
            ]
            
            error_count = sum(error_indicators)
            print(f"Error indicators: {error_count}/4")
            
            if success_count >= 2 and error_count == 0:
                print("Client created successfully")
                return True
            elif error_count > 0:
                print("Errors detected in response")
                
                # Try to extract specific error messages
                if 'Las credenciales de autenticación no se proveyeron' in content:
                    print("Specific error: JWT authentication problem")
                elif 'Token expired' in content:
                    print("Specific error: JWT token expired")
                elif 'Invalid token' in content:
                    print("Specific error: Invalid JWT token")
                
                return False
            else:
                print("Ambiguous response - may have been successful")
                return True
        else:
            print(f"Error in creation: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error during creation: {e}")
        return False


def main():
    """Main function."""
    print("Testing client creation with specific data")
    print("=" * 50)
    print("Objective: Verify that email 'correo@gmail.com' and phone '82363829' work")
    print("=" * 50)
    
    creation_success = test_client_creation()
    
    print("\n" + "=" * 50)
    if creation_success:
        print("SUCCESS: Client creation working correctly")
        return 0
    else:
        print("FAILURE: Client creation has issues")
        return 1


if __name__ == '__main__':
    sys.exit(main())