# Guía de Despliegue - Forge CMMS

Esta guía explica cómo desplegar la aplicación Forge CMMS en un VPS usando Docker.

## Requisitos Previos

- VPS con Ubuntu 20.04+ o similar
- Docker y Docker Compose instalados
- Dominio configurado: `moviax.sagecores.com`
- **PostgreSQL corriendo en contenedor `postgres_core` (puerto 5433)**
- **Nginx Proxy Manager corriendo y configurado**
- Certificados SSL manejados por NPM (Let's Encrypt)

## Estructura del Proyecto

```
forge-cmms/
├── Dockerfile                 # Imagen de la aplicación
├── docker-compose.yml         # Para desarrollo local
├── docker-compose.prod.yml    # Para producción en VPS
├── docker-entrypoint.sh       # Script de inicio del contenedor
├── .env.example              # Variables de entorno de ejemplo
├── nginx/
│   ├── nginx.conf            # Configuración principal de Nginx
│   └── conf.d/
│       └── default.conf      # Configuración del sitio
└── forge_api/                # Código de la aplicación Django
```

## Pasos para Desplegar en el VPS

### 1. Preparar el VPS

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker y Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar sesión o ejecutar:
newgrp docker
```

### 2. Clonar/Subir el Proyecto al VPS

```bash
# Opción A: Si tienes Git
cd /opt
git clone <tu-repositorio> forge-cmms
cd forge-cmms

# Opción B: Subir archivos vía SCP/SFTP
# Sube todos los archivos a /opt/forge-cmms/
```

### 3. Configurar Variables de Entorno

```bash
cd /opt/forge-cmms

# Copiar archivo de ejemplo
cp .env.example .env.production

# Editar con tus valores reales
nano .env.production
```

**Configuración mínima para `.env.production`:**

```env
# Django Settings
SECRET_KEY=genera-una-clave-secreta-muy-segura-aqui
DEBUG=False
ALLOWED_HOSTS=moviax.sagecores.com

# Database Configuration (conectar a PostgreSQL en contenedor postgres_core)
DB_HOST=localhost
DB_NAME=forge_db
DB_USER=postgres
DB_PASSWORD=tu-password-seguro
DB_PORT=5433  # IMPORTANTE: Puerto 5433 (mapeado desde 5432 del contenedor)
```

**Generar SECRET_KEY seguro:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Configurar Nginx Proxy Manager

**IMPORTANTE**: Ya tienes Nginx Proxy Manager corriendo, así que NO necesitas configurar Nginx manualmente.

Sigue las instrucciones en `NGINX_PROXY_MANAGER_SETUP.md` para configurar el proxy host en NPM.

**Resumen rápido**:
1. Accede a NPM (normalmente en `http://tu-vps-ip:81`)
2. Crea un nuevo Proxy Host:
   - Domain: `moviax.sagecores.com`
   - Forward to: `localhost:8000`
   - SSL: Solicita certificado Let's Encrypt
   - Force SSL: Activado
3. Guarda y espera a que se genere el certificado SSL

### 5. Construir y Ejecutar la Aplicación

```bash
cd /opt/forge-cmms

# Construir la imagen
docker-compose -f docker-compose.prod.yml build

# Ejecutar en segundo plano
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f web

# Verificar que está corriendo
docker ps | grep forge-cmms-web-prod
```

### 6. Configurar Proxy en Nginx Proxy Manager

Ver instrucciones detalladas en `NGINX_PROXY_MANAGER_SETUP.md`.

**Resumen**:
1. Accede a NPM en `http://tu-vps-ip:81`
2. Crea Proxy Host para `moviax.sagecores.com` → `localhost:8000`
3. Configura SSL con Let's Encrypt
4. Activa "Force SSL"

### 7. Verificar el Despliegue

```bash
# Verificar que los contenedores están corriendo
docker-compose -f docker-compose.prod.yml ps
docker ps | grep forge-cmms

# Verificar logs
docker-compose -f docker-compose.prod.yml logs web

# Probar la aplicación localmente
curl http://localhost:8000/api/

# Probar a través del dominio (después de configurar NPM)
curl https://moviax.sagecores.com/api/
```

### 8. Ejecutar Migraciones (si es necesario)

```bash
# Ejecutar migraciones manualmente si no se ejecutaron automáticamente
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Crear superusuario
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Comandos Útiles

### Gestión de Contenedores

```bash
# Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# Detener servicios
docker-compose -f docker-compose.prod.yml down

# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx

# Ver estado
docker-compose -f docker-compose.prod.yml ps
```

### Mantenimiento

```bash
# Ejecutar comandos Django
docker-compose -f docker-compose.prod.yml exec web python manage.py <comando>

# Acceder al shell de Django
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Recopilar archivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Hacer backup de la base de datos (si está en Docker)
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres forge_db > backup.sql
```

### Actualizar la Aplicación

```bash
cd /opt/forge-cmms

# Detener servicios
docker-compose -f docker-compose.prod.yml down

# Actualizar código (si usas Git)
git pull

# Reconstruir imagen
docker-compose -f docker-compose.prod.yml build --no-cache

# Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# Ejecutar migraciones si hay cambios
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## Configuración de Firewall

```bash
# Permitir puertos HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Si la BD está en otro servidor, permitir conexión
sudo ufw allow from <ip-bd> to any port 5432
```

## Monitoreo y Logs

Los logs se guardan en:
- Contenedor web: `docker-compose logs web`
- Contenedor nginx: `docker-compose logs nginx`
- Volumen de logs: `/var/lib/docker/volumes/forge-cmms_logs/`

## Troubleshooting

### La aplicación no inicia

```bash
# Ver logs detallados
docker-compose -f docker-compose.prod.yml logs web

# Verificar conexión a BD
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

### Error de permisos

```bash
# Ajustar permisos de volúmenes
sudo chown -R $USER:$USER /opt/forge-cmms
```

### Nginx no puede acceder a archivos estáticos

```bash
# Verificar que los volúmenes están montados correctamente
docker-compose -f docker-compose.prod.yml exec nginx ls -la /app/staticfiles
```

### Renovar certificados SSL (Let's Encrypt)

```bash
# Renovación automática (configurar en cron)
sudo certbot renew --dry-run

# O renovar manualmente
sudo certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
```

## Notas Importantes

1. **Base de datos externa**: Si tu BD está en otro servidor, asegúrate de:
   - Configurar `DB_HOST` con la IP o hostname correcto
   - Permitir conexiones desde el contenedor Docker en el firewall de PostgreSQL
   - Verificar que `pg_hba.conf` permite conexiones remotas

2. **Seguridad**:
   - Nunca commitees `.env.production` al repositorio
   - Usa contraseñas seguras
   - Mantén Docker y las imágenes actualizadas
   - Configura backups automáticos de la BD

3. **Rendimiento**:
   - Ajusta el número de workers de Gunicorn según los recursos del VPS
   - Considera usar Redis para cache si es necesario
   - Monitorea el uso de recursos con `docker stats`

## Siguiente Paso: SaaS Multitenancy

Una vez que la aplicación esté desplegada y funcionando, puedes proceder con la implementación del plan SaaS multitenancy según el documento `docs/SAAS_MULTITENANCY_RECOMMENDATIONS.md`.
