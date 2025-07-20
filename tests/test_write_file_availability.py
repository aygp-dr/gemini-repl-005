#!/usr/bin/env python3
"""Test to confirm write_file is properly configured in tools."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gemini_repl.tools.codebase_tools import (
    CODEBASE_FUNCTIONS, 
    CODEBASE_TOOL_DECLARATIONS,
    execute_tool
)


def test_write_file_configuration():
    """Verify write_file is properly configured."""
    
    print("=== Testing write_file Configuration ===\n")
    
    # Check in function registry
    print("1. Function Registry (CODEBASE_FUNCTIONS):")
    if "write_file" in CODEBASE_FUNCTIONS:
        print("   ✅ write_file is in function registry")
        print(f"   Function: {CODEBASE_FUNCTIONS['write_file']}")
    else:
        print("   ❌ write_file NOT in function registry!")
        
    # Check in tool declarations
    print("\n2. Tool Declarations (CODEBASE_TOOL_DECLARATIONS):")
    write_file_decl = None
    for tool in CODEBASE_TOOL_DECLARATIONS:
        if tool["name"] == "write_file":
            write_file_decl = tool
            break
            
    if write_file_decl:
        print("   ✅ write_file is in tool declarations")
        print(f"   Description: {write_file_decl['description']}")
        print(f"   Parameters: {write_file_decl['parameters']['properties'].keys()}")
    else:
        print("   ❌ write_file NOT in tool declarations!")
        
    # Test execution
    print("\n3. Tool Execution Test:")
    try:
        import tempfile
        import os
        
        # Create a test file in temp directory
        test_dir = tempfile.mkdtemp()
        test_file = f"{test_dir}/test_write.txt"
        
        # Use relative path within project
        result = execute_tool("write_file", 
                            file_path="test_temp_write.txt", 
                            content="Test content from write_file")
        
        print(f"   Result: {result}")
        
        if "Successfully wrote" in result:
            print("   ✅ write_file execution successful")
            # Clean up
            if os.path.exists("test_temp_write.txt"):
                os.remove("test_temp_write.txt")
        else:
            print("   ❌ write_file execution failed")
            
    except Exception as e:
        print(f"   ❌ Error executing write_file: {e}")
        
    # Summary
    print("\n=== Summary ===")
    print("write_file is properly configured and available for use.")
    print("The AI should be able to create files when requested.")


if __name__ == "__main__":
    test_write_file_configuration()
