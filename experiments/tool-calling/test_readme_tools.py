#!/usr/bin/env python3
"""Test the specific tools mentioned in README: list_files, read_file, write_file"""

import subprocess
import time
import json

def test_readme_tools():
    """Test the three tools mentioned in the README."""
    
    test_cases = [
        {
            "name": "List Files",
            "prompts": [
                "What files are in the src directory?",
                "List all files in src/",
                "Show me what's in the src folder",
                "Can you check what files exist in src?",
                "list_files src"  # Direct tool name
            ]
        },
        {
            "name": "Read File",
            "prompts": [
                "Read the Makefile",
                "What's in the Makefile?",
                "Show me the contents of Makefile",
                "Can you read Makefile for me?",
                "read_file Makefile"  # Direct tool name
            ]
        },
        {
            "name": "Write File",
            "prompts": [
                "Create a file called test.txt with 'Hello World'",
                "Write 'Hello World' to test.txt",
                "Can you create test.txt containing Hello World?",
                "Make a new file test.txt that says Hello World",
                "write_file test.txt with content Hello World"  # Direct tool name
            ]
        }
    ]
    
    print("🧪 Testing README Tool Dispatch Consistency")
    print("=" * 60)
    
    results = {}
    
    for test_group in test_cases:
        print(f"\n## {test_group['name']} Tool Tests")
        print("-" * 40)
        
        group_results = []
        
        for i, prompt in enumerate(test_group['prompts'], 1):
            print(f"\nPrompt {i}: \"{prompt}\"")
            
            # Run the REPL with the prompt
            cmd = f'echo -e "{prompt}\\n/exit" | uv run python -m gemini_repl --name tool-test-{test_group["name"]}-{i}'
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = result.stdout
                
                # Check for tool usage
                has_tool = "🔧" in output
                has_emoji = "📂" in output or "📄" in output or "✅" in output
                
                # Tool-specific checks
                success = False
                if test_group['name'] == "List Files":
                    success = "gemini_repl" in output or "directory" in output.lower()
                elif test_group['name'] == "Read File":
                    success = "help" in output or "setup" in output or "test" in output
                elif test_group['name'] == "Write File":
                    success = "success" in output.lower() or "created" in output.lower()
                
                status = "✅" if has_tool else "❌"
                print(f"  Tool called: {status}")
                print(f"  Task completed: {'✅' if success else '❌'}")
                
                group_results.append({
                    "prompt": prompt,
                    "tool_called": has_tool,
                    "success": success
                })
                
            except subprocess.TimeoutExpired:
                print("  ❌ Timeout")
                group_results.append({
                    "prompt": prompt,
                    "tool_called": False,
                    "success": False
                })
            except Exception as e:
                print(f"  ❌ Error: {e}")
                group_results.append({
                    "prompt": prompt,
                    "tool_called": False,
                    "success": False
                })
            
            time.sleep(2)  # Rate limiting
        
        # Summary for this tool
        tool_calls = sum(1 for r in group_results if r['tool_called'])
        successes = sum(1 for r in group_results if r['success'])
        
        print(f"\n{test_group['name']} Summary:")
        print(f"  Tool dispatch rate: {tool_calls}/{len(group_results)} ({tool_calls/len(group_results)*100:.0f}%)")
        print(f"  Success rate: {successes}/{len(group_results)} ({successes/len(group_results)*100:.0f}%)")
        
        results[test_group['name']] = {
            "dispatch_rate": tool_calls / len(group_results),
            "success_rate": successes / len(group_results)
        }
    
    print("\n" + "=" * 60)
    print("📊 Overall Results:")
    for tool, rates in results.items():
        print(f"\n{tool}:")
        print(f"  Dispatch: {rates['dispatch_rate']*100:.0f}%")
        print(f"  Success: {rates['success_rate']*100:.0f}%")
    
    print("\n💡 Recommendations:")
    print("1. Tool dispatch is inconsistent across different phrasings")
    print("2. Even explicit tool names don't guarantee dispatch")
    print("3. Need better prompt engineering or tool descriptions")
    print("4. Consider adding examples to tool definitions")

if __name__ == "__main__":
    test_readme_tools()
