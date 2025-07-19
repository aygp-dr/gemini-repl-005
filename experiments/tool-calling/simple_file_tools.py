#!/usr/bin/env python3
"""
Simple tool calling experiment - file operations only
Based on: https://ai.google.dev/gemini-api/docs/function-calling?example=meeting
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types


def read_file(file_path: str) -> str:
    """Read contents of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


# Define function declarations for codebase work
read_file_function = {
    "name": "read_file",
    "description": "Read the contents of a file from the filesystem.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read (relative or absolute)",
            },
        },
        "required": ["file_path"],
    },
}

write_file_function = {
    "name": "write_file", 
    "description": "Write content to a file on the filesystem.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write (relative or absolute)",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "required": ["file_path", "content"],
    },
}

# Function registry for actual execution
FUNCTION_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
}


def test_tool_calling():
    """Test basic tool calling with file operations."""
    print("🧪 Testing Gemini Tool Calling with File Operations")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        return False
    
    # Configure client and tools
    client = genai.Client()
    tools = types.Tool(function_declarations=[read_file_function, write_file_function])
    config = types.GenerateContentConfig(tools=[tools])
    
    # Test 1: Write a magic file
    magic_value = f"MAGIC_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_queries = [
        f"Create a file called 'date.txt' with the content '{magic_value}'",
        "Read the contents of the file 'date.txt'",
        "What's in the date.txt file?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 30)
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=query,
                config=config,
            )
            
            # Check for function call
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                print(f"🔧 Function to call: {function_call.name}")
                print(f"📋 Arguments: {dict(function_call.args)}")
                
                # Execute the function
                if function_call.name in FUNCTION_REGISTRY:
                    func = FUNCTION_REGISTRY[function_call.name]
                    result = func(**function_call.args)
                    print(f"✅ Execution result: {result}")
                    
                    # Send result back to model for response
                    function_response = types.Part.from_function_response(
                        name=function_call.name,
                        response={"result": result}
                    )
                    
                    follow_up = client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=[
                            types.Content(parts=[types.Part.from_text(query)]),
                            response.candidates[0].content,
                            types.Content(parts=[function_response])
                        ],
                        config=config,
                    )
                    print(f"🤖 Model response: {follow_up.text}")
                else:
                    print(f"❌ Unknown function: {function_call.name}")
            else:
                print("ℹ️  No function call found")
                print(f"🤖 Direct response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True


def validate_magic_file():
    """Validate that the magic file was created correctly."""
    print("\n🔍 Validating Magic File")
    print("=" * 25)
    
    if Path("date.txt").exists():
        content = Path("date.txt").read_text()
        print(f"✅ File exists with content: {content}")
        if "MAGIC_TEST_" in content:
            print("✅ Magic value confirmed - tool calling works!")
            return True
        else:
            print("❌ Magic value not found")
            return False
    else:
        print("❌ File not created")
        return False


if __name__ == "__main__":
    success = test_tool_calling()
    if success:
        validate_magic_file()
    
    print("\n📊 Experiment Complete")
    print("Next: Expand to codebase tools (glob, grep, edit)")
