# Guía de Desarrollo - ForgeDB API REST

## Inicio Rápido

### Prerrequisitos
```bash
# Python 3.11+
# PostgreSQL con ForgeDB configurado
# Git
# Docker (opcional)
```

### Configuración del Entorno
```bash
# 1. Clonar y crear entorno virtual
python -m venv forge_env
source forge_env/bin/activate  # Linux/Mac
# forge_env\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con configuración de BD

# 4. Ejecutar migraciones (solo si es necesario)
python manage.py makemigrations
python manage.py migrate

# 5. Ejecutar servidor
python manage.py runserver
```

---

## Comandos de Desarrollo

### Generación de Modelos
```bash
# Generar modelos desde BD existente
python manage.py inspectdb --database=default --include-schemas --schema=cat,inv,svc,doc,kpi,app,oem > core/models.py

# Personalizar modelos generados
# - Agregar Meta classes
# - Añadir métodos personalizados
# - Configurar relaciones
```

### Testing
```bash
# Ejecutar todos los tests
python manage.py test

# Ejecutar con cobertura
coverage run --source='.' manage.py test
coverage report

# Ejecutar tests específicos
python manage.py test core.tests.test_models

# Property-based testing
python manage.py test core.tests.property_tests
```

### Comandos Útiles
```bash
# Crear superusuario
python manage.py createsuperuser

# Shell interactivo
python manage.py shell

# Recargar servidor automáticamente
python manage.py runserver_plus

# Verificar configuración
python manage.py check --deploy
```

---

## Estructura de Código

### Organización de Archivos
```
core/
├── __init__.py
├── admin.py                 # Configuración admin Django
├── apps.py                  # Configuración de la app
├── models/
│   ├── __init__.py
│   ├── base.py             # Modelos base generados
│   ├── catalog.py          # Modelos cat.*
│   ├── inventory.py        # Modelos inv.*
│   ├── services.py         # Modelos svc.*
│   └── system.py           # Modelos app.*, kpi.*
├── serializers/
│   ├── __init__.py
│   ├── base.py             # Serializers base
│   ├── catalog.py          # Serializers cat.*
│   ├── inventory.py        # Serializers inv.*
│   └── services.py         # Serializers svc.*
├── views/
│   ├── __init__.py
│   ├── auth.py             # Autenticación
│   ├── catalog.py          # Vistas cat.*
│   ├── inventory.py        # Vistas inv.*
│   ├── services.py         # Vistas svc.*
│   ├── documents.py        # Vistas documentos
│   └── analytics.py        # Vistas analytics
├── services/
│   ├── __init__.py
│   ├── inventory_service.py    # Lógica de inventario
│   ├── work_order_service.py   # Lógica de OT
│   └── business_service.py     # Reglas de negocio
├── permissions/
│   ├── __init__.py
│   └── base.py             # Permisos personalizados
└── tests/
    ├── __init__.py
    ├── test_models.py      # Tests de modelos
    ├── test_views.py       # Tests de vistas
    ├── test_services.py    # Tests de servicios
    └── property_tests/     # Property-based tests
```

### Convenciones de Código

#### Modelos
```python
# Usar nombres descriptivos en español para campos
class WorkOrder(models.Model):
    wo_id = models.AutoField(primary_key=True)
    wo_number = models.CharField(max_length=30, unique=True)
    cliente = models.ForeignKey(Client, on_delete=models.CASCADE)
    
    class Meta:
        managed = True
        db_table = 'svc"."work_orders'
        
    def __str__(self):
        return f"OT-{self.wo_number}"
```

#### Serializers
```python
class WorkOrderSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.name', read_only=True)
    
    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ('wo_id', 'created_at', 'updated_at')
```

#### Views
```python
class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.select_related('cliente')
    serializer_class = WorkOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'technician_id']
    search_fields = ['wo_number', 'customer_complaints']
    ordering_fields = ['created_at', 'priority', 'estimated_completion_date']
    ordering = ['-created_at']
```

---

## Patrones de Desarrollo

### Service Layer Pattern
```python
# services/inventory_service.py
class InventoryService:
    @staticmethod
    def reserve_stock(wo_id, sku, qty, warehouse_code=None):
        """Envuelve el procedimiento almacenado de reserva de stock"""
        with connection.cursor() as cursor:
            cursor.callproc('inv.reserve_stock_for_wo', 
                          [wo_id, sku, qty, warehouse_code])
            result = cursor.fetchone()
        return result
```

### Repository Pattern
```python
# repositories/work_order_repository.py
class WorkOrderRepository:
    @staticmethod
    def get_by_technician(technician_id, status=None):
        queryset = WorkOrder.objects.filter(technician_id=technician_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related('cliente', 'equipment')
```

