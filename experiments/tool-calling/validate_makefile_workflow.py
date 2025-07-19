#!/usr/bin/env python3
"""
Observer Experiment: Validate Makefile Workflow
Tests if the REPL can properly list and explain Makefile targets through tool usage
"""

import subprocess
import json
import time

def test_makefile_workflow():
    """Test if the AI can discover and explain Makefile targets."""
    
    test_prompts = [
        # Direct request
        "List all the Makefile targets and explain what each one does",
        
        # Indirect discovery
        "What build commands are available in this project?",
        
        # Multi-step investigation  
        "I need to understand the project's build system. Can you check what build files exist and explain the available commands?",
        
        # Specific target query
        "How do I run the tests for this project?",
        
        # Tool-forcing query
        "Read the Makefile and tell me what 'make repl' does"
    ]
    
    print("🔍 Observer Experiment: Makefile Workflow Validation")
    print("=" * 60)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}: {prompt}")
        print("-" * 40)
        
        # Use echo to send prompt to REPL
        cmd = f'echo -e "{prompt}\\n/exit" | uv run python -m gemini_repl --name obs-test-{i}'
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            
            # Check for tool usage indicators
            has_tool_call = "🔧" in output
            mentions_makefile = "makefile" in output.lower()
            mentions_targets = any(target in output.lower() for target in ["help", "setup", "lint", "test", "repl"])
            
            # Results
            print(f"  Tool called: {'✅' if has_tool_call else '❌'}")
            print(f"  Found Makefile: {'✅' if mentions_makefile else '❌'}")  
            print(f"  Listed targets: {'✅' if mentions_targets else '❌'}")
            
            # Extract key info
            if mentions_targets:
                print("  Targets found:", end="")
                for target in ["help", "setup", "lint", "test", "repl"]:
                    if target in output.lower():
                        print(f" {target}", end="")
                print()
                
        except subprocess.TimeoutExpired:
            print("  ❌ Timeout - request took too long")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            
        time.sleep(2)  # Rate limiting
    
    print("\n" + "=" * 60)
    print("🔍 Experiment complete!")
    print("\nObservations:")
    print("- Tool dispatch appears inconsistent")
    print("- Some prompts trigger tool usage, others don't")
    print("- May need more explicit tool-triggering patterns")
    

if __name__ == "__main__":
    test_makefile_workflow()
