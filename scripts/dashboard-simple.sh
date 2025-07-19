#!/bin/bash
# Simple dashboard launcher for environments without tmux
# Opens multiple terminal windows/tabs if possible

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Gemini REPL Dashboard Launcher (Simple Mode)"
echo "==========================================="
echo ""

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "Virtual environment found. Run this in each terminal:"
    echo "  source .venv/bin/activate"
    echo ""
fi

echo "Open 4 terminal windows/tabs and run these commands:"
echo ""
echo "Terminal 1 - Shell (General commands):"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  # General development commands"
echo ""
echo "Terminal 2 - Builder 1 (Feature implementation):"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  make run  # or your development commands"
echo ""
echo "Terminal 3 - Observer (Monitoring):"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  tail -f logs/gemini.log  # or make monitor"
echo ""
echo "Terminal 4 - Builder 2 (Testing):"
echo "  cd $PROJECT_DIR"
echo "  source .venv/bin/activate"
echo "  make test  # or pytest commands"
echo ""
echo "Quick reference:"
echo "  make help     - Show all available commands"
echo "  make run      - Start the REPL"
echo "  make test     - Run tests"
echo "  make lint     - Run linters"
echo "  make monitor  - Show log monitoring commands"
echo ""

# Try to detect terminal emulator and offer to open tabs
if command -v gnome-terminal &> /dev/null; then
    echo "Detected: gnome-terminal"
    echo -n "Open 4 tabs automatically? (y/n) "
    read -r response
    if [[ "$response" == "y" ]]; then
        gnome-terminal --tab --title="Shell" --working-directory="$PROJECT_DIR" \
                      --tab --title="Builder 1" --working-directory="$PROJECT_DIR" \
                      --tab --title="Observer" --working-directory="$PROJECT_DIR" \
                      --tab --title="Builder 2" --working-directory="$PROJECT_DIR"
    fi
elif command -v konsole &> /dev/null; then
    echo "Detected: konsole"
    echo -n "Open 4 tabs automatically? (y/n) "
    read -r response
    if [[ "$response" == "y" ]]; then
        konsole --new-tab --workdir "$PROJECT_DIR" \
                --new-tab --workdir "$PROJECT_DIR" \
                --new-tab --workdir "$PROJECT_DIR" \
                --new-tab --workdir "$PROJECT_DIR"
    fi
elif command -v xterm &> /dev/null; then
    echo "Detected: xterm"
    echo "Opening 4 xterm windows..."
    xterm -T "Shell" -e "cd $PROJECT_DIR && bash" &
    xterm -T "Builder 1" -e "cd $PROJECT_DIR && bash" &
    xterm -T "Observer" -e "cd $PROJECT_DIR && bash" &
    xterm -T "Builder 2" -e "cd $PROJECT_DIR && bash" &
else
    echo "No supported terminal emulator detected."
    echo "Please open 4 terminal windows manually."
fi
