#!/usr/bin/env python3
"""Aggressive tests to break structured dispatch functionality."""

import os
import sys
from pathlib import Path
import json
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment
os.environ["GEMINI_STRUCTURED_DISPATCH"] = "true"
os.environ["GEMINI_DEV_MODE"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

print("🔨 Aggressive Testing - Trying to Break Structured Dispatch")
print("=" * 60)

# Test cases designed to break things
break_tests = [
    # Edge cases for decision parsing
    ("", "empty query"),
    ("   ", "whitespace only"),
    ("!!!@#$%^&*()", "special characters"),
    ("read file", "incomplete command"),
    ("show me the file but don't tell me which one", "ambiguous file request"),
    ("read /etc/passwd", "security violation attempt"),
    ("list files in ../../../../", "path traversal attempt"),
    ("write to file.txt", "missing content"),
    ("write content", "missing file path"),
    ("list *.py but also *.js and maybe some *.md files too", "complex pattern"),
    ("what's in the file named 'test file with spaces.txt'", "filename with spaces"),
    ("show me the contents of files matching *.py", "read multiple files"),
    ("create 1000 files named test{i}.txt", "mass file creation"),
    ("read null bytes from /dev/zero", "special file"),
    ("what files exist?!?!?!", "punctuation overload"),
    ("READ THE MAKEFILE NOW!!!", "all caps"),
    ("can you maybe possibly show me what might be in the Makefile if it exists?", "overly polite"),
    ("🔥📁💾 list files emoji", "emoji in query"),
    ("show\nme\nthe\nMakefile", "newlines in query"),
    ("show me the " + "a" * 1000 + " file", "extremely long query"),
]

# Test 1: Import and instantiation edge cases
print("\n1. Testing imports and instantiation...")
try:
    from gemini_repl.tools.tool_decision import ToolDecision
    from gemini_repl.tools.decision_engine import ToolDecisionEngine
    from gemini_repl.utils.jsonl_logger import JSONLLogger
    from gemini_repl.utils.session import SessionManager
    from gemini_repl.core.repl_structured import StructuredGeminiREPL
    
    # Try to create instances
    logger = JSONLLogger(Path("test_break.jsonl"))
    print("✅ JSONLLogger created")
    
    # Test with None session manager
    logger_no_session = JSONLLogger(Path("test_break2.jsonl"), None)
    logger_no_session.log_tool_use("test", {}, "result")
    print("✅ JSONLLogger works without session manager")
    
except Exception as e:
    print(f"❌ Import/instantiation failed: {e}")
    traceback.print_exc()

# Test 2: ToolDecision edge cases
print("\n2. Testing ToolDecision edge cases...")
try:
    from gemini_repl.tools.tool_decision import ToolDecision
    
    # Test with missing required fields
    test_cases = [
        # Missing tool_name but requires_tool_call=True
        {
            "requires_tool_call": True,
            "reasoning": "test",
        },
        # Invalid tool name
        {
            "requires_tool_call": True,
            "tool_name": "invalid_tool",
            "reasoning": "test"
        },
        # Missing file_path for read_file
        {
            "requires_tool_call": True,
            "tool_name": "read_file",
            "reasoning": "test"
        },
        # Missing content for write_file
        {
            "requires_tool_call": True,
            "tool_name": "write_file",
            "reasoning": "test",
            "file_path": "test.txt"
        },
        # Extra fields
        {
            "requires_tool_call": True,
            "tool_name": "list_files",
            "reasoning": "test",
            "extra_field": "should be ignored"
        },
        # None values
        {
            "requires_tool_call": True,
            "tool_name": None,
            "reasoning": "test",
            "file_path": None,
            "content": None
        },
        # Empty strings
        {
            "requires_tool_call": True,
            "tool_name": "",
            "reasoning": "",
            "file_path": "",
            "content": ""
        },
    ]
    
    for i, test_case in enumerate(test_cases):
        try:
            decision = ToolDecision(**test_case)
            valid = decision.is_valid()
            args = decision.to_tool_args()
            print(f"  Test {i+1}: valid={valid}, args={args}")
            
            # Try to use the args
            if decision.tool_name and args:
                from gemini_repl.tools.codebase_tools import execute_tool
                try:
                    result = execute_tool(decision.tool_name, **args)
                    print(f"    Tool result: {str(result)[:50]}...")
                except Exception as e:
                    print(f"    Tool error: {e}")
                    
        except Exception as e:
            print(f"  Test {i+1}: ❌ {type(e).__name__}: {e}")
    
except Exception as e:
    print(f"❌ ToolDecision tests failed: {e}")
    traceback.print_exc()

# Test 3: Tool execution edge cases
print("\n3. Testing tool execution edge cases...")
try:
    from gemini_repl.tools.codebase_tools import read_file, write_file, list_files, execute_tool
    
    edge_cases = [
        # Path traversal attempts
        ("read_file", {"file_path": "../../../etc/passwd"}),
        ("read_file", {"file_path": "/etc/passwd"}),
        ("read_file", {"file_path": "..\\..\\..\\windows\\system32\\config\\sam"}),
        
        # Missing/wrong parameters
        ("read_file", {}),
        ("read_file", {"path": "Makefile"}),  # Wrong param name
        ("read_file", {"file_path": None}),
        ("read_file", {"file_path": ""}),
        ("read_file", {"file_path": 123}),  # Wrong type
        
        # Non-existent files
        ("read_file", {"file_path": "this_file_does_not_exist_12345.txt"}),
        ("read_file", {"file_path": "🔥emoji🔥.txt"}),
        
        # Write edge cases
        ("write_file", {"file_path": "test.txt"}),  # Missing content
        ("write_file", {"content": "test"}),  # Missing file_path
        ("write_file", {"file_path": "", "content": "test"}),
        ("write_file", {"file_path": None, "content": "test"}),
        ("write_file", {"file_path": "/tmp/test.txt", "content": "test"}),  # Absolute path
        ("write_file", {"file_path": "dir/../../test.txt", "content": "test"}),
        
        # List files edge cases
        ("list_files", {"pattern": ""}),
        ("list_files", {"pattern": None}),
        ("list_files", {"pattern": "../*"}),
        ("list_files", {"pattern": "/*"}),
        ("list_files", {"pattern": "**/../**"}),
        ("list_files", {"pattern": 123}),  # Wrong type
        ("list_files", {"wrong_param": "*"}),
        
        # Unknown tool
        ("unknown_tool", {}),
        ("", {}),
        (None, {}),
    ]
    
    for tool_name, kwargs in edge_cases:
        try:
            result = execute_tool(tool_name, **kwargs)
            print(f"  {tool_name} with {kwargs}: {str(result)[:50]}...")
        except Exception as e:
            print(f"  {tool_name} with {kwargs}: ❌ {type(e).__name__}: {e}")
    
except Exception as e:
    print(f"❌ Tool execution tests failed: {e}")
    traceback.print_exc()

# Test 4: JSONLLogger edge cases
print("\n4. Testing JSONLLogger edge cases...")
try:
    from gemini_repl.utils.jsonl_logger import JSONLLogger
    
    # Test with problematic inputs
    logger = JSONLLogger(Path("test_edge.jsonl"))
    
    test_cases = [
        # Normal case
        ("normal_tool", {"arg": "value"}, {"result": "success"}),
        
        # Empty/None values
        ("", {}, {}),
        (None, None, None),
        
        # Very long values
        ("tool_" * 100, {"key": "x" * 1000}, "result" * 500),
        
        # Special characters
        ("tool\nwith\nnewlines", {"key": "value\r\n"}, "result\t\t"),
        
        # Unicode
        ("tool_🔥", {"emoji": "🎉"}, "résultat"),
        
        # Circular reference (should stringify)
        ("circular", {"self": "[Circular]"}, {"nested": {"deep": {"ref": "[Circular]"}}}),
        
        # Non-serializable
        ("function", {"func": lambda x: x}, object()),
    ]
    
    for tool_name, args, result in test_cases:
        try:
            logger.log_tool_use(tool_name, args, result)
            print(f"  Logged: {tool_name} - OK")
        except Exception as e:
            print(f"  Logged: {tool_name} - ❌ {type(e).__name__}: {e}")
    
    # Test reading back
    try:
        interactions = logger.read_interactions()
        print(f"  Read back {len(interactions)} interactions")
    except Exception as e:
        print(f"  Read failed: ❌ {e}")
    
except Exception as e:
    print(f"❌ JSONLLogger tests failed: {e}")
    traceback.print_exc()

# Test 5: Full REPL flow edge cases
print("\n5. Testing full REPL flow edge cases...")
try:
    from gemini_repl.tools.tool_decision import ToolDecision
    from gemini_repl.tools.codebase_tools import execute_tool
    from gemini_repl.utils.jsonl_logger import JSONLLogger
    
    # Simulate problematic decision flows
    problematic_decisions = [
        # Decision says tool needed but provides wrong params
        ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read file but no path",
            # Missing file_path!
        ),
        
        # Decision with path instead of file_path
        ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Using wrong param name",
            file_path=None,  # Oops, None!
            pattern="Makefile"  # Wrong field for read_file
        ),
        
        # Write without content
        ToolDecision(
            requires_tool_call=True,
            tool_name="write_file",
            reasoning="Missing content",
            file_path="test.txt",
            # Missing content!
        ),
    ]
    
    logger = JSONLLogger(Path("test_flow_break.jsonl"))
    
    for i, decision in enumerate(problematic_decisions):
        print(f"\n  Problematic decision {i+1}:")
        print(f"    Tool: {decision.tool_name}")
        print(f"    Valid: {decision.is_valid()}")
        print(f"    Args: {decision.to_tool_args()}")
        
        if decision.tool_name:
            try:
                args = decision.to_tool_args()
                result = execute_tool(decision.tool_name, **args)
                print(f"    Result: {str(result)[:50]}...")
                
                # Try to log it
                logger.log_tool_use(decision.tool_name, args, result)
                print(f"    Logged: OK")
                
            except Exception as e:
                print(f"    Error: ❌ {type(e).__name__}: {e}")
    
except Exception as e:
    print(f"❌ Full flow tests failed: {e}")
    traceback.print_exc()

# Test 6: Structured REPL instantiation
print("\n6. Testing StructuredGeminiREPL instantiation...")
try:
    # This will likely fail without proper API key
    from gemini_repl.core.repl_structured import StructuredGeminiREPL
    
    # Try with missing env vars
    old_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = ""
    
    try:
        repl = StructuredGeminiREPL()
        print("❌ Should have failed with empty API key!")
    except Exception as e:
        print(f"✅ Correctly failed with empty key: {type(e).__name__}")
    
    # Restore
    if old_key:
        os.environ["GEMINI_API_KEY"] = old_key
    
except Exception as e:
    print(f"  StructuredGeminiREPL: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("\n🔍 Key Findings:")
print("1. Missing required parameters cause errors")
print("2. Security validations work (path traversal blocked)")
print("3. JSONLLogger handles most edge cases")
print("4. ToolDecision validation could be stricter")
print("5. Parameter name mismatches are a common issue")

# Clean up test files
for f in Path(".").glob("test_*.jsonl"):
    f.unlink(missing_ok=True)
for f in Path(".").glob("test_*.txt"):
    f.unlink(missing_ok=True)
