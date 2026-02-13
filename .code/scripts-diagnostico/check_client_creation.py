#!/usr/bin/env python
"""
Script to check and diagnose client creation functionality in ForgeDB system.
"""
import os
import sys
import django
import requests
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forge_api"))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

# Setup Django
django.setup()

def check_database_connection():
    \"\"\"Check if we can connect to the database and access the Client model.\"\"\"
    try:
        from core.models import Client
        # Try to count existing clients
        count = Client.objects.count()
        print(f\"✓ Database connection: OK. Found {count} existing clients in the database.\")
        return True
    except Exception as e:
        print(f\"✗ Database connection: FAILED - {e}\")
        return False

def check_frontend_urls():
    \"\"\"Check if frontend URLs are properly configured.\"\"\"
    try:
        from django.urls import reverse
        create_url = reverse('frontend:client_create')
        list_url = reverse('frontend:client_list')
        print(f\"✓ Frontend URLs: OK. Create URL: {create_url}, List URL: {list_url}\")
        return True
    except Exception as e:
        print(f\"✗ Frontend URLs: FAILED - {e}\")
        return False

def check_client_form():
    \"\"\"Check if ClientForm is properly configured.\"\"\"
    try:
        from frontend.forms import ClientForm
        form = ClientForm()
        fields = list(form.fields.keys())
        print(f\"✓ ClientForm: OK. Available fields: {fields}\")
        return True
    except Exception as e:
        print(f\"✗ ClientForm: FAILED - {e}\")
        return False

def check_api_client_service():
    \"\"\"Check if API client service is properly configured.\"\"\"
    try:
        from frontend.services.api_client import ForgeAPIClient
        # Try to initialize without request (for testing)
        client = ForgeAPIClient()
        print(f\"✓ API Client Service: OK. Base URL: {client.base_url}\")
        return True
    except Exception as e:
        print(f\"✗ API Client Service: FAILED - {e}\")
        return False

def check_auth_service():
    \"\"\"Check if authentication service is properly configured.\"\"\"
    try:
        from frontend.services.auth_service import AuthenticationService
        print(\"✓ Auth Service: OK. Service is properly configured.\")
        return True
    except Exception as e:
        print(f\"✗ Auth Service: FAILED - {e}\")
        return False

def check_client_view():
    \"\"\"Check if ClientCreateView is properly configured.\"\"\"
    try:
        from frontend.views import ClientCreateView
        view = ClientCreateView()
        print(f\"✓ ClientCreateView: OK. Template: {view.template_name}\")
        return True
    except Exception as e:
        print(f\"✗ ClientCreateView: FAILED - {e}\")
        return False

def check_django_settings():
    \"\"\"Check relevant Django settings.\"\"\"
    try:
        from django.conf import settings
        print(f\"✓ Django Settings: OK. Debug: {settings.DEBUG}, Allowed Hosts: {settings.ALLOWED_HOSTS[:3]}\")
        
        # Check if core and frontend apps are in INSTALLED_APPS
        apps = settings.INSTALLED_APPS
        if 'core' in apps and 'frontend' in apps:
            print(\"✓ Required apps: core and frontend are properly installed.\")
        else:
            print(f\"✗ Required apps: Missing core or frontend in INSTALLED_APPS: {apps}\")
            return False
        
        return True
    except Exception as e:
        print(f\"✗ Django Settings: FAILED - {e}\")
        return False

def run_all_checks():
    \"\"\"Run all diagnostic checks.\"\"\"
    print(\"Running diagnostic checks for client creation functionality...\\n\")
    
    checks = [
        (\"Django Settings\", check_django_settings),
        (\"Database Connection\", check_database_connection),
        (\"Frontend URLs\", check_frontend_urls),
        (\"Client Form\", check_client_form),
        (\"API Client Service\", check_api_client_service),
        (\"Auth Service\", check_auth_service),
        (\"Client View\", check_client_view),
    ]
    
    results = []
    for name, check_func in checks:
        print(f\"\\n{name}:\")
        result = check_func()
        results.append((name, result))
    
    print(f\"\\n\\nSUMMARY:\")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = \"PASS\" if result else \"FAIL\"
        print(f\"  {name}: {status}\")
    
    print(f\"\\nOverall: {passed}/{total} checks passed\")
    
    if passed == total:
        print(\"✓ All checks passed! The client creation functionality should work properly.\")
    else:
        print(\"✗ Some checks failed. Please review the errors above.\")
    
    return passed == total

if __name__ == \"__main__\":
    run_all_checks()