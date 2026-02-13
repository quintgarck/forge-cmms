# Guía de Desarrollo: Manejo de Esquemas en ForgeDB

## Estado Actual ✅

- ✅ Tablas duplicadas eliminadas
- ✅ Tablas correctas en sus esquemas correspondientes
- ✅ Modelos configurados con `db_table` correcto
- ✅ Settings con `search_path` configurado

## Estructura de Esquemas

```
forge_db/
├── app/          # Application Management
│   ├── alerts
│   ├── audit_logs
│   └── business_rules
│
├── cat/          # Catalog and Master Data
│   ├── clients
│   ├── technicians
│   ├── equipment
│   └── ... (códigos maestros)
│
├── inv/          # Inventory Management
│   ├── warehouses
│   ├── stock
│   ├── transactions
│   ├── product_master
│   └── ...
│
├── svc/          # Service Management
│   ├── work_orders
│   ├── invoices
│   └── ...
│
├── doc/          # Document Management
│   └── documents
│
├── kpi/          # Key Performance Indicators
│   └── ...
│
└── oem/          # Original Equipment Manufacturer
    └── ...
```

## Cómo Agregar un Nuevo Modelo

### Paso 1: Determinar el Esquema Correcto

Consulta la documentación o los modelos existentes para determinar en qué esquema debe ir tu modelo:

- **`cat`** - Datos maestros y catálogos (clients, technicians, equipment)
- **`inv`** - Inventario (warehouses, stock, transactions, products)
- **`svc`** - Servicios (work_orders, invoices, payments)
- **`doc`** - Documentos (documents)
- **`app`** - Gestión de la aplicación (alerts, audit_logs, business_rules)
- **`kpi`** - Indicadores de rendimiento
- **`oem`** - Fabricantes de equipos originales

### Paso 2: Crear el Modelo con Esquema Correcto

```python
# En core/models.py

class MyNewModel(models.Model):
    """Descripción del modelo"""
    
    # Definir campos
    my_new_model_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    # ... más campos
    
    class Meta:
        db_table = 'schema_name.my_new_model'  # ⚠️ IMPORTANTE: Usar formato schema.table
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
```

**⚠️ CRÍTICO:** Siempre usar formato `'schema.table'` en `db_table`, NO solo `'table'`

### Paso 3: Verificar que el Esquema Existe

Si el esquema no existe, créalo:

```sql
-- Ejecutar en PostgreSQL
CREATE SCHEMA IF NOT EXISTS schema_name;
```

O usar el script de inicialización (`database/forge_db.sql`).

### Paso 4: Crear la Migración

```bash
python manage.py makemigrations core
```

**Revisar la migración generada** para asegurarse de que Django la creó correctamente.

### Paso 5: Aplicar la Migración

```bash
python manage.py migrate core
```

### Paso 6: Verificar

```bash
# Verificar que la tabla se creó en el esquema correcto
python manage.py dbshell

# En el shell de PostgreSQL:
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename = 'my_new_model';
```

Debe mostrar: `schema_name | my_new_model`

## Ejemplo Completo

### Agregar un modelo de "Vehicles" en el esquema `cat`

```python
# core/models.py

class Vehicle(models.Model):
    """Client vehicles"""
    
    vehicle_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='vehicles')
    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cat.vehicles'  # ✅ Esquema correcto
        ordering = ['make', 'model']
        indexes = [
            models.Index(fields=['vin']),
            models.Index(fields=['client', 'make']),
        ]
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model}"
```

Luego:
```bash
python manage.py makemigrations core
python manage.py migrate core
```

## Verificación de Modelos Existentes

Para verificar que todos los modelos están correctamente configurados:

```bash
python fix_schemas.py
```

Este script verifica que cada modelo tiene su tabla en el esquema correcto.

## Problemas Comunes y Soluciones

### Problema: Django crea tabla en esquema incorrecto

**Causa:** `db_table` no tiene formato `schema.table`

**Solución:** Asegúrate de usar `db_table = 'schema.table'`, no solo `'table'`

### Problema: Error "relation does not exist"

**Causa:** El esquema no está en el `search_path`

**Solución:** Verificar `settings.py` que tenga:
```python
'options': '-c search_path=app,cat,doc,inv,kpi,oem,svc,public'
```

### Problema: Migración no encuentra la tabla

**Causa:** La tabla fue creada manualmente o en otro esquema

**Solución:** 
1. Verificar en qué esquema está la tabla
2. Ajustar `db_table` en el modelo
3. Marcar la migración como aplicada: `python manage.py migrate --fake core`

## Scripts de Utilidad

1. **`manage_schemas.py`** - Lista todos los esquemas y tablas
2. **`fix_schemas.py`** - Verifica ubicación de tablas de modelos
3. **`clean_duplicate_tables.py`** - Identifica tablas duplicadas

## Checklist para Nuevos Modelos

- [ ] Determinar el esquema correcto
- [ ] Definir modelo con `db_table = 'schema.table'`
- [ ] Verificar que el esquema existe
- [ ] Crear migración
- [ ] Revisar migración generada
- [ ] Aplicar migración
- [ ] Verificar que la tabla está en el esquema correcto
- [ ] Probar consultas básicas
- [ ] Documentar el modelo

## Referencias

- Estructura SQL: `database/forge_db.sql`
- Scripts de limpieza: `database/cleanup_duplicate_tables*.sql`
- Documentación de esquemas: Este archivo

