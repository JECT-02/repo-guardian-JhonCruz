#!/bin/bash

# Script para simular GitHub Actions localmente
# Ubicación: repo-guardian-JhonCruz/run-ci-local.sh

echo "Instalando dependencias..."
pip install -r requirements.txt
pip install pytest pytest-cov ruff

echo "Ejecutando linter (Ruff)..."
ruff check src/ tests/

echo "Ejecutando pruebas..."
pytest tests/ --verbose --cov=src --cov-report=term-missing

echo "Verificando cobertura..."
coverage report --fail-under=80

echo "CI local completado!"