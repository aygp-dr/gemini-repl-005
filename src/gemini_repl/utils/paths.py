"""Path management for Gemini REPL."""

from pathlib import Path
import re


class PathManager:
    """Manages paths for project-specific storage."""

    def __init__(self):
        self.home = Path.home()
        self.cwd = Path.cwd()

        # Create base directories
        self.gemini_dir = self.home / ".gemini"
        self.projects_dir = self.gemini_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # Generate project-specific directory name (like Claude's)
        self.project_name = self._get_project_name()
        self.project_dir = self.projects_dir / self.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Setup project-specific paths
        self.history_file = self.project_dir / "history"
        self.context_file = self.project_dir / "context.json"
        self.logs_dir = self.project_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Local logs directory (git ignored)
        self.local_logs_dir = Path("logs")
        self.local_logs_dir.mkdir(exist_ok=True)

        # FIFO path
        self.fifo_path = self.project_dir / "repl.fifo"

    def _get_project_name(self) -> str:
        """Generate project name from current working directory."""
        # Convert path to string and replace separators with dashes
        # This matches Claude's pattern: ~/.claude/projects/{pwd | sed -e s#/#-#}
        project_path = str(self.cwd.absolute())

        # Remove leading slash and replace all slashes with dashes
        if project_path.startswith("/"):
            project_path = project_path[1:]

        # Replace slashes with dashes
        project_name = project_path.replace("/", "-")

        # Handle Windows paths
        project_name = project_name.replace("\\", "-")

        # Clean up any double dashes
        project_name = re.sub(r"-+", "-", project_name)

        return project_name

    def get_log_file(self, name: str = "gemini.log") -> Path:
        """Get path for a log file."""
        return self.logs_dir / name

    def get_jsonl_file(self, name: str = "interactions.jsonl") -> Path:
        """Get path for JSONL file (like Claude's)."""
        return self.project_dir / name

    def get_session_file(self, session_id: str) -> Path:
        """Get path for a session JSONL file."""
        return self.project_dir / f"{session_id}.jsonl"

    def list_sessions(self):
        """List all session files."""
        return sorted(self.project_dir.glob("session_*.json"))

    def info(self) -> dict:
        """Get information about paths."""
        return {
            "project_name": self.project_name,
            "project_dir": str(self.project_dir),
            "history_file": str(self.history_file),
            "context_file": str(self.context_file),
            "logs_dir": str(self.logs_dir),
            "local_logs_dir": str(self.local_logs_dir),
            "fifo_path": str(self.fifo_path),
            "cwd": str(self.cwd),
        }
