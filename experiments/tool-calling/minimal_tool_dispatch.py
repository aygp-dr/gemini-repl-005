#!/usr/bin/env python3
"""
Minimal tool dispatch test bed with Pydantic schemas.
Tests edge cases for tool calling vs direct responses.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types


# Pydantic models for the three core functions
class ListFilesParams(BaseModel):
    """Parameters for listing files."""
    pattern: str = Field(
        default="*",
        description="Glob pattern to match files (e.g., '*.py', 'src/**/*.md')"
    )


class ReadFileParams(BaseModel):
    """Parameters for reading a file."""
    file_path: str = Field(
        description="Path to the file to read (relative or absolute)"
    )


class WriteFileParams(BaseModel):
    """Parameters for writing a file."""
    file_path: str = Field(
        description="Path to the file to write (relative or absolute)"
    )
    content: str = Field(
        description="Content to write to the file"
    )


# Function implementations
def list_files(pattern: str = "*") -> str:
    """List files matching a glob pattern."""
    try:
        import glob
        files = glob.glob(pattern, recursive=True)
        if not files:
            return f"No files found matching pattern: {pattern}"
        # Limit output for readability
        files = sorted(files)[:30]
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"


def read_file(file_path: str) -> str:
    """Read contents of a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Limit size for testing
            if len(content) > 1000:
                return content[:1000] + f"\n... (truncated, {len(content)} total chars)"
            return content
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        # For safety in testing, only write to experiments/temp/
        if not file_path.startswith("experiments/temp/"):
            return "Error: Test mode - can only write to experiments/temp/"
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} chars to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


# Generate tool declarations from Pydantic models
TOOL_DECLARATIONS = [
    {
        "name": "list_files",
        "description": "List files in the codebase matching a glob pattern.",
        "parameters": ListFilesParams.model_json_schema()
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file from the filesystem.",
        "parameters": ReadFileParams.model_json_schema()
    },
    {
        "name": "write_file",
        "description": "Write content to a file on the filesystem.",
        "parameters": WriteFileParams.model_json_schema()
    }
]

# Function registry
FUNCTION_REGISTRY = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}


def run_test_queries():
    """Run comprehensive test queries."""
    
    # Test categories with expected behavior
    test_cases = [
        # SHOULD trigger tool calls - explicit file operations
        ("🔧 EXPECT TOOL", [
            "List all Python files",
            "Show me what's in the src directory",
            "What files are in experiments/",
            "Read the contents of README.org",
            "Show me CLAUDE.md",
            "What's in the Makefile?",
            "Read src/gemini_repl/core/repl.py",
            "List all markdown files",
            "Show all test files",
            "What configuration files exist?",
            "Read pyproject.toml",
            "Show me the main entry point file",
            "List everything in the tools directory",
            "Read the changelog",
            "What's in experiments/tool-calling/",
        ]),
        
        # AMBIGUOUS - might or might not trigger tools
        ("❓ AMBIGUOUS", [
            "Explain the project structure",
            "What does this codebase do?",
            "Show me how the REPL works",
            "What are the main components?",
            "How is logging implemented?",
            "Describe the API client",
            "What tools are available?",
            "How do tests work?",
            "What's the architecture?",
            "Show me the error handling",
        ]),
        
        # SHOULD NOT trigger tools - pure generation/analysis
        ("❌ NO TOOLS", [
            "Write a Python function to calculate factorial",
            "Implement quicksort in Haskell",
            "Explain monads",
            "What's the time complexity of merge sort?",
            "Write a SQL query to find duplicate emails",
            "Create a React component for a button",
            "Explain the CAP theorem",
            "Write a bash script to monitor CPU usage",
            "Implement a linked list in C",
            "What's the difference between TCP and UDP?",
        ]),
        
        # EDGE CASES - testing boundaries
        ("🤔 EDGE CASES", [
            "Save this code to experiments/temp/test.py: print('hello')",
            "Create a new file called experiments/temp/config.json with {}",
            "Update README.md with installation instructions",
            "Add a comment to the main function",
            "Refactor the logger class",
            "Fix the bug in line 42",
            "Optimize the search algorithm",
            "Add type hints to all functions",
            "Generate documentation",
            "Create unit tests for the API client",
        ]),
    ]
    
    print("🧪 Minimal Tool Dispatch Test Bed")
    print("=" * 60)
    print(f"Testing {sum(len(cases) for _, cases in test_cases)} queries")
    print(f"Tools available: {', '.join(FUNCTION_REGISTRY.keys())}")
    print("\nPydantic Schemas:")
    for decl in TOOL_DECLARATIONS:
        print(f"  - {decl['name']}: {len(decl['parameters']['properties'])} params")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        return
    
    # Configure client
    client = genai.Client()
    tools = types.Tool(function_declarations=TOOL_DECLARATIONS)
    config = types.GenerateContentConfig(
        tools=[tools],
        temperature=0.1,  # Lower temperature for more consistent behavior
    )
    
    results = []
    
    import time
    request_count = 0
    
    for category, queries in test_cases:
        print(f"\n{category}")
        print("-" * 40)
        
        for query in queries:
            # Rate limiting - 10 requests per minute
            if request_count >= 10:
                print(f"\n⏳ Rate limit reached. Waiting 60s...")
                time.sleep(60)
                request_count = 0
            
            # Additional throttling between requests
            if request_count > 1:
                time.sleep(6)  # ~10 requests per minute
            
            try:
                request_count += 1
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=query,
                    config=config,
                )
                
                # Check if tool was called
                tool_called = False
                function_name = None
                
                if (response.candidates and 
                    response.candidates[0].content.parts and
                    response.candidates[0].content.parts[0].function_call):
                    
                    function_call = response.candidates[0].content.parts[0].function_call
                    tool_called = True
                    function_name = function_call.name
                    
                result = {
                    "query": query,
                    "category": category,
                    "tool_called": tool_called,
                    "function": function_name,
                }
                results.append(result)
                
                # Print result
                if tool_called:
                    print(f"  ✓ {query[:50]:<50} → {function_name}")
                else:
                    print(f"  · {query[:50]:<50} → (no tool)")
                    
            except Exception as e:
                print(f"  ✗ {query[:50]:<50} → Error: {e}")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("📊 Summary Statistics")
    print("=" * 60)
    
    for category, _ in test_cases:
        cat_results = [r for r in results if r["category"] == category]
        total = len(cat_results)
        with_tools = sum(1 for r in cat_results if r["tool_called"])
        
        if total > 0:
            percentage = (with_tools / total) * 100
            print(f"{category:<20} {with_tools:>3}/{total:<3} ({percentage:>5.1f}%) used tools")
    
    # Tool usage breakdown
    print("\n🔧 Tool Usage:")
    tool_counts = {}
    for r in results:
        if r["function"]:
            tool_counts[r["function"]] = tool_counts.get(r["function"], 0) + 1
    
    for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool:<15} {count:>3} calls")
    
    return results


if __name__ == "__main__":
    # Change to project root
    os.chdir(Path(__file__).parent.parent.parent)
    
    # Ensure temp directory exists
    Path("experiments/temp").mkdir(parents=True, exist_ok=True)
    
    # Run tests
    results = run_test_queries()
    
    print("\n✅ Test bed complete!")
    print(f"Total queries tested: {len(results)}")
    print(f"Tool calls triggered: {sum(1 for r in results if r['tool_called'])}")
