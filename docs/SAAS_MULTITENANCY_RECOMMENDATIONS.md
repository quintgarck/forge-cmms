# Recomendaciones: SaaS multi-tenant para Forge CMMS

## Resumen ejecutivo

Hoy el sistema está pensado para **un solo taller**: no existe el concepto de "empresa cliente" (tenant) ni de "cuántos talleres tengo". Para ofrecerlo como **SaaS a varios talleres** hace falta introducir **multi-tenancy** y separar claramente:

- **Tú (plataforma)**: administras **empresas cliente** (cada taller que contrata el sistema).
- **Cada empresa cliente (tenant)**: tiene sus **colaboradores** (usuarios) y sus **clientes** (quienes llevan vehículos al taller) y toda la operación (órdenes de trabajo, inventario, etc.).

Este documento describe qué falta en **base de datos** y **backend** (y un poco frontend) y cómo desarrollarlo por fases.

---

## 1. Estado actual (lo que ya tienes)

### Base de datos / modelos (core)

- **Client**: son los **clientes del taller** (quienes llevan el auto a reparar). **No** es la empresa que paga el SaaS.
- **Technician**: colaboradores del taller (técnicos). Sin vínculo a "qué taller".
- **Equipment, WorkOrder, Invoice, Quote, etc.**: toda la operación. **Ninguna tabla tiene `tenant_id` ni `workshop_id`**.
- **Auth**: Django `User`; `TechnicianUser` (proxy) relaciona por `username = employee_code` con `Technician`. No hay noción de "a qué taller pertenece este usuario".
- **Tablas**: la mayoría en esquema por defecto (sin esquema explícito en `db_table`); algunas en `cat`, `oem`. **Todo es un solo tenant implícito.**

### Backend (API)

- API REST en `core/views/` (clientes, equipos, órdenes, técnicos, etc.). **No filtra por tenant** porque no existe el concepto.
- Autenticación: JWT + `TechnicianAuthBackend` (technician por `employee_code` o User Django). Sin contexto de tenant.
- Permisos: `is_superuser`, `is_staff`, permisos Django. Nada por tenant.

### Frontend

- Login único (admin o técnico). Dashboard y menús para "el" taller.
- No hay pantallas de: "lista de empresas cliente", "cuántos tenants hay", "alta/baja de taller", ni cambio de contexto por tenant.

Conclusión: **falta por completo la capa "tenant / empresa cliente / taller que usa el SaaS"** y el aislamiento de datos por ese tenant.

---

## 2. Lo que hace falta: concepto de datos

| Concepto | Hoy | Objetivo SaaS |
|----------|-----|----------------|
| **Empresa que paga el SaaS** (taller) | No existe | **Tenant / Workshop / Organization** (una tabla nueva). |
| **"Cuántos clientes tengo"** | No existe | Número de **tenants** activos. |
| **Colaboradores del taller** | Technician (sin taller) | Usuarios asociados a **un (o más) tenant(s)** con rol en ese tenant. |
| **Clientes del taller** | Client | Siguen siendo Client, pero cada uno pertenece a **un tenant** (el taller que los atiende). |
| **Órdenes, inventario, etc.** | Globales | Cada registro debe pertenecer a **un tenant**. |

Nomenclatura sugerida en el documento: **Tenant** = empresa cliente del SaaS = un taller que usa el sistema. En BD puede llamarse `tenants` o `workshops` (lo importante es un único concepto).

---

## 3. Cambios en base de datos

### 3.1 Tablas nuevas

**1) `tenants` (o `workshops`) – empresas cliente del SaaS**

- `tenant_id` (PK).
- `name`, `legal_name`, `tax_id`, `email`, `phone`, `address`, `city`, `country`, etc.
- `slug` o `code` único (para subdominio o URL, ej. `taller-garcia.forgecmms.com`).
- `status`: activo, suspendido, cancelado.
- `plan` / `subscription_plan` (opcional): básico, profesional, etc.
- `settings` (JSONB): configuración por taller (moneda, idioma, etc.).
- `created_at`, `updated_at`.
- Opcional: `max_users`, `max_technicians`, fechas de suscripción.

Recomendación: crear esta tabla en el esquema `public` o un esquema dedicado `tenant`/`platform`. El resto de tablas operativas pueden seguir en sus esquemas actuales y añadir `tenant_id`.

**2) Relación usuario ↔ tenant (y rol por tenant)**

- Opción A – tabla **`user_tenants`** (N a N):  
  `user_id`, `tenant_id`, `role` (admin_taller, manager, technician, viewer), `is_default`, `created_at`.  
  Un usuario puede pertenecer a varios talleres (ej. mismo gerente en dos sucursales).
- Opción B – campo en User: **`tenant_id`** (FK nullable). Un usuario = un solo taller (más simple).  
  Para SaaS con muchos talleres pequeños, la opción A es más flexible (invitaciones, roles, múltiples talleres).

