import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from core.models import Technician

print(f"Tabla: {Technician._meta.db_table}")
print(f"Total técnicos: {Technician.objects.count()}")

for tech in Technician.objects.all()[:5]:
    print(f"- {tech.employee_code}: {tech.first_name} {tech.last_name} ({tech.status})")
