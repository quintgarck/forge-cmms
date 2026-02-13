# Configuración de Redes Docker - Forge CMMS

Este documento explica cómo configurar las redes Docker para una arquitectura segura y escalable.

## Arquitectura de Redes

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Nginx Proxy Manager (npm_core)              │
│              Red: proxy_network                         │
└────────────────────┬────────────────────────────────────┘
                     │ (comunicación interna)
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Forge CMMS (forge-cmms-web-prod)                │
│         Redes: proxy_network + postgres_network         │
└────────────────────┬────────────────────────────────────┘
                     │ (comunicación interna)
                     ▼
┌─────────────────────────────────────────────────────────┐
│         PostgreSQL (postgres_core)                       │
│         Red: postgres_network                           │
└─────────────────────────────────────────────────────────┘
```

## Ventajas de Usar Redes Docker

1. **Seguridad**: Los contenedores solo se comunican a través de redes internas
2. **Aislamiento**: Cada servicio está aislado en su propia red
3. **Escalabilidad**: Fácil agregar más servicios sin exponer puertos
4. **DNS Interno**: Docker resuelve nombres de contenedores automáticamente
5. **Mejores Prácticas**: Sigue las recomendaciones de Docker

## Configuración Paso a Paso

### Paso 1: Verificar Red Existente

En tu VPS, tanto NPM como PostgreSQL están en la red `core_shared-network`:

```bash
# Verificar que la red existe
docker network ls | grep core_shared-network

# Verificar que NPM está en la red
docker inspect npm_core | grep -A 10 "Networks"

# Verificar que PostgreSQL está en la red
docker inspect postgres_core | grep -A 10 "Networks"
```

**Resultado esperado**: Ambos contenedores deben estar en `core_shared-network`.

### Paso 2: Verificar docker-compose.prod.yml

El archivo `docker-compose.prod.yml` ya está configurado para usar `core_shared-network`. Verifica que tiene:

```yaml
networks:
  core_shared-network:
    external: true
    name: core_shared-network
```

### Paso 3: Ejecutar Script de Verificación

Usa el script proporcionado para verificar la configuración:

```bash
chmod +x setup-networks.sh
./setup-networks.sh
```

Este script verificará que todo está correctamente configurado.

### Paso 6: Verificar Configuración

```bash
# Verificar que las redes existen
docker network ls | grep -E "proxy_network|postgres"

# Verificar que los contenedores están en las redes correctas
docker network inspect proxy_network
docker network inspect <nombre-red-postgres>
```

## Configuración Manual (Alternativa)

Si prefieres configurar manualmente:

### Opción A: Usar Red Existente de PostgreSQL

Si PostgreSQL ya está en una red, conecta Forge CMMS a esa red:

```bash
# 1. Identificar la red
POSTGRES_NET=$(docker inspect postgres_core --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}}{{end}}' | head -1)

# 2. Actualizar docker-compose.prod.yml con el nombre correcto
# 3. Ejecutar docker-compose
```

### Opción B: Crear Nueva Red y Conectar Todo

```bash
# Crear red compartida
docker network create --driver bridge app_network

# Conectar PostgreSQL
docker network connect app_network postgres_core

# Conectar NPM
docker network connect app_network npm_core

# Actualizar docker-compose.prod.yml para usar app_network
```

## Configuración en docker-compose.prod.yml

```yaml
services:
  web:
    # ... otras configuraciones ...
    networks:
      - core_shared-network  # Red compartida con NPM y PostgreSQL
    expose:
      - "8000"               # Solo expone internamente, no públicamente

networks:
  core_shared-network:
    external: true
    name: core_shared-network
```

## Configuración en Nginx Proxy Manager

En NPM, cuando crees el Proxy Host:

1. **Domain Names**: `moviax.sagecores.com`
2. **Forward Hostname/IP**: `forge-cmms-web-prod` (nombre del contenedor)
3. **Forward Port**: `8000`
4. **Scheme**: `http`

**IMPORTANTE**: Usa el **nombre del contenedor** (`forge-cmms-web-prod`), no `localhost` ni una IP.

## Verificación de Conectividad

### Desde el contenedor de Forge CMMS:

```bash
# Verificar que puede resolver el nombre de PostgreSQL
docker exec forge-cmms-web-prod ping -c 2 postgres_core

