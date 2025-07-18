#!/usr/bin/env bash
# Common utilities for all scripts

set -euo pipefail

# Find project root by looking for pyproject.toml
find_project_root() {
    local dir="${PWD}"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/pyproject.toml" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "Error: Could not find project root (no pyproject.toml found)" >&2
    return 1
}

# Ensure we're in project root
ensure_project_root() {
    local project_root
    project_root="$(find_project_root)" || exit 1
    cd "$project_root"
}

# Check and activate virtual environment
activate_venv() {
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        if [ -f .venv/bin/activate ]; then
            source .venv/bin/activate
        else
            echo "Error: Virtual environment not found. Run '${MAKE_CMD:-make} setup' first." >&2
            return 1
        fi
    fi
}

# Install package if not present
ensure_package() {
    local package="$1"
    local import_name="${2:-$package}"
    
    if ! python -c "import $import_name" 2>/dev/null; then
        echo "Installing $package..."
        uv pip install "$package"
    fi
}

# Load environment variables from .env
load_env() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
    fi
}

# Print colored output
print_status() {
    local status="$1"
    local message="$2"
    
    case "$status" in
        "info")
            echo -e "\033[34m→\033[0m $message"
            ;;
        "success")
            echo -e "\033[32m✓\033[0m $message"
            ;;
        "error")
            echo -e "\033[31m✗\033[0m $message" >&2
            ;;
        "warning")
            echo -e "\033[33m!\033[0m $message"
            ;;
    esac
}

# Check for required commands
require_command() {
    local cmd="$1"
    local install_msg="${2:-Please install $cmd}"
    
    if ! command -v "$cmd" &> /dev/null; then
        print_error "Error: $cmd not found. $install_msg"
        return 1
    fi
}

# Detect make command (gmake on FreeBSD, make elsewhere)
detect_make() {
    if command -v gmake &> /dev/null; then
        echo "gmake"
    else
        echo "make"
    fi
}

# Export common variables
export PROJECT_ROOT="$(find_project_root 2>/dev/null || echo "$PWD")"
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}"
export MAKE_CMD="$(detect_make)"