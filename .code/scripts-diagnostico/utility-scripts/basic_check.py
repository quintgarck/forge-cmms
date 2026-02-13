import os
import sys
import django

sys.path.append('C:/Users/Oskar QuintGarck/DataMain/02-DataCore/01-DevOps/02-Docker/project-root/building/tunning-management/cmms/forge_api')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

django.setup()

def main():
    print("Starting Django setup check...")
    
    try:
        from core.models import Client
        count = Client.objects.count()
        print("Database connection: OK - Found %d clients" % count)
        
        from frontend.forms import ClientForm
        form = ClientForm()
        print("Form import: OK - Form has %d fields" % len(form.fields))
        
        print("All basic components are working")
        print("Now checking for common issues...")
        
        # Check if technicians exist
        from core.models import Technician
        tech_count = Technician.objects.count()
        print("Technicians: %d found" % tech_count)
        
        if tech_count == 0:
            print("WARNING: No technicians found. Client creation needs a technician for 'created_by' field.")
        
        print("\\nTo create a client via web interface:")
        print("- Make sure you're logged in")
        print("- Ensure all required fields are filled")
        print("- Client code must be unique")
        print("- Internet connection for API calls")
        
    except Exception as e:
        print("Error: %s" % str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()