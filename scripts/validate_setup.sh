#!/bin/bash
# Comprehensive setup validation for gemini-repl-005
# Run this to ensure all requirements are met

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Status tracking
ISSUES=0

echo "🔍 Validating gemini-repl-005 Setup"
echo "==================================="
echo "Environment: $(uname -a)"
echo ""

# Function to check command exists
check_command() {
    local cmd=$1
    local required=$2
    local install_hint=$3
    
    if command -v "$cmd" &> /dev/null; then
        local version=$(eval "$cmd --version 2>&1 | head -n1" || echo "version unknown")
        echo -e "${GREEN}✓${NC} $cmd: $version"
    else
        echo -e "${RED}✗${NC} $cmd: NOT FOUND"
        if [ "$required" = "required" ]; then
            echo "  ${YELLOW}→ Install hint: $install_hint${NC}"
            ((ISSUES++))
        else
            echo "  ${YELLOW}→ Optional: $install_hint${NC}"
        fi
    fi
}

# Function to check Python package
check_python_package() {
    local package=$1
    local import_name=${2:-$package}
    
    if python -c "import $import_name" 2>/dev/null; then
        local version=$(python -c "import $import_name; print(getattr($import_name, '__version__', 'installed'))" 2>/dev/null || echo "installed")
        echo -e "${GREEN}✓${NC} Python package $package: $version"
    else
        echo -e "${RED}✗${NC} Python package $package: NOT INSTALLED"
        ((ISSUES++))
    fi
}

# Function to check file exists
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description: $file"
    else
        echo -e "${RED}✗${NC} $description: NOT FOUND at $file"
        ((ISSUES++))
    fi
}

# Function to check directory exists
check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description: $dir"
    else
        echo -e "${RED}✗${NC} $description: NOT FOUND at $dir"
        ((ISSUES++))
    fi
}

# Function to check environment variable
check_env() {
    local var=$1
    local description=$2
    
    if [ -n "${!var:-}" ]; then
        echo -e "${GREEN}✓${NC} $description: Set (${#!var} chars)"
    else
        echo -e "${YELLOW}⚠${NC} $description: NOT SET"
        echo "  ${YELLOW}→ Add to .env or export $var=...${NC}"
    fi
}

echo "1. System Requirements"
echo "----------------------"
check_command "python3" "required" "apt-get install python3"
check_command "python" "required" "apt-get install python3"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if (( $(echo "$PYTHON_VERSION >= 3.11" | bc -l) )); then
        echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION (>= 3.11)"
    else
        echo -e "${RED}✗${NC} Python version: $PYTHON_VERSION (requires >= 3.11)"
        ((ISSUES++))
    fi
fi

echo ""
echo "2. Development Tools"
echo "--------------------"
check_command "uv" "required" "curl -LsSf https://astral.sh/uv/install.sh | sh"
check_command "git" "required" "apt-get install git"
check_command "make" "required" "apt-get install make"
check_command "emacs" "optional" "apt-get install emacs"
check_command "expect" "optional" "apt-get install expect"
check_command "tmux" "optional" "apt-get install tmux"
check_command "rg" "optional" "apt-get install ripgrep"

echo ""
echo "3. Project Structure"
echo "--------------------"
check_file "Makefile" "Makefile"
check_file "pyproject.toml" "Project config"
check_file "PYTHON-GEMINI-REPL.org" "Main source"
check_file ".env.example" "Env template"
check_dir "src/gemini_repl" "Source directory"
check_dir "tests" "Test directory"
check_dir "experiments" "Experiments"

echo ""
echo "4. Python Environment"
echo "---------------------"
# Check if we're in a virtual environment
if [ -n "${VIRTUAL_ENV:-}" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment: Active"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment: Not active"
    echo "  ${YELLOW}→ Run: uv venv && source .venv/bin/activate${NC}"
fi

# Check for .venv directory
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment directory: .venv"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment directory: Not found"
    echo "  ${YELLOW}→ Run: make setup${NC}"
fi

echo ""
echo "5. Dependencies"
echo "---------------"
# Check if uv.lock exists
if [ -f "uv.lock" ]; then
    echo -e "${GREEN}✓${NC} Dependencies lock file: uv.lock"
    
    # Check key packages if in venv
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        check_python_package "google-genai" "google.genai"
        check_python_package "tiktoken"
        check_python_package "pytest"
        check_python_package "ruff"
        check_python_package "mypy"
    else
        echo -e "${YELLOW}⚠${NC} Activate venv to check Python packages"
    fi
else
    echo -e "${RED}✗${NC} Dependencies not installed"
    echo "  ${YELLOW}→ Run: make setup${NC}"
    ((ISSUES++))
fi

echo ""
echo "6. Environment Variables"
echo "------------------------"
check_env "GEMINI_API_KEY" "Gemini API Key"
check_env "LOG_LEVEL" "Log Level (optional)"
check_env "LOG_FILE" "Log File (optional)"

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} Environment file: .env exists"
else
    echo -e "${YELLOW}⚠${NC} Environment file: .env not found"
    echo "  ${YELLOW}→ Run: cp .env.example .env && edit .env${NC}"
fi

echo ""
echo "7. Build Artifacts"
echo "------------------"
# Check if tangled files exist
if [ -f "src/gemini_repl/core/repl.py" ]; then
    echo -e "${GREEN}✓${NC} Tangled source files: Present"
else
    echo -e "${YELLOW}⚠${NC} Tangled source files: Not found"
    echo "  ${YELLOW}→ Run: make tangle${NC}"
fi

# Check logs directory
if [ -d "logs" ]; then
    echo -e "${GREEN}✓${NC} Logs directory: logs/"
else
    echo -e "${YELLOW}⚠${NC} Logs directory: Not found"
    echo "  ${YELLOW}→ Will be created on first run${NC}"
fi

echo ""
echo "8. Quick Tests"
echo "--------------"
# Test imports if in venv
if [ -n "${VIRTUAL_ENV:-}" ]; then
    if python -c "from src.gemini_repl.core import api_client" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Can import core modules"
    else
        echo -e "${RED}✗${NC} Cannot import core modules"
        echo "  ${YELLOW}→ Run: make tangle${NC}"
        ((ISSUES++))
    fi
fi

# Check if we can run make commands
if command -v make &> /dev/null && [ -f "Makefile" ]; then
    if make help &> /dev/null; then
        echo -e "${GREEN}✓${NC} Makefile is valid"
    else
        echo -e "${RED}✗${NC} Makefile has errors"
        ((ISSUES++))
    fi
fi

echo ""
echo "================================"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set up environment: cp .env.example .env && edit .env"
    echo "2. Install dependencies: make setup"
    echo "3. Run the REPL: make run"
else
    echo -e "${RED}❌ Found $ISSUES issues${NC}"
    echo ""
    echo "Fix the issues above, then run this script again."
fi

echo ""
echo "Quick setup commands:"
echo "---------------------"
echo "# Full setup from scratch"
echo "make clean && make setup && source .venv/bin/activate"
echo ""
echo "# Run tests"
echo "make test"
echo ""
echo "# Start REPL"
echo "make run"

exit $ISSUES
