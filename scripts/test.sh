#!/usr/bin/env bash
set -euo pipefail

# Load common utilities
source "$(dirname "$0")/common.sh"

# Run test suite with coverage
#
# Usage: test.sh

print_status "info" "Running tests..."

# Ensure we're in project root
ensure_project_root

# Run tests with coverage using uv
print_status "info" "Running pytest with coverage..."
if uv run pytest tests/ -v --cov=src --cov-report=term-missing; then
    print_status "success" "All tests passed"
else
    print_status "error" "Some tests failed"
    exit 1
fi
