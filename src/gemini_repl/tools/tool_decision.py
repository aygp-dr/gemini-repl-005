"""Tool decision model for structured dispatch."""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any


class ToolDecision(BaseModel):
    """Structured decision about tool usage."""

    requires_tool_call: bool = Field(description="Whether this query requires a tool call")
    tool_name: Optional[Literal["list_files", "read_file", "write_file"]] = Field(
        None, description="The name of the tool to use"
    )
    reasoning: str = Field(description="Explanation of the decision")
    file_path: Optional[str] = Field(None, description="Path to file or directory")
    pattern: Optional[str] = Field(None, description="File pattern for list_files (e.g., '*.py')")
    content: Optional[str] = Field(None, description="Content to write for write_file")

    def to_tool_args(self) -> Dict[str, Any]:
        """Convert decision to tool arguments."""
        args = {}

        if self.tool_name == "list_files":
            # list_files only takes pattern parameter
            if self.pattern:
                args["pattern"] = self.pattern
            elif self.file_path:
                # If file_path was provided, use it as pattern
                args["pattern"] = self.file_path

        elif self.tool_name == "read_file":
            if self.file_path:
                args["file_path"] = self.file_path

        elif self.tool_name == "write_file":
            if self.file_path:
                args["file_path"] = self.file_path
            if self.content is not None:
                args["content"] = self.content

        return args

    def is_valid(self) -> bool:
        """Check if the decision has required fields for the tool."""
        if not self.requires_tool_call:
            return True

        if not self.tool_name:
            return False

        if self.tool_name in ["read_file", "write_file"] and not self.file_path:
            return False

        if self.tool_name == "write_file" and self.content is None:
            return False

        return True
