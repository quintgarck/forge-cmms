"""
Script de diagnóstico para probar la creación de clientes
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from frontend.views.client_views import ClientCreateView, ClientListView
from frontend.services.api_client import ForgeAPIClient, APIException
import json

def test_client_creation():
    """Test client creation"""
    print("=" * 60)
    print("TEST: Creación de Cliente")
    print("=" * 60)
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Usuario de prueba creado: {user.username}")
    else:
        print(f"✅ Usuario de prueba existe: {user.username}")
    
    # Create Django test client
    client = Client()
    logged_in = client.login(username='testuser', password='testpass123')
    print(f"✅ Login exitoso: {logged_in}")
    
    # Test GET request to client create view
    print("\n1. Probando GET /clients/create/")
    try:
        response = client.get('/clients/create/')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Vista de creación carga correctamente")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            print(f"   Contenido: {response.content[:200]}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
        import traceback
        traceback.print_exc()
    
    # Test GET request to client list view
    print("\n2. Probando GET /clients/")
    try:
        response = client.get('/clients/')
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Vista de lista carga correctamente")
            # Check if clients are in context
            if hasattr(response, 'context') and 'clients' in response.context:
                clients = response.context['clients']
                print(f"   Clientes encontrados: {len(clients) if clients else 0}")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            print(f"   Contenido: {response.content[:200]}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
        import traceback
        traceback.print_exc()
    
    # Test API client directly
    print("\n3. Probando API Client directamente")
    try:
        factory = RequestFactory()
        request = factory.get('/clients/create/')
        request.user = user
        request.session = client.session
        
        api_client = ForgeAPIClient(request=request)
        print(f"   Base URL: {api_client.base_url}")
        
        # Try to get clients
        try:
            clients_data = api_client.get_clients(page=1)
            print(f"   ✅ API get_clients exitoso")
            print(f"   Count: {clients_data.get('count', 0)}")
            print(f"   Results: {len(clients_data.get('results', []))}")
        except APIException as e:
            print(f"   ❌ APIException: {e.message}")
            print(f"   Status Code: {e.status_code}")
            print(f"   Response Data: {e.response_data}")
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"   ❌ Excepción al crear API client: {e}")
        import traceback
        traceback.print_exc()
    
    # Test POST request to client create view
    print("\n4. Probando POST /clients/create/ (creación de cliente)")
    try:
        client_data = {
            'client_code': 'TEST001',
            'type': 'individual',
            'name': 'Cliente Test',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': 'Dirección Test',
            'credit_limit': '1000.00',
        }
        
        response = client.post('/clients/create/', data=client_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("   ✅ Redirect (creación exitosa)")
            print(f"   Redirect URL: {response.url}")
        elif response.status_code == 200:
            print("   ⚠️  Status 200 (puede indicar error en el formulario)")
            # Check for form errors
            if hasattr(response, 'context') and 'form' in response.context:
                form = response.context['form']
                if form.errors:
                    print(f"   ❌ Errores en formulario: {form.errors}")
                else:
                    print("   ✅ Formulario válido pero no redirigió")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
            print(f"   Contenido: {response.content[:500]}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETADO")
    print("=" * 60)

if __name__ == '__main__':
    test_client_creation()