Recomendación: **Opción A** (`user_tenants`) para no limitarte después.

**3) Usuarios "plataforma"**

- No hace falta otra tabla: los usuarios con `is_staff=True` y/o `is_superuser=True` pueden ser **admin de plataforma**.
- Regla: si el usuario tiene al menos un registro en `user_tenants`, es usuario de tenant; si no tiene ninguno pero es staff/superuser, es solo plataforma (o puedes marcar "platform_only" en un perfil si lo añades).

### 3.2 Tablas existentes: añadir `tenant_id`

Todas las tablas **operativas** del taller deben tener `tenant_id` (FK a `tenants`) y todas las consultas deben filtrar por él.

Lista sugerida (revisar contra tus modelos reales):

| Tabla / modelo | Comentario |
|----------------|------------|
| `clients` (Client) | Clientes del taller → de quién es el taller (tenant). |
| `technicians` (Technician) | Colaboradores del taller → tenant. |
| `equipment` (Equipment) | Vehículos/equipos de los clientes del taller → tenant. |
| `work_orders` (WorkOrder) | Órdenes del taller → tenant. |
| `invoices` (Invoice) | Facturas del taller → tenant. |
| `quotes` (Quote) | Cotizaciones del taller → tenant. |
| `warehouses` (Warehouse) | Almacenes del taller → tenant. |
| `product_master` (ProductMaster) | Productos del taller (opcional compartir catálogo global y solo stock por tenant). |
| `stock` (Stock) | Stock por almacén → ya va por warehouse → tenant. |
| `documents` (Document) | Documentos del taller → tenant. |
| Alertas, auditoría, etc. | Por tenant si son datos de operación. |

Catálogos **globales** (que tú mantienes para todos los talleres) normalmente **no** llevan `tenant_id`:

- Códigos de referencia (combustible, transmisión, color, etc.).
- Tipos de equipo, taxonomía, categorías de equipo.
- OEM (marcas, equivalencias), UOM, categorías/tipos de producto.
- Monedas (o sí por tenant si cada taller tiene su moneda).

Decisión de diseño: **catálogos maestros globales** (un solo conjunto para toda la plataforma) vs **catálogos por tenant** (cada taller tiene sus propios códigos). Para empezar suele ser más simple: catálogos globales sin `tenant_id`; solo datos operativos (clientes, técnicos, WO, facturas, inventario) con `tenant_id`.

### 3.3 Migraciones

- Crear `tenants` y `user_tenants`.
- Añadir `tenant_id` (nullable al principio) a las tablas listadas.
- **Datos existentes**: crear un tenant por defecto (ej. "Taller demo" o "Mi taller") y asignar todos los registros actuales a ese `tenant_id`; luego poner `tenant_id` NOT NULL donde corresponda.
- Índices: en todas las tablas con `tenant_id`, índice compuesto `(tenant_id, ...)` según consultas frecuentes (p. ej. `tenant_id + status`, `tenant_id + created_at`).

---

## 4. Cambios en backend (Django / API)

### 4.1 Resolver el tenant del usuario en cada request

- **Middleware** (o lógica al inicio de cada vista/API):  
  - Si el usuario es superuser/staff y no tiene `user_tenants` (o tiene un flag "platform"), dejar **sin** tenant (modo plataforma).  
  - Si el usuario tiene `user_tenants`, leer el tenant actual:  
    - Por header (ej. `X-Tenant-Id` o `X-Tenant-Slug`), o  
    - Por subdominio (ej. `taller-garcia.forgecmms.com` → slug → tenant), o  
    - Por defecto: el tenant marcado como `is_default` para ese usuario.  
  - Guardar en `request.tenant` (y opcionalmente en un thread-local o en el token JWT) para usarlo en toda la petición.

### 4.2 Filtrar todas las lecturas/escrituras por tenant

- En **vistas y APIs** que toquen Client, Technician, WorkOrder, Equipment, Invoice, etc.:  
  - Siempre filtrar por `request.tenant.id` (o `request.tenant_id`).  
  - En creación: asignar `tenant_id=request.tenant.id`.
- Opción más limpia: **manager por defecto** en Django que inyecte `tenant_id` (ej. `Technician.objects.filter(tenant_id=current_tenant_id)` como base y usar ese manager en todo el código). Así no se te escapa un query sin filtrar.

### 4.3 API de plataforma (solo admin)

- **Listar tenants**: GET `/api/platform/tenants/` (solo staff/superuser). Respuesta: cantidad total, lista con nombre, estado, plan, fecha alta, etc. Aquí es donde "ves cuántos clientes (tenants) tienes".
- **Crear tenant**: POST (nombre, datos de facturación, plan). Opcional: crear usuario admin del tenant y enviar invitación.
- **Detalle / editar / suspender tenant**: PATCH, PUT, POST suspend.
- **Usuarios por tenant**: GET `/api/platform/tenants/<id>/users/` (lista de user_tenants de ese tenant). Alta/baja de usuarios al tenant y asignación de rol.

