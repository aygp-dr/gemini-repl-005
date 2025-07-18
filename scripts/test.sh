#!/usr/bin/env bash
set -euo pipefail

# Load common utilities
source "$(dirname "$0")/common.sh"

# Run test suite with coverage
#
# Usage: test.sh

print_status "info" "Running tests..."

# Ensure we're in project root and venv is active
ensure_project_root
activate_venv

# Install test dependencies
ensure_package "pytest"
ensure_package "pytest-cov" "pytest_cov"

# Run tests with coverage
print_status "info" "Running pytest with coverage..."
if python -m pytest tests/ -v --cov=src --cov-report=term-missing; then
    print_status "success" "All tests passed"
else
    print_status "error" "Some tests failed"
    exit 1
fi