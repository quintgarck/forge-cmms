# Plan Integral de Transformación a Arquitectura SaaS Multitenant para Forge CMMS

## Tabla de Contenidos
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis Comparativo](#análisis-comparativo)
3. [Objetivos del Proyecto](#objetivos-del-proyecto)
4. [Arquitectura SaaS Propuesta](#arquitectura-saas-propuesta)
5. [Modelos de Base de Datos](#modelos-de-base-de-datos)
6. [Cambios en el Backend](#cambios-en-el-backend)
7. [Cambios en el Frontend](#cambios-en-el-frontend)
8. [Gestión de Seguridad y Acceso](#gestión-de-seguridad-y-acceso)
9. [Plan de Implementación por Fases](#plan-de-implementación-por-fases)
10. [Consideraciones Técnicas](#consideraciones-técnicas)

## Resumen Ejecutivo

Este documento combina las recomendaciones existentes en `SAAS_MULTITENANCY_RECOMMENDATIONS.md` con las propuestas adicionales para crear un plan integral de transformación del sistema actual en una plataforma SaaS multitenant para talleres automotrices. La transformación permitirá que múltiples empresas de talleres automotrices utilicen la plataforma de manera aislada, cada una con sus propios datos, usuarios y configuraciones.

## Análisis Comparativo

### Coincidencias Clave
- Ambos documentos reconocen que **falta el concepto de "empresa cliente" (tenant)** en el sistema actual
- Ambos identifican la **necesidad de aislamiento de datos** por empresa
- Ambos proponen **añadir `tenant_id` a modelos operativos** (clientes, técnicos, órdenes de trabajo, etc.)
- Ambos recomiendan **crear tablas nuevas** para gestionar tenants y relaciones usuario-tenant
- Ambos proponen **un plan por fases** para la implementación

### Diferencias y Complementariedades
- **Mi propuesta** incluye modelos más detallados para planes de suscripción y facturación
- **SAAS_MULTITENANCY_RECOMMENDATIONS** profundiza más en la **arquitectura de autenticación** y resolución de tenant
- **Mi propuesta** incluye más detalles de frontend y componentes React
- **SAAS_MULTITENANCY_RECOMMENDATIONS** incluye más detalles sobre **estrategias de migración** de datos existentes

## Objetivos del Proyecto

### Objetivo Principal
Transformar la plataforma en un sistema SaaS multitenant donde múltiples empresas puedan contratar servicios de gestión para sus talleres automotrices.

### Objetivos Secundarios
- Implementar aislamiento de datos por empresa
- Crear sistema de suscripciones y facturación
- Mantener la funcionalidad existente
- Asegurar escalabilidad horizontal
- Preservar la calidad del código
- Permitir gestión de múltiples talleres por usuario (opcional)

## Arquitectura SaaS Propuesta

### Estrategia de Multitenancia
**Recomendación**: Estrategia híbrida que combina:
- **Esquema compartido para tablas maestras** (catálogos globales, códigos de referencia)
- **Filtros por tenant_id para tablas operativas** (clientes del taller, técnicos, órdenes de trabajo)
- **Relación N a N entre usuarios y tenants** para permitir flexibilidad (un usuario puede pertenecer a múltiples talleres)

### Componentes Principales
```
SaaS Platform Structure:
├── Shared Schema (global tables)
│   ├── reference codes
│   ├── equipment types
│   ├── taxonomy
│   └── global catalogs
├── Tenant Schema (operational data)
│   ├── tenants (ClientCompany)
│   ├── user_tenants (user-tenant-role relationship)
│   ├── tenant-specific operational data
│   └── tenant settings
└── Tenant Data Isolation
    ├── clients (of the workshop)
    ├── technicians (of the workshop)
    ├── work_orders
    ├── inventory
    └── customizations
```

## Modelos de Base de Datos

### Nuevos Modelos Principales

#### 1. Tenant (Empresa Cliente)
```python
class Tenant(models.Model):
    """Empresa cliente del SaaS (un taller que usa el sistema)"""
    tenant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)  # Nombre del taller
    legal_name = models.CharField(max_length=200)  # Razón social
    tax_id = models.CharField(max_length=30, unique=True)  # RUT/CUIT
    slug = models.SlugField(unique=True)  # Para subdominio: taller-garcia.forgecmms.com
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Activo'),
        ('SUSPENDED', 'Suspendido'),
        ('CANCELLED', 'Cancelado'),
    ], default='ACTIVE')
    plan = models.CharField(max_length=20, choices=[
        ('BASIC', 'Básico'),
        ('PROFESSIONAL', 'Profesional'),
        ('ENTERPRISE', 'Empresarial'),
    ], default='BASIC')
    settings = models.JSONField(default=dict)  # Configuración por taller (moneda, idioma, etc.)
    max_users = models.IntegerField(default=10)
    max_technicians = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenants'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['tax_id']),
            models.Index(fields=['status']),
        ]
```

#### 2. UserTenant (Relación Usuario-Tenant-Rol)
```python
class UserTenant(models.Model):
    """Relación N a N entre usuarios y tenants con roles específicos"""
    user_tenant_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('ADMIN', 'Admin Taller'),
        ('MANAGER', 'Gerente'),
        ('TECHNICIAN', 'Técnico'),
        ('VIEWER', 'Visualizador'),
    ])
    is_default = models.BooleanField(default=False)  # Tenant por defecto para el usuario
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tenants')
    
    class Meta:
        db_table = 'user_tenants'
        unique_together = [['user', 'tenant']]  # Un usuario no puede tener múltiples roles en el mismo tenant
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['user', 'is_default']),
        ]
```

### Modificaciones a Modelos Existentes

Todos los modelos operativos deben modificarse para incluir una referencia al tenant:

#### Client (Clientes del Taller)
```python
class Client(models.Model):
    # ... campos existentes ...
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)  # Cliente del taller
    # ... resto de campos ...
    
    class Meta:
        db_table = 'clients'
        indexes = [
            models.Index(fields=['tenant', 'status']),  # Filtrar clientes por tenant y estado
            models.Index(fields=['tenant', 'created_at']),  # Consultas históricas por tenant
        ]
```

#### Technician (Técnicos del Taller)
```python
class Technician(models.Model):
    # ... campos existentes ...
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)  # Técnico del taller
    # ... resto de campos ...
    
    class Meta:
        db_table = 'technicians'
        indexes = [
            models.Index(fields=['tenant', 'status']),
        ]
```

#### WorkOrder (Órdenes de Trabajo)
```python
class WorkOrder(models.Model):
    # ... campos existentes ...
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)  # Órden del taller
    # ... resto de campos ...
    
    class Meta:
        db_table = 'work_orders'
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['tenant', 'due_date']),
        ]
```

#### Equipment (Vehículos/Equipos)
```python
class Equipment(models.Model):
    # ... campos existentes ...
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)  # Equipo del taller
    # ... resto de campos ...
    
    class Meta:
        db_table = 'equipment'
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'client_id']),
        ]
```

## Cambios en el Backend

### 1. Middleware de Multitenancia
```python
import threading
from django.db import connection
from django.http import Http404
from .models import Tenant, UserTenant

_thread_locals = threading.local()

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Determinar tenant actual basado en subdominio o header
        tenant = self.resolve_tenant(request)
        
        if tenant:
            # Almacenar tenant en el request para uso en vistas
            request.tenant = tenant
            # Almacenar en thread local para managers por defecto
            _thread_locals.tenant_id = tenant.tenant_id
            
            # Opcional: cambiar esquema de base de datos si se usa estrategia de esquema por tenant
            # connection.set_tenant(tenant)
        else:
            # Para usuarios del sistema (no tenants)
            request.tenant = None
            _thread_locals.tenant_id = None
        
        response = self.get_response(request)
        return response
    
    def resolve_tenant(self, request):
        """Resolver tenant basado en subdominio, header o tenant por defecto del usuario"""
        # Opción 1: Por subdominio (taller-garcia.forgecmms.com)
        host = request.get_host()
        subdomain = host.split('.')[0] if '.' in host else None
        
        if subdomain:
            try:
                return Tenant.objects.get(slug=subdomain, status='ACTIVE')
            except Tenant.DoesNotExist:
                pass
        
        # Opción 2: Por header (X-Tenant-ID)
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        if tenant_id:
            try:
                return Tenant.objects.get(tenant_id=tenant_id, status='ACTIVE')
            except Tenant.DoesNotExist:
                pass
        
        # Opción 3: Por tenant por defecto del usuario
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_tenant = UserTenant.objects.select_related('tenant').get(
                    user=request.user,
                    is_default=True,
                    is_active=True
                )
                return user_tenant.tenant
            except UserTenant.DoesNotExist:
                pass
        
        return None
```

### 2. Managers por Defecto con Filtro de Tenant
```python
from django.db import models
from django.db.models import Q
import threading

_thread_locals = threading.local()

class TenantManager(models.Manager):
    """Manager que automáticamente filtra por tenant_id del usuario actual"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(_thread_locals, 'tenant_id', None)
        
        if tenant_id:
            # Asumiendo que el modelo tiene un campo 'tenant'
            return qs.filter(tenant_id=tenant_id)
        else:
            # Para usuarios de plataforma (staff/superuser)
            return qs

class TenantAwareModel(models.Model):
    """Clase base para modelos que deben filtrarse por tenant"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    objects = TenantManager()
    # Mantener acceso al manager original para usuarios de plataforma
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
```

### 3. Serializadores Adaptados
```python
from rest_framework import serializers
from .models import Client, Technician, WorkOrder

class TenantClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['tenant']
    
    def create(self, validated_data):
        # Asegurar que el objeto pertenece al tenant actual
        validated_data['tenant'] = self.context['request'].tenant
        return super().create(validated_data)

class TenantWorkOrderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    technician_name = serializers.CharField(source='technician.name', read_only=True)
    
    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ['tenant']
    
    def create(self, validated_data):
        validated_data['tenant'] = self.context['request'].tenant
        return super().create(validated_data)
```

### 4. Vistas Protegidas
```python
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import Client, WorkOrder

def tenant_required(view_func):
    """Decorador para vistas que requieren tenant"""
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            # Redirigir a página de selección de tenant o error
            return redirect('tenant_selection')
        return view_func(request, *args, **kwargs)
    return wrapper

@method_decorator(tenant_required, name='dispatch')
class TenantClientListView(ListView):
    model = Client
    template_name = 'tenant/clients/list.html'
    
    def get_queryset(self):
        # El manager por defecto ya filtra por tenant
        return Client.objects.all()

@method_decorator(tenant_required, name='dispatch')
class TenantWorkOrderListView(ListView):
    model = WorkOrder
    template_name = 'tenant/work_orders/list.html'
    
    def get_queryset(self):
        return WorkOrder.objects.all().select_related('client', 'technician')
```

### 5. API Endpoints para Gestión de Tenants (Solo Staff)
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Tenant, UserTenant

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_tenants(request):
    """API para listar todos los tenants (solo admin de plataforma)"""
    tenants = Tenant.objects.all()
    data = []
    
    for tenant in tenants:
        # Contar usuarios y datos operativos del tenant
        user_count = UserTenant.objects.filter(tenant=tenant, is_active=True).count()
        
        data.append({
            'tenant_id': tenant.tenant_id,
            'name': tenant.name,
            'status': tenant.status,
            'plan': tenant.plan,
            'user_count': user_count,
            'created_at': tenant.created_at,
            'max_users': tenant.max_users,
        })
    
    return Response({
        'total_tenants': len(data),
        'tenants': data
    })

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_tenant(request):
    """API para crear un nuevo tenant (solo admin de plataforma)"""
    # Validar datos
    required_fields = ['name', 'legal_name', 'tax_id', 'email', 'slug']
    for field in required_fields:
        if field not in request.data:
            return Response({f'{field}_required': True}, status=status.HTTP_400_BAD_REQUEST)
    
    # Crear tenant
    try:
        tenant = Tenant.objects.create(
            name=request.data['name'],
            legal_name=request.data['legal_name'],
            tax_id=request.data['tax_id'],
            email=request.data['email'],
            phone=request.data.get('phone', ''),
            address=request.data.get('address', ''),
            city=request.data.get('city', ''),
            country=request.data.get('country', 'CL'),
            slug=request.data['slug'],
            status=request.data.get('status', 'ACTIVE'),
            plan=request.data.get('plan', 'BASIC'),
            max_users=request.data.get('max_users', 10),
            max_technicians=request.data.get('max_technicians', 10),
        )
        
        # Opcional: crear usuario admin del tenant
        if 'admin_email' in request.data:
            # Lógica para crear usuario admin y asociarlo al tenant
            pass
        
        return Response({
            'tenant_id': tenant.tenant_id,
            'name': tenant.name,
            'slug': tenant.slug,
            'status': tenant.status,
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def tenant_detail(request, tenant_id):
    """API para detalle, edición y eliminación de tenant (solo admin de plataforma)"""
    try:
        tenant = Tenant.objects.get(tenant_id=tenant_id)
    except Tenant.DoesNotExist:
        return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Contar usuarios del tenant
        user_count = UserTenant.objects.filter(tenant=tenant, is_active=True).count()
        
        return Response({
            'tenant_id': tenant.tenant_id,
            'name': tenant.name,
            'legal_name': tenant.legal_name,
            'tax_id': tenant.tax_id,
            'email': tenant.email,
            'phone': tenant.phone,
            'address': tenant.address,
            'city': tenant.city,
            'country': tenant.country,
            'status': tenant.status,
            'plan': tenant.plan,
            'max_users': tenant.max_users,
            'max_technicians': tenant.max_technicians,
            'user_count': user_count,
            'created_at': tenant.created_at,
            'updated_at': tenant.updated_at,
        })
    
    elif request.method == 'PUT':
        # Actualizar tenant
        for field in ['name', 'legal_name', 'tax_id', 'email', 'phone', 'address', 'city', 'country', 'status', 'plan', 'max_users', 'max_technicians']:
            if field in request.data:
                setattr(tenant, field, request.data[field])
        
        tenant.save()
        return Response({'message': 'Tenant updated successfully'})
    
    elif request.method == 'DELETE':
        # Opcional: soft delete o eliminación real
        tenant.status = 'CANCELLED'
        tenant.save()
        return Response({'message': 'Tenant deactivated successfully'})
```

## Cambios en el Frontend

### 1. Nueva Interfaz de Gestión de Tenants (Solo Admin Plataforma)
```html
<!-- templates/platform/tenants/list.html -->
{% extends 'frontend/base/base.html' %}

{% block title %}Empresas Cliente - Panel de Administración{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>Empresas Cliente ({{ total_tenants }})</h1>
                <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createTenantModal">
                    <i class="bi bi-plus-lg"></i> Nuevo Taller
                </button>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <h5>Total Talleres</h5>
                            <h2>{{ total_tenants }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <h5>Activos</h5>
                            <h2>{{ active_tenants }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <h5>Suspendidos</h5>
                            <h2>{{ suspended_tenants }}</h2>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body">
                            <h5>Usuarios Totales</h5>
                            <h2>{{ total_users }}</h2>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Nombre</th>
                                    <th>RUT</th>
                                    <th>Email</th>
                                    <th>Plan</th>
                                    <th>Estado</th>
                                    <th>Usuarios</th>
                                    <th>Fecha Alta</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for tenant in tenants %}
                                <tr>
                                    <td>{{ tenant.tenant_id }}</td>
                                    <td>{{ tenant.name }}</td>
                                    <td>{{ tenant.tax_id }}</td>
                                    <td>{{ tenant.email }}</td>
                                    <td>
                                        <span class="badge bg-{{ tenant.plan|lower }}">{{ tenant.plan }}</span>
                                    </td>
                                    <td>
                                        <span class="badge bg-{% if tenant.status == 'ACTIVE' %}success{% elif tenant.status == 'SUSPENDED' %}warning{% else %}secondary{% endif %}">
                                            {{ tenant.status }}
                                        </span>
                                    </td>
                                    <td>{{ tenant.user_count }}</td>
                                    <td>{{ tenant.created_at|date:"d/m/Y" }}</td>
                                    <td>
                                        <div class="btn-group">
                                            <button class="btn btn-sm btn-outline-primary" onclick="editTenant({{ tenant.tenant_id }})">
                                                <i class="bi bi-pencil"></i>
                                            </button>
                                            <button class="btn btn-sm btn-outline-info" onclick="viewTenantUsers({{ tenant.tenant_id }})">
                                                <i class="bi bi-people"></i>
                                            </button>
                                            <button class="btn btn-sm btn-outline-danger" onclick="deleteTenant({{ tenant.tenant_id }})">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal para crear/editar tenant -->
<div class="modal fade" id="createTenantModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Nuevo Taller</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="tenantForm">
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="name" class="form-label">Nombre del Taller</label>
                                <input type="text" class="form-control" id="name" name="name" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="legal_name" class="form-label">Razón Social</label>
                                <input type="text" class="form-control" id="legal_name" name="legal_name" required>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="tax_id" class="form-label">RUT/CUIT</label>
                                <input type="text" class="form-control" id="tax_id" name="tax_id" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="email" name="email" required>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="slug" class="form-label">Slug (subdominio)</label>
                                <input type="text" class="form-control" id="slug" name="slug" required>
                                <small class="form-text text-muted">Ej: taller-garcia (resultará en taller-garcia.forgecmms.com)</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="plan" class="form-label">Plan</label>
                                <select class="form-select" id="plan" name="plan" required>
                                    <option value="BASIC">Básico</option>
                                    <option value="PROFESSIONAL">Profesional</option>
                                    <option value="ENTERPRISE">Empresarial</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="phone" class="form-label">Teléfono</label>
                                <input type="tel" class="form-control" id="phone" name="phone">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="status" class="form-label">Estado</label>
                                <select class="form-select" id="status" name="status" required>
                                    <option value="ACTIVE">Activo</option>
                                    <option value="SUSPENDED">Suspendido</option>
                                    <option value="CANCELLED">Cancelado</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="address" class="form-label">Dirección</label>
                        <textarea class="form-control" id="address" name="address" rows="2"></textarea>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="city" class="form-label">Ciudad</label>
                                <input type="text" class="form-control" id="city" name="city">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="country" class="form-label">País</label>
                                <input type="text" class="form-control" id="country" name="country" value="CL">
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Guardar Taller</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function editTenant(tenantId) {
    // Cargar datos del tenant y abrir modal de edición
    fetch(`/api/platform/tenants/${tenantId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('name').value = data.name;
            document.getElementById('legal_name').value = data.legal_name;
            document.getElementById('tax_id').value = data.tax_id;
            document.getElementById('email').value = data.email;
            document.getElementById('slug').value = data.slug;
            document.getElementById('plan').value = data.plan;
            document.getElementById('status').value = data.status;
            document.getElementById('phone').value = data.phone || '';
            document.getElementById('address').value = data.address || '';
            document.getElementById('city').value = data.city || '';
            document.getElementById('country').value = data.country || 'CL';
            
            // Cambiar título del modal
            document.querySelector('#createTenantModal .modal-title').textContent = 'Editar Taller';
            document.getElementById('tenantForm').dataset.editId = tenantId;
            
            // Cambiar texto del botón submit
            document.querySelector('#createTenantModal .btn-primary').textContent = 'Actualizar Taller';
            
            // Abrir modal
            new bootstrap.Modal(document.getElementById('createTenantModal')).show();
        });
}

function deleteTenant(tenantId) {
    if (confirm('¿Está seguro de que desea desactivar este taller?')) {
        fetch(`/api/platform/tenants/${tenantId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert('Error al desactivar el taller');
            }
        });
    }
}

function viewTenantUsers(tenantId) {
    // Redirigir a la página de usuarios del tenant
    window.location.href = `/platform/tenants/${tenantId}/users/`;
}

// Manejar envío del formulario
document.getElementById('tenantForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    let url, method;
    const editId = this.dataset.editId;
    
    if (editId) {
        // Edición
        url = `/api/platform/tenants/${editId}/`;
        method = 'PUT';
    } else {
        // Creación
        url = '/api/platform/tenants/';
        method = 'POST';
    }
    
    fetch(url, {
        method: method,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('Error al guardar el taller');
        }
    });
});

// Función auxiliar para obtener CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
</script>
{% endblock %}
```

### 2. Dashboard de Administración de Tenant
```html
<!-- templates/tenant/dashboard.html -->
{% extends 'frontend/base/base.html' %}

{% block title %}Dashboard - {{ request.tenant.name }}{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1>Bienvenido a {{ request.tenant.name }}</h1>
            <p class="text-muted">Panel de control de su taller automotriz</p>
        </div>
    </div>
    
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card border-primary">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <i class="bi bi-people text-primary" style="font-size: 2rem;"></i>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h5 class="card-title">Clientes</h5>
                            <h3 class="card-text">{{ client_count }}</h3>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-success">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <i class="bi bi-tools text-success" style="font-size: 2rem;"></i>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h5 class="card-title">Técnicos</h5>
                            <h3 class="card-text">{{ technician_count }}</h3>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-warning">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <i class="bi bi-clipboard-check text-warning" style="font-size: 2rem;"></i>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h5 class="card-title">WO Abiertas</h5>
                            <h3 class="card-text">{{ open_work_orders }}</h3>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-info">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <i class="bi bi-car-front text-info" style="font-size: 2rem;"></i>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h5 class="card-title">Vehículos</h5>
                            <h3 class="card-text">{{ equipment_count }}</h3>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Últimas Órdenes de Trabajo</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Número</th>
                                    <th>Cliente</th>
                                    <th>Vehículo</th>
                                    <th>Estado</th>
                                    <th>Asignado a</th>
                                    <th>Fecha</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for wo in recent_work_orders %}
                                <tr>
                                    <td><a href="{% url 'frontend:work_order_detail' wo.id %}">#{{ wo.wo_number }}</a></td>
                                    <td>{{ wo.client.name }}</td>
                                    <td>{{ wo.equipment.display_name }}</td>
                                    <td>
                                        <span class="badge bg-{% if wo.status == 'COMPLETED' %}success{% elif wo.status == 'IN_PROGRESS' %}warning{% else %}secondary{% endif %}">
                                            {{ wo.get_status_display }}
                                        </span>
                                    </td>
                                    <td>{{ wo.assigned_technician.name }}</td>
                                    <td>{{ wo.created_at|date:"d/m/Y" }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Estadísticas</h5>
                </div>
                <div class="card-body">
                    <div class="progress mb-3">
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: {{ completion_rate }}%" 
                             aria-valuenow="{{ completion_rate }}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                            {{ completion_rate }}% Completadas
                        </div>
                    </div>
                    <p class="text-muted small">Tasa de completitud de órdenes</p>
                    
                    <div class="progress mb-3">
                        <div class="progress-bar bg-info" role="progressbar" 
                             style="width: {{ avg_completion_time }}%" 
                             aria-valuenow="{{ avg_completion_time }}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">
                            {{ avg_completion_time|floatformat:0 }} días promedio
                        </div>
                    </div>
                    <p class="text-muted small">Tiempo promedio de entrega</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 3. Componentes React para Gestión de Usuarios por Tenant
```javascript
// components/tenant/UserManagement.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Table, Form } from 'react-bootstrap';

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);
    const [formData, setFormData] = useState({
        email: '',
        role: 'TECHNICIAN',
        is_active: true
    });

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await fetch('/api/tenant/users/');
            const data = await response.json();
            setUsers(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching users:', error);
            setLoading(false);
        }
    };

    const handleShowModal = (user = null) => {
        setCurrentUser(user);
        if (user) {
            setFormData({
                email: user.email,
                role: user.role,
                is_active: user.is_active
            });
        } else {
            setFormData({
                email: '',
                role: 'TECHNICIAN',
                is_active: true
            });
        }
        setShowModal(true);
    };

    const handleClose = () => {
        setShowModal(false);
        setCurrentUser(null);
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        try {
            let response;
            if (currentUser) {
                // Actualizar usuario
                response = await fetch(`/api/tenant/users/${currentUser.id}/`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
            } else {
                // Crear nuevo usuario
                response = await fetch('/api/tenant/users/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
            }
            
            if (response.ok) {
                await fetchUsers(); // Refrescar lista
                handleClose();
            } else {
                console.error('Error saving user:', await response.text());
            }
        } catch (error) {
            console.error('Error saving user:', error);
        }
    };

    const toggleUserStatus = async (userId, currentStatus) => {
        try {
            const response = await fetch(`/api/tenant/users/${userId}/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_active: !currentStatus })
            });
            
            if (response.ok) {
                await fetchUsers(); // Refrescar lista
            }
        } catch (error) {
            console.error('Error toggling user status:', error);
        }
    };

    const deleteUser = async (userId) => {
        if (window.confirm('¿Está seguro de que desea eliminar este usuario?')) {
            try {
                const response = await fetch(`/api/tenant/users/${userId}/`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                
                if (response.ok) {
                    await fetchUsers(); // Refrescar lista
                }
            } catch (error) {
                console.error('Error deleting user:', error);
            }
        }
    };

    if (loading) return <div className="text-center p-4">Cargando usuarios...</div>;

    return (
        <div className="user-management">
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h3>Usuarios del Taller</h3>
                <Button variant="primary" onClick={() => handleShowModal()}>
                    <i className="bi bi-plus-lg"></i> Agregar Usuario
                </Button>
            </div>
            
            <Table striped bordered hover responsive>
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Email</th>
                        <th>Rol</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map(user => (
                        <tr key={user.id}>
                            <td>{user.first_name} {user.last_name}</td>
                            <td>{user.email}</td>
                            <td>
                                <span className={`badge bg-${user.role.toLowerCase()}`}>
                                    {user.role_display}
                                </span>
                            </td>
                            <td>
                                <span className={`badge ${user.is_active ? 'bg-success' : 'bg-secondary'}`}>
                                    {user.is_active ? 'Activo' : 'Inactivo'}
                                </span>
                            </td>
                            <td>
                                <div className="btn-group">
                                    <Button 
                                        size="sm" 
                                        variant={user.is_active ? "outline-secondary" : "outline-success"}
                                        onClick={() => toggleUserStatus(user.id, user.is_active)}
                                    >
                                        {user.is_active ? 'Desactivar' : 'Activar'}
                                    </Button>
                                    <Button 
                                        size="sm" 
                                        variant="outline-primary" 
                                        onClick={() => handleShowModal(user)}
                                    >
                                        Editar
                                    </Button>
                                    <Button 
                                        size="sm" 
                                        variant="outline-danger" 
                                        onClick={() => deleteUser(user.id)}
                                    >
                                        Eliminar
                                    </Button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </Table>

            {/* Modal para crear/editar usuarios */}
            <Modal show={showModal} onHide={handleClose}>
                <Modal.Header closeButton>
                    <Modal.Title>
                        {currentUser ? 'Editar Usuario' : 'Agregar Nuevo Usuario'}
                    </Modal.Title>
                </Modal.Header>
                <Form onSubmit={handleSubmit}>
                    <Modal.Body>
                        <Form.Group className="mb-3">
                            <Form.Label>Email</Form.Label>
                            <Form.Control
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                required
                            />
                        </Form.Group>
                        
                        <Form.Group className="mb-3">
                            <Form.Label>Rol</Form.Label>
                            <Form.Select
                                name="role"
                                value={formData.role}
                                onChange={handleInputChange}
                                required
                            >
                                <option value="ADMIN">Admin Taller</option>
                                <option value="MANAGER">Gerente</option>
                                <option value="TECHNICIAN">Técnico</option>
                                <option value="VIEWER">Visualizador</option>
                            </Form.Select>
                        </Form.Group>
                        
                        <Form.Group className="mb-3">
                            <Form.Check
                                type="checkbox"
                                name="is_active"
                                label="Usuario Activo"
                                checked={formData.is_active}
                                onChange={handleInputChange}
                            />
                        </Form.Group>
                    </Modal.Body>
                    <Modal.Footer>
                        <Button variant="secondary" onClick={handleClose}>
                            Cancelar
                        </Button>
                        <Button variant="primary" type="submit">
                            {currentUser ? 'Actualizar' : 'Crear'} Usuario
                        </Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </div>
    );
};

export default UserManagement;
```

### 4. Barra de Navegación Personalizada por Tenant
```html
<!-- templates/tenant/base.html -->
{% extends 'frontend/base/base.html' %}

{% block extra_nav %}
{% if request.tenant %}
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
        <a class="navbar-brand" href="{% url 'frontend:tenant_dashboard' %}">
            <i class="bi bi-building me-2"></i>{{ request.tenant.name }}
        </a>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#tenantNavbar">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="tenantNavbar">
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'frontend:tenant_dashboard' %}">
                        <i class="bi bi-speedometer2 me-1"></i> Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'frontend:client_list' %}">
                        <i class="bi bi-people me-1"></i> Clientes
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'frontend:work_order_list' %}">
                        <i class="bi bi-clipboard-check me-1"></i> Órdenes
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'frontend:equipment_list' %}">
                        <i class="bi bi-car-front me-1"></i> Vehículos
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'frontend:technician_list' %}">
                        <i class="bi bi-tools me-1"></i> Técnicos
                    </a>
                </li>
            </ul>
            
            <ul class="navbar-nav">
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" id="tenantMenu" data-bs-toggle="dropdown">
                        <i class="bi bi-person-circle me-1"></i> {{ request.user.username }}
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="{% url 'frontend:profile' %}"><i class="bi bi-person me-2"></i> Mi Perfil</a></li>
                        <li><a class="dropdown-item" href="{% url 'frontend:user_management' %}"><i class="bi bi-people me-2"></i> Usuarios del Taller</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="{% url 'frontend:tenant_settings' %}"><i class="bi bi-gear me-2"></i> Configuración</a></li>
                        <li><a class="dropdown-item" href="{% url 'frontend:logout' %}"><i class="bi bi-box-arrow-right me-2"></i> Salir</a></li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</nav>
{% endif %}
{% endblock %}
```

## Gestión de Seguridad y Acceso

### 1. Control de Acceso Basado en Roles
```python
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from .models import UserTenant

class TenantAccessPermission(BasePermission):
    """Permiso para verificar que el usuario tiene acceso al tenant actual"""
    
    def has_permission(self, request, view):
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return False
        
        # Verificar que el request tenga un tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        
        # Verificar que el usuario tenga acceso a este tenant
        try:
            user_tenant = UserTenant.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )
            request.user_role = user_tenant.role
            return True
        except UserTenant.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # Verificar que el objeto pertenece al tenant del usuario
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.tenant
        return True

