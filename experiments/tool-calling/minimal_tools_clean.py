#!/usr/bin/env python3
"""
Clean minimal tools implementation using the new SDK pattern.
Shows the exact syntax for function declarations.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types


# Function implementations
def list_files(pattern: str = "*") -> str:
    """List files matching a glob pattern."""
    import glob
    files = glob.glob(pattern, recursive=True)
    return "\n".join(sorted(files)[:20]) if files else f"No files matching: {pattern}"


def read_file(file_path: str) -> str:
    """Read contents of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()[:1000]  # Limit for demo
    except Exception as e:
        return f"Error: {e}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {file_path}"
    except Exception as e:
        return f"Error: {e}"


# Define individual function declarations
list_files_function = types.FunctionDeclaration(
    name="list_files",
    description="List files in the codebase matching a glob pattern",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern (e.g., '*.py', 'src/**/*.md')",
                "default": "*"
            }
        }
    }
)

read_file_function = types.FunctionDeclaration(
    name="read_file",
    description="Read the contents of a file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["file_path"]
    }
)

write_file_function = types.FunctionDeclaration(
    name="write_file", 
    description="Write content to a file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["file_path", "content"]
    }
)

# Create tool with function declarations
tools = types.Tool(
    function_declarations=[
        list_files_function,
        read_file_function,
        write_file_function
    ]
)

# Function registry for execution
FUNCTION_REGISTRY = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}


def demo_minimal_tools():
    """Demo the minimal tool setup."""
    print("🛠️  Minimal Tools Demo")
    print("=" * 40)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Set GEMINI_API_KEY first")
        return
    
    # Initialize client
    client = genai.Client()
    
    # Configure with tools
    config = types.GenerateContentConfig(
        tools=[tools],
        temperature=0.1
    )
    
    # Test queries
    queries = [
        "List all Python files in src/",
        "Read the Makefile",
        "What's the project structure?",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=query,
                config=config
            )
            
            # Check for function call
            if (response.candidates and 
                response.candidates[0].content.parts and
                response.candidates[0].content.parts[0].function_call):
                
                fc = response.candidates[0].content.parts[0].function_call
                print(f"🔧 Called: {fc.name}({dict(fc.args)})")
                
                # Execute function
                if fc.name in FUNCTION_REGISTRY:
                    result = FUNCTION_REGISTRY[fc.name](**fc.args)
                    print(f"📄 Result: {result[:100]}...")
            else:
                print(f"💬 Response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent.parent)
    demo_minimal_tools()