### Factory Pattern para Serializers
```python
# serializers/factory.py
class SerializerFactory:
    @staticmethod
    def get_serializer(model_type):
        serializers = {
            'client': ClientSerializer,
            'equipment': EquipmentSerializer,
            'work_order': WorkOrderSerializer,
        }
        return serializers.get(model_type)
```

---

## Manejo de Errores

### Custom Exceptions
```python
# exceptions.py
class ForgeDBException(Exception):
    """Excepción base para ForgeDB"""
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)

class InventoryException(ForgeDBException):
    """Excepción específica de inventario"""
    pass

class WorkOrderException(ForgeDBException):
    """Excepción específica de órdenes de trabajo"""
    pass
```

### Exception Handlers
```python
# views/handlers.py
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if isinstance(exc, ForgeDBException):
        return Response({
            'error': {
                'code': exc.code or 'FORGE_ERROR',
                'message': exc.message,
                'details': exc.details
            }
        }, status=400)
    
    return response
```

---

## Validaciones de Negocio

### Validators Personalizados
```python
# validators.py
from django.core.exceptions import ValidationError

def validate_client_credit_limit(client_id, amount):
    """Validar límite de crédito del cliente"""
    client = Client.objects.get(client_id=client_id)
    if client.credit_used + amount > client.credit_limit:
        raise ValidationError(
            f"Límite de crédito excedido. Disponible: "
            f"{client.credit_limit - client.credit_used}"
        )

def validate_inventory_availability(sku, quantity):
    """Validar disponibilidad de inventario"""
    available = InventoryService.get_available_stock(sku)
    if available < quantity:
        raise ValidationError(
            f"Stock insuficiente. Disponible: {available}, "
            f"Solicitado: {quantity}"
        )
```

### Integración con Business Rules
```python
# services/business_service.py
class BusinessRuleService:
    @staticmethod
    def evaluate_rules(table_name, new_data, old_data=None):
        """Evaluar reglas de negocio antes de guardar"""
        rules = BusinessRule.objects.filter(
            applies_to_table=table_name,
            is_active=True
        )
        
        for rule in rules:
            if BusinessRuleValidator.evaluate(rule, new_data, old_data):
                BusinessRuleAction.execute(rule)
```

---

## Performance y Optimización

### Query Optimization
```python
# Usar select_related y prefetch_related
class WorkOrderViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return WorkOrder.objects.select_related(
            'cliente', 'equipment', 'technician'
        ).prefetch_related(
            'wo_services', 'wo_items'
        )
```

### Caching
```python
# caching.py
from django.core.cache import cache

class CacheService:
    @staticmethod
    def get_client_data(client_id):
        cache_key = f"client_{client_id}"
        data = cache.get(cache_key)
        
        if not data:
            data = Client.objects.get(id=client_id)
            cache.set(cache_key, data, timeout=300)  # 5 minutos
        
        return data
```

### Database Indexes
```python
# migrations/0001_add_indexes.py
class Migration(migrations.Migration):
    dependencies = []
    
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX CONCURRENTLY idx_work_orders_status 
            ON svc.work_orders(status);
            CREATE INDEX CONCURRENTLY idx_work_orders_technician 
            ON svc.work_orders(technician_id);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_work_orders_status;"
        ),
    ]
```

---

## Deployment

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "forge_api.wsgi:application"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: forge_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ********
    volumes:
      - postgres_data:/var/lib/postgresql/data/

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgres://postgres:********@db:5432/forge_db

volumes:
  postgres_data:
```

---

## Troubleshooting

### Problemas Comunes

#### Error de Conexión a PostgreSQL
```bash
# Verificar configuración
python manage.py dbshell

# Test de conexión
python manage.py shell -c "from django.db import connection; print(connection.cursor())"
```

#### Problemas con inspectdb
```bash
# Regenerar modelos con más detalles
python manage.py inspectdb --table-name-filter="cat.*" > temp_models.py

# Revisar relaciones manualmente
# Agregar ForeignKey manualmente donde sea necesario
```

#### Performance Issues
```bash
# Analizar queries lentas
python manage.py shell -c "
from django.db import connection, reset_queries
from core.models import WorkOrder
reset_queries()
qs = WorkOrder.objects.all()
list(qs)
print(connection.queries)
"

# Usar django-debug-toolbar
pip install django-debug-toolbar
```

---

**Documento**: Guía de Desarrollo  
**Fecha**: 2025-12-29  
**Versión**: 1.0  
**Estado**: Lista para Desarrollo