# Forge CMMS - Guía Rápida de Docker

## Inicio Rápido - Desarrollo Local

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones locales
```

### 2. Iniciar la aplicación

```bash
# Construir e iniciar todos los servicios (web, db, nginx)
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Verificar que todo está corriendo
docker-compose ps
```

### 3. Acceder a la aplicación

- **Frontend**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin
- **API Swagger**: http://localhost:8000/swagger/

### 4. Comandos útiles

```bash
# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Acceder al shell de Django
docker-compose exec web python manage.py shell

# Ver logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx
```

## Despliegue en VPS

Ver el archivo `DEPLOYMENT.md` para instrucciones completas de despliegue en producción.

### Resumen rápido:

1. Subir código al VPS
2. Crear `.env.production` con configuración de producción
3. Configurar SSL (Let's Encrypt recomendado)
4. Ejecutar: `docker-compose -f docker-compose.prod.yml up -d`

## Estructura de Archivos Docker

- `Dockerfile`: Imagen de la aplicación Django
- `docker-compose.yml`: Configuración para desarrollo (incluye BD)
- `docker-compose.prod.yml`: Configuración para producción (BD externa)
- `docker-entrypoint.sh`: Script de inicio del contenedor
- `.env.example`: Plantilla de variables de entorno
- `nginx/`: Configuración de Nginx como reverse proxy

## Cambios Necesarios Antes del Despliegue

### 1. Variables de Entorno (.env.production)

```env
SECRET_KEY=<generar-clave-segura>
DEBUG=False
ALLOWED_HOSTS=moviax.sagecores.com
DB_HOST=localhost  # o IP de tu servidor BD
DB_NAME=forge_db
DB_USER=postgres
DB_PASSWORD=<tu-password>
DB_PORT=5432
```

### 2. Configurar SSL en Nginx

**Opción A: Let's Encrypt (Recomendado)**

```bash
sudo certbot --nginx -d moviax.sagecores.com
```

Luego actualizar `nginx/conf.d/default.conf` para usar:
```nginx
ssl_certificate /etc/letsencrypt/live/moviax.sagecores.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/moviax.sagecores.com/privkey.pem;
```

**Opción B: Certificados Propios**

Copiar certificados a `nginx/ssl/`:
- `cert.pem`
- `key.pem`

### 3. Verificar Conexión a Base de Datos

Asegúrate de que:
- PostgreSQL está corriendo en el VPS
- El firewall permite conexiones al puerto 5432 (si es necesario)
- Las credenciales en `.env.production` son correctas
- La base de datos `forge_db` existe

### 4. Ajustar Configuración de Nginx

Si usas `network_mode: host` en producción, actualiza `nginx/conf.d/default.conf`:

```nginx
upstream django {
    server localhost:8000;  # Cambiar de 'web:8000' a 'localhost:8000'
}
```

## Troubleshooting

### Error: No se puede conectar a la base de datos

```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Probar conexión manualmente
docker-compose exec web python manage.py dbshell
```

### Error: Archivos estáticos no se cargan

```bash
# Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

### Error: Permisos denegados

```bash
# Ajustar permisos
sudo chown -R $USER:$USER .
```

### Ver logs detallados

```bash
# Logs de la aplicación
docker-compose logs web

# Logs de Nginx
docker-compose logs nginx

# Logs de todos los servicios
docker-compose logs
```

## Próximos Pasos

Una vez que la aplicación esté corriendo en Docker:

1. ✅ Verificar que todo funciona correctamente
2. ✅ Configurar backups de la base de datos
3. ✅ Configurar monitoreo y alertas
4. ✅ Proceder con el plan SaaS Multitenancy (ver `docs/SAAS_MULTITENANCY_RECOMMENDATIONS.md`)
