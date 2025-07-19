"""Session management with UUID-based logging."""

import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse


class SessionManager:
    """Manages REPL sessions with UUID-based identification."""

    def __init__(self, project_dir: Path, session_id: Optional[str] = None):
        self.project_dir = project_dir
        self.session_id = session_id or str(uuid.uuid4())
        self.session_file = project_dir / f"{self.session_id}.jsonl"
        self.parent_uuid = None
        self.message_count = 0

    def create_message_uuid(self) -> str:
        """Create a new UUID for a message."""
        return str(uuid.uuid4())

    def log_entry(
        self, entry_type: str, message: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an entry in Claude's JSONL format."""
        message_uuid = self.create_message_uuid()

        entry = {
            "sessionId": self.session_id,
            "uuid": message_uuid,
            "parentUuid": self.parent_uuid,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": entry_type,
            "message": message,
        }

        if metadata:
            entry.update(metadata)

        # Write to JSONL file
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Update parent for threading
        self.parent_uuid: Optional[str] = message_uuid
        self.message_count += 1

        return message_uuid

    def log_user_message(self, content: str, tokens: int = 0) -> str:
        """Log a user message."""
        message = {"role": "user", "content": content}
        metadata = {"metadata": {"tokens": tokens}}
        return self.log_entry("user", message, metadata)

    def log_assistant_message(
        self, content: str, tokens: int = 0, cost: float = 0.0, duration: float = 0.0
    ) -> str:
        """Log an assistant message."""
        message = {"role": "assistant", "content": content}
        metadata = {"metadata": {"tokens": tokens, "cost": cost, "duration": duration}}
        return self.log_entry("assistant", message, metadata)

    def log_command(self, command: str, args: str = "", result: str = "") -> str:
        """Log a command execution."""
        message = {"type": "command", "command": command, "args": args, "result": result}
        return self.log_entry("command", message)

    def log_error(self, error: str, context: Optional[Dict] = None) -> str:
        """Log an error."""
        message = {"type": "error", "error": error, "context": context or {}}
        return self.log_entry("error", message)

    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Load a previous session's messages."""
        session_file = self.project_dir / f"{session_id}.jsonl"
        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        messages = []
        with open(session_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    messages.append(entry)

        # Set parent UUID to last message for threading continuity
        if messages:
            self.parent_uuid = messages[-1]["uuid"]
            self.message_count = len(messages)

        return messages

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions."""
        sessions = []
        for jsonl_file in sorted(
            self.project_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True
        ):
            # Skip non-UUID named files
            try:
                uuid.UUID(jsonl_file.stem)
            except ValueError:
                continue

            # Get session info
            stat = jsonl_file.stat()
            first_message = None
            last_message = None
            message_count = 0

            with open(jsonl_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    first_message = json.loads(lines[0])
                    last_message = json.loads(lines[-1])
                    message_count = len(lines)

            sessions.append(
                {
                    "session_id": jsonl_file.stem,
                    "file": str(jsonl_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "message_count": message_count,
                    "first_timestamp": first_message.get("timestamp") if first_message else None,
                    "last_timestamp": last_message.get("timestamp") if last_message else None,
                }
            )

        return sessions

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session."""
        return {
            "session_id": self.session_id,
            "session_file": str(self.session_file),
            "message_count": self.message_count,
            "parent_uuid": self.parent_uuid,
        }


def name_to_uuid(name: str) -> str:
    """Convert a name to a deterministic UUID using namespace UUID."""
    # Use DNS namespace for consistency
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    return str(uuid.uuid5(namespace, name))


def find_session_by_name_or_id(project_dir: Path, name_or_id: str) -> Optional[str]:
    """Find a session by name (converted to UUID) or direct UUID."""
    # First try as direct UUID
    try:
        uuid.UUID(name_or_id)
        session_file = project_dir / f"{name_or_id}.jsonl"
        if session_file.exists():
            return name_or_id
    except ValueError:
        pass

    # Try as name
    session_id = name_to_uuid(name_or_id)
    session_file = project_dir / f"{session_id}.jsonl"
    if session_file.exists():
        return session_id

    return None


def add_session_args(parser: argparse.ArgumentParser):
    """Add session-related arguments to argument parser."""
    parser.add_argument(
        "--resume",
        type=str,
        metavar="UUID_OR_NAME",
        help="Resume a previous session by UUID or name",
    )
    parser.add_argument(
        "--name",
        type=str,
        metavar="NAME",
        help="Name for the session (creates deterministic UUID from name)",
    )
    parser.add_argument(
        "--list-sessions", action="store_true", help="List available sessions and exit"
    )
