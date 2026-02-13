# Especificaciones Técnicas - ForgeDB API REST

## Configuración del Proyecto

### Dependencias
```bash
# Instalación de dependencias
pip install django==4.2.7
pip install djangorestframework==3.14.0
pip install psycopg2-binary==2.9.7
pip install djangorestframework-simplejwt==5.2.2
pip install drf-yasg==1.21.7
pip install django-filter==23.3
pip install django-cors-headers==4.3.1
pip install redis==5.0.1
pip install celery==5.3.4
pip install gunicorn==21.2.0
pip install hypothesis==6.90.0
```

### Configuración Django (settings.py)
```python
# Configuración base
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'django_filters',
    'corsheaders',
    'celery',
    
    # Local apps
    'core',
]

# Configuración de base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'forge_db',
        'USER': 'postgres',
        'PASSWORD': '********',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'charset': 'utf8',
        },
    }
}

# Configuración DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Configuración JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## Estructura de Modelos

### Esquemas de Base de Datos
El sistema debe manejar los siguientes esquemas de PostgreSQL:

1. **cat (Catálogo)**: Entidades maestras
   - `clients`: Clientes del taller
   - `equipment`: Equipos/vehículos
   - `technicians`: Técnicos
   - `equipment_types`: Tipos de equipos
   - `taxonomy_*`: Sistemas de clasificación

2. **inv (Inventario)**: Gestión de inventario
   - `product_master`: Productos principales
   - `stock`: Existencias
   - `transactions`: Movimientos
   - `purchase_orders`: Órdenes de compra

3. **svc (Servicios)**: Órdenes de trabajo
   - `work_orders`: Órdenes principales
   - `invoices`: Facturas
   - `payments`: Pagos
   - `wo_services`: Servicios en OT

4. **kpi (Métricas)**: Analytics
   - Vistas materializadas para reportes
   - Funciones de análisis

5. **app (Aplicación)**: Sistema
   - `alerts`: Alertas
   - `audit_logs`: Auditoría
   - `business_rules`: Reglas de negocio

---

## Endpoints de la API

### Estructura de URLs
```
/api/v1/
├── auth/
│   ├── login/
│   ├── refresh/
│   └── logout/
├── catalog/
│   ├── clients/
│   ├── equipment/
│   ├── technicians/
│   └── taxonomies/
├── inventory/
│   ├── products/
│   ├── stock/
│   ├── transactions/
│   ├── purchase-orders/
│   └── operations/
├── services/
│   ├── work-orders/
│   ├── invoices/
│   ├── payments/
│   └── operations/
├── documents/
│   ├── upload/
│   ├── download/
│   └── list/
├── analytics/
│   ├── kpis/
│   ├── reports/
│   └── materialized-views/
└── system/
    ├── alerts/
    ├── health/
    └── admin/
```

### Ejemplos de Endpoints Principales

#### Gestión de Clientes
```http
GET    /api/v1/catalog/clients/           # Listar clientes
POST   /api/v1/catalog/clients/           # Crear cliente
GET    /api/v1/catalog/clients/{id}/      # Obtener cliente
PUT    /api/v1/catalog/clients/{id}/      # Actualizar cliente
DELETE /api/v1/catalog/clients/{id}/      # Eliminar cliente
```

#### Órdenes de Trabajo
```http
GET    /api/v1/services/work-orders/                    # Listar OT
POST   /api/v1/services/work-orders/                    # Crear OT
GET    /api/v1/services/work-orders/{id}/               # Obtener OT
POST   /api/v1/services/work-orders/{id}/advance-status/ # Avanzar estado
POST   /api/v1/services/work-orders/{id}/add-service/   # Agregar servicio
```

#### Operaciones de Inventario
```http
POST /api/v1/inventory/operations/reserve-stock/    # Reservar stock
POST /api/v1/inventory/operations/release-stock/    # Liberar stock
POST /api/v1/inventory/operations/replenish/        # Reabastecer
```

#### Analytics
```http
GET /api/v1/analytics/kpis/productivity/            # Productividad técnicos
GET /api/v1/analytics/kpis/inventory-abc/          # Análisis ABC
GET /api/v1/analytics/kpis/technician-efficiency/  # Eficiencia
```

---

## Manejo de Procedimientos Almacenados

### Integración con Funciones PostgreSQL
```python
# Ejemplo: Reserva de stock
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reserve_stock(request):
    wo_id = request.data.get('wo_id')
    sku = request.data.get('sku')
    qty = request.data.get('qty')
    
    with connection.cursor() as cursor:
        cursor.callproc('inv.reserve_stock_for_wo', [wo_id, sku, qty])
        result = cursor.fetchone()
    
    return Response({
        'success': result[0]['success'],
        'message': result[0]['message'],
        'data': result[0]
    })
```

### Funciones Principales a Integrar
1. **Inventario**:
   - `inv.reserve_stock_for_wo()`
   - `inv.release_reserved_stock()`
   - `inv.auto_replenishment()`
   - `inv.calculate_inventory_age()`

2. **Servicios**:
   - `svc.advance_work_order_status()`
   - `svc.add_service_to_wo()`
   - `svc.create_invoice_from_wo()`
   - `svc.register_payment()`

3. **Analytics**:
   - `kpi.analyze_abc_inventory()`
   - `kpi.generate_technician_productivity_report()`
   - `kpi.forecast_demand()`

---

## Autenticación y Permisos

### Sistema de Roles
```python
class RoleBasedPermission(BasePermission):
    """
    Permisos basados en roles:
    - ADMIN: Acceso completo
    - TECHNICIAN: Acceso a órdenes asignadas
    - VIEWER: Solo lectura
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Admin tiene acceso total
        if request.user.is_staff or request.user.is_superuser:
            return True
            
        # Technician tiene acceso limitado
        if hasattr(request.user, 'technician_profile'):
            return self.check_technician_access(request, view)
            
        return False
```

### Configuración JWT
```python
# URLs de autenticación
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

---

## Testing Strategy

### Unit Tests
```python
# Ejemplo: Test de modelo
class ClientModelTest(TestCase):
    def test_client_creation(self):
        client = Client.objects.create(
            client_code='CLI001',
            name='Test Client',
            type='INDIVIDUAL'
        )
        self.assertEqual(client.client_code, 'CLI001')
        self.assertTrue(client.uuid)
```

### Property-Based Tests
```python
# Ejemplo: Test de propiedades
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=20))
def test_client_code_uniqueness(client_code):
    # Property: Los códigos de cliente deben ser únicos
    # **Feature: forge-api-rest, Property 1: Entity serialization completeness**
    pass
```

---

## Documentación API

### Configuración Swagger
```python
# urls.py
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="ForgeDB API",
        default_version='v1',
        description="API REST para Sistema de Gestión de Talleres",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
```

---

## Monitoreo y Logging

### Configuración de Logging
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
    },
}
```

### Middleware de Auditoría
```python
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request
        response = self.get_response(request)
        
        # Log response
        if hasattr(request, 'user') and request.user.is_authenticated:
            self.log_audit(request, response)
            
        return response
```

---

**Documento**: Especificaciones Técnicas  
**Fecha**: 2025-12-29  
**Versión**: 1.0  
**Estado**: Especificación Detallada