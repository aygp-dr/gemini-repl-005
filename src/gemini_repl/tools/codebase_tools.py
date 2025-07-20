"""Codebase tools for self-hosting capabilities with security sandboxing.

Security Model:
- Sandboxed to current working directory (pwd at startup)
- No access to parent directories (..)
- No absolute paths allowed
- No symlinks allowed
- Only read, write, and list operations
- Limited to modifying files within this repository only
"""

import os
import glob
import subprocess
from pathlib import Path

# Security: Sandbox to current working directory from startup
SANDBOX_DIR = Path.cwd().resolve()
print(f"🔒 Tool sandbox: {SANDBOX_DIR}")


class SecurityError(Exception):
    """Raised when a security violation is detected."""

    pass


def validate_path(file_path: str) -> Path:
    """Validate and sanitize file path for security.

    Args:
        file_path: Path to validate

    Returns:
        Resolved safe path

    Raises:
        SecurityError: If path would escape sandbox
    """
    # Reject absolute paths immediately
    if os.path.isabs(file_path):
        raise SecurityError(f"Absolute paths not allowed: {file_path}")

    # Reject parent directory references
    if ".." in file_path:
        raise SecurityError(f"Parent directory references not allowed: {file_path}")

    # Resolve the path relative to sandbox
    try:
        full_path = (SANDBOX_DIR / file_path).resolve()
    except Exception:
        raise SecurityError(f"Invalid path: {file_path}")

    # Ensure resolved path is within sandbox
    try:
        full_path.relative_to(SANDBOX_DIR)
    except ValueError:
        raise SecurityError(f"Path escapes sandbox: {file_path}")

    # Check for symlinks
    if full_path.is_symlink():
        raise SecurityError(f"Symlinks not allowed: {file_path}")

    return full_path


def read_file(file_path: str) -> str:
    """Read contents of a file (sandboxed)."""
    try:
        safe_path = validate_path(file_path)
        with open(safe_path, "r") as f:
            return f.read()
    except SecurityError as e:
        return f"Security error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file (sandboxed)."""
    try:
        safe_path = validate_path(file_path)
        # Ensure directory exists within sandbox
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        with open(safe_path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except SecurityError as e:
        return f"Security error: {e}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_files(pattern: str = "*") -> str:
    """List files matching a glob pattern (sandboxed)."""
    try:
        # Validate pattern doesn't escape
        if pattern.startswith("/"):
            raise SecurityError(f"Absolute paths not allowed: {pattern}")
        if ".." in pattern:
            raise SecurityError(f"Parent directory references not allowed: {pattern}")

        # Ensure glob is within sandbox
        safe_pattern = str(SANDBOX_DIR / pattern)
        files = glob.glob(safe_pattern, recursive=True)

        # Filter to only show relative paths within sandbox
        relative_files = []
        for f in files:
            file_path = Path(f)
            try:
                rel_path = file_path.relative_to(SANDBOX_DIR)
                relative_files.append(str(rel_path))
            except ValueError:
                # Skip files outside sandbox
                continue

        if not relative_files:
            return f"No files found matching pattern: {pattern}"
        return "\n".join(sorted(relative_files)[:50])  # Limit to 50 files
    except SecurityError as e:
        return f"Security error: {e}"
    except Exception as e:
        return f"Error listing files: {e}"


def search_code(pattern: str, file_pattern: str = "*.py") -> str:
    """Search for code patterns using ripgrep (sandboxed)."""
    try:
        # Validate file pattern
        if file_pattern.startswith("/"):
            raise SecurityError(f"Absolute paths not allowed: {file_pattern}")
        if ".." in file_pattern:
            raise SecurityError(f"Parent directory references not allowed: {file_pattern}")

        # Run ripgrep within sandbox directory
        cmd = ["rg", "--line-number", pattern]

        # Add file pattern if specified
        if file_pattern != "*.py":
            cmd.extend(["--glob", file_pattern])
        else:
            cmd.extend(["--type", "py"])

        # Run in sandbox directory
        result = subprocess.run(cmd, cwd=SANDBOX_DIR, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return "\n".join(lines[:20])  # Limit to 20 matches
        elif result.returncode == 1:
            return f"No matches found for pattern: {pattern}"
        else:
            return f"Search error: {result.stderr}"
    except SecurityError as e:
        return f"Security error: {e}"
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
