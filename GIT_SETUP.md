# Configuración de Git para Forge CMMS

Este documento explica cómo configurar Git correctamente antes de subir el proyecto a GitHub.

## Archivos que NO deben subirse a Git

### 1. Entornos Virtuales (venv/)

**¿Por qué?**
- Son específicos del sistema operativo
- Ocupan mucho espacio (cientos de MB)
- Se regeneran fácilmente con `pip install -r requirements.txt`
- Cada desarrollador tiene su propio entorno

**Ubicación**: `forge_api/venv/` o cualquier carpeta `venv/`

**Solución**: Ya está en `.gitignore`, pero verifica:

```bash
# Verificar que venv está ignorado
git check-ignore forge_api/venv/
# Debe mostrar: forge_api/venv/
```

### 2. Variables de Entorno (.env)

**¿Por qué?**
- Contienen credenciales sensibles
- Son específicas de cada entorno (desarrollo/producción)
- No deben estar en el repositorio por seguridad

**Archivos a ignorar**:
- `.env`
- `.env.local`
- `.env.production`
- `.env.*.local`

**Archivo de ejemplo**: `.env.example` (SÍ debe subirse, sin valores reales)

### 3. Archivos Generados

- `staticfiles/` - Archivos estáticos recopilados
- `media/` - Archivos subidos por usuarios
- `logs/` - Archivos de log
- `__pycache__/` - Caché de Python
- `*.pyc` - Bytecode compilado

### 4. Archivos de IDE

- `.vscode/`
- `.idea/`
- `*.swp`, `*.swo`

## Verificar .gitignore

### 1. Verificar que existe .gitignore en la raíz

```bash
# En la raíz del proyecto
ls -la .gitignore
```

Si no existe, ya lo creamos. Si existe, verifica que incluye:

```
venv/
.env
.env.production
staticfiles/
media/
logs/
__pycache__/
```

### 2. Verificar que venv está ignorado

```bash
# Verificar que Git ignora venv
git status --ignored | grep venv

# O específicamente
git check-ignore -v forge_api/venv/
```

### 3. Ver archivos que serán ignorados

```bash
# Ver todos los archivos ignorados
git status --ignored

# Ver solo archivos que SÍ se subirán
git status
```

## Configuración Inicial de Git

### 1. Inicializar repositorio (si no está inicializado)

```bash
cd /ruta/a/forge-cmms
git init
```

### 2. Agregar archivos al staging

```bash
# Ver qué se va a agregar
git status

# Agregar todos los archivos (excepto los ignorados)
git add .

# Verificar que venv NO está incluido
git status | grep venv
# No debe mostrar nada
```

### 3. Commit inicial

```bash
git commit -m "Initial commit: Forge CMMS with Docker configuration"
```

### 4. Configurar repositorio remoto

```bash
# Crear repositorio en GitHub primero, luego:
git remote add origin https://github.com/tu-usuario/forge-cmms.git

# O con SSH
git remote add origin git@github.com:tu-usuario/forge-cmms.git
```

### 5. Push inicial

```bash
git branch -M main
git push -u origin main
```

## Estructura Recomendada para Git

```
forge-cmms/
├── .gitignore                 ✅ SÍ subir
├── .env.example              ✅ SÍ subir (sin valores reales)
├── Dockerfile                ✅ SÍ subir
├── docker-compose.yml        ✅ SÍ subir
├── docker-compose.prod.yml   ✅ SÍ subir
├── docker-entrypoint.sh      ✅ SÍ subir
├── setup-networks.sh         ✅ SÍ subir
├── README.md                 ✅ SÍ subir
├── docs/                     ✅ SÍ subir
├── nginx/                    ✅ SÍ subir (para desarrollo)
├── forge_api/
│   ├── .gitignore           ✅ SÍ subir
│   ├── requirements.txt    ✅ SÍ subir
│   ├── manage.py           ✅ SÍ subir
│   ├── venv/               ❌ NO subir (ignorado)
│   ├── .env                ❌ NO subir (ignorado)
│   ├── staticfiles/        ❌ NO subir (ignorado)
│   ├── media/              ❌ NO subir (ignorado)
│   └── logs/               ❌ NO subir (ignorado)
└── ...
```

