# Guía: Documentación de API con Swagger/OpenAPI

**Fecha**: Enero 2026  
**Estado**: ✅ **Swagger está configurado y funcionando**

---

## 🌐 **ACCESO A LA DOCUMENTACIÓN**

La documentación de la API está disponible en las siguientes URLs:

### **URLs Disponibles:**

1. **Swagger UI (Interactivo)**: 
   - **URL**: http://127.0.0.1:8000/swagger/
   - **Descripción**: Interfaz interactiva de Swagger donde puedes probar los endpoints

2. **ReDoc (Documentación Estilizada)**:
   - **URL**: http://127.0.0.1:8000/redoc/
   - **Descripción**: Documentación con formato más limpio y legible

3. **Schema JSON (Raw)**:
   - **URL**: http://127.0.0.1:8000/swagger.json
   - **Descripción**: Esquema OpenAPI en formato JSON

4. **Schema YAML (Raw)**:
   - **URL**: http://127.0.0.1:8000/swagger.yaml
   - **Descripción**: Esquema OpenAPI en formato YAML

---

## ✅ **ESTADO ACTUAL**

### **Lo que YA está configurado:**

1. ✅ **drf-yasg instalado** (`drf-yasg==1.21.7`)
2. ✅ **Swagger configurado en urls.py**
3. ✅ **SWAGGER_SETTINGS configurados** en settings.py
4. ✅ **Autenticación JWT documentada**
5. ✅ **ViewSets registrados** (se documentan automáticamente)
6. ✅ **Endpoints funcionando** (Status 200 confirmado)

### **Lo que se documenta automáticamente:**

- ✅ Todos los ViewSets (ClientViewSet, EquipmentViewSet, etc.)
- ✅ Endpoints básicos (GET, POST, PUT, DELETE)
- ✅ Serializadores (campos, tipos, validaciones)
- ✅ Filtros y búsquedas
- ✅ Paginación

---

## 📝 **MEJORAS DISPONIBLES**

Para mejorar la documentación, puedes agregar:

### **1. Descripciones en ViewSets**

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Clients.
    
    list:
    Retorna una lista paginada de todos los clientes.
    Permite filtrado por tipo, estado, ciudad, estado y país.
    Permite búsqueda por nombre, email, teléfono y código de cliente.
    
    create:
    Crea un nuevo cliente.
    Requiere: client_code, type, name (mínimo)
    
    retrieve:
    Retorna los detalles de un cliente específico.
    
    update:
    Actualiza todos los campos de un cliente.
    
    partial_update:
    Actualiza campos específicos de un cliente.
    
    destroy:
    Elimina un cliente.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    # ... resto del código
```

### **2. Documentación de Endpoints Específicos**

Para endpoints que NO son ViewSets (como stored procedures):

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_description="Reserve stock for a work order",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['wo_id', 'internal_sku', 'qty_needed'],
        properties={
            'wo_id': openapi.Schema(
                type=openapi.TYPE_INTEGER, 
                description='Work order ID'
            ),
            'internal_sku': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description='Product SKU'
            ),
            'qty_needed': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                description='Quantity needed'
            ),
        }
    ),
    responses={
        200: openapi.Response('Stock reserved successfully'),
        400: openapi.Response('Bad request - validation error'),
        401: openapi.Response('Unauthorized'),
        403: openapi.Response('Forbidden'),
    }
)
@api_view(['POST'])
def reserve_stock(request):
    # ... código
```

### **3. Ejemplos en Serializadores**

```python
from rest_framework import serializers

class ClientSerializer(serializers.ModelSerializer):
    client_code = serializers.CharField(
        help_text="Código único del cliente (ej: CLI-001)",
        example="CLI-001"
    )
    name = serializers.CharField(
        help_text="Nombre completo del cliente",
        example="Juan Pérez"
    )
    # ... resto de campos
```

### **4. Tags para Organizar Endpoints**

```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    tags=['Clientes'],
    operation_summary="Listar clientes",
    operation_description="Retorna una lista paginada de clientes"
)
class ClientViewSet(viewsets.ModelViewSet):
    # ...
```

---

## 🔧 **MEJORAS RECOMENDADAS**

### **Prioridad Alta:**

1. **Agregar descripciones a ViewSets**
   - Agregar docstrings detallados en cada ViewSet
   - Describir cada acción (list, create, retrieve, etc.)

2. **Documentar endpoints de stored procedures**
   - Ya hay algunos con `@swagger_auto_schema`
   - Revisar que todos estén documentados

3. **Agregar ejemplos a serializadores**
   - Ayuda a entender qué formato esperar

### **Prioridad Media:**

4. **Agregar tags para organizar**
   - Agrupar endpoints por categoría (Clientes, Inventario, etc.)

5. **Mejorar descripciones de respuestas**
   - Documentar códigos de error comunes
   - Agregar ejemplos de respuestas

6. **Documentar autenticación**
   - Ya está configurada pero se puede mejorar la descripción

### **Prioridad Baja:**

7. **Agregar esquemas personalizados**
   - Para respuestas complejas
   - Para parámetros de consulta complejos

---

## 📋 **ARCHIVOS QUE PODRÍAN MEJORARSE**

### **ViewSets que necesitan documentación:**

1. `core/views/client_views.py` - ClientViewSet
2. `core/views/equipment_views.py` - EquipmentViewSet
3. `core/views/technician_views.py` - TechnicianViewSet
4. `core/views/product_views.py` - ProductMasterViewSet
5. `core/views/stock_views.py` - StockViewSet
6. `core/views/workorder_views.py` - WorkOrderViewSet
7. `core/views/invoice_views.py` - InvoiceViewSet
8. `core/views/document_views.py` - DocumentViewSet
9. `core/views/warehouse_views.py` - WarehouseViewSet
10. `core/views/alert_views.py` - AlertViewSet
11. `core/views/businessrule_views.py` - BusinessRuleViewSet
12. `core/views/auditlog_views.py` - AuditLogViewSet

### **Endpoints que necesitan documentación:**

1. `core/views/dashboard_views.py` - dashboard_data, kpi_details
2. `core/views/notification_views.py` - todos los endpoints
3. `core/views/auth_views.py` - CustomTokenObtainPairView y otros
4. `core/views/stored_procedures_views.py` - algunos ya tienen, otros no
5. `core/views/analytics_stored_procedures_views.py` - endpoints de analytics

---

## 🎯 **RESUMEN**

### **✅ Lo que YA funciona:**

- Swagger está instalado y configurado
- Las URLs están accesibles
- Los ViewSets se documentan automáticamente
- La autenticación JWT está documentada

### **📝 Lo que se puede mejorar:**

- Agregar descripciones detalladas a ViewSets
- Agregar ejemplos en serializadores
- Documentar endpoints que no son ViewSets
- Agregar tags para organizar
- Mejorar descripciones de respuestas

### **🔗 Acceso:**

**Swagger UI**: http://127.0.0.1:8000/swagger/  
**ReDoc**: http://127.0.0.1:8000/redoc/

---

**Documento generado**: Enero 2026  
**Estado**: ✅ **Swagger funcionando - Mejoras opcionales disponibles**

