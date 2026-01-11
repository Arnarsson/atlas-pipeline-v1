#!/usr/bin/env bash
set -euo pipefail

# Simple helper to create a local virtualenv for backend tests without touching the system Python.
# Usage: ./scripts/setup_venv.sh [.venv]

VENV_DIR="${1:-.venv}"

python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements-simple.txt pytest

echo "Virtualenv ready at ${VENV_DIR}. Activate with: source ${VENV_DIR}/bin/activate"
