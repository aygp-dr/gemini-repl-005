#!/bin/bash
# Simple REPL test with timeout

echo "Testing Gemini REPL with timeout..."

# Create test input
cat > test_input.txt << EOF
/help
/stats
/exit
EOF

# Run with timeout and input
source .env && timeout 10s uv run python -m gemini_repl < test_input.txt > test_output.txt 2>&1

EXIT_CODE=$?

echo "Exit code: $EXIT_CODE"
echo "Output:"
echo "---"
cat test_output.txt
echo "---"

# Check for expected output
if grep -q "Available Commands" test_output.txt; then
    echo "✓ Help command worked"
else
    echo "✗ Help command failed"
fi

# Cleanup
rm -f test_input.txt test_output.txt

# Exit codes: 0=success, 124=timeout, other=error
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ REPL exited normally"
elif [ $EXIT_CODE -eq 124 ]; then
    echo "✗ REPL timed out (might be stuck waiting for input)"
else
    echo "✗ REPL exited with error: $EXIT_CODE"
fi