## Comandos Útiles

### Verificar qué se ignorará

```bash
# Ver archivos ignorados
git status --ignored

# Verificar un archivo específico
git check-ignore -v forge_api/venv/

# Ver todos los archivos que Git rastrea
git ls-files
```

### Limpiar archivos ya rastreados (si se agregaron por error)

```bash
# Si venv fue agregado por error antes de .gitignore
git rm -r --cached forge_api/venv/
git commit -m "Remove venv from tracking"

# Si .env fue agregado por error
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### Ver tamaño del repositorio

```bash
# Ver tamaño de archivos rastreados
git count-objects -vH

# Ver archivos más grandes
git ls-files | xargs du -h | sort -rh | head -20
```

## Checklist Antes de Push

- [ ] `.gitignore` existe en la raíz y en `forge_api/`
- [ ] `venv/` está en `.gitignore`
- [ ] `.env` está en `.gitignore`
- [ ] `.env.production` está en `.gitignore`
- [ ] `staticfiles/`, `media/`, `logs/` están en `.gitignore`
- [ ] `__pycache__/` está en `.gitignore`
- [ ] `.env.example` existe (sin valores reales)
- [ ] `git status` no muestra archivos sensibles
- [ ] `git status --ignored` muestra venv como ignorado
- [ ] No hay credenciales hardcodeadas en el código

## Archivos Sensibles que NUNCA deben subirse

❌ **NUNCA subir**:
- `.env` con valores reales
- `.env.production` con credenciales
- `SECRET_KEY` real en código
- Passwords de base de datos
- API keys
- Certificados SSL privados
- Archivos de configuración con IPs/puertos específicos del servidor

✅ **SÍ subir**:
- `.env.example` (con placeholders)
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- Código fuente
- Documentación

## Si ya subiste archivos sensibles por error

### 1. Eliminar del historial (si es reciente)

```bash
# Eliminar archivo del tracking
git rm --cached .env

# Commit
git commit -m "Remove sensitive file"

# Force push (si ya hiciste push)
git push --force
```

### 2. Rotar credenciales

Si subiste credenciales reales:
1. **Cambia todas las contraseñas/keys inmediatamente**
2. Regenera `SECRET_KEY` de Django
3. Cambia passwords de base de datos
4. Regenera cualquier API key

### 3. Usar git-secrets (prevención futura)

```bash
# Instalar git-secrets
# En macOS: brew install git-secrets
# En Linux: seguir instrucciones de GitHub

# Configurar
git secrets --install
git secrets --register-aws  # Si usas AWS
git secrets --add 'password.*=.*'
git secrets --add 'SECRET_KEY.*=.*'
```

## Buenas Prácticas

1. **Siempre revisa antes de commit**:
   ```bash
   git status
   git diff
   ```

2. **Usa .env.example como plantilla**:
   - Mantén `.env.example` actualizado
   - Documenta qué variables se necesitan
   - No incluyas valores reales

3. **Revisa el tamaño del repo**:
   ```bash
   git count-objects -vH
   ```
   Si es muy grande (>100MB), probablemente hay archivos que no deberían estar.

4. **Usa Git LFS para archivos grandes** (si es necesario):
   ```bash
   git lfs install
   git lfs track "*.pdf"
   git lfs track "*.zip"
   ```

## Resumen

✅ **SÍ subir a Git**:
- Código fuente
- Dockerfiles y docker-compose
- Requirements.txt
- Documentación
- `.env.example` (sin valores reales)
- Scripts de configuración

❌ **NO subir a Git**:
- `venv/` o cualquier entorno virtual
- `.env` con valores reales
- Archivos generados (staticfiles, media, logs)
- Caché de Python (`__pycache__`)
- Credenciales y secrets
- Archivos de IDE

## Siguiente Paso

Una vez configurado Git correctamente:

1. Haz commit inicial
2. Crea repositorio en GitHub
3. Haz push
4. En el VPS, clona el repositorio
5. Crea `.env.production` localmente (no se subirá)
