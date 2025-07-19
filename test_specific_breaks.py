#!/usr/bin/env python3
"""Test specific breaks found in the REPL session."""

import os
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🔍 Testing Specific REPL Breaks")
print("=" * 50)

# The user's query that broke: "what's in the makefile and what are the core targets"
# The error: "Tool execution error: read_file() got an unexpected keyword argument 'path'"

print("\n1. Investigating the 'path' vs 'file_path' issue...")

try:
    from gemini_repl.tools.tool_decision import ToolDecision
    from gemini_repl.tools.codebase_tools import execute_tool
    
    # Test what happens when decision engine returns 'path' instead of 'file_path'
    print("\nScenario A: Decision engine returns 'path' (wrong param):")
    decision = ToolDecision(
        requires_tool_call=True,
        tool_name="read_file",
        reasoning="User wants to see Makefile",
        file_path="Makefile"  # We set file_path
    )
    
    # But what if the AI returns this JSON?
    ai_response_json = {
        "requires_tool_call": True,
        "tool_name": "read_file",
        "reasoning": "I'll read the Makefile",
        "path": "Makefile"  # AI uses 'path' instead of 'file_path'
    }
    
    print(f"  AI response: {ai_response_json}")
    
    # This would fail validation
    try:
        bad_decision = ToolDecision(**ai_response_json)
        print(f"  ❌ Should have failed - no file_path!")
    except Exception as e:
        print(f"  ✅ Correctly failed without file_path")
    
    print("\nScenario B: Tool args mismatch:")
    # Even if decision has file_path, what if it's converted wrong?
    args = decision.to_tool_args()
    print(f"  Decision args: {args}")
    
    # What if someone calls with wrong param?
    try:
        result = execute_tool("read_file", path="Makefile")  # Wrong!
        print(f"  ❌ Should have failed with 'path'")
    except Exception as e:
        print(f"  ✅ Correctly failed: {e}")
    
    # Correct call
    try:
        result = execute_tool("read_file", file_path="Makefile")
        print(f"  ✅ Correct call works: {result[:50]}...")
    except Exception as e:
        print(f"  ❌ Even correct call failed: {e}")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing how structured REPL handles tool calls...")

try:
    from gemini_repl.core.repl_structured import StructuredGeminiREPL
    
    # Let's trace the flow
    print("\nThe flow should be:")
    print("  1. User query → Decision Engine")
    print("  2. Decision Engine → ToolDecision (with file_path)")
    print("  3. ToolDecision.to_tool_args() → {file_path: ...}")
    print("  4. execute_tool(tool_name, **args)")
    
    # Check if there's a mismatch in the chain
    from gemini_repl.tools.codebase_tools import CODEBASE_TOOL_DECLARATIONS
    
    print("\nTool declarations expect:")
    for tool in CODEBASE_TOOL_DECLARATIONS:
        if tool["name"] == "read_file":
            print(f"  read_file parameters: {tool['parameters']['properties'].keys()}")
            
    # Check actual function signature
    from inspect import signature
    from gemini_repl.tools.codebase_tools import read_file
    sig = signature(read_file)
    print(f"  read_file function expects: {list(sig.parameters.keys())}")
    
except Exception as e:
    print(f"  Error: {e}")

print("\n3. Testing the actual error case...")

# The error suggests the structured REPL is passing 'path' instead of 'file_path'
# This could happen if:
# 1. The AI returns 'path' in its structured output
# 2. The ToolDecision doesn't validate/convert properly
# 3. The execute_tool is called with wrong params

try:
    # Simulate what the AI might return
    possible_ai_responses = [
        # Correct format
        {
            "requires_tool_call": True,
            "tool_name": "read_file",
            "file_path": "Makefile",
            "reasoning": "Reading Makefile"
        },
        # Wrong param name (common AI mistake)
        {
            "requires_tool_call": True,
            "tool_name": "read_file",
            "path": "Makefile",  # Wrong!
            "reasoning": "Reading Makefile"
        },
        # Both params (confusion)
        {
            "requires_tool_call": True,
            "tool_name": "read_file",
            "path": "Makefile",
            "file_path": "Makefile",
            "reasoning": "Reading Makefile"
        },
        # Missing params
        {
            "requires_tool_call": True,
            "tool_name": "read_file",
            "reasoning": "Reading Makefile"
        },
    ]
    
    for i, ai_response in enumerate(possible_ai_responses):
        print(f"\n  AI Response {i+1}: {ai_response}")
        try:
            decision = ToolDecision(**ai_response)
            args = decision.to_tool_args()
            print(f"    → Valid: {decision.is_valid()}")
            print(f"    → Args: {args}")
            
            if args and decision.tool_name:
                result = execute_tool(decision.tool_name, **args)
                print(f"    → Result: {str(result)[:30]}...")
        except Exception as e:
            print(f"    → Error: {type(e).__name__}: {str(e)[:50]}...")

except Exception as e:
    print(f"❌ Test failed: {e}")

print("\n4. The root cause...")
print("\nThe error 'read_file() got an unexpected keyword argument 'path'' means:")
print("1. The structured dispatch is somehow passing 'path' instead of 'file_path'")
print("2. This likely happens in the AI's response parsing")
print("3. The decision engine prompt might be causing the AI to use 'path'")

# Let's check the decision engine prompt
try:
    # Read the decision engine to see the prompt
    from gemini_repl.tools.decision_engine import ToolDecisionEngine
    
    # Can't instantiate without API key, but let's check the prompt format
    print("\nThe decision engine should instruct the AI to use:")
    print("- 'file_path' for read_file and write_file")
    print("- 'pattern' for list_files")
    print("- 'content' for write_file")
    
except ImportError:
    print("\nCan't import decision engine (missing dependencies)")

print("\n" + "=" * 50)
print("\n💡 Likely fixes needed:")
print("1. Update decision engine prompt to emphasize 'file_path' not 'path'")
print("2. Add validation in ToolDecision to handle common AI mistakes")
print("3. Add parameter mapping/correction before execute_tool")
print("4. Make structured REPL more robust to AI response variations")
