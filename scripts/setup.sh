#!/usr/bin/env bash
set -euo pipefail

# Load common utilities
source "$(dirname "$0")/common.sh"

# Set up Gemini REPL development environment
#
# Usage: setup.sh

print_status "info" "Setting up Gemini REPL development environment..."

# Ensure we're in project root
ensure_project_root

# Check for uv
require_command "uv" "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

# Create virtual environment if it doesn't exist
if [ ! -d .venv ]; then
    print_status "info" "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
print_status "info" "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
print_status "info" "Installing dependencies..."
uv pip install -r requirements.txt

# Run tangled setup.sh if it exists and is different from this script
if [ -f setup.sh ] && [ -x setup.sh ] && [ "$(realpath setup.sh)" != "$(realpath "$0")" ]; then
    print_status "info" "Running tangled setup script..."
    ./setup.sh
fi

print_status "success" "Setup complete. Run 'source .venv/bin/activate' to activate the environment."
if [[ "$(uname)" == "FreeBSD" ]]; then
    print_status "info" "On FreeBSD, use 'gmake' instead of 'make' for all commands."
fi