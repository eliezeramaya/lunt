#!/bin/bash
# Remediación 002: Instalación de Docker
# Prioridad: CRÍTICA
# Tiempo estimado: 10-15 minutos

set -e

echo "=== REMEDIACIÓN 002: Instalación de Docker ==="
echo ""
echo "NOTA: Este script instala Docker Engine en WSL Ubuntu."
echo "Alternativa recomendada: Docker Desktop for Windows con integración WSL2"
echo ""
read -p "¿Continuar con instalación de Docker Engine? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Instalación cancelada."
    echo ""
    echo "Para instalar Docker Desktop:"
    echo "1. Descarga desde https://www.docker.com/products/docker-desktop"
    echo "2. Instala en Windows"
    echo "3. Habilita integración WSL2 en Settings > Resources > WSL Integration"
    exit 0
fi

echo ""
echo "1. Actualizando repositorios..."
sudo apt update

echo ""
echo "2. Instalando dependencias..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

echo ""
echo "3. Agregando clave GPG de Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo ""
echo "4. Agregando repositorio de Docker..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo ""
echo "5. Instalando Docker..."
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo ""
echo "6. Agregando usuario al grupo docker..."
sudo usermod -aG docker $USER

echo ""
echo "7. Verificando instalación..."
docker --version
docker compose version

echo ""
echo "✅ Docker instalado exitosamente"
echo ""
echo "IMPORTANTE: Debes cerrar y reabrir la terminal (o ejecutar 'newgrp docker')"
echo "para que los cambios de grupo surtan efecto."
echo ""
echo "Para verificar: docker run hello-world"