class PlatformAdminPermission(BasePermission):
    """Permiso para usuarios de plataforma (staff/superuser)"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )

def tenant_admin_required(view_func):
    """Decorador para vistas que requieren rol de admin en el tenant"""
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            raise PermissionDenied("Tenant requerido")
        
        try:
            user_tenant = UserTenant.objects.get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )
            
            if user_tenant.role in ['ADMIN', 'MANAGER']:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied("Se requiere rol de admin o manager")
        except UserTenant.DoesNotExist:
            raise PermissionDenied("No tiene acceso a este taller")
    
    return wrapper
```

### 2. Auditoría de Acceso
```python
from django.db import models
from django.contrib.auth.models import User

class AccessAudit(models.Model):
    """Registro de auditoría de acceso a datos por tenant"""
    AUDIT_ACTIONS = [
        ('CREATE', 'Creación'),
        ('READ', 'Lectura'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
    ]
    
    audit_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=AUDIT_ACTIONS)
    resource_type = models.CharField(max_length=50)  # 'client', 'work_order', 'equipment', etc.
    resource_id = models.IntegerField()
    old_values = models.JSONField(null=True, blank=True)  # Valores antes de la modificación
    new_values = models.JSONField(null=True, blank=True)  # Valores después de la modificación
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    class Meta:
        db_table = 'access_audit'
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def save(self, *args, **kwargs):
        # Registrar auditoría antes de guardar
        super().save(*args, **kwargs)
```

## Plan de Implementación por Fases

### Fase 1: Infraestructura de Multitenancia (2-3 semanas)
- [ ] Crear modelo `Tenant` y tabla en base de datos
- [ ] Crear modelo `UserTenant` para relación usuario-tenant-rol
- [ ] Implementar middleware de resolución de tenant
- [ ] Crear managers por defecto con filtro de tenant
- [ ] Añadir campo `tenant` a modelos operativos (Client, Technician, WorkOrder, etc.)
- [ ] Crear migraciones para modelos nuevos y modificados
- [ ] Migrar datos existentes a un tenant por defecto

### Fase 2: Backend: Contexto Tenant y Filtrado (2-3 semanas)
- [ ] Adaptar todas las vistas/APIs para filtrar por tenant
- [ ] Implementar serializadores adaptados para tenant
- [ ] Actualizar lógica de autenticación para incluir información de tenant
- [ ] Crear decoradores y permisos de seguridad por tenant
- [ ] Implementar auditoría de acceso
- [ ] Probar aislamiento de datos entre tenants

### Fase 3: API y Pantallas de Plataforma (1-2 semanas)
- [ ] Crear API endpoints para gestión de tenants (solo staff)
- [ ] Desarrollar vistas de listado y gestión de tenants
- [ ] Crear interfaces para alta y edición de tenants
- [ ] Implementar gestión de usuarios por tenant
- [ ] Desarrollar dashboard de administración de plataforma

### Fase 4: Adaptación de Funcionalidades Existentes (2-3 semanas)
- [ ] Adaptar todas las vistas existentes para usar tenant
- [ ] Actualizar formularios existentes para incluir contexto de tenant
- [ ] Modificar lógica de negocio para considerar tenant
- [ ] Adaptar reportes y estadísticas por tenant
- [ ] Actualizar notificaciones y procesos automáticos

### Fase 5: Frontend de Tenant (1-2 semanas)
- [ ] Crear dashboard específico por tenant
- [ ] Desarrollar componentes React para gestión de usuarios por tenant
- [ ] Actualizar barra de navegación con contexto de tenant
- [ ] Adaptar todas las pantallas operativas para usar tenant
- [ ] Implementar selector de tenant para usuarios multi-tenant (opcional)

### Fase 6: Suscripciones y Facturación (2-3 semanas)
- [ ] Crear modelos de planes de suscripción
- [ ] Implementar lógica de límites por plan
- [ ] Integrar con sistema de pagos
- [ ] Crear paneles de facturación
- [ ] Implementar notificaciones de vencimiento

### Fase 7: Pruebas y Despliegue (1 semana)
- [ ] Pruebas de aislamiento de datos
- [ ] Pruebas de rendimiento con múltiples tenants
- [ ] Pruebas de seguridad
- [ ] Pruebas de usuario final
- [ ] Documentación del sistema
- [ ] Plan de migración para tenants existentes

## Consideraciones Técnicas

### 1. Rendimiento
- Implementar índices compuestos por `(tenant_id, ...)` en todas las tablas operativas
- Considerar particionamiento horizontal si se espera gran cantidad de tenants
- Implementar caché por tenant para datos frecuentemente accedidos
- Optimizar consultas con `select_related` y `prefetch_related` adecuados

### 2. Seguridad
- Validación exhaustiva de que los usuarios solo acceden a datos de su tenant
- Auditoría completa de todas las operaciones
- Encriptación de datos sensibles
- Validación de subdominios para prevenir ataque de inyección

### 3. Escalabilidad
- Arquitectura preparada para múltiples servidores de aplicación
- Considerar balanceo de carga entre tenants
- Implementar monitorización de recursos por tenant
- Preparar para sharding horizontal si es necesario

### 4. Backup y Recuperación
- Estrategia de backup por tenant para recuperación selectiva
- Procedimientos de restauración a nivel de tenant
- Versionado de datos para recuperación de punto en el tiempo

### 5. Costos
- Implementar límites por plan de suscripción
- Medición de uso de recursos por tenant
- Optimización de consumo de base de datos
- Considerar costos de hosting y mantenimiento por tenant

---

*Documento elaborado combinando las recomendaciones existentes en SAAS_MULTITENANCY_RECOMMENDATIONS.md con propuestas adicionales. Este plan servirá como guía para la transformación completa del sistema actual en una plataforma SaaS multitenant funcional y escalable.*