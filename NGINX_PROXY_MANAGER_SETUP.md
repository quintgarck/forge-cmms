# Configuración de Nginx Proxy Manager para Forge CMMS

Este documento explica cómo configurar Nginx Proxy Manager (NPM) para hacer proxy reverso a la aplicación Forge CMMS.

## Arquitectura

```
Internet → Nginx Proxy Manager (puerto 443) → Forge CMMS (puerto 8000)
```

## Pasos de Configuración

### 1. Acceder a Nginx Proxy Manager

1. Accede a la interfaz web de NPM (normalmente en `http://tu-vps-ip:81`)
2. Inicia sesión con tus credenciales

### 2. Crear Proxy Host

1. Ve a **Proxy Hosts** → **Add Proxy Host**

2. **Details Tab:**
   - **Domain Names**: `moviax.sagecores.com`
   - **Scheme**: `http`
   - **Forward Hostname/IP**: `forge-cmms-web-prod` (nombre del contenedor)
   - **Forward Port**: `8000`
   - ✅ **Block Common Exploits**
   - ✅ **Websockets Support** (si tu app usa WebSockets)
   
   **IMPORTANTE**: Usa el **nombre del contenedor** (`forge-cmms-web-prod`), NO `localhost` ni `127.0.0.1`. Esto funciona porque ambos contenedores están en la misma red Docker (`proxy_network`).

3. **SSL Tab:**
   - **SSL Certificate**: Selecciona "Request a new SSL Certificate"
   - ✅ **Force SSL**
   - ✅ **HTTP/2 Support**
   - ✅ **HSTS Enabled**
   - ✅ **HSTS Subdomains** (opcional)
   - Email: tu email para notificaciones de Let's Encrypt
   - ✅ **I Agree to the Let's Encrypt Terms of Service**

4. **Advanced Tab (Opcional):**
   Puedes agregar configuraciones personalizadas si es necesario:

   ```nginx
   # Timeouts para operaciones largas
   proxy_read_timeout 300s;
   proxy_connect_timeout 300s;
   proxy_send_timeout 300s;
   
   # Tamaño máximo de archivo
   client_max_body_size 20M;
   
   # Headers adicionales
   proxy_set_header X-Real-IP $remote_addr;
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   proxy_set_header X-Forwarded-Proto $scheme;
   proxy_set_header Host $host;
   ```

5. Haz clic en **Save**

### 3. Configurar Archivos Estáticos y Media

NPM puede servir archivos estáticos directamente, pero es más simple dejar que Django los sirva a través del proxy.

Si quieres optimizar el rendimiento, puedes configurar NPM para servir archivos estáticos directamente:

**En el Advanced Tab de NPM:**

```nginx
# Servir archivos estáticos directamente (opcional)
location /static/ {
    alias /var/lib/docker/volumes/forge-cmms_staticfiles/_data/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /var/lib/docker/volumes/forge-cmms_media/_data/;
    expires 7d;
    add_header Cache-Control "public";
}

# Proxy para el resto
location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}
```

**Nota**: Para esto necesitarías montar los volúmenes de Docker en el contenedor de NPM, lo cual puede ser complicado. Es más simple dejar que Django sirva todo.

### 4. Verificar Configuración

1. Espera unos minutos para que Let's Encrypt genere el certificado SSL
2. Verifica que el certificado está activo (debería aparecer un candado verde)
3. Accede a `https://moviax.sagecores.com` en tu navegador

### 5. Verificar que la Aplicación Responde

```bash
# Desde el VPS, verificar que el contenedor está corriendo
docker ps | grep forge-cmms

# Verificar que responde en el puerto 8000
curl http://localhost:8000/api/

# Verificar logs si hay problemas
docker logs forge-cmms-web-prod
```

## Troubleshooting

### Error: "502 Bad Gateway"

**Causa**: El contenedor de Forge CMMS no está corriendo, no responde en el puerto 8000, o NPM no puede alcanzarlo a través de la red Docker.

**Solución**:
```bash
# Verificar que el contenedor está corriendo
docker ps | grep forge-cmms-web-prod

# Verificar logs
docker logs forge-cmms-web-prod

# Verificar que ambos contenedores están en la misma red
docker network inspect proxy_network | grep -E "npm_core|forge-cmms"

# Verificar conectividad desde NPM al contenedor
docker exec npm_core ping -c 2 forge-cmms-web-prod

# Verificar que NPM puede acceder al puerto 8000
docker exec npm_core wget -O- http://forge-cmms-web-prod:8000/api/ 2>&1

# Si usas localhost en NPM, cambiar a nombre del contenedor
# En NPM: Forward Hostname/IP debe ser "forge-cmms-web-prod", NO "localhost"
```

### Error: "SSL Certificate Error"

**Causa**: El certificado SSL no se generó correctamente.

**Solución**:
1. Ve a NPM → SSL Certificates
2. Verifica que el certificado para `moviax.sagecores.com` existe y está activo
3. Si no existe, elimina el proxy host y créalo de nuevo
4. Asegúrate de que el dominio apunta correctamente al VPS

### Error: "Connection Refused"

**Causa**: El puerto 8000 no está accesible desde NPM.

**Solución**:
- Si usas `network_mode: host`, debería funcionar con `localhost:8000`
- Si usas una red Docker, asegúrate de que ambos contenedores están en la misma red
- Verifica el firewall: `sudo ufw status`

### Archivos Estáticos No Se Cargan

**Causa**: Los archivos estáticos no se recopilaron o no están accesibles.

**Solución**:
```bash
# Recopilar archivos estáticos
docker exec forge-cmms-web-prod python manage.py collectstatic --noinput

# Verificar que los archivos existen
docker exec forge-cmms-web-prod ls -la /app/staticfiles/
```

## Configuración Avanzada

### Redirección HTTP a HTTPS

NPM debería hacer esto automáticamente cuando configuras SSL con "Force SSL", pero puedes verificar en la configuración del Proxy Host.

### Rate Limiting

Puedes agregar rate limiting en el Advanced Tab:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://localhost:8000;
    # ... resto de configuración proxy
}
```

### Caching

Para mejorar el rendimiento, puedes agregar caching para archivos estáticos:

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
    proxy_pass http://localhost:8000;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## Verificación Final

Una vez configurado, deberías poder:

1. ✅ Acceder a `https://moviax.sagecores.com` sin errores SSL
2. ✅ Ver la aplicación funcionando correctamente
3. ✅ Los archivos estáticos se cargan (CSS, JS, imágenes)
4. ✅ La API responde en `https://moviax.sagecores.com/api/`
5. ✅ El admin de Django funciona en `https://moviax.sagecores.com/admin/`

## Notas Importantes

1. **Puerto 8000**: Asegúrate de que el puerto 8000 no esté bloqueado por el firewall
2. **ALLOWED_HOSTS**: En `.env.production`, asegúrate de incluir `moviax.sagecores.com`
3. **CORS**: Si tienes un frontend separado, configura CORS en Django settings para permitir el dominio
4. **Backups**: Configura backups regulares de la base de datos y volúmenes Docker
