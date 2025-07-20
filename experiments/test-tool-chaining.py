#!/usr/bin/env python3
"""Test script to verify tool chaining works correctly."""

import subprocess
import time
import sys

def test_tool_chaining():
    """Test that 'summarize this codebase' executes multiple tools automatically."""
    print("Testing tool chaining with 'summarize this codebase'...")
    
    # Start the REPL
    proc = subprocess.Popen(
        [sys.executable, "-m", "gemini_repl"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    # Send the test query
    proc.stdin.write("summarize this codebase\n")
    proc.stdin.flush()
    
    # Give it time to process
    time.sleep(15)
    
    # Send exit command
    proc.stdin.write("/exit\n")
    proc.stdin.flush()
    
    # Get output
    stdout, stderr = proc.communicate(timeout=5)
    
    # Check for tool execution indicators
    tool_indicators = [
        "🔧 Using tool: list_files",
        "📂 Listing files...",
        "🔧 Executing tool: read_file",
        "✅ Tool result:"
    ]
    
    found_indicators = []
    for indicator in tool_indicators:
        if indicator in stdout:
            found_indicators.append(indicator)
            print(f"✅ Found: {indicator}")
        else:
            print(f"❌ Missing: {indicator}")
    
    # Check for the bad pattern (AI telling user what to do)
    bad_patterns = [
        "To gain a deeper understanding, you should now:",
        "I can help you read any of these files"
    ]
    
    found_bad = []
    for pattern in bad_patterns:
        if pattern in stdout:
            found_bad.append(pattern)
            print(f"❌ Found bad pattern: {pattern}")
    
    print("\n--- Full Output ---")
    print(stdout)
    
    if stderr:
        print("\n--- Errors ---")
        print(stderr)
    
    # Success criteria
    if len(found_indicators) >= 3 and not found_bad:
        print("\n✅ Tool chaining appears to be working!")
        return True
    else:
        print("\n❌ Tool chaining is not working properly")
        return False

if __name__ == "__main__":
    success = test_tool_chaining()
    sys.exit(0 if success else 1)
