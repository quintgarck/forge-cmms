import os
import sys
import django

sys.path.append('C:/Users/Oskar QuintGarck/DataMain/02-DataCore/01-DevOps/02-Docker/project-root/building/tunning-management/cmms/forge_api')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

django.setup()

def main():
    print("Adding a default technician to the database...")
    
    try:
        from core.models import Technician
        from django.contrib.auth.models import User
        import uuid
        from datetime import date
        
        # Create a default user first if doesn't exist
        default_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@forgedb.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            default_user.set_password('admin123')  # Set a default password
            default_user.save()
            print("Created default admin user: admin / admin123")
        else:
            print("Using existing admin user")
        
        # Check if a technician already exists
        if Technician.objects.exists():
            print("Technician already exists in the database.")
            tech = Technician.objects.first()
            print(f"Using existing technician: {tech.first_name} {tech.last_name} ({tech.employee_code})")
        else:
            # Create a default technician
            technician = Technician.objects.create(
                uuid=uuid.uuid4(),
                employee_code='TECH001',
                first_name='System',
                last_name='Administrator',
                email='admin@forgedb.com',
                phone='1234567890',
                mobile='1234567890',
                hire_date=date.today(),
                hourly_rate=50.00,
                status='active'
            )
            print(f"Created default technician: {technician.first_name} {technician.last_name}")
        
        # Verify the technician exists
        tech_count = Technician.objects.count()
        print(f"Total technicians in database: {tech_count}")
        
        print("\nNow client creation should work!")
        print("\nTo test client creation:")
        print("1. Make sure the Django server is running")
        print("2. Go to http://localhost:8000/")
        print("3. Log in with username: admin and password: admin123")
        print("4. Navigate to Clients -> Create New Client")
        print("5. Fill in the required fields and submit")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()