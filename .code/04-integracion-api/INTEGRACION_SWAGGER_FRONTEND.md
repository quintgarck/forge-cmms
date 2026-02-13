# Integración de Swagger con Frontend y Backend

**Fecha**: Enero 2026  
**Estado**: ✅ **Completado**

---

## ✅ **CAMBIOS REALIZADOS**

### **1. Enlaces en el Menú de Usuario**

Se agregaron enlaces a la documentación de la API en el menú desplegable del usuario (dropdown):

- **API Documentation (Swagger)**: `/swagger/` - Abre en nueva pestaña
- **API Documentation (ReDoc)**: `/redoc/` - Abre en nueva pestaña
- **Admin Panel**: `/admin/` - Abre en nueva pestaña

**Ubicación**: Menú desplegable del usuario (esquina superior derecha)

### **2. Enlaces en el Footer**

Se actualizaron los enlaces del footer:

- **API Docs**: `/swagger/` - Abre en nueva pestaña
- **ReDoc**: `/redoc/` - Abre en nueva pestaña

**Ubicación**: Footer de todas las páginas

---

## 🌐 **URLs DISPONIBLES**

### **Documentación de la API:**

1. **Swagger UI (Interactivo)**
   - URL: http://127.0.0.1:8000/swagger/
   - Descripción: Interfaz interactiva donde puedes probar los endpoints
   - Acceso: Menú usuario → "API Documentation (Swagger)" o Footer → "API Docs"

2. **ReDoc (Documentación Estilizada)**
   - URL: http://127.0.0.1:8000/redoc/
   - Descripción: Documentación con formato más limpio y legible
   - Acceso: Menú usuario → "API Documentation (ReDoc)" o Footer → "ReDoc"

3. **Schema JSON**
   - URL: http://127.0.0.1:8000/swagger.json
   - Descripción: Esquema OpenAPI en formato JSON

4. **Schema YAML**
   - URL: http://127.0.0.1:8000/swagger.yaml
   - Descripción: Esquema OpenAPI en formato YAML

---

## 🔧 **CONFIGURACIÓN TÉCNICA**

### **Backend (urls.py):**

Las URLs de Swagger están configuradas en `forge_api/urls.py`:

```python
# API Documentation
path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
path('api/', schema_view.with_ui('swagger', cache_timeout=0), name='api-root'),
```

**Nota**: Las URLs están configuradas **después** del frontend, pero el frontend solo captura rutas específicas, por lo que `/swagger/` y `/redoc/` funcionan correctamente.

### **Frontend (base.html):**

Se agregaron enlaces en dos ubicaciones:

1. **Menú de Usuario** (línea ~290):
   - Enlaces en el dropdown del usuario
   - Todos abren en nueva pestaña (`target="_blank"`)

2. **Footer** (línea ~374):
   - Enlaces en el footer
   - Todos abren en nueva pestaña (`target="_blank"`)

---

## ✅ **VERIFICACIÓN**

### **Para verificar que funciona:**

1. **Inicia sesión** en el frontend
2. **Haz clic en tu nombre/usuario** (esquina superior derecha)
3. **Deberías ver**:
   - "API Documentation (Swagger)"
   - "API Documentation (ReDoc)"
   - "Admin Panel"

4. **Haz clic en "API Documentation (Swagger)"**
   - Debería abrir una nueva pestaña con Swagger UI
   - Deberías ver todos los endpoints de la API

5. **Desplázate al footer** de cualquier página
   - Deberías ver enlaces a "API Docs" y "ReDoc"

---

## 📋 **ENDPOINTS DOCUMENTADOS**

Todos los endpoints de la API están documentados automáticamente:

- ✅ **Clientes**: `/api/v1/clients/`
- ✅ **Equipos**: `/api/v1/equipment/`
- ✅ **Técnicos**: `/api/v1/technicians/`
- ✅ **Productos**: `/api/v1/products/`
- ✅ **Stock**: `/api/v1/stock/`
- ✅ **Órdenes de Trabajo**: `/api/v1/work-orders/`
- ✅ **Facturas**: `/api/v1/invoices/`
- ✅ **Almacenes**: `/api/v1/warehouses/`
- ✅ **Alertas**: `/api/v1/alerts/`
- ✅ **Documentos**: `/api/v1/documents/`
- ✅ **Reglas de Negocio**: `/api/v1/business-rules/`
- ✅ **Auditoría**: `/api/v1/audit-logs/`
- ✅ **Autenticación**: `/api/v1/auth/login/`, etc.
- ✅ **Dashboard**: `/api/v1/dashboard/`
- ✅ **Notificaciones**: `/api/v1/notifications/`
- ✅ **Stored Procedures**: Varios endpoints

---

## 🎯 **RESUMEN**

### **✅ Integración Completada:**

- ✅ Swagger configurado en el backend
- ✅ Enlaces agregados en el menú de usuario
- ✅ Enlaces agregados en el footer
- ✅ Todos los enlaces abren en nueva pestaña
- ✅ URLs funcionando correctamente

### **🔗 Acceso Rápido:**

- **Desde el frontend**: Menú usuario → "API Documentation (Swagger)"
- **Directo**: http://127.0.0.1:8000/swagger/
- **Desde el footer**: Click en "API Docs"

---

**Documento generado**: Enero 2026  
**Estado**: ✅ **INTEGRACIÓN COMPLETA**

