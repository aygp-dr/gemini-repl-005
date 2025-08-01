"""JSONL logger for interaction history (like Claude's)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .session import SessionManager


class JSONLLogger:
    """Log interactions in JSONL format for analysis."""

    def __init__(self, jsonl_path: Path, session_manager: Optional[SessionManager] = None):
        self.jsonl_path = jsonl_path
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_manager = session_manager

    def log_interaction(self, interaction: Dict[str, Any]):
        """Log a single interaction to JSONL file."""
        # Add timestamp if not present
        if "timestamp" not in interaction:
            interaction["timestamp"] = datetime.now().isoformat()

        # Append to JSONL file
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(interaction, ensure_ascii=False) + "\n")

    def log_user_input(self, input_text: str, metadata: Optional[Dict] = None):
        """Log user input."""
        if self.session_manager:
            tokens = metadata.get("tokens", 0) if metadata else 0
            self.session_manager.log_user_message(input_text, tokens)
        else:
            interaction = {"type": "user_input", "content": input_text, "metadata": metadata or {}}
            self.log_interaction(interaction)

    def log_assistant_response(self, response_text: str, metadata: Optional[Dict] = None):
        """Log assistant response."""
        if self.session_manager:
            tokens = metadata.get("tokens", 0) if metadata else 0
            cost = metadata.get("cost", 0.0) if metadata else 0.0
            duration = metadata.get("time", 0.0) if metadata else 0.0
            self.session_manager.log_assistant_message(response_text, tokens, cost, duration)
        else:
            interaction = {
                "type": "assistant_response",
                "content": response_text,
                "metadata": metadata or {},
            }
            self.log_interaction(interaction)

    def log_command(self, command: str, args: str = "", result: str = ""):
        """Log command execution."""
        if self.session_manager:
            self.session_manager.log_command(command, args, result)
        else:
            interaction = {"type": "command", "command": command, "args": args, "result": result}
            self.log_interaction(interaction)

    def log_error(self, error: str, context: Optional[Dict] = None):
        """Log error."""
        if self.session_manager:
            self.session_manager.log_error(error, context)
        else:
            interaction = {"type": "error", "error": error, "context": context or {}}
            self.log_interaction(interaction)

    def log_tool_use(self, tool_name: str, args: Dict[str, Any], result: Any):
        """Log tool usage."""
        interaction = {
            "type": "tool_use",
            "tool": tool_name,
            "args": args,
            "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
            "timestamp": datetime.now().isoformat(),
        }
        if self.session_manager:
            interaction["session_id"] = self.session_manager.session_id
        self.log_interaction(interaction)

    def read_interactions(self, last_n: Optional[int] = None):
        """Read interactions from JSONL file."""
        if not self.jsonl_path.exists():
            return []

        interactions = []
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    interactions.append(json.loads(line))

        if last_n:
            return interactions[-last_n:]
        return interactions
