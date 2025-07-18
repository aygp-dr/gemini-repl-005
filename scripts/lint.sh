#!/usr/bin/env bash
set -euo pipefail

# Load common utilities
source "$(dirname "$0")/common.sh"

# Run linters on the codebase
#
# Usage: lint.sh

print_status "info" "Running linters..."

# Ensure we're in project root and venv is active
ensure_project_root
activate_venv

# Install lint tools if not present
ensure_package "ruff"
ensure_package "mypy"

# Run ruff
print_status "info" "Running ruff check..."
ruff check src/ tests/ --fix

# Run ruff format (replaces black)
print_status "info" "Running ruff format..."
ruff format src/ tests/

# Run mypy
print_status "info" "Running mypy..."
mypy src/ --ignore-missing-imports || print_status "warning" "MyPy found some issues"

print_status "success" "Linting complete"