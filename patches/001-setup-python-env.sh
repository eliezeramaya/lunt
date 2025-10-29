#!/bin/bash
# Remediación 001: Setup de Entorno Python
# Prioridad: CRÍTICA
# Tiempo estimado: 5 minutos

set -e

echo "=== REMEDIACIÓN 001: Setup de Entorno Python ==="
echo ""

echo "1. Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3.12-venv python3-pip

echo ""
echo "2. Creando entorno virtual..."
cd /home/eliezer/lunt
python3 -m venv venv

echo ""
echo "3. Activando entorno virtual..."
source venv/bin/activate

echo ""
echo "4. Actualizando pip..."
pip install --upgrade pip

echo ""
echo "5. Instalando dependencias del proyecto..."
pip install -r requirements.txt

echo ""
echo "6. Verificando instalación..."
echo "Ruff version: $(ruff --version)"
echo "Black version: $(black --version)"
echo "Pytest version: $(pytest --version)"

echo ""
echo "✅ Remediación completada exitosamente"
echo ""
echo "Para activar el entorno en futuras sesiones:"
echo "  source /home/eliezer/lunt/venv/bin/activate"
