#!/bin/bash

# Script para simular GitHub Actions localmente
echo "Configurando entorno..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Ejecutando linter..."
ruff check src/ tests/

echo "Ejecutando pruebas..."
pytest tests/ --cov=src --cov-report=term-missing

echo "Verificando cobertura..."
coverage report --fail-under=80

echo "CI local completado!"