# Resumen: Preparación para Despliegue en VPS

Este documento responde las preguntas frecuentes sobre el despliegue.

## 1. ¿Qué hacer con la carpeta `venv`?

### ❌ NO subir `venv/` a GitHub

**Razones:**
- Es específico del sistema operativo (Windows/Linux/Mac)
- Ocupa mucho espacio (cientos de MB)
- Se regenera fácilmente con `pip install -r requirements.txt`
- Cada desarrollador/servidor tiene su propio entorno

### ✅ Solución

1. **Ya está configurado**: El `.gitignore` en la raíz y en `forge_api/` ya incluye `venv/`
2. **Verificar antes de commit**:
   ```bash
   git status | grep venv
   # No debe mostrar nada
   ```
3. **Si ya está en Git** (por error):
   ```bash
   git rm -r --cached forge_api/venv/
   git commit -m "Remove venv from tracking"
   ```

### 📝 En el VPS

Cuando clones el repositorio en el VPS:
- **NO** necesitas crear `venv/` manualmente
- Docker construye la imagen con todas las dependencias
- Las dependencias se instalan en el contenedor, no en el host

## 2. ¿Cómo interactúan Nginx y Nginx Proxy Manager?

### 🔧 Desarrollo Local (`docker-compose.yml`)

**Tiene su propio Nginx** porque:
- Simula el entorno de producción
- Sirve archivos estáticos eficientemente
- Permite probar SSL localmente

```
Cliente → Nginx (puerto 80) → Django (puerto 8000)
```

### 🚀 Producción en VPS (`docker-compose.prod.yml`)

**NO tiene Nginx** porque:
- Ya tienes **Nginx Proxy Manager (NPM)** corriendo
- NPM hace el trabajo de proxy reverso y SSL
- Evita duplicación y conflictos de puertos

```
Internet → NPM (puerto 443) → Forge CMMS (puerto 8000 interno)
```

### 🔄 Interacción NPM ↔ Forge CMMS

1. **Ambos en la misma red**: `core_shared-network`
2. **Comunicación por nombre**: NPM usa `forge-cmms-web-prod:8000`
3. **Protocolo interno**: HTTP (sin SSL)
4. **Protocolo externo**: HTTPS (SSL agregado por NPM)

**Configuración en NPM:**
- Domain: `moviax.sagecores.com`
- Forward to: `forge-cmms-web-prod` (nombre del contenedor)
- Port: `8000`
- SSL: Let's Encrypt (manejado por NPM)

## Comparación Visual

| Aspecto | Desarrollo | Producción |
|---------|-----------|------------|
| **Nginx** | ✅ Contenedor propio | ❌ Usa NPM existente |
| **Puertos** | 80, 443 expuestos | Ninguno (solo interno) |
| **SSL** | Self-signed o local | Let's Encrypt via NPM |
| **Archivos estáticos** | Servidos por Nginx | Servidos por Django/NPM |
| **Red** | `forge-network` | `core_shared-network` |

## Checklist Antes de Subir a GitHub

- [ ] `.gitignore` existe en la raíz (✅ ya creado)
- [ ] `venv/` está en `.gitignore` (✅ ya configurado)
- [ ] `.env` está en `.gitignore` (✅ ya configurado)
- [ ] `.env.production` está en `.gitignore` (✅ ya configurado)
- [ ] Verificar que `venv/` no se subirá:
  ```bash
  git status | grep venv
  # No debe mostrar nada
  ```
- [ ] `.env.example` existe (sin valores reales) (✅ ya creado)

## Comandos para Subir a GitHub

```bash
# 1. Verificar qué se va a subir
git status

# 2. Verificar que venv NO está incluido
git status --ignored | grep venv
# Debe mostrar: forge_api/venv/

# 3. Agregar archivos (venv se ignorará automáticamente)
git add .

# 4. Verificar nuevamente
git status | grep venv
# No debe mostrar nada

# 5. Commit
git commit -m "Initial commit: Forge CMMS with Docker"

# 6. Agregar remote (después de crear repo en GitHub)
git remote add origin https://github.com/tu-usuario/forge-cmms.git

# 7. Push
git push -u origin main
```

## En el VPS: Clonar y Configurar

```bash
# 1. Clonar repositorio
cd /opt
git clone https://github.com/tu-usuario/forge-cmms.git
cd forge-cmms

# 2. Crear .env.production (NO está en Git)
cp .env.example .env.production
nano .env.production
# Configurar con valores reales del VPS

# 3. Verificar redes
chmod +x setup-networks.sh
./setup-networks.sh

# 4. Construir y ejecutar
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Configurar NPM (ver NGINX_PROXY_MANAGER_SETUP.md)
# - Domain: moviax.sagecores.com
# - Forward to: forge-cmms-web-prod
# - Port: 8000
```

## Resumen de Archivos

### ✅ SÍ subir a GitHub:
- Código fuente (`forge_api/`)
- Dockerfiles y docker-compose
- `requirements.txt`
- `.env.example` (sin valores reales)
- Scripts (`setup-networks.sh`, `docker-entrypoint.sh`)
- Documentación (`.md`)

### ❌ NO subir a GitHub:
- `venv/` o cualquier entorno virtual
- `.env` con valores reales
- `.env.production` con credenciales
- `staticfiles/`, `media/`, `logs/`
- `__pycache__/`

## Documentación Relacionada

- `GIT_SETUP.md` - Guía completa de configuración de Git
- `NGINX_EXPLANATION.md` - Explicación detallada de Nginx vs NPM
- `NGINX_PROXY_MANAGER_SETUP.md` - Cómo configurar NPM
- `DOCKER_NETWORKS.md` - Configuración de redes Docker

## Preguntas Frecuentes

### ¿Por qué no usar Nginx en producción también?

Ya tienes NPM corriendo que hace exactamente lo mismo. Agregar otro Nginx sería duplicación innecesaria y causaría conflictos de puertos.

### ¿Necesito crear venv en el VPS?

No. Docker construye la imagen con todas las dependencias instaladas. El contenedor tiene su propio entorno Python.

### ¿Cómo sé qué docker-compose usar?

- **Desarrollo local**: `docker-compose.yml` (con Nginx y BD propia)
- **Producción VPS**: `docker-compose.prod.yml` (sin Nginx, usa NPM y BD existente)

### ¿Qué pasa si subo venv por error?

1. Eliminar del tracking: `git rm -r --cached forge_api/venv/`
2. Commit: `git commit -m "Remove venv"`
3. Push: `git push`
