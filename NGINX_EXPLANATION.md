# Explicación: Nginx en Desarrollo vs Producción

Este documento explica cómo funciona Nginx en desarrollo local vs producción en el VPS.

## Arquitectura: Desarrollo vs Producción

### 🔧 Desarrollo Local (`docker-compose.yml`)

```
┌─────────────────────────────────────────────────────────┐
│              Tu Máquina Local                            │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                │
│  │   Nginx      │───▶ │  Django      │                │
│  │  (puerto 80) │    │  (puerto 8000)│                │
│  └──────────────┘    └──────────────┘                │
│         │                    │                          │
│         └────────────────────┘                          │
│              (red: forge-network)                        │
└─────────────────────────────────────────────────────────┘
```

**¿Por qué Nginx en desarrollo?**
- Para simular el entorno de producción
- Servir archivos estáticos eficientemente
- Probar configuración SSL localmente
- Testing de headers y configuración

### 🚀 Producción en VPS (`docker-compose.prod.yml`)

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Nginx Proxy Manager (npm_core)                  │
│         Ya está corriendo en tu VPS                     │
│         Puertos: 80, 443, 81                            │
└────────────────────┬────────────────────────────────────┘
                     │ (red: core_shared-network)
                     │ Proxy reverso
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Forge CMMS (forge-cmms-web-prod)                │
│         Puerto: 8000 (solo interno)                     │
│         NO expone puertos públicamente                   │
└────────────────────┬────────────────────────────────────┘
                     │ (red: core_shared-network)
                     ▼
┌─────────────────────────────────────────────────────────┐
│         PostgreSQL (postgres_core)                      │
└─────────────────────────────────────────────────────────┘
```

**¿Por qué NO hay Nginx en producción?**
- Ya tienes **Nginx Proxy Manager** corriendo
- NPM hace el trabajo de proxy reverso y SSL
- Evita duplicar servicios y conflictos de puertos
- Más simple y eficiente

## Comparación Detallada

| Aspecto | Desarrollo (`docker-compose.yml`) | Producción (`docker-compose.prod.yml`) |
|---------|-----------------------------------|----------------------------------------|
| **Nginx** | ✅ Sí, contenedor propio | ❌ No, usa NPM existente |
| **Puertos expuestos** | 80, 443 (Nginx) | Ninguno (solo interno) |
| **SSL** | Certificados locales o self-signed | Let's Encrypt via NPM |
| **Archivos estáticos** | Servidos por Nginx | Servidos por Django o NPM |
| **Proxy reverso** | Nginx → Django | NPM → Django |
| **Red Docker** | `forge-network` (aislada) | `core_shared-network` (compartida) |
| **Base de datos** | Contenedor propio (`db`) | Externa (`postgres_core`) |

## Flujo de Peticiones

### Desarrollo Local

1. **Cliente** → `http://localhost` → **Nginx** (puerto 80)
2. **Nginx** → `http://web:8000` → **Django** (red interna)
3. **Django** → Responde → **Nginx** → **Cliente**

### Producción en VPS

1. **Cliente** → `https://moviax.sagecores.com` → **NPM** (puerto 443)
2. **NPM** → `http://forge-cmms-web-prod:8000` → **Django** (red interna)
3. **Django** → Responde → **NPM** → **Cliente**

## ¿Cómo Interactúan NPM y Forge CMMS?

### Configuración en Nginx Proxy Manager

Cuando configuras el Proxy Host en NPM:

1. **Domain**: `moviax.sagecores.com`
2. **Forward Hostname/IP**: `forge-cmms-web-prod` (nombre del contenedor)
3. **Forward Port**: `8000`
4. **Scheme**: `http` (interno, NPM maneja HTTPS)

### Comunicación Interna

