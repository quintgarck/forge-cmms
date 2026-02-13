# ForgeDB Client CRUD Implementation Guide

## Overview
This document provides a step-by-step implementation guide for the client CRUD (Create, Read, Update, Delete) functionality in the ForgeDB automotive workshop management system.

## Prerequisites
Before implementing client functionality, ensure the following components are in place:
1. Django 4.2+ project with PostgreSQL database
2. Django REST Framework 3.14+ installed
3. JWT authentication configured
4. Frontend Django app for web interface

## Step 1: Database Model Implementation

### 1.1 Create the Client Model
The Client model is defined in `core/models.py`:

```python
class Client(models.Model):
    TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('fleet', 'Fleet'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blocked', 'Blocked'),
    ]

    client_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    client_code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    name = models.CharField(max_length=150)
    legal_name = models.CharField(max_length=150, blank=True, null=True)
    tax_id = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    mobile = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    payment_days = models.IntegerField(blank=True, null=True)
    credit_used = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    preferred_contact_method = models.CharField(max_length=20, blank=True, null=True)
    send_reminders = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'cat.clients'
        ordering = ['name']
        indexes = [
            models.Index(fields=['client_code']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} ({self.client_code})"

    @property
    def available_credit(self):
        if self.credit_limit:
            return self.credit_limit - (self.credit_used or Decimal('0.00'))
        return None
```

### 1.2 Apply Database Migrations
Run the following command to create the client table:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Step 2: Serializer Implementation

### 2.1 Create Client Serializer
The ClientSerializer is defined in `core/serializers/main_serializers.py`:

```python
class ClientSerializer(serializers.ModelSerializer):
    available_credit = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = [
            'client_id', 'uuid', 'client_code', 'type', 'name', 'legal_name',
            'tax_id', 'email', 'phone', 'mobile', 'address', 'city', 'state',
            'country', 'postal_code', 'credit_limit', 'payment_days', 'credit_used',
            'available_credit', 'preferred_contact_method', 'send_reminders',
            'status', 'created_by', 'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['client_id', 'uuid', 'created_at', 'updated_at', 'credit_used']

    def validate_client_code(self, value):
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Client code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_credit_limit(self, value):
        if value is not None:
            if value < Decimal('0'):
                raise serializers.ValidationError("Credit limit cannot be negative")
            if value > Decimal('9999999.99'):
                raise serializers.ValidationError(
                    "Credit limit seems unreasonably high"
                )
        return value

    def validate_payment_days(self, value):
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Payment days cannot be negative")
            if value > 365:
                raise serializers.ValidationError(
                    "Payment days cannot exceed 365"
                )
        return value
```

## Step 3: View Implementation

### 3.1 Create Client ViewSet
The ClientViewSet is defined in `core/views/client_views.py`:

```python
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all().select_related('created_by')
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'status', 'city', 'state', 'country']
    search_fields = ['name', 'legal_name', 'email', 'phone', 'mobile', 'client_code']
    ordering_fields = ['name', 'created_at', 'updated_at', 'credit_used']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
```

## Step 4: URL Configuration

### 4.1 Configure API URLs
The client endpoints are configured in `core/urls.py`:

```python
from .views import ClientViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet)

urlpatterns = [
    # Other URL patterns...
    path('', include(router.urls)),  # This includes the clients endpoints
]
```

## Step 5: Frontend Implementation

### 5.1 Create Client Form
The ClientForm is defined in `frontend/forms.py`:

```python
class ClientForm(forms.Form):
    client_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código de cliente solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )

    client_code = forms.CharField(
        max_length=20,
        validators=[client_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CLI-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Cliente',
        help_text='Código único para identificar al cliente (ej: CLI-001)'
    )
    # Additional fields...
    
    def clean_client_code(self):
        client_code = self.cleaned_data.get('client_code', '').strip().upper()
        if not client_code:
            raise ValidationError("El código de cliente es obligatorio.")
        if len(client_code) < 3:
            raise ValidationError("El código de cliente debe tener al menos 3 caracteres.")
        return client_code
    # Additional validation methods...
```

### 5.2 Create Frontend Views
The frontend client views are defined in `frontend/views.py`:

```python
class ClientListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    template_name = 'frontend/clients/client_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        # Implementation for client listing with pagination and filters
        pass

class ClientCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    template_name = 'frontend/clients/client_form.html'
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        # Implementation for client creation
        pass

class ClientUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    template_name = 'frontend/clients/client_form.html'
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        # Implementation for client update
        pass

class ClientDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    template_name = 'frontend/clients/client_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        # Implementation for client detail view
        pass

class ClientDeleteView(LoginRequiredMixin, APIClientMixin, View):
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        # Implementation for client deletion
        pass
```

### 5.3 Configure Frontend URLs
The frontend client URLs are configured in `frontend/urls.py`:

```python
urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
]
```

## Step 6: API Client Service

### 6.1 Implement API Client Service
The API client service is implemented in `frontend/services/api_client.py`:

```python
class ForgeAPIClient:
    # ... initialization and helper methods ...
    
    def get_clients(self, page: int = 1, search: str = None, **filters) -> Dict[str, Any]:
        params = {'page': page}
        if search:
            params['search'] = search
        params.update(filters)
        return self.get('clients/', params=params, use_cache=True)
    
    def get_client(self, client_id: int) -> Dict[str, Any]:
        return self.get(f'clients/{client_id}/', use_cache=True)
    
    def create_client(self, client_data: Dict) -> Dict[str, Any]:
        return self.post('clients/', data=client_data)
    
    def update_client(self, client_id: int, client_data: Dict) -> Dict[str, Any]:
        return self.put(f'clients/{client_id}/', data=client_data)
    
    def delete_client(self, client_id: int) -> Dict[str, Any]:
        return self.delete(f'clients/{client_id}/')
```

## Step 7: Testing

### 7.1 Create Unit Tests
Create tests to verify client functionality in `core/tests/test_clients.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Client, Technician

class ClientModelTest(TestCase):
    def setUp(self):
        self.technician = Technician.objects.create(
            employee_code='TECH001',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            hire_date='2023-01-01'
        )
    
    def test_client_creation(self):
        client = Client.objects.create(
            client_code='CLI001',
            type='individual',
            name='Test Client',
            created_by=self.technician
        )
        self.assertEqual(client.client_code, 'CLI001')
        self.assertEqual(client.name, 'Test Client')
        self.assertEqual(client.type, 'individual')
        self.assertEqual(client.status, 'active')
        
    def test_available_credit_property(self):
        client = Client.objects.create(
            client_code='CLI002',
            type='business',
            name='Business Client',
            credit_limit=1000.00,
            credit_used=300.00,
            created_by=self.technician
        )
        self.assertEqual(client.available_credit, 700.00)
```

## Step 8: Deployment

### 8.1 Configure Production Settings
Ensure your production settings include:
- Proper database connection to PostgreSQL
- Secure JWT settings
- CORS and security headers
- Static file handling

## Summary
This implementation provides a complete client CRUD functionality with:

1. **Database layer**: Proper model with validation and relationships
2. **API layer**: REST API with filtering, searching, and ordering
3. **Business logic layer**: Proper validation and business rules
4. **Authentication layer**: JWT-based authentication
5. **Frontend layer**: Django forms and views for web interface
6. **Service layer**: API client service for communication
7. **Security layer**: Proper permissions and validation

The implementation follows Django and DRF best practices, with proper separation of concerns and comprehensive validation at every layer.