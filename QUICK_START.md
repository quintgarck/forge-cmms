# Inicio Rápido - Forge CMMS en VPS

## Resumen de tu Stack Actual

- ✅ PostgreSQL corriendo en `postgres_core` (puerto 5433)
- ✅ Nginx Proxy Manager corriendo en puertos 80, 443, 81
- ✅ Dominio: `moviax.sagecores.com`

## Pasos Rápidos para Desplegar

### 1. Subir Código al VPS

```bash
# En tu máquina local
cd /ruta/a/forge-cmms
scp -r . usuario@tu-vps:/opt/forge-cmms/

# O usar Git
cd /opt/forge-cmms
git clone <tu-repo> .
```

### 2. Configurar Variables de Entorno

```bash
cd /opt/forge-cmms
cp .env.example .env.production
nano .env.production
```

**Configuración mínima:**
```env
SECRET_KEY=<generar-clave-segura>
DEBUG=False
ALLOWED_HOSTS=moviax.sagecores.com,localhost,127.0.0.1
DB_HOST=postgres_core  # Nombre del contenedor, NO localhost
DB_NAME=forge_db
DB_USER=postgres
DB_PASSWORD=<tu-password-postgres>
DB_PORT=5432  # Puerto interno del contenedor, NO 5433
```

**Generar SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Verificar Redes Docker

```bash
cd /opt/forge-cmms

# Ejecutar script de verificación de redes
chmod +x setup-networks.sh
./setup-networks.sh

# Este script verifica que la red core_shared-network existe
# y que NPM y PostgreSQL están conectados a ella
```

### 4. Construir y Ejecutar

```bash
cd /opt/forge-cmms

# Construir imagen
docker-compose -f docker-compose.prod.yml build

# Iniciar contenedor
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f web
```

### 4. Verificar que Funciona

```bash
# Verificar contenedor
docker ps | grep forge-cmms

# Probar API localmente
curl http://localhost:8000/api/

# Ver logs si hay problemas
docker logs forge-cmms-web-prod
```

### 5. Configurar Nginx Proxy Manager

1. Accede a NPM: `http://tu-vps-ip:81`
2. Ve a **Proxy Hosts** → **Add Proxy Host**
3. Configura:
   - **Domain**: `moviax.sagecores.com`
   - **Forward Hostname/IP**: `forge-cmms-web-prod` (nombre del contenedor)
   - **Forward Port**: `8000`
   - **SSL**: Solicita certificado Let's Encrypt
   - **Force SSL**: ✅ Activado
4. Guarda y espera a que se genere el SSL

**IMPORTANTE**: Usa el nombre del contenedor (`forge-cmms-web-prod`), NO `localhost`. Esto funciona porque ambos están en la red `proxy_network`.

### 6. Verificar Despliegue

```bash
# Probar desde el dominio
curl https://moviax.sagecores.com/api/

# O abrir en navegador
# https://moviax.sagecores.com
```

## Comandos Útiles

```bash
# Ver logs
docker logs forge-cmms-web-prod -f

# Reiniciar aplicación
docker-compose -f docker-compose.prod.yml restart

# Ejecutar migraciones
docker exec forge-cmms-web-prod python manage.py migrate

# Crear superusuario
docker exec -it forge-cmms-web-prod python manage.py createsuperuser

# Recopilar archivos estáticos
docker exec forge-cmms-web-prod python manage.py collectstatic --noinput

# Acceder al shell de Django
docker exec -it forge-cmms-web-prod python manage.py shell
```

## Troubleshooting Rápido

### Error: No se conecta a la BD

```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep postgres_core

# Verificar que ambos contenedores están en la misma red
docker network inspect <nombre-red-postgres> | grep -E "postgres_core|forge-cmms"

# Verificar resolución DNS desde Forge CMMS
docker exec forge-cmms-web-prod ping -c 2 postgres_core

# Probar conexión manual
docker exec forge-cmms-web-prod python manage.py dbshell

# Verificar variables de entorno
docker exec forge-cmms-web-prod env | grep DB_
```

### Error: 502 Bad Gateway en NPM

```bash
# Verificar que el contenedor está corriendo
docker ps | grep forge-cmms

# Verificar que responde en puerto 8000
curl http://localhost:8000/api/

# Ver logs
docker logs forge-cmms-web-prod
```

### Error: Archivos estáticos no cargan

```bash
# Recopilar archivos estáticos
docker exec forge-cmms-web-prod python manage.py collectstatic --noinput
```

## Documentación Completa

- `DEPLOYMENT.md` - Guía completa de despliegue
- `NGINX_PROXY_MANAGER_SETUP.md` - Configuración detallada de NPM
- `CHANGES_REQUIRED.md` - Checklist de cambios necesarios
- `README_DOCKER.md` - Guía de uso de Docker
