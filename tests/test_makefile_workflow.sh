#!/bin/bash
# Test script for Makefile target listing workflow

echo "Testing Makefile target listing workflow..."
echo "=========================================="

# Test 1: Direct question about Makefile
echo -e "\n1. Testing: List Makefile targets"
echo -e "List all the Makefile targets and explain what each one does\n/exit" | \
    uv run python -m gemini_repl --name test-makefile-1 2>/dev/null | \
    grep -E "(help|setup|lint|test|repl|make)" && echo "✅ Test 1 passed" || echo "❌ Test 1 failed"

# Test 2: Indirect question requiring discovery
echo -e "\n2. Testing: Build commands discovery"
echo -e "What build commands are available in this project?\n/exit" | \
    uv run python -m gemini_repl --name test-makefile-2 2>/dev/null | \
    grep -E "(make|Makefile|build|lint|test)" && echo "✅ Test 2 passed" || echo "❌ Test 2 failed"

# Test 3: Multi-step workflow
echo -e "\n3. Testing: Multi-step investigation"
echo -e "I need to understand the project's build system. First check what files exist, then examine the build configuration.\n/exit" | \
    uv run python -m gemini_repl --name test-makefile-3 2>/dev/null | \
    grep -E "(Makefile|pyproject\.toml|setup)" && echo "✅ Test 3 passed" || echo "❌ Test 3 failed"

echo -e "\n✅ Workflow tests completed"
