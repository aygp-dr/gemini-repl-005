#!/usr/bin/env bash
set -euo pipefail

# Load common utilities
source "$(dirname "$0")/common.sh"

# Run the Gemini REPL
#
# Usage: run.sh [args...]

# Ensure we're in project root and venv is active
ensure_project_root
activate_venv

# Load environment variables
load_env

# Check for API key
if [ -z "${GEMINI_API_KEY:-}" ]; then
    print_status "error" "GEMINI_API_KEY not set. Please set it in .env or environment."
    exit 1
fi

# PYTHONPATH is already set by common.sh

# Run the REPL
print_status "info" "Starting Gemini REPL..."
exec python -m gemini_repl "$@"