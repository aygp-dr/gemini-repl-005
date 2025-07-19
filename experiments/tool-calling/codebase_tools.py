#!/usr/bin/env python3
"""
Codebase tool calling experiment - essential tools for working with code
Based on successful simple_file_tools.py experiment
"""

import os
import sys
import glob
import subprocess
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
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_files(pattern: str = "*") -> str:
    """List files matching a glob pattern."""
    try:
        files = glob.glob(pattern, recursive=True)
        if not files:
            return f"No files found matching pattern: {pattern}"
        return "\n".join(sorted(files)[:50])  # Limit to 50 files
    except Exception as e:
        return f"Error listing files: {e}"


def search_code(pattern: str, file_pattern: str = "*.py") -> str:
    """Search for code patterns using ripgrep."""
    try:
        cmd = ["rg", "--type", "py", "--line-number", pattern]
        if file_pattern != "*.py":
            cmd.extend(["--glob", file_pattern])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return '\n'.join(lines[:20])  # Limit to 20 matches
        elif result.returncode == 1:
            return f"No matches found for pattern: {pattern}"
        else:
            return f"Search error: {result.stderr}"
    except Exception as e:
        return f"Error searching code: {e}"


# Function declarations for codebase operations
TOOL_DECLARATIONS = [
    {
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
    },
    {
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
    },
    {
        "name": "list_files",
        "description": "List files matching a glob pattern (supports ** for recursive).",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files (e.g., '*.py', 'src/**/*.py')",
                    "default": "*",
                },
            },
        },
    },
    {
        "name": "search_code",
        "description": "Search for patterns in code using ripgrep.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to search for",
                },
                "file_pattern": {
                    "type": "string", 
                    "description": "File pattern to search in (e.g., '*.py', '*.js')",
                    "default": "*.py",
                },
            },
            "required": ["pattern"],
        },
    },
]

# Function registry
FUNCTION_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "search_code": search_code,
}


def test_codebase_tools():
    """Test tool calling with codebase operations."""
    print("🧪 Testing Gemini Tool Calling with Codebase Tools")
    print("=" * 55)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        return False
    
    # Configure client and tools
    client = genai.Client()
    tools = types.Tool(function_declarations=TOOL_DECLARATIONS)
    config = types.GenerateContentConfig(tools=[tools])
    
    # Test queries for codebase work
    test_queries = [
        "List all Python files in the src directory",
        "Search for 'class.*REPL' in Python files",
        "Read the main REPL file src/gemini_repl/core/repl.py",
        "What's the structure of this codebase? Show me the main directories and files",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=query,
                config=config,
            )
            
            # Check for function call
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                print(f"🔧 Function: {function_call.name}")
                print(f"📋 Args: {dict(function_call.args)}")
                
                # Execute the function
                if function_call.name in FUNCTION_REGISTRY:
                    func = FUNCTION_REGISTRY[function_call.name]
                    result = func(**function_call.args)
                    print(f"✅ Result preview: {result[:200]}...")
                else:
                    print(f"❌ Unknown function: {function_call.name}")
            else:
                print("ℹ️  No function call")
                print(f"🤖 Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True


if __name__ == "__main__":
    # Change to project root for relative paths
    os.chdir(Path(__file__).parent.parent.parent)
    
    test_codebase_tools()
    
    print("\n📊 Codebase Tool Calling Experiment Complete")
    print("Next: Integrate into REPL for self-hosting")
