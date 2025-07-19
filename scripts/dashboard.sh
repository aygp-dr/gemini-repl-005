#!/bin/bash
# Launch tmux dashboard for Gemini REPL development
# Creates a session with 4 panes: shell, builder, observer, builder2

set -euo pipefail

# Session name
SESSION="gemini-repl"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is not installed."
    echo ""
    echo "You can either:"
    echo "1. Install tmux: apt-get install tmux (or brew install tmux on macOS)"
    echo "2. Use the simple dashboard: ./scripts/dashboard-simple.sh"
    echo ""
    # Try to run simple dashboard
    if [ -f "$PROJECT_DIR/scripts/dashboard-simple.sh" ]; then
        exec "$PROJECT_DIR/scripts/dashboard-simple.sh"
    fi
    exit 1
fi

# Check if session already exists
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists."
    echo -n "Attach to existing session? (y/n) "
    read -r response
    if [[ "$response" == "y" ]]; then
        tmux attach-session -t "$SESSION"
        exit 0
    else
        echo "Please kill the existing session first: tmux kill-session -t $SESSION"
        exit 1
    fi
fi

echo "Creating tmux dashboard session '$SESSION'..."

# Create new session with first window (shell)
tmux new-session -d -s "$SESSION" -n "dashboard" -c "$PROJECT_DIR"

# Split horizontally to create top and bottom rows
tmux split-window -v -p 50 -t "$SESSION:0"

# Split top row vertically (shell | builder)
tmux split-window -h -p 50 -t "$SESSION:0.0"

# Split bottom row vertically (observer | builder2)
tmux split-window -h -p 50 -t "$SESSION:0.2"

# Configure panes
# Pane 0 (top-left): Shell
tmux send-keys -t "$SESSION:0.0" "# Shell - General commands" C-m
tmux send-keys -t "$SESSION:0.0" "source .venv/bin/activate 2>/dev/null || echo 'Run: make setup'" C-m
tmux send-keys -t "$SESSION:0.0" "clear" C-m

# Pane 1 (top-right): Builder 1
tmux send-keys -t "$SESSION:0.1" "# Builder 1 - Feature implementation" C-m
tmux send-keys -t "$SESSION:0.1" "source .venv/bin/activate 2>/dev/null || true" C-m
tmux send-keys -t "$SESSION:0.1" "clear" C-m
tmux send-keys -t "$SESSION:0.1" "echo 'Ready for building. Use: make run'" C-m

# Pane 2 (bottom-left): Observer
tmux send-keys -t "$SESSION:0.2" "# Observer - Monitoring and logs" C-m
tmux send-keys -t "$SESSION:0.2" "source .venv/bin/activate 2>/dev/null || true" C-m
tmux send-keys -t "$SESSION:0.2" "clear" C-m
tmux send-keys -t "$SESSION:0.2" "echo 'Observer pane. Use: tail -f logs/gemini.log'" C-m

# Pane 3 (bottom-right): Builder 2
tmux send-keys -t "$SESSION:0.3" "# Builder 2 - Testing and debugging" C-m
tmux send-keys -t "$SESSION:0.3" "source .venv/bin/activate 2>/dev/null || true" C-m
tmux send-keys -t "$SESSION:0.3" "clear" C-m
tmux send-keys -t "$SESSION:0.3" "echo 'Ready for testing. Use: make test'" C-m

# Set pane titles (requires tmux 3.0+)
if tmux -V | grep -qE "3\.[0-9]|[4-9]\.[0-9]"; then
    tmux select-pane -t "$SESSION:0.0" -T "Shell"
    tmux select-pane -t "$SESSION:0.1" -T "Builder 1"
    tmux select-pane -t "$SESSION:0.2" -T "Observer"
    tmux select-pane -t "$SESSION:0.3" -T "Builder 2"
fi

# Select the shell pane by default
tmux select-pane -t "$SESSION:0.0"

# Add status bar customization
tmux set-option -t "$SESSION" status-style bg=blue,fg=white
tmux set-option -t "$SESSION" status-left "[#S] "
tmux set-option -t "$SESSION" status-right "#(cd #{pane_current_path}; git branch --show-current) | %H:%M "
tmux set-option -t "$SESSION" status-left-length 20
tmux set-option -t "$SESSION" status-right-length 60

# Enable mouse support
tmux set-option -t "$SESSION" mouse on

# Set pane borders
tmux set-option -t "$SESSION" pane-border-style fg=blue
tmux set-option -t "$SESSION" pane-active-border-style fg=brightblue

echo "✓ Dashboard created successfully!"
echo ""
echo "Layout:"
echo "┌─────────────┬─────────────┐"
echo "│   Shell     │  Builder 1  │"
echo "├─────────────┼─────────────┤"
echo "│  Observer   │  Builder 2  │"
echo "└─────────────┴─────────────┘"
echo ""

# Check if we should attach (default is detached mode)
if [[ "${1:-}" == "--attach" ]]; then
    echo "Attaching to session..."
    tmux attach-session -t "$SESSION"
else
    echo "Session created in detached mode."
    echo "To attach: tmux attach -t $SESSION"
    echo "To list panes: tmux list-panes -t $SESSION"
    echo "To kill session: tmux kill-session -t $SESSION"
fi
