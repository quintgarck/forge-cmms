# Guía para Desarrollo con Esquemas de Base de Datos

## Estado Actual

✅ Las tablas duplicadas han sido eliminadas
✅ Las tablas correctas están en sus esquemas correspondientes:
- `cat.*` - Catalog and Master Data (clients, technicians, equipment)
- `inv.*` - Inventory (warehouses, stock, transactions, products)
- `svc.*` - Service (work_orders, invoices)
- `doc.*` - Documents
- `app.*` - Application Management (alerts, audit_logs, business_rules)

## Configuración Actual

### 1. Modelos Django (`core/models.py`)
Los modelos ya están correctamente configurados con `db_table`:
```python
class Client(models.Model):
    class Meta:
        db_table = 'cat.clients'  # ✅ Correcto
```

### 2. Settings (`forge_api/settings.py`)
El `search_path` está configurado:
```python
DATABASES = {
    'default': {
        'OPTIONS': {
            'options': '-c search_path=app,cat,doc,inv,kpi,oem,svc,public'
        },
    }
}
```

## Problema Identificado

Django interpreta `db_table='cat.clients'` como un **nombre literal de tabla**, no como `schema.table`. Por eso creó tablas con nombres como `cat.clients` en el esquema por defecto.

## Solución: Custom Database Router

Para que Django maneje correctamente los esquemas en migraciones futuras, necesitamos:

1. **Crear un Database Router personalizado** que maneje los esquemas
2. **Asegurar que las migraciones usen los esquemas correctos**
3. **Documentar el proceso para nuevos modelos**

## Mejores Prácticas para Futuros Modelos

### Al agregar un nuevo modelo:

1. **Definir el esquema correcto:**
   ```python
   class MyModel(models.Model):
       # campos...
       
       class Meta:
           db_table = 'schema_name.table_name'  # Usar esquema correcto
   ```

2. **Verificar que el esquema existe:**
   ```sql
   CREATE SCHEMA IF NOT EXISTS schema_name;
   ```

3. **Crear la migración:**
   ```bash
   python manage.py makemigrations
   ```

4. **Revisar la migración generada** para asegurarse de que respeta el esquema

5. **Aplicar la migración:**
   ```bash
   python manage.py migrate
   ```

## Esquemas Disponibles

- **`cat`** - Catalog and Master Data
  - clients, technicians, equipment
  - aspiration_codes, color_codes, etc.

- **`inv`** - Inventory Management
  - warehouses, stock, transactions
  - product_master, bins, purchase_orders

- **`svc`** - Service Management
  - work_orders, invoices, payments
  - service_checklists, flat_rate_standards

- **`doc`** - Document Management
  - documents

- **`app`** - Application Management
  - alerts, audit_logs, business_rules

- **`kpi`** - Key Performance Indicators
  - wo_metrics, etc.

- **`oem`** - Original Equipment Manufacturer
  - brands, catalog_items, equivalences

## Comandos Útiles

### Verificar esquemas:
```sql
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema');
```

### Verificar tablas por esquema:
```sql
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname = 'cat'
ORDER BY tablename;
```

### Crear nuevo esquema (si es necesario):
```sql
CREATE SCHEMA IF NOT EXISTS nuevo_esquema;
```

## Próximos Pasos

1. ✅ Verificar que todos los modelos tienen `db_table` correcto
2. ⏳ Crear Database Router personalizado (opcional, para mejor manejo)
3. ⏳ Documentar proceso para agregar nuevos modelos
4. ⏳ Crear script de verificación de esquemas
5. ⏳ Establecer proceso de revisión de migraciones

