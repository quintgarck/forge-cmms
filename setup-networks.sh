#!/bin/bash
# Script para verificar la configuración de redes Docker
# La red core_shared-network ya existe y contiene NPM y PostgreSQL

set -e

echo "=== Verificando configuración de redes Docker para Forge CMMS ==="

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Verificar que la red core_shared-network existe
echo -e "${YELLOW}1. Verificando red core_shared-network...${NC}"
if docker network ls | grep -q "core_shared-network"; then
    echo -e "${GREEN}✓ Red core_shared-network existe${NC}"
else
    echo -e "${RED}✗ Red core_shared-network NO existe${NC}"
    echo "Esta red debería existir. Verifica tu configuración."
    exit 1
fi

# 2. Verificar que NPM está en la red
echo -e "${YELLOW}2. Verificando que NPM está en core_shared-network...${NC}"
if docker inspect npm_core 2>/dev/null | grep -q "core_shared-network"; then
    echo -e "${GREEN}✓ NPM (npm_core) está conectado a core_shared-network${NC}"
else
    echo -e "${RED}✗ NPM no está en core_shared-network${NC}"
    echo "Conectando npm_core a core_shared-network..."
    docker network connect core_shared-network npm_core 2>/dev/null || echo -e "${YELLOW}⚠ No se pudo conectar NPM${NC}"
fi

# 3. Verificar que PostgreSQL está en la red
echo -e "${YELLOW}3. Verificando que PostgreSQL está en core_shared-network...${NC}"
if docker inspect postgres_core 2>/dev/null | grep -q "core_shared-network"; then
    echo -e "${GREEN}✓ PostgreSQL (postgres_core) está conectado a core_shared-network${NC}"
else
    echo -e "${RED}✗ PostgreSQL no está en core_shared-network${NC}"
    echo "Conectando postgres_core a core_shared-network..."
    docker network connect core_shared-network postgres_core 2>/dev/null || echo -e "${YELLOW}⚠ No se pudo conectar PostgreSQL${NC}"
fi

# 4. Verificar conectividad entre servicios
echo -e "${YELLOW}4. Verificando conectividad...${NC}"

# Verificar PostgreSQL
if docker exec postgres_core pg_isready -U postgres >/dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL está accesible${NC}"
else
    echo -e "${RED}✗ No se pudo conectar a PostgreSQL${NC}"
    echo "Verifica que el contenedor postgres_core está corriendo"
fi

# 5. Mostrar información de la red
echo -e "${YELLOW}5. Información de la red core_shared-network:${NC}"
echo -e "${BLUE}Contenedores en la red:${NC}"
docker network inspect core_shared-network --format='{{range .Containers}}{{.Name}} ({{.IPv4Address}}){{"\n"}}{{end}}' 2>/dev/null || echo "No se pudo obtener información"

echo ""
echo -e "${GREEN}=== Verificación completada ===${NC}"
echo ""
echo "Configuración:"
echo "  - Red: core_shared-network"
echo "  - NPM: npm_core"
echo "  - PostgreSQL: postgres_core"
echo "  - Forge CMMS: Se conectará automáticamente al ejecutar docker-compose"
echo ""
echo "Ahora puedes ejecutar:"
echo "  docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "En Nginx Proxy Manager, configura:"
echo "  - Forward Hostname/IP: forge-cmms-web-prod"
echo "  - Forward Port: 8000"