### 4.4 Autenticación y JWT

- Tras login, incluir en el payload del JWT (o en la respuesta de login):  
  - `tenant_id` y `tenant_slug` (tenant por defecto del usuario), y opcionalmente lista de `tenants` a los que tiene acceso.  
- El frontend enviará en cada petición el tenant (header o subdominio). El backend valida que el usuario pertenezca a ese tenant (vía `user_tenants`).

### 4.5 Permisos

- **Plataforma**: is_staff / is_superuser para rutas `/api/platform/*` y vistas de "lista de empresas cliente".
- **Dentro del tenant**: mismos roles que ahora (admin taller, manager, technician, viewer) pero aplicados **por tenant** (tabla `user_tenants.role`). Un usuario puede ser admin en taller A y solo viewer en taller B.

---

## 5. Frontend (resumen)

- **Admin plataforma** (cuando el usuario es staff y no tiene tenant o está en "modo plataforma"):  
  - Menú o sección "Empresas cliente" / "Talleres".  
  - Listado: cantidad de tenants, lista con nombre, estado, plan.  
  - Alta de nuevo tenant, edición, suspensión.  
  - Por tenant: ver usuarios/colaboradores y roles.
- **Usuario de tenant** (técnico, manager, admin del taller):  
  - Sin acceso a lista de tenants.  
  - Todas las pantallas actuales (clientes, órdenes, inventario, etc.) deben usar el tenant que viene del login/contexto (header o tenant por defecto).  
  - El "Client" en el frontend sigue siendo "clientes del taller" (quienes llevan el auto); la "empresa cliente del SaaS" es invisible para ellos.

---

## 6. Orden de desarrollo sugerido (fases)

### Fase 1 – Base de datos y modelo de tenant (sin romper lo actual)

1. Crear modelo `Tenant` (tabla `tenants`) y migración.
2. Crear modelo `UserTenant` (user_id, tenant_id, role, is_default) y migración.
3. Añadir `tenant_id` (nullable) a: Client, Technician, Equipment, WorkOrder, Invoice, Quote, Warehouse (y las que decidas). Migraciones.
4. Crear un tenant por defecto y asignar todos los datos existentes a ese tenant; luego poner NOT NULL y migración.
5. Crear índices compuestos (tenant_id, ...).

### Fase 2 – Backend: contexto tenant y filtrado

1. Middleware (o equivalente) que resuelva `request.tenant` según usuario y header/subdominio/default.
2. En todas las vistas/APIs que toquen datos por tenant: filtrar por `request.tenant_id` y asignar en altas. Ideal: managers por defecto con tenant inyectado.
3. Ajustar autenticación (login) para devolver tenant por defecto y lista de tenants del usuario.
4. Tests: un usuario de tenant A no ve datos de tenant B.

### Fase 3 – API y pantallas de plataforma

1. API GET/POST/PATCH para tenants (solo staff).
2. API de usuarios por tenant (listar, agregar, quitar, rol).
3. Frontend: sección "Empresas cliente" (lista, detalle, alta, edición). Aquí ves "cuántos clientes (tenants) tengo" y cuántas empresas usan el sistema.
4. (Opcional) Subdominios o selector de taller en el frontend para usuarios multi-tenant.

### Fase 4 – Refinamiento

1. Catálogos: decidir qué es global y qué por tenant; si algo pasa a ser por tenant, añadir `tenant_id` y filtrar.
2. Facturación/planes: si aplica, campos en `tenants` y lógica de límites (usuarios, técnicos, etc.).
3. Onboarding: flujo de alta de nuevo tenant (registro, correo, activación).

---

## 7. Resumen: qué te falta antes de iniciar

| Área | Qué falta |
|------|-----------|
| **Base de datos** | Tabla `tenants`; tabla `user_tenants`; campo `tenant_id` en todas las tablas operativas del taller; un tenant por defecto y migración de datos. |
| **Backend** | Resolver tenant en cada request (middleware + header/subdominio/default); filtrar todas las lecturas/escrituras por `tenant_id`; API de plataforma para CRUD de tenants y usuarios por tenant; JWT/login con información de tenant. |
| **Frontend** | Zona "Empresas cliente" (solo admin plataforma) para ver cuántos tenants hay y gestionarlos; resto de la app debe usar siempre el tenant del usuario. |

Si quieres, el siguiente paso puede ser bajar esto a **cambios concretos en tu repo**: nombres de tablas/campos en `core/models.py`, ejemplo de middleware, y lista exacta de vistas/APIs a tocar en la Fase 2.
