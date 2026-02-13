"""
Test script to check client form submission
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from frontend.forms import ClientForm

# Create test user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()

# Create Django test client
client = Client()
logged_in = client.login(username='testuser', password='testpass123')
print(f"Logged in: {logged_in}")

# Test form validation
form_data = {
    'client_code': 'TEST001',
    'type': 'individual',
    'name': 'Test Client',
    'email': 'test@example.com',
    'phone': '1234567890',
    'address': 'Test Address 123',
    'credit_limit': '1000.00',
}

form = ClientForm(data=form_data)
print(f"\nForm is valid: {form.is_valid()}")
if not form.is_valid():
    print(f"Form errors: {form.errors}")
    print(f"Non-field errors: {form.non_field_errors()}")

# Test POST to create view
print("\nTesting POST to /clients/create/")
response = client.post('/clients/create/', data=form_data)
print(f"Status code: {response.status_code}")
print(f"Redirect URL: {getattr(response, 'url', 'No redirect')}")

# Check messages
from django.contrib.messages import get_messages
messages = list(get_messages(response.wsgi_request))
for msg in messages:
    print(f"Message: {msg.level_tag} - {msg}")

