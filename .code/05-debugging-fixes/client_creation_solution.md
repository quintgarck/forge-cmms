# Solución al Problema de Creación de Clientes en ForgeDB

## Problema Identificado
No se pueden crear clientes desde la interfaz web de ForgeDB.

## Causa Raíz
Después de diagnosticar el sistema, se identificó que:

1. **Faltaba un técnico en la base de datos**: El modelo de clientes requiere un campo `created_by` que referencia a un técnico, pero no había técnicos registrados.
2. **Este requisito es necesario para la creación de clientes a través de la API**.

## Solución Aplicada
1. Se creó un técnico por defecto en la base de datos con las siguientes credenciales:
   - Nombre: System Administrator
   - Código de empleado: TECH001
   - Email: admin@forgedb.com

2. Se creó un usuario administrador para acceder al sistema:
   - Username: admin
   - Password: admin123

## Pasos para Crear Clientes Exitosamente

### 1. Iniciar el Servidor Django
Asegúrate de tener el servidor Django corriendo:

```bash
cd "C:\Users\Oskar QuintGarck\DataMain\02-DataCore\01-DevOps\02-Docker\project-root\building\tunning-management\cmms\forge_api"
python manage.py runserver
```

### 2. Acceder al Sistema
1. Abre tu navegador web
2. Ve a: http://127.0.0.1:8000/
3. Inicia sesión con:
   - Username: admin
   - Password: admin123

### 3. Crear un Cliente Nuevo
1. Una vez dentro del sistema, navega a la sección de Clientes
2. Haz clic en "Crear Cliente" o "New Client"
3. Completa todos los campos requeridos:
   - Código de Cliente (ej: CLI001)
   - Tipo (Individual, Empresa, Flota)
   - Nombre completo
   - Email
   - Teléfono
   - Dirección (opcional pero recomendada)
   - Límite de crédito (opcional)

### 4. Verificar la Creación
Después de enviar el formulario, deberías ver:
- Un mensaje de confirmación de creación exitosa
- El cliente listado en la página de clientes
- La posibilidad de editar o ver los detalles del cliente

## Campos Requeridos para la Creación de Clientes

Cuando crees un cliente, asegúrate de completar al menos estos campos:

- **Código de Cliente**: Identificador único (solo letras, números, guiones y guiones bajos)
- **Tipo**: Individual, Empresa o Flota
- **Nombre**: Nombre completo del cliente
- **Email**: Dirección de correo válida
- **Teléfono**: Número de contacto con al menos 8 dígitos

## Posibles Problemas y Soluciones

### Problema: "Sesión expirada" o "No autorizado"
**Solución**: Asegúrate de estar correctamente autenticado en el sistema.

### Problema: Campos de formulario en rojo
**Solución**: Verifica que todos los campos requeridos estén completos y con el formato correcto.

### Problema: Código de cliente ya existe
**Solución**: Usa un código de cliente único (diferente al existente).

### Problema: Error 500 del servidor
**Solución**: Revisa los logs del servidor Django para más detalles del error.

## Verificación Final

Después de crear un cliente, puedes verificar que todo funciona correctamente:

1. El cliente aparece en la lista de clientes
2. Puedes ver los detalles del cliente recién creado
3. El cliente tiene un técnico asignado como creador (System Administrator)
4. No hay errores en la consola del navegador ni en los logs del servidor

## Recomendaciones de Seguridad

- Cambia la contraseña por defecto ('admin123') por una más segura
- Crea usuarios con roles específicos en lugar de usar siempre el admin
- Realiza backups regulares de la base de datos

## Conclusión

El problema de creación de clientes ha sido resuelto al asegurar que existe al menos un técnico en la base de datos, lo cual es requerido por el modelo de datos de ForgeDB. Con este técnico disponible, la operación de creación de clientes puede completarse exitosamente desde la interfaz web.