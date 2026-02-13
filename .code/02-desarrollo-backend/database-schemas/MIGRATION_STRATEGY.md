# Estrategia de Migraciones cuando las Tablas ya Existen

## Situación Actual

Las tablas ya existen en la base de datos porque fueron creadas desde el script SQL `database/forge_db.sql`. Django tiene modelos definidos pero las migraciones no están sincronizadas con la realidad de la base de datos.

## ¿Qué Pasa si Ejecuto Migraciones con Tablas Existentes?

### Escenario 1: Primera Migración (Initial Migration)
Si ejecutas `python manage.py migrate` y la migración intenta crear una tabla que ya existe:

**Sin `--fake-initial`:**
- Django intentará ejecutar `CREATE TABLE`
- PostgreSQL lanzará error: `relation "schema.table" already exists`
- La migración fallará

**Con `--fake-initial`:**
- Django detectará que la tabla ya existe
- Marcará la migración como aplicada sin ejecutar el SQL
- ✅ **Esto es lo que queremos**

### Escenario 2: Migraciones Posteriores
Si las tablas ya existen y ejecutas una migración que:
- **Agrega columnas:** Funcionará normalmente (ALTER TABLE)
- **Elimina columnas:** Funcionará normalmente (ALTER TABLE)
- **Crea índices:** Funcionará normalmente
- **Crea tablas nuevas:** Funcionará normalmente

## Estrategia Recomendada

### Opción 1: Usar --fake-initial (RECOMENDADO)

Si las tablas ya existen y coinciden con los modelos:

```bash
# 1. Crear las migraciones (si no existen)
python manage.py makemigrations core

# 2. Marcar como aplicadas sin ejecutar (fake initial)
python manage.py migrate --fake-initial core
```

**Ventajas:**
- No intenta crear tablas existentes
- Marca las migraciones como aplicadas
- Permite continuar con migraciones futuras normalmente

### Opción 2: Eliminar Tablas y Recrear (NO RECOMENDADO en producción)

```bash
# 1. Eliminar todas las tablas
# 2. Ejecutar migraciones normalmente
python manage.py migrate
```

**Desventajas:**
- Pierdes todos los datos
- Solo para desarrollo/estándares

### Opción 3: Migración Manual (Para casos complejos)

1. Crear migraciones vacías
2. Manualmente marcar como aplicadas
3. Continuar con migraciones futuras

## Proceso Paso a Paso

### Paso 1: Verificar Estado Actual

```bash
# Ver qué migraciones existen
python manage.py showmigrations core

# Ver qué tablas existen en la BD
python manage_schemas.py
```

### Paso 2: Crear Migraciones (si no existen)

```bash
python manage.py makemigrations core
```

Esto creará archivos de migración basados en los modelos actuales.

### Paso 3: Aplicar Migraciones con --fake-initial

```bash
python manage.py migrate --fake-initial core
```

Esto:
- Intentará aplicar las migraciones
- Si detecta que las tablas ya existen (y coinciden), las marcará como aplicadas sin ejecutar
- Si hay diferencias, te avisará

### Paso 4: Verificar

```bash
# Ver estado de migraciones
python manage.py showmigrations core

# Debe mostrar [X] para todas las migraciones
```

## ¿Qué Hace --fake-initial Exactamente?

Django usa `--fake-initial` para:

1. **Detectar tablas existentes:** Revisa si la tabla ya existe en la BD
2. **Comparar estructura:** Verifica si la estructura coincide con el modelo
3. **Marcar como aplicada:** Si coincide, marca la migración como aplicada SIN ejecutar SQL
4. **Aplicar diferencias:** Si hay diferencias (columnas faltantes, etc.), aplica solo esas diferencias

## Verificación de Coincidencia

Para que `--fake-initial` funcione correctamente, la estructura de la tabla debe coincidir con el modelo:

- ✅ Mismos campos (nombre y tipo)
- ✅ Mismas restricciones básicas (NOT NULL, UNIQUE, etc.)
- ✅ Misma clave primaria
- ⚠️ Índices y foreign keys pueden diferir ligeramente

Si hay diferencias significativas:
- Django intentará aplicar solo las diferencias (ALTER TABLE)
- O puede fallar si la diferencia es incompatible

## Comandos Útiles

### Ver diferencias entre modelo y BD:

```bash
# Ver estado de migraciones
python manage.py showmigrations core

# Verificar estructura de tabla
python manage.py dbshell
# Luego en PostgreSQL:
\d cat.clients
```

### Si --fake-initial no funciona:

```bash
# Opción 1: Marcar manualmente como aplicada
python manage.py migrate core 0001_initial --fake

# Opción 2: Ver qué SQL se ejecutaría
python manage.py sqlmigrate core 0001_initial
```

## Recomendación Final

1. ✅ **Usar `--fake-initial`** si las tablas ya existen
2. ✅ **Verificar después** que las migraciones están marcadas como aplicadas
3. ✅ **Continuar normalmente** con migraciones futuras
4. ✅ **No recrear las tablas** a menos que sea absolutamente necesario