```
NPM (npm_core)                    Forge CMMS (forge-cmms-web-prod)
     │                                    │
     │  HTTP Request                      │
     │  Host: moviax.sagecores.com        │
     │───────────────────────────────────▶│
     │                                    │ Procesa request
     │                                    │ Consulta PostgreSQL
     │                                    │
     │  HTTP Response                     │
     │  (HTML, JSON, archivos estáticos)   │
     │◀───────────────────────────────────│
     │                                    │
     │  HTTPS Response                    │
     │  (con SSL)                          │
     └────────────────────────────────────┘
```

**Puntos clave:**
- NPM y Forge CMMS están en la misma red (`core_shared-network`)
- Se comunican por nombre de contenedor, no por IP
- La comunicación interna es HTTP (sin SSL)
- NPM agrega SSL al final antes de enviar al cliente

## Archivos Estáticos

### Opción 1: Django sirve todo (Recomendado para empezar)

Django sirve archivos estáticos y media a través de NPM:

```
Cliente → NPM → Django (static/media) → NPM → Cliente
```

**Ventajas:**
- Simple, no requiere configuración adicional
- Funciona inmediatamente

**Desventajas:**
- Menos eficiente para archivos estáticos grandes

### Opción 2: NPM sirve archivos estáticos (Optimización futura)

Puedes configurar NPM para servir archivos estáticos directamente:

**En NPM Advanced Tab:**
```nginx
location /static/ {
    alias /var/lib/docker/volumes/forge-cmms_staticfiles/_data/;
    expires 30d;
}

location / {
    proxy_pass http://forge-cmms-web-prod:8000;
}
```

**Ventajas:**
- Más eficiente
- Mejor rendimiento

**Desventajas:**
- Requiere montar volúmenes Docker en NPM
- Configuración más compleja

## Resumen

### ✅ En Desarrollo (`docker-compose.yml`)
- **Sí tiene Nginx**: Para simular producción localmente
- **Puertos**: 80, 443 expuestos
- **SSL**: Opcional, para testing

### ✅ En Producción (`docker-compose.prod.yml`)
- **NO tiene Nginx**: Usa NPM existente
- **Puertos**: Ninguno expuesto públicamente
- **SSL**: Manejado por NPM con Let's Encrypt

### 🔄 Interacción NPM ↔ Forge CMMS
- **Red compartida**: `core_shared-network`
- **Comunicación**: Por nombre de contenedor (`forge-cmms-web-prod`)
- **Protocolo interno**: HTTP (sin SSL)
- **Protocolo externo**: HTTPS (SSL agregado por NPM)

## Preguntas Frecuentes

### ¿Por qué no usar Nginx en producción también?

**Respuesta**: Ya tienes NPM corriendo que hace exactamente lo mismo. Agregar otro Nginx sería:
- Duplicación innecesaria
- Conflicto de puertos (ambos quieren 80/443)
- Más complejidad sin beneficio

### ¿Puedo usar el Nginx del docker-compose.yml en producción?

**Respuesta**: No es recomendable porque:
- NPM ya está configurado y funcionando
- NPM maneja SSL automáticamente con Let's Encrypt
- NPM tiene interfaz web para gestión fácil
- Evita conflictos y duplicación

### ¿Cómo sé qué usar en cada caso?

- **Desarrollo local**: Usa `docker-compose.yml` (con Nginx)
- **Producción VPS**: Usa `docker-compose.prod.yml` (sin Nginx, usa NPM)

### ¿Qué pasa si quiero probar SSL localmente?

Puedes usar el Nginx del `docker-compose.yml` con certificados self-signed o usar herramientas como `mkcert`.

## Comandos Útiles

### Desarrollo
```bash
# Iniciar con Nginx
docker-compose up -d

# Ver logs de Nginx
docker-compose logs nginx

# Ver logs de Django
docker-compose logs web
```

### Producción
```bash
# Iniciar sin Nginx (usa NPM)
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs web

# Verificar conectividad desde NPM
docker exec npm_core ping forge-cmms-web-prod
```
