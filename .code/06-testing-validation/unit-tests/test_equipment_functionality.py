#!/usr/bin/env python3
"""
Test script for Equipment functionality
Tests the Equipment registry interface implementation
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

def test_equipment_views():
    """Test Equipment views are accessible"""
    print("Testing Equipment Views...")
    
    client = Client()
    
    # Test equipment list view
    try:
        response = client.get(reverse('frontend:equipment_list'))
        print(f"✓ Equipment list view: {response.status_code}")
        if response.status_code == 302:  # Redirect to login
            print("  → Redirects to login (expected for protected view)")
    except Exception as e:
        print(f"✗ Equipment list view error: {e}")
    
    # Test equipment create view
    try:
        response = client.get(reverse('frontend:equipment_create'))
        print(f"✓ Equipment create view: {response.status_code}")
        if response.status_code == 302:  # Redirect to login
            print("  → Redirects to login (expected for protected view)")
    except Exception as e:
        print(f"✗ Equipment create view error: {e}")

def test_equipment_forms():
    """Test Equipment forms"""
    print("\nTesting Equipment Forms...")
    
    try:
        from frontend.forms import EquipmentForm, EquipmentSearchForm
        
        # Test EquipmentForm
        form_data = {
            'equipment_code': 'EQ-001',
            'client_id': 1,
            'year': 2020,
            'make': 'Toyota',
            'model': 'Corolla',
            'status': 'active'
        }
        
        form = EquipmentForm(data=form_data)
        print(f"✓ EquipmentForm created")
        
        # Test form validation
        if form.is_valid():
            print("✓ EquipmentForm validation passed")
        else:
            print(f"✗ EquipmentForm validation failed: {form.errors}")
        
        # Test EquipmentSearchForm
        search_form = EquipmentSearchForm()
        print(f"✓ EquipmentSearchForm created")
        
    except Exception as e:
        print(f"✗ Equipment forms error: {e}")

def test_equipment_templates():
    """Test Equipment templates exist"""
    print("\nTesting Equipment Templates...")
    
    templates = [
        'templates/frontend/equipment/equipment_list.html',
        'templates/frontend/equipment/equipment_detail.html',
        'templates/frontend/equipment/equipment_form.html'
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"✓ Template exists: {template}")
        else:
            print(f"✗ Template missing: {template}")

def test_equipment_css():
    """Test Equipment CSS files exist"""
    print("\nTesting Equipment CSS Files...")
    
    css_files = [
        'static/frontend/css/equipment-list.css',
        'static/frontend/css/equipment-detail.css',
        'static/frontend/css/equipment-form.css'
    ]
    
    for css_file in css_files:
        if os.path.exists(css_file):
            print(f"✓ CSS file exists: {css_file}")
        else:
            print(f"✗ CSS file missing: {css_file}")

def test_equipment_urls():
    """Test Equipment URLs are configured"""
    print("\nTesting Equipment URLs...")
    
    urls = [
        'frontend:equipment_list',
        'frontend:equipment_create',
        'frontend:equipment_detail',
        'frontend:equipment_update',
        'frontend:equipment_delete'
    ]
    
    for url_name in urls:
        try:
            if 'detail' in url_name or 'update' in url_name or 'delete' in url_name:
                url = reverse(url_name, kwargs={'pk': 1})
            else:
                url = reverse(url_name)
            print(f"✓ URL configured: {url_name} -> {url}")
        except Exception as e:
            print(f"✗ URL error: {url_name} -> {e}")

def test_api_client_methods():
    """Test API client has Equipment methods"""
    print("\nTesting API Client Equipment Methods...")
    
    try:
        from frontend.services.api_client import ForgeAPIClient
        
        # Create API client instance
        api_client = ForgeAPIClient()
        
        # Check if Equipment methods exist
        methods = [
            'get_equipment',
            'get_equipment_detail',
            'create_equipment',
            'update_equipment',
            'delete_equipment'
        ]
        
        for method_name in methods:
            if hasattr(api_client, method_name):
                print(f"✓ API method exists: {method_name}")
            else:
                print(f"✗ API method missing: {method_name}")
                
    except Exception as e:
        print(f"✗ API client error: {e}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("EQUIPMENT FUNCTIONALITY TEST")
    print("=" * 60)
    
    test_equipment_views()
    test_equipment_forms()
    test_equipment_templates()
    test_equipment_css()
    test_equipment_urls()
    test_api_client_methods()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == '__main__':
    main()