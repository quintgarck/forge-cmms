
# ForgeDB API REST Specification (Django + DRF)

## Proyecto base
- **Framework:** Django 4.x
- **API:** Django REST Framework
- **DB:** PostgreSQL
- **Esquemas incluidos:** `cat`, `inv`, `svc`, `doc`, `kpi`, `app`, `oem`

## 1. Estructura general del proyecto

```
forge_api/
├── core/                   ← App base del sistema
│   ├── models.py           ← Modelos desde la base de datos (inspectdb)
│   ├── serializers.py      ← Serializers DRF
│   ├── views/              ← Carpeta con vistas organizadas por recurso
│   │    ├── equipment.py
│   │    ├── clients.py
│   ├── urls.py             ← URL dispatcher de la app
│   └── permissions.py      ← Permisos personalizados si se requiere
├── manage.py
└── forge_api/              ← Configuración del proyecto
```

## 2. Instalación de dependencias

```bash
pip install django djangorestframework psycopg2-binary drf-yasg
```

## 3. Configuración inicial (`settings.py`)

- Agregar `'rest_framework'`, `'core'`, y `'drf_yasg'` a `INSTALLED_APPS`
- Configurar conexión a PostgreSQL con nombre `forge_db`

## 4. Carga de modelos desde la BD

```bash
python manage.py inspectdb --database=default --include-schemas --schema=cat,inv,svc,doc,kpi,app,oem > core/models.py
```

## 5. Generación de endpoints por entidad

Para cada tabla (ej: `cat.clients`), crear:

### Modelo

(Ya generado por `inspectdb`)

### Serializer (`core/serializers.py`)

```python
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
```

### Vista tipo ViewSet (`core/views/clients.py`)

```python
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
```

### Registro en el router (`core/urls.py`)

```python
router.register(r'clients', ClientViewSet)
```

## 6. Exposición de vistas SQL y materializadas

- Crear modelos con `managed = False` para las vistas
- Serializar y exponer vía `ListAPIView`

## 7. Exposición de funciones SQL (stored procedures)

- Crear endpoints tipo `APIView` o `@action(detail=False)` que usen `connection.cursor()` para ejecutar la función y retornar JSON

## 8. Seguridad

- Autenticación: Token o JWT
- Permisos personalizados según `is_staff`, `groups`, etc.

## 9. Documentación Swagger

- Usar `drf-yasg` para documentación Swagger/OpenAPI
