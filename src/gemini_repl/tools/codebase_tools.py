"""Codebase tools for self-hosting capabilities."""

import os
import glob
import subprocess
from pathlib import Path
from typing import Dict, Any, List


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


# Function registry for tool execution
CODEBASE_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "search_code": search_code,
}

# Tool declarations for Gemini API
CODEBASE_TOOL_DECLARATIONS = [
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


def execute_tool(function_name: str, **kwargs) -> str:
    """Execute a codebase tool function."""
    if function_name not in CODEBASE_FUNCTIONS:
        return f"Unknown function: {function_name}"
    
    try:
        func = CODEBASE_FUNCTIONS[function_name]
        result = func(**kwargs)
        return str(result)
    except Exception as e:
        return f"Error executing {function_name}: {e}"
