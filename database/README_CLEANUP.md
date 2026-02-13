# Scripts de Limpieza de Tablas Duplicadas

## Problema

Django creó tablas duplicadas en el esquema `app` con nombres incorrectos porque interpretó `db_table='cat.clients'` como un nombre literal de tabla, no como `schema.table`.

## Scripts Disponibles

### 1. `cleanup_duplicate_tables_safe.sql` (EJECUTAR PRIMERO)
**Solo consultas, NO elimina nada.**

Este script verifica y lista:
- Todas las tablas en el esquema `app`
- Qué tablas son problemáticas
- Qué tablas son correctas
- Qué tablas serían eliminadas

**Ejecutar:**
```bash
psql -U postgres -d forge_db -f database/cleanup_duplicate_tables_safe.sql
```

O desde Django:
```bash
python manage.py dbshell < database/cleanup_duplicate_tables_safe.sql
```

### 2. `cleanup_duplicate_tables.sql` (EJECUTAR DESPUÉS)
**SÍ ELIMINA tablas duplicadas.**

Este script:
1. Verifica que las tablas correctas existen
2. Elimina las tablas duplicadas del esquema `app`
3. Verifica que la limpieza fue exitosa
4. Lista las tablas finales en `app`

**IMPORTANTE:**
- ⚠️ **HACER BACKUP ANTES DE EJECUTAR**
- ⚠️ Ejecutar primero en desarrollo
- ⚠️ Verificar los resultados del script seguro primero

**Ejecutar:**
```bash
psql -U postgres -d forge_db -f database/cleanup_duplicate_tables.sql
```

O desde Django:
```bash
python manage.py dbshell < database/cleanup_duplicate_tables.sql
```

## Tablas que serán Eliminadas

Las siguientes tablas duplicadas serán eliminadas del esquema `app`:

1. `app."app.alerts"` (duplicado de `app.alerts`)
2. `app."app.audit_logs"` (duplicado de `app.audit_logs`)
3. `app."app.business_rules"` (duplicado de `app.business_rules`)
4. `app."cat.clients"` (duplicado de `cat.clients`)
5. `app."cat.equipment"` (duplicado de `cat.equipment`)
6. `app."cat.technicians"` (duplicado de `cat.technicians`)
7. `app."doc.documents"` (duplicado de `doc.documents`)
8. `app."inv.product_master"` (duplicado de `inv.product_master`)
9. `app."inv.stock"` (duplicado de `inv.stock`)
10. `app."inv.transactions"` (duplicado de `inv.transactions`)
11. `app."inv.warehouses"` (duplicado de `inv.warehouses`)
12. `app."svc.invoices"` (duplicado de `svc.invoices`)
13. `app."svc.work_orders"` (duplicado de `svc.work_orders`)

## Tablas que NO serán Eliminadas

Las siguientes tablas en `app` son CORRECTAS y NO serán eliminadas:

- `app.alerts` (correcta)
- `app.audit_logs` (correcta)
- `app.business_rules` (correcta)
- `auth_*` (tablas de Django)
- `django_*` (tablas de Django)

## Proceso Recomendado

1. **Hacer backup de la base de datos:**
   ```bash
   pg_dump -U postgres forge_db > backup_before_cleanup.sql
   ```

2. **Ejecutar script seguro para verificar:**
   ```bash
   psql -U postgres -d forge_db -f database/cleanup_duplicate_tables_safe.sql
   ```

3. **Revisar los resultados** y asegurarse de que:
   - Las tablas correctas existen en sus esquemas
   - Las tablas duplicadas no tienen datos importantes
   - Las tablas correctas tienen los datos correctos

4. **Ejecutar script de limpieza:**
   ```bash
   psql -U postgres -d forge_db -f database/cleanup_duplicate_tables.sql
   ```

5. **Verificar resultados:**
   - Las tablas duplicadas deben haber sido eliminadas
   - Las tablas correctas deben seguir existiendo
   - La aplicación debe funcionar normalmente

## Verificación Post-Limpieza

Después de ejecutar el script, verifica:

1. **Que las tablas correctas existen:**
   ```sql
   SELECT schemaname, tablename 
   FROM pg_tables 
   WHERE (schemaname, tablename) IN (
       ('cat', 'clients'),
       ('inv', 'warehouses'),
       ('svc', 'work_orders'),
       -- etc.
   )
   ORDER BY schemaname, tablename;
   ```

2. **Que las tablas duplicadas fueron eliminadas:**
   ```sql
   SELECT tablename 
   FROM pg_tables 
   WHERE schemaname = 'app' 
   AND tablename LIKE '%.%';
   -- No debe devolver resultados
   ```

3. **Que Django puede acceder a las tablas:**
   ```bash
   python manage.py dbshell
   # Luego en el shell:
   SELECT COUNT(*) FROM cat.clients;
   SELECT COUNT(*) FROM inv.warehouses;
   -- etc.
   ```

## Notas Adicionales

- El script usa `CASCADE` para eliminar dependencias automáticamente
- El script está dentro de una transacción (BEGIN/COMMIT) para poder revertir si es necesario
- Si hay errores, la transacción se revertirá automáticamente
- Las tablas de Django (auth_*, django_*) NO serán afectadas

## Solución de Problemas

Si después de ejecutar el script hay problemas:

1. **Restaurar desde backup:**
   ```bash
   psql -U postgres -d forge_db < backup_before_cleanup.sql
   ```

2. **Verificar logs de PostgreSQL** para errores específicos

3. **Ejecutar el script seguro** nuevamente para ver el estado actual

