#!/bin/bash

set -euo pipefail

echo "Iniciando CI Local Profesional"
echo "================================="

# Configuración
PYTHON=python
COV_THRESHOLD=80

# 1. Ambiente limpio
echo "Limpiando ambiente..."
find . -type d -name "__pycache__" -exec rm -r {} + || true
find . -type d -name ".pytest_cache" -exec rm -r {} + || true
rm -f .coverage coverage.xml || true

# 2. Instalación
echo "Instalando dependencias..."
$PYTHON -m pip install --upgrade pip
pip install -r requirements.txt pytest-mock==3.14.0 > /dev/null

# 3. Linting
echo "Ejecutando linter..."
ruff check src/ tests/ --fix --quiet || true
if ! ruff check src/ tests/; then
    echo "Problemas de estilo encontrados"
    exit 1
fi
echo "Linter aprobado"

# 4. Type checking
echo "🔍 Verificación de tipos..."
if ! mypy src/; then
    echo "Problemas de tipado encontrados"
    exit 1
fi
echo "Tipado correcto"

# 5. Pruebas
echo "Ejecutando pruebas..."
pytest tests/ \
    --verbose \
    --cov=src \
    --cov-report=xml \
    --cov-report=term \
    --cov-branch \
    --junitxml=test-results.xml

# 6. Cobertura
echo "Analizando cobertura..."
coverage report --fail-under=$COV_THRESHOLD --skip-covered
coverage_percent=$(coverage report | tail -n 1 | awk '{print $NF}' | tr -d '%')

echo "================================="
if [ "$coverage_percent" -ge "$COV_THRESHOLD" ]; then
    echo "CI completado exitosamente! Cobertura: ${coverage_percent}%"
    exit 0
else
    echo "CI fallido. Cobertura insuficiente: ${coverage_percent}% (mínimo ${COV_THRESHOLD}%)"
    exit 1
fi