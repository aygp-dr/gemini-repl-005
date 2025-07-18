# Tool Base and Registry


# [[file:../../../PYTHON-GEMINI-REPL.org::*Tool Base and Registry][Tool Base and Registry:1]]
"""Tool system for file operations and self-modification."""

import os
from pathlib import Path
from typing import Dict, Any, List
import google.generativeai as genai


class ToolSystem:
    """Manages tool definitions and execution."""

    def __init__(self, repl_instance):
        self.repl = repl_instance
        self.workspace = Path(os.getenv("WORKSPACE_DIR", "workspace"))
        self.workspace.mkdir(exist_ok=True)
        self.enable_self_modify = (
            os.getenv("ENABLE_SELF_MODIFY", "true").lower() == "true"
        )

        # Tool registry
        self.tools = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "list_files": self.list_files,
            "create_directory": self.create_directory,
            "delete_file": self.delete_file,
            "execute_python": self.execute_python,
        }

        if self.enable_self_modify:
            self.tools["modify_source"] = self.modify_source
            self.tools["restart_repl"] = self.restart_repl

    def get_tool_definitions(self) -> List[genai.Tool]:
        """Get tool definitions for Gemini API."""
        functions = []

        # File operations
        functions.extend(
            [
                genai.FunctionDeclaration(
                    name="read_file",
                    description="Read the contents of a file",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file relative to workspace",
                            }
                        },
                        "required": ["path"],
                    },
                ),
                genai.FunctionDeclaration(
                    name="write_file",
                    description="Write content to a file",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file relative to workspace",
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file",
                            },
                        },
                        "required": ["path", "content"],
                    },
                ),
                genai.FunctionDeclaration(
                    name="list_files",
                    description="List files in a directory",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path relative to workspace (default: root)",
                            }
                        },
                    },
                ),
                genai.FunctionDeclaration(
                    name="create_directory",
                    description="Create a directory",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path relative to workspace",
                            }
                        },
                        "required": ["path"],
                    },
                ),
                genai.FunctionDeclaration(
                    name="delete_file",
                    description="Delete a file or directory",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to delete relative to workspace",
                            }
                        },
                        "required": ["path"],
                    },
                ),
                genai.FunctionDeclaration(
                    name="execute_python",
                    description="Execute Python code in a sandboxed environment",
                    parameters={
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute",
                            }
                        },
                        "required": ["code"],
                    },
                ),
            ]
        )

        # Self-modification tools
        if self.enable_self_modify:
            functions.extend(
                [
                    genai.FunctionDeclaration(
                        name="modify_source",
                        description="Modify the REPL's own source code",
                        parameters={
                            "type": "object",
                            "properties": {
                                "file": {
                                    "type": "string",
                                    "description": "Source file path relative to src/",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "New content for the file",
                                },
                            },
                            "required": ["file", "content"],
                        },
                    ),
                    genai.FunctionDeclaration(
                        name="restart_repl",
                        description="Restart the REPL to apply changes",
                        parameters={"type": "object", "properties": {}},
                    ),
                ]
            )

        return [genai.Tool(function_declarations=functions)]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool function."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = self.tools[tool_name](**args)
            self.repl.logger.debug(
                f"Tool executed: {tool_name}", {"args": args, "result": result}
            )
            return result
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self.repl.logger.error(error_msg, {"tool": tool_name, "args": args})
            return {"error": error_msg}

    # Tool implementations
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file from the workspace."""
        file_path = self.workspace / path

        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}

        try:
            content = file_path.read_text()
            return {"content": content, "size": len(content), "path": str(path)}
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file in the workspace."""
        file_path = self.workspace / path

        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            file_path.write_text(content)

            return {"success": True, "path": str(path), "size": len(content)}
        except Exception as e:
            return {"error": f"Failed to write file: {e}"}

    def list_files(self, path: str = ".") -> Dict[str, Any]:
        """List files in a directory."""
        dir_path = self.workspace / path

        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}

        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}"}

        try:
            files = []
            for item in sorted(dir_path.iterdir()):
                files.append(
                    {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )

            return {"path": str(path), "files": files, "count": len(files)}
        except Exception as e:
            return {"error": f"Failed to list files: {e}"}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory in the workspace."""
        dir_path = self.workspace / path

        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"error": f"Failed to create directory: {e}"}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file or directory."""
        file_path = self.workspace / path

        if not file_path.exists():
            return {"error": f"Path not found: {path}"}

        try:
            if file_path.is_file():
                file_path.unlink()
            else:
                import shutil

                shutil.rmtree(file_path)

            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"error": f"Failed to delete: {e}"}

    def execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code in a sandboxed environment."""
        import io
        import contextlib

        # Create string buffer to capture output
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()

        # Create restricted globals
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "bool": bool,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
            }
        }

        try:
            # Redirect stdout
            with contextlib.redirect_stdout(output_buffer):
                with contextlib.redirect_stderr(error_buffer):
                    exec(code, safe_globals)

            return {
                "success": True,
                "output": output_buffer.getvalue(),
                "error": error_buffer.getvalue(),
            }
        except Exception as e:
            return {
                "success": False,
                "output": output_buffer.getvalue(),
                "error": str(e),
            }

    def modify_source(self, file: str, content: str) -> Dict[str, Any]:
        """Modify the REPL's source code (self-hosting)."""
        if not self.enable_self_modify:
            return {"error": "Self-modification is disabled"}

        # Resolve source file path
        src_path = Path("src") / file

        if not src_path.exists():
            return {"error": f"Source file not found: {file}"}

        try:
            # Backup original
            backup_path = src_path.with_suffix(src_path.suffix + ".bak")
            backup_path.write_text(src_path.read_text())

            # Write new content
            src_path.write_text(content)

            return {
                "success": True,
                "file": str(file),
                "backup": str(backup_path),
                "message": "Source modified. Use restart_repl to apply changes.",
            }
        except Exception as e:
            return {"error": f"Failed to modify source: {e}"}

    def restart_repl(self) -> Dict[str, Any]:
        """Restart the REPL process."""
        if not self.enable_self_modify:
            return {"error": "Self-modification is disabled"}

        import sys
        import subprocess

        try:
            # Save current context
            self.repl.context._save_context()

            # Restart using same Python interpreter and arguments
            args = [sys.executable] + sys.argv
            subprocess.Popen(args)

            # Exit current process
            self.repl.running = False

            return {"success": True, "message": "Restarting REPL..."}
        except Exception as e:
            return {"error": f"Failed to restart: {e}"}


# Tool Base and Registry:1 ends here
