# Plan unificado de transformación SaaS – Forge CMMS

Este documento integra el **Plan de Transformación a Arquitectura SaaS** (`SaaS_Transformation_Plan.md`) y las **Recomendaciones de multi-tenancy** (`SAAS_MULTITENANCY_RECOMMENDATIONS.md`) en un solo plan de implementación.

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Estado actual del sistema](#2-estado-actual-del-sistema)
3. [Objetivos](#3-objetivos)
4. [Estrategia de multi-tenancy](#4-estrategia-de-multi-tenancy)
5. [Modelos de base de datos](#5-modelos-de-base-de-datos)
6. [Cambios en backend](#6-cambios-en-backend)
7. [Cambios en frontend](#7-cambios-en-frontend)
8. [Seguridad y auditoría](#8-seguridad-y-auditoría)
9. [Plan de implementación por fases](#9-plan-de-implementación-por-fases)
10. [Consideraciones técnicas](#10-consideraciones-técnicas)

---

## 1. Resumen ejecutivo

El sistema actual está pensado para **un solo taller**. Para ofrecerlo como **SaaS a múltiples talleres** es necesario:

- Introducir la capa **Tenant** (empresa cliente del SaaS = taller que contrata el sistema).
- Aislar todos los datos operativos por tenant.
- Diferenciar **usuarios de plataforma** (administran empresas cliente) y **usuarios de tenant** (colaboradores del taller que usan el sistema).
- Añadir **suscripciones y planes** (y opcionalmente facturación).

La transformación debe mantener la funcionalidad existente (catálogos, órdenes de trabajo, inventario, etc.) y permitir escalabilidad y seguridad por tenant.

---

## 2. Estado actual del sistema

### Limitaciones (de ambos documentos)

- **Un solo “tenant” implícito**: no existe el concepto de empresa cliente (taller que paga el SaaS).
- **Sin aislamiento**: ninguna tabla tiene `tenant_id`; no hay forma de ver “cuántos clientes (tenants) tengo”.
- **Client** = clientes del taller (quienes llevan el auto a reparar), **no** la empresa que paga el SaaS.
- **Technician** y **User**: sin vínculo a “a qué taller pertenecen”.
- **Auth**: JWT + TechnicianAuthBackend; no hay contexto de tenant ni roles por tenant.
- **Frontend**: sin pantallas de administración de empresas cliente ni de suscripciones.

### Ventajas a preservar

- Funcionalidades completas (catálogos, WO, inventario, facturas, etc.).
- Código organizado (core, frontend, APIs).
- Buena experiencia de usuario en la interfaz actual.

---

## 3. Objetivos

| Objetivo | Descripción |
|----------|-------------|
| **Principal** | Transformar la plataforma en SaaS multi-tenant con múltiples talleres (tenants) aislados. |
| **Datos** | Aislamiento total de datos por tenant; consultas y altas siempre filtradas por tenant. |
| **Usuarios** | Distinguir admin plataforma (gestión de tenants) y usuarios por tenant (colaboradores del taller). |
| **Visibilidad** | Poder ver y gestionar “cuántas empresas cliente (tenants) tengo” y sus usuarios/suscripciones. |
| **Suscripciones** | Planes (Básico, Profesional, etc.) y suscripción por tenant; límites (usuarios, vehículos) según plan. |
| **No romper** | Mantener la funcionalidad actual y migrar los datos existentes a un tenant por defecto. |

---

## 4. Estrategia de multi-tenancy

Se consideran dos enfoques; el plan unificado recomienda **A** para la primera versión.

### Opción A: Tenant por fila (recomendada para arranque)

- **Una sola base de datos**; tablas operativas con columna **`tenant_id`** (FK a `tenants`).
- Todas las consultas filtran por `tenant_id`; en altas se asigna `tenant_id` del request.
- **Ventajas**: implementación más simple, una sola migración por tabla, backups y despliegue estándar.
- **Desventajas**: un error de filtrado podría filtrar datos entre tenants (mitigable con managers y tests).

### Opción B: Schema por tenant

- Esquema **compartido** para tablas de sistema (`tenants`, `subscription_plans`, `user_tenants`, etc.).
- **Un esquema por tenant** (ej. `tenant_001`, `tenant_002`) con copia de tablas operativas (work_orders, clients, etc.).
- Middleware cambia `search_path` según el tenant (`connection.set_tenant(tenant)`).
- **Ventajas**: aislamiento fuerte a nivel de esquema.
- **Desventajas**: más complejidad (migraciones x N, provisioning de esquemas, backups por esquema). Adecuado para fases posteriores o planes “Enterprise”.

**Decisión para este plan**: implementar **Opción A** (tenant por fila). Si más adelante se requiere schema por tenant para clientes enterprise, se puede plantear como evolución.

---

## 5. Modelos de base de datos

### 5.1 Esquema compartido / tablas de sistema

Todas estas tablas **no** llevan `tenant_id`; viven en esquema `public` o en un esquema `platform`/`tenants`.

#### 5.1.1 Tenant (empresa cliente del SaaS)

Equivalente a “ClientCompany” del plan original. Una fila = un taller que usa el sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tenant_id` | PK | Identificador interno. |
| `name` | string | Nombre comercial (ej. “Taller García”). |
| `legal_name` | string | Razón social. |
| `tax_id` | string | RFC/CIF/NIF, único. |
| `slug` | string | Único; para subdominio o URL (ej. `taller-garcia`). |
| `contact_email` | email | Contacto principal. |
| `contact_phone` | string | Teléfono. |
| `address`, `city`, `state`, `country`, `postal_code` | string | Dirección. |
| `status` | enum | activo, suspendido, cancelado. |
| `settings` | JSONB | Configuración por taller (moneda, idioma, etc.). |
| `max_users` | int | Límite de usuarios (según plan). |
| `max_vehicles` | int | Límite de vehículos/equipos (según plan). |
| `created_at`, `updated_at` | datetime | Auditoría. |

Opcional: si no se usa “schema por tenant”, no hace falta `tenant_schema`. Si en el futuro se adopta Opción B, se puede añadir.

#### 5.1.2 UserTenant (usuario ↔ tenant, N:N)

Un usuario puede pertenecer a **varios** tenants (ej. gerente de dos sucursales) con un rol por tenant.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | PK | Identificador. |
| `user_id` | FK → auth.User | Usuario. |
| `tenant_id` | FK → Tenant | Tenant (taller). |
| `role` | enum | admin_taller, manager, technician, clerk, viewer. |
| `is_default` | bool | Si es el tenant por defecto al iniciar sesión. |
| `is_active` | bool | Si sigue teniendo acceso. |
| `created_at` | datetime | Fecha de asignación. |

**Unique**: `(user_id, tenant_id)`.

- **Plataforma**: usuarios con `is_staff`/`is_superuser` que **no** tienen filas en UserTenant (o con flag “solo plataforma”) actúan como admin de plataforma.
- **Tenant**: usuarios con al menos una fila en UserTenant solo ven datos de los tenants a los que pertenecen.

#### 5.1.3 SubscriptionPlan (planes de suscripción)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `plan_id` | PK | Identificador. |
| `plan_name` | string | Ej. “Básico”, “Profesional”. |
| `plan_type` | enum | BASIC, PROFESSIONAL, ENTERPRISE. |
| `monthly_price` | decimal | Precio mensual. |
| `max_users` | int | Límite de usuarios. |
| `max_vehicles` | int | Límite de vehículos. |
| `max_work_orders` | int | Opcional; límite de Órdenes de trabajo. |
| `features` | JSON | Lista de características incluidas. |
| `is_active` | bool | Si el plan está disponible. |
| `created_at` | datetime | Auditoría. |

#### 5.1.4 ClientSubscription (suscripción activa de un tenant)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `subscription_id` | PK | Identificador. |
| `tenant_id` | FK → Tenant | Empresa cliente. |
| `plan_id` | FK → SubscriptionPlan | Plan contratado. |
| `start_date` | date | Inicio de vigencia. |
| `end_date` | date | Fin de vigencia. |
| `status` | enum | ACTIVE, EXPIRED, CANCELLED, PAST_DUE. |
| `payment_method` | string | Opcional. |
| `auto_renew` | bool | Renovación automática. |
| `created_at` | datetime | Auditoría. |

#### 5.1.5 AccessAudit (auditoría de acceso – opcional pero recomendada)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `audit_id` | PK | Identificador. |
| `user_id` | FK → User | Usuario. |
| `tenant_id` | FK → Tenant, nullable | Tenant (null si es acción de plataforma). |
| `action` | string | Ej. “view”, “create”, “update”, “delete”. |
| `resource_type` | string | Ej. “work_order”, “client”. |
| `resource_id` | int | ID del recurso. |
| `timestamp` | datetime | Momento del acceso. |
| `ip_address` | string | IP del request. |

### 5.2 Tablas operativas: añadir `tenant_id`

Todas las tablas que contienen **datos del taller** deben tener `tenant_id` (FK a `Tenant`) y ser filtradas en todas las consultas.

| Modelo / tabla | Comentario |
|----------------|------------|
| `Client` (clients) | Clientes del taller (quienes llevan el auto). |
| `Technician` (technicians) | Colaboradores del taller. |
| `Equipment` (equipment) | Vehículos/equipos de los clientes del taller. |
| `WorkOrder` (work_orders) | Órdenes de trabajo. |
| `Invoice` (invoices) | Facturas. |
| `Quote` (quotes) | Cotizaciones. |
| `Warehouse` (warehouses) | Almacenes. |
| `ProductMaster` (product_master) | Opcional: compartido globalmente con catálogo y solo stock por tenant; o con tenant_id si cada taller tiene su catálogo. |
| `Stock` (stock) | Por almacén → el warehouse ya tendrá tenant_id. |
| `Document` (documents) | Documentos del taller. |
| Otras operativas (alertas, WO items, etc.) | Según corresponda; si son datos del taller, llevar `tenant_id` o heredar vía FK (ej. wo_items vía work_order). |

### 5.3 Tablas que NO llevan tenant_id (catálogos globales)

- Códigos de referencia (combustible, transmisión, color, etc.).
- Tipos de equipo, categorías de equipo, taxonomía.
- OEM (marcas, equivalencias), UOM, categorías/tipos de producto.
- Monedas (o por tenant si cada taller elige su moneda).
- SubscriptionPlan (es de sistema).

### 5.4 Migración de datos existentes

1. Crear tabla `tenants` y un registro **tenant por defecto** (ej. “Taller demo” o “Mi taller”).
2. Crear `user_tenants` y, si aplica, `subscription_plans` y `client_subscriptions`.
3. Añadir columna `tenant_id` (nullable) a las tablas operativas listadas.
4. Actualizar todos los registros existentes: `UPDATE ... SET tenant_id = <id_tenant_por_defecto>`.
5. Poner `tenant_id` NOT NULL y crear FK e índices compuestos `(tenant_id, ...)` según uso.

---

## 6. Cambios en backend

### 6.1 Middleware de tenant

- Resolver el tenant en cada request y asignar **`request.tenant`** (y opcionalmente `request.tenant_id`).
- Lógica sugerida:
  - Si el usuario es **staff/superuser** y no tiene registros en `UserTenant` (o tiene flag “solo plataforma”): **modo plataforma** → `request.tenant = None`; puede acceder a `/api/platform/*` y listado de tenants.
  - Si el usuario tiene registros en `UserTenant`:
    - Resolver tenant por **header** (`X-Tenant-Id` o `X-Tenant-Slug`), o por **subdominio** (ej. `taller-garcia.app.com` → slug → tenant), o por **tenant por defecto** (`is_default=True`).
    - Validar que el usuario pertenezca a ese tenant (UserTenant).
    - Asignar `request.tenant`.
- No hacer `connection.set_schema()` si se sigue la Opción A (tenant por fila).

### 6.2 Filtrado por tenant en vistas y APIs

- En todas las vistas/APIs que lean o escriban Client, Technician, WorkOrder, Equipment, Invoice, etc.:
  - **Lecturas**: filtrar por `request.tenant_id` (o `request.tenant.id`).
  - **Altas**: asignar `tenant_id = request.tenant_id`.
- Recomendación: usar un **manager por defecto** en Django que inyecte el tenant actual (variable de thread-local o similar) para no olvidar el filtro.

### 6.3 Serializadores y creación

- En creación, no confiar en el cliente para `tenant_id`; asignar siempre desde `request.tenant` en el serializer o en la vista.

### 6.4 API de plataforma (solo staff/superuser)

- `GET /api/platform/tenants/` – Listar tenants (aquí se ve “cuántos clientes tengo”), con filtros y paginación.
- `POST /api/platform/tenants/` – Crear tenant (y opcionalmente usuario admin y suscripción).
- `GET/PATCH/PUT /api/platform/tenants/<id>/` – Detalle y edición.
- `POST /api/platform/tenants/<id>/suspend/` – Suspender tenant.
- `GET /api/platform/tenants/<id>/users/` – Listar usuarios del tenant (UserTenant).
- `POST /api/platform/tenants/<id>/users/` – Asignar usuario al tenant (rol).
- `DELETE /api/platform/tenants/<id>/users/<user_tenant_id>/` – Quitar usuario del tenant.

### 6.5 Autenticación y JWT

- Tras el login, incluir en la respuesta (o en el payload del JWT):
  - `tenant_id` y `tenant_slug` del tenant por defecto del usuario.
  - Lista de `tenants` a los que tiene acceso (id, name, slug, role) para selector en el frontend.
- El frontend enviará en cada petición el tenant elegido (header `X-Tenant-Id` o similar); el backend validará contra UserTenant.

### 6.6 Permisos

- **Plataforma**: `IsAuthenticated` + (`is_staff` o `is_superuser`) para rutas `/api/platform/*`.
- **Tenant**: permisos por recurso (view_workorder, add_client, etc.) comprobando además que `obj.tenant_id == request.tenant_id` (o que el recurso pertenezca al tenant vía FK).

---

## 7. Cambios en frontend

### 7.1 Usuario plataforma (admin)

- Menú o sección **“Empresas cliente”** / **“Talleres”** (solo visible para staff/superuser cuando está en modo plataforma).
- **Listado**: cantidad total de tenants, tabla con nombre, estado, plan, fecha alta, acciones (ver, editar, suspender).
- **Alta**: formulario de creación de tenant (datos de empresa, plan inicial, opcional usuario admin).
- **Detalle**: datos del tenant, pestaña “Usuarios” (lista de UserTenant con roles, alta/baja).
- **Sin** acceso a datos operativos de un tenant concreto (clientes del taller, WO, etc.) salvo que se implemente un “impersonate” o vista de solo lectura; por defecto el admin plataforma solo gestiona tenants y sus usuarios.

### 7.2 Usuario de tenant (colaborador del taller)

- **Sin** acceso al listado de empresas cliente.
- Todas las pantallas actuales (clientes, órdenes, inventario, técnicos, etc.) deben usar el **tenant del contexto** (header o tenant por defecto enviado desde el frontend).
- **Dashboard del tenant** (opcional pero recomendado): resumen con contadores (usuarios X / max_users, vehículos X / max_vehicles, WO del mes, etc.) y enlace a “Mi empresa” / configuración del tenant (si el rol lo permite).
- **Barra/navegación**: mostrar nombre del tenant actual y, si tiene varios tenants, **selector de taller** para cambiar de contexto (y reenviar header con el nuevo tenant).

### 7.3 Registro de nueva empresa (onboarding)

- Flujo opcional: página pública o semipública de **registro de nueva empresa** (tenant).
  - Formulario: datos del taller, plan elegido, usuario administrador del taller (email, nombre, contraseña).
  - Backend: crea Tenant, ClientSubscription, User, UserTenant (rol admin_taller), y opcionalmente envía correo de activación.
- Puede ser parte de la Fase 5 o 6 según prioridad.

### 7.4 Gestión de usuarios dentro del tenant

- Para **admin del tenant**: pantalla “Usuarios de la empresa” (lista de UserTenant de ese tenant): agregar colaboradores (por email o usuario existente), asignar rol, desactivar acceso. Llamadas a API de plataforma con scope al tenant actual o a un endpoint específico del tenant (`/api/tenant/users/` si el backend lo expone para el admin del tenant).

---

## 8. Seguridad y auditoría

- **Control de acceso**: en cada vista/API que toque datos por tenant, comprobar que `request.tenant` esté definido (para usuarios de tenant) y que el recurso pertenezca a ese tenant.
- **Roles por tenant**: admin_taller (gestión de usuarios y configuración del taller), manager, technician, clerk, viewer; permisos por recurso según rol.
- **Auditoría**: registrar accesos sensibles en `AccessAudit` (tenant_id, user_id, action, resource_type, resource_id, timestamp, ip).
- **Validación de límites**: al crear usuarios en un tenant, comprobar `max_users`; al dar de alta equipos/vehículos, comprobar `max_vehicles` (si aplica).

---

## 9. Plan de implementación por fases

Las fases siguientes integran ambos documentos y mantienen un orden que evita romper el sistema actual.

### Fase 1: Infraestructura de multi-tenancy (2–3 semanas)

- [ ] Crear modelo **Tenant** (tabla `tenants`) y migración.
- [ ] Crear modelo **UserTenant** (user_id, tenant_id, role, is_default, is_active) y migración.
- [ ] Crear modelo **SubscriptionPlan** y **ClientSubscription** (y migraciones).
- [ ] (Opcional) Crear modelo **AccessAudit** y migración.
- [ ] Añadir **tenant_id** (nullable) a: Client, Technician, Equipment, WorkOrder, Invoice, Quote, Warehouse, Document (y demás tablas operativas definidas).
- [ ] Crear **tenant por defecto** y script/migración de datos: asignar todos los registros existentes a ese tenant.
- [ ] Poner **tenant_id NOT NULL** donde corresponda y crear **índices** compuestos (tenant_id, status), (tenant_id, created_at), etc.
- [ ] Definir si catálogos (ProductMaster, etc.) son globales o por tenant y aplicar.

### Fase 2: Contexto tenant y filtrado en backend (2–3 semanas)

- [ ] Implementar **middleware** que resuelva `request.tenant` (header, subdominio o tenant por defecto) y valide UserTenant.
- [ ] Actualizar **todas las vistas/APIs** que toquen datos por tenant: filtrar lecturas por `request.tenant_id`, asignar `tenant_id` en altas.
- [ ] (Opcional) Introducir **managers** por modelo que inyecten el tenant actual para no olvidar filtros.
- [ ] Ajustar **login/JWT**: devolver tenant por defecto y lista de tenants del usuario.
- [ ] **Tests**: usuario de tenant A no ve datos de tenant B; usuario plataforma puede listar tenants.

### Fase 3: API y pantallas de plataforma (2 semanas)

- [ ] Implementar **API de plataforma**: GET/POST/PATCH tenants, GET/POST/DELETE usuarios por tenant (solo staff/superuser).
- [ ] Frontend: **“Empresas cliente”** – listado (con total “cuántos clientes tengo”), detalle, alta, edición, suspensión.
- [ ] Frontend: por tenant, **pestaña o pantalla “Usuarios”** (lista UserTenant, agregar, quitar, rol).
- [ ] Restringir visibilidad del menú “Empresas cliente” a usuarios con permisos de plataforma.

### Fase 4: Experiencia de usuario tenant (1–2 semanas)

- [ ] **Dashboard del tenant**: tarjetas con usuarios X/max_users, vehículos X/max_vehicles, WO recientes, etc.
- [ ] **Barra/navegación**: nombre del tenant actual; si el usuario tiene varios tenants, **selector de taller** (cambiar contexto y reenviar header).
- [ ] Asegurar que **todas** las pantallas existentes (clientes, WO, inventario, etc.) envíen el header de tenant y que el backend siga filtrando correctamente.
- [ ] (Opcional) Pantalla “Mi empresa” / configuración del tenant para admin del taller.

### Fase 5: Suscripciones y facturación (2–3 semanas)

- [ ] **Seed** de planes (Básico, Profesional, Empresarial) en SubscriptionPlan.
- [ ] Al crear tenant, crear **ClientSubscription** con plan inicial y fechas.
- [ ] **Validación de límites**: max_users, max_vehicles (y max_work_orders si aplica) en altas y en la UI.
- [ ] (Opcional) Integración con **pasarela de pagos** y renovación automática.
- [ ] Notificaciones de **vencimiento** de suscripción (email o en dashboard de plataforma).
- [ ] Panel o sección de **facturación** en frontend (plataforma y/o tenant según diseño).

### Fase 6: Registro, onboarding y pruebas (1–2 semanas)

- [ ] (Opcional) **Página de registro de nueva empresa**: formulario público o semipúblico que cree Tenant + User + UserTenant + ClientSubscription.
- [ ] Flujo de **activación** por correo (opcional).
- [ ] **Pruebas de aislamiento**: dos tenants con datos; comprobar que no se cruzan.
- [ ] **Pruebas de rendimiento**: consultas con tenant_id en índices.
- [ ] **Documentación**: cómo dar de alta un tenant, cómo asignar usuarios, límites por plan.

---

## 10. Consideraciones técnicas

- **Rendimiento**: índices compuestos (tenant_id, ...) en todas las tablas con tenant_id; evitar full table scans por tenant.
- **Seguridad**: nunca confiar en tenant_id enviado por el cliente en el body; siempre usar el resuelto por middleware y UserTenant.
- **Escalabilidad**: arquitectura actual compatible con varios workers; en el futuro, caché por tenant si hace falta.
- **Backup y recuperación**: con Opción A, un solo backup de BD; restaurar y listo. Con Opción B (futuro), considerar backup por esquema si se implementa.
- **Costos**: revisar uso de BD y almacenamiento por tenant para planes y precios.
- **Duplicados**: se eliminó la sección duplicada “Costos” del plan original; queda una sola subsección en este documento.

---

## Referencia cruzada

| Tema | SaaS_Transformation_Plan | SAAS_MULTITENANCY_RECOMMENDATIONS | Este documento |
|------|---------------------------|-------------------------------------|-----------------|
| Estrategia multi-tenant | Schema por tenant | Tenant por fila (tenant_id) | Opción A (tenant_id) recomendada; B descrita como evolución |
| Entidad empresa cliente | ClientCompany | Tenant | **Tenant** (alias ClientCompany) |
| Usuario ↔ tenant | TenantUser (1 user : 1 company) | UserTenant (N:N) | **UserTenant** (N:N, rol por tenant) |
| Planes / suscripción | SubscriptionPlan, ClientSubscription | Opcional Fase 4 | **Incluido** en modelos y Fase 5 |
| Auditoría | AccessAudit | No | **AccessAudit** incluido |
| Migración datos | Implícito | Tenant por defecto + UPDATE | **Explícito** en Fase 1 |
| Fases | 6 fases | 4 fases | **6 fases** unificadas y ordenadas |

---

*Documento unificado. Utilizar este plan como referencia única para la transformación SaaS de Forge CMMS; los documentos originales se mantienen como respaldo.*