# Verificar conexión a PostgreSQL
docker exec forge-cmms-web-prod python manage.py dbshell
```

### Desde NPM:

```bash
# Verificar que puede resolver el nombre de Forge CMMS
docker exec npm_core ping -c 2 forge-cmms-web-prod

# Verificar que puede acceder al puerto 8000
docker exec npm_core wget -O- http://forge-cmms-web-prod:8000/api/
```

## Troubleshooting

### Error: "network not found"

**Problema**: La red externa `core_shared-network` no existe.

**Solución**:
```bash
# Verificar si la red existe
docker network ls | grep core_shared-network

# Si no existe, crearla (aunque debería existir ya)
docker network create --driver bridge core_shared-network

# Conectar los contenedores existentes si no están conectados
docker network connect core_shared-network npm_core
docker network connect core_shared-network postgres_core
```

### Error: "Cannot connect to postgres_core"

**Problema**: Forge CMMS no puede conectarse a PostgreSQL.

**Solución**:
```bash
# Verificar que ambos están en core_shared-network
docker network inspect core_shared-network | grep -E "postgres_core|forge-cmms"

# Verificar resolución DNS desde Forge CMMS
docker exec forge-cmms-web-prod ping -c 2 postgres_core

# Verificar variables de entorno
docker exec forge-cmms-web-prod env | grep DB_

# Verificar que DB_HOST=postgres_core (nombre del contenedor)
```

### Error: "502 Bad Gateway" en NPM

**Problema**: NPM no puede alcanzar Forge CMMS.

**Solución**:
```bash
# Verificar que ambos están en core_shared-network
docker network inspect core_shared-network | grep -E "npm_core|forge-cmms"

# Verificar que Forge CMMS está corriendo
docker ps | grep forge-cmms-web-prod

# Verificar conectividad desde NPM
docker exec npm_core ping -c 2 forge-cmms-web-prod

# Verificar que NPM puede acceder al puerto 8000
docker exec npm_core wget -O- http://forge-cmms-web-prod:8000/api/ 2>&1

# Verificar configuración en NPM:
# Forward Hostname/IP debe ser "forge-cmms-web-prod", NO "localhost"
```

### Error: "Connection refused" desde Forge CMMS a PostgreSQL

**Problema**: Configuración incorrecta de DB_HOST.

**Solución**:
- Verificar que `.env.production` tiene `DB_HOST=postgres_core` (nombre del contenedor)
- Verificar que `DB_PORT=5432` (puerto interno del contenedor, no el mapeado)
- Verificar que ambos contenedores están en la misma red

## Mejores Prácticas

1. **Usar nombres de contenedores**: Siempre usa nombres de contenedores en lugar de IPs
2. **Redes externas**: Define redes como `external: true` para compartirlas entre proyectos
3. **No exponer puertos innecesariamente**: Usa `expose` en lugar de `ports` para comunicación interna
4. **Nombres descriptivos**: Usa nombres claros para redes y contenedores
5. **Documentar redes**: Mantén documentación de qué servicios están en qué redes

## Comandos Útiles

```bash
# Listar todas las redes
docker network ls

# Inspeccionar una red específica
docker network inspect proxy_network

# Ver contenedores en una red
docker network inspect proxy_network --format='{{range .Containers}}{{.Name}} {{end}}'

# Desconectar un contenedor de una red
docker network disconnect proxy_network container_name

# Conectar un contenedor a una red
docker network connect proxy_network container_name

# Eliminar una red (solo si está vacía)
docker network rm network_name
```

## Seguridad Adicional

Para mayor seguridad, puedes:

1. **Usar redes con restricciones**:
```bash
docker network create --driver bridge --internal proxy_network
```

2. **Configurar políticas de firewall** en el host
3. **Usar secrets de Docker** para credenciales sensibles
4. **Implementar network policies** si usas Kubernetes

## Referencias

- [Docker Networking Documentation](https://docs.docker.com/network/)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
- [Best Practices for Docker Networking](https://docs.docker.com/network/bridge/)
