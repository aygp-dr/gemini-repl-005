#!/usr/bin/env bash
set -euo pipefail

# Load common utilities
source "$(dirname "$0")/common.sh"

# Build distribution packages
#
# Usage: build.sh

print_status "info" "Building Gemini REPL..."

# Ensure we're in project root and venv is active
ensure_project_root
activate_venv

# Clean previous builds
print_status "info" "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info

# Install build tools
ensure_package "build"

# Build the package
print_status "info" "Building package..."
if python -m build; then
    print_status "success" "Build complete. Check dist/ for packages."
else
    print_status "error" "Build failed"
    exit 1
fi