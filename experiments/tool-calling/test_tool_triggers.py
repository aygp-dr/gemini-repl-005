#!/usr/bin/env python3
"""
Experiment to understand what triggers tool calling vs text generation
"""

import subprocess
import time

test_prompts = [
    # Direct commands
    "List all Python files in the src directory",
    "Show me the Python files in src",
    "What Python files are in src?",
    
    # File reading
    "Read the Makefile",
    "Show me what's in the Makefile",
    "Can you check what build commands are in the Makefile?",
    
    # Indirect requests
    "I need to see the project structure",
    "Help me understand the codebase organization",
    "What's the structure of this project?",
    
    # Analysis requests
    "Analyze the build system",
    "What build tools does this project use?",
    "How is this project configured?",
]

def test_prompt(prompt):
    """Test a single prompt and capture response."""
    print(f"\n{'='*60}")
    print(f"PROMPT: {prompt}")
    print(f"{'='*60}")
    
    cmd = f'echo -e "{prompt}\\n/exit" | uv run python -m gemini_repl --name tool-test 2>&1'
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout
    
    # Check for tool usage indicators
    tool_used = "🔧 Executing tool:" in output
    result_shown = "✅ Tool result:" in output
    
    print(f"Tool Called: {'YES' if tool_used else 'NO'}")
    
    if tool_used:
        # Extract tool name
        for line in output.split('\n'):
            if "🔧 Executing tool:" in line:
                print(f"Tool: {line.strip()}")
            if "✅ Tool result:" in line:
                print(f"Result preview: {line.strip()[:100]}...")
    
    # Show AI response
    print("\nAI Response:")
    in_response = False
    for line in output.split('\n'):
        if "] > " in line and not line.strip().startswith("["):
            in_response = True
            continue
        if in_response and line.strip() and not line.startswith("[🟢"):
            print(f"  {line.strip()}")
            if len(line.strip()) > 100:
                break
    
    return tool_used

def main():
    print("🧪 Testing Tool Calling Triggers")
    print("================================\n")
    
    # Quick check that tools are available
    print("Checking REPL configuration...")
    check_cmd = 'echo -e "/help\\n/exit" | uv run python -m gemini_repl 2>&1 | grep -i tool'
    subprocess.run(check_cmd, shell=True)
    
    print("\nTesting various prompts...\n")
    
    tool_count = 0
    for prompt in test_prompts:
        if test_prompt(prompt):
            tool_count += 1
        time.sleep(1)  # Rate limiting
    
    print(f"\n\n📊 Summary: {tool_count}/{len(test_prompts)} prompts triggered tool calling")

if __name__ == "__main__":
    main()
