#!/usr/bin/env python3
"""Test minimal REPL functionality."""

import sys
import os
import subprocess
import time

# Test the REPL can handle basic input and exit
def test_repl_basic():
    """Test REPL with '2 + 2' and '/exit'."""
    
    # Create test input
    test_input = "2 + 2\n/exit\n"
    
    # Run REPL with input
    env = os.environ.copy()
    env['CONTEXT_FILE'] = 'test_context.json'
    env['LOG_FILE'] = 'test_gemini.log'
    env['LOG_LEVEL'] = 'DEBUG'  # Enable debug logging
    
    print("Testing REPL with '2 + 2' and '/exit'...")
    
    try:
        # Start REPL process using uv run
        proc = subprocess.Popen(
            ['uv', 'run', 'python', '-m', 'gemini_repl'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send input and get output
        stdout, stderr = proc.communicate(input=test_input, timeout=10)
        
        print("STDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)
        
        # Check if process exited cleanly
        if proc.returncode == 0:
            print("\n✓ REPL exited cleanly")
        else:
            print(f"\n✗ REPL exited with code {proc.returncode}")
            return False
            
        # Check output contains expected elements
        if "2 + 2" in stdout:
            print("✓ REPL received input")
        else:
            print("✗ Input not echoed")
            
        if "4" in stdout or "equals 4" in stdout or "is 4" in stdout:
            print("✓ REPL computed correct answer")
        else:
            print("✗ Answer not found in output")
            
        if "Goodbye" in stdout:
            print("✓ REPL said goodbye on exit")
        else:
            print("✗ No goodbye message")
            
        # Check log file was created
        if os.path.exists('test_gemini.log'):
            print("✓ Log file created")
            with open('test_gemini.log', 'r') as f:
                log_content = f.read()
                if "2 + 2" in log_content:
                    print("✓ User input logged")
                else:
                    print("✗ User input not found in log")
                    print("Log content:", log_content[:200])
            # Don't remove yet for debugging
            # os.remove('test_gemini.log')
        else:
            print("✗ No log file created")
            
        # Clean up context file
        if os.path.exists('test_context.json'):
            os.remove('test_context.json')
            
        return True
        
    except subprocess.TimeoutExpired:
        print("\n✗ REPL timed out - may be hanging")
        proc.kill()
        return False
    except Exception as e:
        print(f"\n✗ Error running REPL: {e}")
        return False

if __name__ == "__main__":
    # Add src to path
    sys.path.insert(0, 'src')
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("ERROR: GEMINI_API_KEY not set")
        print("Run: source .env")
        sys.exit(1)
    
    # Run test
    success = test_repl_basic()
    sys.exit(0 if success else 1)
