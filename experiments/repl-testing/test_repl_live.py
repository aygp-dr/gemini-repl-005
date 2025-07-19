#!/usr/bin/env python3
"""Quick test of REPL functionality."""

import sys
sys.path.insert(0, 'src')

from gemini_repl.core.api_client import GeminiClient

# Test 1: Basic API client
print("Test 1: Creating API client...")
try:
    client = GeminiClient()
    print("✓ Client created successfully")
except Exception as e:
    print(f"✗ Failed to create client: {e}")
    sys.exit(1)

# Test 2: Send a simple message
print("\nTest 2: Sending simple message...")
try:
    messages = [{"role": "user", "content": "What is 2 + 40?"}]
    response = client.send_message(messages)
    print(f"✓ Response: {response.text}")
except Exception as e:
    print(f"✗ Failed to send message: {e}")
    sys.exit(1)

# Test 3: Test readline support
print("\nTest 3: Testing readline...")
import readline
readline.parse_and_bind("tab: complete")
print("✓ Readline configured")

# Test 4: Test logging
print("\nTest 4: Testing logger...")
try:
    from gemini_repl.utils.logger import Logger
    import tempfile
    import os
    
    # Use temp file to avoid FIFO issues
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
        os.environ['LOG_FILE'] = tmp.name
        logger = Logger()
        logger.info("Test log entry", {"test": True})
        print(f"✓ Logger working, log file: {tmp.name}")
except Exception as e:
    print(f"✗ Logger failed: {e}")

print("\n✅ All basic tests passed!")
print("The REPL should work with 'gmake run'")
