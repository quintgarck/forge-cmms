# Plan de Transformación a Arquitectura SaaS para Plataforma de Talleres Automotrices

## Tabla de Contenidos
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis de la Situación Actual](#análisis-de-la-situación-actual)
3. [Objetivos del Proyecto](#objetivos-del-proyecto)
4. [Arquitectura SaaS Propuesta](#arquitectura-saas-propuesta)
5. [Modelos de Base de Datos](#modelos-de-base-de-datos)
6. [Cambios en el Backend](#cambios-en-el-backend)
7. [Cambios en el Frontend](#cambios-en-el-frontend)
8. [Gestión de Seguridad y Acceso](#gestión-de-seguridad-y-acceso)
9. [Plan de Implementación](#plan-de-implementación)
10. [Consideraciones Técnicas](#consideraciones-técnicas)

## Resumen Ejecutivo

Este documento detalla el plan integral para transformar el sistema actual de gestión para talleres automotrices en una plataforma SaaS (Software as a Service) multitenant. La transformación permitirá que múltiples empresas de talleres automotrices utilicen la plataforma de manera aislada, cada una con sus propios datos, usuarios y configuraciones.

## Análisis de la Situación Actual

### Limitaciones del Sistema Actual
- **Arquitectura Monolítica**: Diseñado para una sola empresa/instancia
- **Falta de Aislamiento de Datos**: No existe separación entre diferentes empresas
- **Usuario Único de Sistema**: No hay distinción entre usuarios administrativos y usuarios de clientes
- **Ausencia de Gestión de Clientes**: No hay modelos para empresas clientes ni suscripciones
- **No Hay Facturación**: No existe sistema de planes de servicio ni cobros

### Ventajas del Sistema Actual
- **Funcionalidades Completas**: Catálogos, órdenes de trabajo, inventario, etc.
- **Buena Arquitectura**: Código organizado y mantenible
- **Interfaz de Usuario**: Experiencia de usuario bien desarrollada

## Objetivos del Proyecto

### Objetivo Principal
Transformar la plataforma en un sistema SaaS multitenant donde múltiples empresas puedan contratar servicios de gestión para sus talleres automotrices.

### Objetivos Secundarios
- Implementar aislamiento de datos por empresa
- Crear sistema de suscripciones y facturación
- Mantener la funcionalidad existente
- Asegurar escalabilidad horizontal
- Preservar la calidad del código

## Arquitectura SaaS Propuesta

### Estrategia de Multitenancia
**Recomendación**: Estrategia de "Schema por Tenant" con un esquema compartido para tablas de sistema y esquemas individuales para datos de cada cliente.

### Componentes Principales
```
SaaS Platform Structure:
├── Shared Schema (core tables)
│   ├── tenants (ClientCompany)
│   ├── subscriptions
│   ├── plans
│   └── system_users
├── Tenant Schema 1 (customer data)
│   ├── work_orders
│   ├── inventory
│   ├── employees
│   └── customizations
├── Tenant Schema 2 (customer data)
│   └── ...
└── Tenant Schema N (customer data)
    └── ...
```

## Modelos de Base de Datos

### Nuevos Modelos Principales

#### 1. ClientCompany (Empresa Cliente)
```python
class ClientCompany(models.Model):
    company_id = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=100)
    legal_name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=30, unique=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_users = models.IntegerField(default=10)
    max_vehicles = models.IntegerField(default=100)
    tenant_schema = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_companies')
    
    class Meta:
        db_table = 'tenants.companies'
        indexes = [
            models.Index(fields=['tax_id']),
            models.Index(fields=['tenant_schema']),
        ]
```

#### 2. SubscriptionPlan (Plan de Suscripción)
```python
class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('BASIC', 'Básico'),
        ('PROFESSIONAL', 'Profesional'),
        ('ENTERPRISE', 'Empresarial'),
    ]
    
    plan_id = models.AutoField(primary_key=True)
    plan_name = models.CharField(max_length=50)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.IntegerField()
    max_vehicles = models.IntegerField()
    max_work_orders = models.IntegerField()
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenants.subscription_plans'
```

#### 3. ClientSubscription (Suscripción de Cliente)
```python
class ClientSubscription(models.Model):
    subscription_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(ClientCompany, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Activo'),
        ('EXPIRED', 'Expirado'),
        ('CANCELLED', 'Cancelado'),
        ('PAST_DUE', 'Atrasado'),
    ])
    payment_method = models.CharField(max_length=20)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenants.subscriptions'
```

#### 4. TenantUser (Usuario de Empresa)
```python
class TenantUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(ClientCompany, on_delete=models.CASCADE, related_name='users')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('ADMIN', 'Administrador'),
        ('MANAGER', 'Gerente'),
        ('TECHNICIAN', 'Técnico'),
        ('CLERK', 'Auxiliar'),
    ])
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenants.users'
        unique_together = [['company', 'user']]
```

### Modificaciones a Modelos Existentes

Todos los modelos existentes (WorkOrder, Inventory, Equipment, etc.) deben modificarse para incluir una referencia al tenant:

```python
class WorkOrder(models.Model):
    # ... campos existentes ...
    tenant_company = models.ForeignKey(ClientCompany, on_delete=models.CASCADE)
    # ... resto de campos ...
```

## Cambios en el Backend

### 1. Middleware de Multitenancia
```python
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Determinar tenant actual basado en dominio/subdominio
        host = request.get_host()
        tenant = self.get_tenant_for_host(host)
        
        if tenant:
            # Cambiar esquema de base de datos
            connection.set_tenant(tenant)
            request.tenant = tenant
        else:
            # Para usuarios del sistema (no tenants)
            connection.set_schema_to_public()
        
        response = self.get_response(request)
        return response
```

### 2. Decoradores de Seguridad
```python
def tenant_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            return redirect('tenant_not_found')
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 3. Serializadores Adaptados
```python
class TenantWorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = '__all__'
        read_only_fields = ['tenant_company']
    
    def create(self, validated_data):
        # Asegurar que el objeto pertenece al tenant actual
        validated_data['tenant_company'] = self.context['request'].tenant
        return super().create(validated_data)
```

### 4. Vistas Protegidas
```python
@method_decorator(tenant_required, name='dispatch')
class TenantWorkOrderListView(ListView):
    model = WorkOrder
    template_name = 'tenant/work_orders/list.html'
    
    def get_queryset(self):
        return WorkOrder.objects.filter(
            tenant_company=self.request.tenant
        )
```

### 5. API Endpoints para Gestión de Tenants
```python
# API para administradores del sistema
class AdminTenantAPI(APIView):
    permission_classes = [IsSystemAdmin]
    
    def get(self, request):
        tenants = ClientCompany.objects.all()
        serializer = ClientCompanySerializer(tenants, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        # Crear nuevo tenant y esquema
        serializer = ClientCompanySerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save()
            # Crear esquema para el tenant
            self.create_tenant_schema(company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## Cambios en el Frontend

### 1. Nueva Interfaz de Registro de Clientes
```html
<!-- templates/registration/signup_tenant.html -->
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h4>Registro de Nueva Empresa</h4>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        {{ form.as_p }}
                        <button type="submit" class="btn btn-primary">Registrarse</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 2. Dashboard de Administración de Tenant
```html
<!-- templates/tenant/dashboard.html -->
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1>Panel de Administración - {{ request.tenant.company_name }}</h1>
            <div class="row">
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>Usuarios</h5>
                            <p>{{ user_count }} / {{ request.tenant.max_users }}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card">
                        <div class="card-body">
                            <h5>Vehículos</h5>
                            <p>{{ vehicle_count }} / {{ request.tenant.max_vehicles }}</p>
                        </div>
                    </div>
                </div>
                <!-- Más estadísticas -->
            </div>
        </div>
    </div>
</div>
```

### 3. Componentes React para Gestión de Usuarios
```javascript
// components/tenant/UserManagement.jsx
import React, { useState, useEffect } from 'react';

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/tenant/users/')
            .then(response => response.json())
            .then(data => {
                setUsers(data);
                setLoading(false);
            });
    }, []);

    const deleteUser = (userId) => {
        fetch(`/api/tenant/users/${userId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        }).then(() => {
            setUsers(users.filter(user => user.id !== userId));
        });
    };

    if (loading) return <div>Cargando...</div>;

    return (
        <div className="user-management">
            <h3>Usuarios de la Empresa</h3>
            <table className="table">
                <thead>
                    <tr>
                        <th>Nombre</th>
                        <th>Rol</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map(user => (
                        <tr key={user.id}>
                            <td>{user.first_name} {user.last_name}</td>
                            <td>{user.role}</td>
                            <td>
                                <button onClick={() => deleteUser(user.id)} className="btn btn-danger">
                                    Eliminar
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default UserManagement;
```

### 4. Barra de Navegación Personalizada por Tenant
```html
<!-- templates/tenant/base.html -->
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
        <a class="navbar-brand" href="#">
            {{ request.tenant.company_name }}
        </a>
        <div class="navbar-nav ms-auto">
            <span class="navbar-text me-3">
                Plan: {{ request.tenant.current_subscription.plan.plan_name }}
            </span>
            <a class="nav-link" href="/tenant/profile/">Mi Empresa</a>
            <a class="nav-link" href="/tenant/users/">Usuarios</a>
            <a class="nav-link" href="/tenant/billing/">Facturación</a>
        </div>
    </div>
</nav>
```

## Gestión de Seguridad y Acceso

### 1. Control de Acceso Basado en Roles
```python
# permissions/tenant_permissions.py
class TenantAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request, 'tenant'):
            return False
        
        if view.action == 'list':
            return request.user.has_perm('tenant.view_workorder')
        elif view.action in ['create']:
            return request.user.has_perm('tenant.add_workorder')
        elif view.action in ['update', 'partial_update']:
            return request.user.has_perm('tenant.change_workorder')
        elif view.action == 'destroy':
            return request.user.has_perm('tenant.delete_workorder')
        
        return True

    def has_object_permission(self, request, view, obj):
        # Asegurar que el objeto pertenece al tenant del usuario
        return obj.tenant_company == request.tenant
```

### 2. Auditoría de Acceso
```python
class AccessAudit(models.Model):
    audit_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(ClientCompany, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        db_table = 'tenants.access_audit'
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
```

## Plan de Implementación

### Fase 1: Infraestructura de Multitenancia (2-3 semanas)
- [ ] Crear modelos de tenant (ClientCompany, SubscriptionPlan, etc.)
- [ ] Implementar middleware de multitenancia
- [ ] Configurar esquemas de base de datos
- [ ] Crear migraciones para modelos de tenant

### Fase 2: Sistema de Registro y Autenticación (2 semanas)
- [ ] Página de registro para nuevas empresas
- [ ] Flujo de activación de cuentas
- [ ] Sistema de autenticación por tenant
- [ ] Roles y permisos por tenant

### Fase 3: Adaptación de Modelos Existentes (2-3 semanas)
- [ ] Modificar todos los modelos existentes para incluir tenant
- [ ] Actualizar vistas para filtrar por tenant
- [ ] Adaptar formularios existentes
- [ ] Asegurar que todas las consultas estén aisladas por tenant

### Fase 4: Interfaz de Administración de Tenant (1-2 semanas)
- [ ] Dashboard de administración de tenant
- [ ] Gestión de usuarios por tenant
- [ ] Configuración de empresa
- [ ] Estadísticas y métricas por tenant

### Fase 5: Sistema de Suscripciones y Facturación (2-3 semanas)
- [ ] Modelos de planes y suscripciones
- [ ] Integración con pasarela de pagos
- [ ] Sistema de notificaciones de vencimiento
- [ ] Panel de facturación

### Fase 6: Pruebas y Despliegue (1 semana)
- [ ] Pruebas de aislamiento de datos
- [ ] Pruebas de rendimiento
- [ ] Pruebas de seguridad
- [ ] Documentación del sistema

## Consideraciones Técnicas

### 1. Rendimiento
- Uso de índices apropiados para consultas por tenant
- Considerar particionamiento de tablas grandes
- Implementar caché por tenant

### 2. Seguridad
- Validación exhaustiva de acceso a recursos
- Auditoría de todas las operaciones
- Encriptación de datos sensibles

### 3. Escalabilidad
- Arquitectura preparada para múltiples servidores
- Balanceo de carga entre tenants
- Monitorización de recursos por tenant

### 4. Backup y Recuperación
- Backup separado por tenant
- Procedimientos de recuperación por tenant
- Versionado de datos por tenant

### 5. Costos
- Evaluación de recursos por tenant
- Optimización de uso de base de datos
- Costos de hosting y mantenimiento

### 6. Costos
- Evaluación de recursos por tenant
- Optimización de uso de base de datos
- Costos de hosting y mantenimiento

---

*Documento elaborado el día actual. Este plan servirá como guía para la transformación del sistema actual en una plataforma SaaS multitenant completa y funcional.*