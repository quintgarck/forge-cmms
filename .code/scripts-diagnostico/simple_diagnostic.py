#!/usr/bin/env python
\"\"\"
Simple diagnostic script for ForgeDB client creation functionality.
\"\"\"
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('C:/Users/Oskar QuintGarck/DataMain/02-DataCore/01-DevOps/02-Docker/project-root/building/tunning-management/cmms/forge_api')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

# Setup Django
django.setup()

def main():
    print(\"Running simple diagnostic for ForgeDB client creation functionality...\")
    
    try:
        # Check if we can import necessary modules
        from core.models import Client
        print(\"✓ Successfully imported Client model\")
        
        from frontend.forms import ClientForm
        print(\"✓ Successfully imported ClientForm\")
        
        from frontend.views import ClientCreateView
        print(\"✓ Successfully imported ClientCreateView\")
        
        from django.urls import reverse
        create_url = reverse('frontend:client_create')
        print(f\"✓ Successfully resolved client create URL: {create_url}\")
        
        list_url = reverse('frontend:client_list')
        print(f\"✓ Successfully resolved client list URL: {list_url}\")
        
        # Check if database connection works
        client_count = Client.objects.count()
        print(f\"✓ Database connection works. Found {client_count} existing clients.\")
        
        # Try to create a minimal form instance
        form = ClientForm()
        print(f\"✓ Successfully created ClientForm instance with {len(form.fields)} fields\")
        
        print(\"\\n✓ All basic checks passed! The client creation components are available.\")
        print(\"\\nIf you're still having issues creating clients through the web interface:\")
        print(\"1. Make sure the Django development server is running\")
        print(\"2. Navigate to http://127.0.0.1:8000/clients/create/\")
        print(\"3. Ensure you're logged in with valid credentials\")
        print(\"4. Check browser console and Django logs for specific error messages\")
        
    except ImportError as e:
        print(f\"✗ Import error: {e}\")
        return False
    except Exception as e:
        print(f\"✗ Error during diagnostic: {e}\")
        return False
    
    return True

if __name__ == \"__main__\":
    main()