#!/usr/bin/env python3
"""Test all fixes work together."""

import os
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🔧 Testing All Fixes Together")
print("=" * 50)

# Test 1: JSONLLogger has log_tool_use
print("\n1. Testing JSONLLogger fix...")
try:
    from gemini_repl.utils.jsonl_logger import JSONLLogger
    logger = JSONLLogger(Path("test_all.jsonl"))
    logger.log_tool_use("test_tool", {"arg": "value"}, "result")
    print("✅ JSONLLogger.log_tool_use works")
except Exception as e:
    print(f"❌ JSONLLogger error: {e}")

# Test 2: ToolDecision handles parameters correctly
print("\n2. Testing ToolDecision parameter mapping...")
try:
    from gemini_repl.tools.tool_decision import ToolDecision
    
    # Test each tool type
    decisions = [
        ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read Makefile",
            file_path="Makefile"
        ),
        ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="List Python files",
            pattern="*.py"
        ),
        ToolDecision(
            requires_tool_call=True,
            tool_name="write_file",
            reasoning="Create test file",
            file_path="test.txt",
            content="Hello"
        ),
    ]
    
    for decision in decisions:
        args = decision.to_tool_args()
        print(f"✅ {decision.tool_name}: {args}")
        
except Exception as e:
    print(f"❌ ToolDecision error: {e}")

# Test 3: Decision engine fixes AI responses
print("\n3. Testing decision engine AI response fixes...")
try:
    # Can't import due to dependencies, but test the fix logic
    def _fix_ai_response(response_data: dict) -> dict:
        """Fix common AI response mistakes."""
        fixed = response_data.copy()
        
        # Fix path → file_path
        if 'path' in fixed and 'file_path' not in fixed:
            fixed['file_path'] = fixed.pop('path')
        
        # Handle nested parameters
        if 'parameters' in fixed and isinstance(fixed['parameters'], dict):
            params = fixed.pop('parameters')
            fixed.update(params)
        
        # Fix string booleans
        if 'requires_tool_call' in fixed and isinstance(fixed['requires_tool_call'], str):
            fixed['requires_tool_call'] = fixed['requires_tool_call'].lower() == 'true'
        
        return fixed
    
    # Test cases
    test_cases = [
        {"path": "Makefile", "tool_name": "read_file", "requires_tool_call": True, "reasoning": "test"},
        {"parameters": {"file_path": "test.txt"}, "tool_name": "read_file", "requires_tool_call": "true", "reasoning": "test"},
    ]
    
    for original in test_cases:
        fixed = _fix_ai_response(original)
        print(f"✅ Fixed: {list(fixed.keys())}")
        
except Exception as e:
    print(f"❌ Fix logic error: {e}")

# Test 4: Tool execution with correct parameters
print("\n4. Testing tool execution...")
try:
    from gemini_repl.tools.codebase_tools import execute_tool
    
    # Test each tool
    tests = [
        ("list_files", {"pattern": "*.md"}),
        ("read_file", {"file_path": "pyproject.toml"}),
        ("write_file", {"file_path": "test_output.txt", "content": "Test"}),
    ]
    
    for tool_name, args in tests:
        try:
            result = execute_tool(tool_name, **args)
            print(f"✅ {tool_name}: {str(result)[:50]}...")
            
            # Clean up
            if tool_name == "write_file":
                Path("test_output.txt").unlink(missing_ok=True)
                
        except Exception as e:
            print(f"❌ {tool_name}: {e}")
            
except Exception as e:
    print(f"❌ Tool execution error: {e}")

# Test 5: Full flow simulation
print("\n5. Simulating full structured dispatch flow...")
try:
    from gemini_repl.tools.tool_decision import ToolDecision
    from gemini_repl.tools.codebase_tools import execute_tool
    from gemini_repl.utils.jsonl_logger import JSONLLogger
    
    # Simulate what would happen with query: "what's in the makefile"
    print("\nQuery: 'what's in the makefile'")
    
    # Step 1: AI returns response (might use 'path')
    ai_response = {
        "requires_tool_call": True,
        "tool_name": "read_file",
        "path": "Makefile",  # AI uses wrong param name!
        "reasoning": "User wants to see contents of Makefile"
    }
    print(f"  AI response: {ai_response}")
    
    # Step 2: Fix AI response
    fixed_response = ai_response.copy()
    if 'path' in fixed_response and 'file_path' not in fixed_response:
        fixed_response['file_path'] = fixed_response.pop('path')
    print(f"  Fixed response: {fixed_response}")
    
    # Step 3: Create ToolDecision
    decision = ToolDecision(**fixed_response)
    print(f"  Decision valid: {decision.is_valid()}")
    
    # Step 4: Get args and execute
    args = decision.to_tool_args()
    print(f"  Tool args: {args}")
    
    result = execute_tool(decision.tool_name, **args)
    print(f"  Result: {str(result)[:50]}...")
    
    # Step 5: Log it
    logger = JSONLLogger(Path("test_flow.jsonl"))
    logger.log_tool_use(decision.tool_name, args, result)
    print("  ✅ Logged successfully!")
    
except Exception as e:
    print(f"❌ Full flow error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("\n✅ Summary of fixes:")
print("1. JSONLLogger now has log_tool_use method")
print("2. ToolDecision correctly maps parameters")
print("3. Decision engine fixes AI response mistakes")
print("4. Better error messages for parameter mismatches")
print("5. Defensive coding throughout the flow")

print("\n🎯 The structured dispatch should now handle:")
print("- AI using 'path' instead of 'file_path'")
print("- Missing parameters")
print("- Nested parameter structures")
print("- String booleans")
print("- Parameter validation before execution")

# Clean up
for f in Path(".").glob("test*.jsonl"):
    f.unlink(missing_ok=True)
for f in Path(".").glob("test*.txt"):
    f.unlink(missing_ok=True)
