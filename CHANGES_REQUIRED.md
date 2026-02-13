# Cambios Necesarios Antes del Despliegue

## Resumen de Cambios

Este documento lista los cambios que debes hacer antes de desplegar la aplicación en el VPS.

## 1. Configurar Variables de Entorno

### Crear archivo `.env.production` en el VPS

```bash
cp .env.example .env.production
nano .env.production
```

**Configuración mínima requerida:**

```env
# Django Settings
SECRET_KEY=<generar-clave-segura-aqui>
DEBUG=False
ALLOWED_HOSTS=moviax.sagecores.com

# Database Configuration
# IMPORTANTE: Ajustar según tu configuración de BD en el VPS
DB_HOST=localhost
DB_NAME=forge_db
DB_USER=postgres
DB_PASSWORD=<tu-password-real>
DB_PORT=5433  # IMPORTANTE: Puerto 5433 (mapeado desde contenedor postgres_core)
```

**Generar SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 2. Configurar Nginx Proxy Manager

**IMPORTANTE**: Ya tienes Nginx Proxy Manager corriendo, así que NO necesitas configurar Nginx manualmente.

Sigue las instrucciones en `NGINX_PROXY_MANAGER_SETUP.md` para configurar el proxy host.

**Resumen**:
1. Accede a NPM (normalmente en `http://tu-vps-ip:81`)
2. Crea Proxy Host:
   - Domain: `moviax.sagecores.com`
   - Forward to: `localhost:8000`
   - SSL: Let's Encrypt
   - Force SSL: Activado

## 3. Ajustar Configuración de Red

### Configuración Actual (Recomendada)

**En `docker-compose.prod.yml`** ya está configurado con `network_mode: "host"` para acceder a PostgreSQL en `localhost:5433`.

**No necesitas configurar Nginx** porque NPM maneja el proxy reverso.

### Si prefieres usar networks (BD en otro servidor)

**En `docker-compose.prod.yml`**, cambiar:
```yaml
services:
  web:
    # ... otras configuraciones ...
    networks:
      - forge-network
    # Eliminar: network_mode: "host"
  
  nginx:
    # ... otras configuraciones ...
    networks:
      - forge-network
    # Eliminar: network_mode: "host"
```

**Nota**: Si usas networks, también necesitarías configurar NPM para conectarse a través de la red Docker, lo cual es más complejo. Se recomienda usar `network_mode: host`.

## 4. Verificar Base de Datos

### Asegurar que PostgreSQL está configurado correctamente

```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Verificar que la base de datos existe
sudo -u postgres psql -l | grep forge_db

# Si no existe, crearla
sudo -u postgres psql -c "CREATE DATABASE forge_db;"

# Verificar permisos de usuario
sudo -u postgres psql -c "\du"
```

### Configurar acceso remoto (si BD está en otro servidor)

**En `/etc/postgresql/*/main/pg_hba.conf`:**
```
host    forge_db    postgres    0.0.0.0/0    md5
```

**En `/etc/postgresql/*/main/postgresql.conf`:**
```
listen_addresses = '*'
```

## 5. Configurar Firewall

```bash
# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Si la BD está en otro servidor
sudo ufw allow from <ip-bd> to any port 5432

# Verificar estado
sudo ufw status
```

## 6. Crear Directorios Necesarios

```bash
# Crear directorios para volúmenes
mkdir -p logs
mkdir -p nginx/ssl

# Ajustar permisos
chmod +x docker-entrypoint.sh
```

## 7. Verificar Configuración de Django

### Revisar `forge_api/forge_api/settings.py`

Asegúrate de que:
- `DEBUG = False` en producción (se controla con variable de entorno)
- `ALLOWED_HOSTS` incluye tu dominio
- La configuración de BD lee correctamente las variables de entorno

## Checklist de Despliegue

- [ ] Archivo `.env.production` creado y configurado
- [ ] `SECRET_KEY` generado y configurado
- [ ] `DEBUG=False` en `.env.production`
- [ ] `ALLOWED_HOSTS` incluye `moviax.sagecores.com`
- [ ] Credenciales de BD configuradas correctamente
- [ ] PostgreSQL corriendo y accesible
- [ ] Base de datos `forge_db` existe
- [ ] Nginx Proxy Manager configurado (ver `NGINX_PROXY_MANAGER_SETUP.md`)
- [ ] Proxy Host creado en NPM para `moviax.sagecores.com`
- [ ] SSL configurado en NPM (Let's Encrypt)
- [ ] Firewall configurado (puertos 80, 443 ya manejados por NPM)
- [ ] Directorios creados con permisos correctos
- [ ] `docker-entrypoint.sh` tiene permisos de ejecución

## Comandos de Verificación

```bash
# Verificar que Docker está instalado
docker --version
docker-compose --version

# Verificar configuración de docker-compose
docker-compose -f docker-compose.prod.yml config

# Probar conexión a BD desde el contenedor
docker-compose -f docker-compose.prod.yml run --rm web python manage.py dbshell

# Verificar variables de entorno
docker-compose -f docker-compose.prod.yml run --rm web env | grep DB_
```

## Siguiente Paso

Una vez completados todos los cambios, seguir las instrucciones en `DEPLOYMENT.md` para desplegar la aplicación.
