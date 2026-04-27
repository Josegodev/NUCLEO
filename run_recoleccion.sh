#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "[INFO] Activando entorno..."
source .venv/bin/activate

echo "[INFO] Ejecutando script..."
python runtime_lab/recoleccion/scripts/calcular_recoleccion.py

echo "[OK] Fin"
