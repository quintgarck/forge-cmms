import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

# Setup Django
django.setup()

def main():
    print(\"Testing basic client creation components...\")
    
    try:
        # Import the form and test it
        from frontend.forms import ClientForm
        
        # Test with valid data
        valid_data = {
            'client_code': 'CLI001',
            'type': 'individual',
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone': '82363829',
            'address': '123 Test Street'
        }
        
        form = ClientForm(valid_data)
        
        if form.is_valid():
            print(\"[OK] ClientForm validates correctly with valid data\")
            print(\"  Cleaned data keys: %s\" % list(form.cleaned_data.keys()))
        else:
            print(\"[ERROR] ClientForm has validation errors:\")
            for field, errors in form.errors.items():
                print(\"  %s: %s\" % (field, errors))
    
        # Check if we can connect to the database
        from core.models import Client
        client_count = Client.objects.count()
        print(\"[OK] Database connection OK. Found %d existing clients.\" % client_count)
        
        # Check if we can find technicians (needed for created_by)
        from core.models import Technician
        tech_count = Technician.objects.count()
        print(\"[OK] Technicians in database: %d\" % tech_count)
        
        if tech_count == 0:
            print(\"[WARNING] No technicians found. Client creation requires a technician for the 'created_by' field.\")
    
        print(\"\\n[OK] Basic components are working.\")
        print(\"\\nFor client creation to work through the web interface:\")
        print(\"1. You must be logged in with valid credentials\")
        print(\"2. All required form fields must be filled in correctly\")
        print(\"3. The technician user must exist in the database\")
        print(\"4. The client code must be unique\")
        print(\"5. The API client service must be able to communicate with the backend\")
        
    except Exception as e:
        print(\"[ERROR] %s\" % e)
        import traceback
        traceback.print_exc()

if __name__ == \"__main__\":
    main()