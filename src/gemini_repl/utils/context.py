# Context Management


# [[file:../../../PYTHON-GEMINI-REPL.org::*Context Management][Context Management:1]]
"""Context management for conversation history."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import tiktoken


class ContextManager:
    """Manage conversation context and history."""

    def __init__(self, context_file=None):
        self.context_file = context_file or os.getenv("CONTEXT_FILE", "conversation.json")
        self.max_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", "100000"))
        self.messages: List[Dict[str, Any]] = []
        self.session_start = datetime.now()

        # Token counter (using tiktoken for estimation)
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.encoder = tiktoken.get_encoding("cl100k_base")

        # Load existing context if available
        self._load_context()

        # Load system prompt if starting fresh
        if not self.messages:
            self._load_system_prompt()

    def _load_context(self):
        """Load context from file if it exists."""
        if os.path.exists(self.context_file):
            try:
                with open(self.context_file, "r") as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
            except (FileNotFoundError, json.JSONDecodeError):
                pass

    def _load_system_prompt(self):
        """Load system prompt from resources."""
        # Try multiple locations for the system prompt
        prompt_locations = [
            Path(__file__).parent.parent.parent / "resources" / "system_prompt.txt",
            Path.cwd() / "resources" / "system_prompt.txt",
            Path(os.getenv("GEMINI_SYSTEM_PROMPT", "")),
        ]

        for prompt_path in prompt_locations:
            if prompt_path and prompt_path.exists():
                try:
                    system_prompt = prompt_path.read_text().strip()
                    if system_prompt:
                        self.add_message("system", system_prompt)
                        return
                except Exception:
                    pass

    def _save_context(self):
        """Save context to file."""
        data = {
            "messages": self.messages,
            "saved_at": datetime.now().isoformat(),
            "session_duration": str(datetime.now() - self.session_start),
        }
        with open(self.context_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_message(self, role: str, content: str):
        """Add a message to the context."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tokens": self._count_tokens(content),
        }
        self.messages.append(message)

        # Trim context if needed
        self._trim_context()

        # Auto-save
        self._save_context()

    def add_tool_response(self, tool_name: str, response: Any):
        """Add a tool response to the context."""
        self.add_message("tool", f"{tool_name}: {json.dumps(response)}")

    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages for API calls."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]

    def get_token_count(self) -> int:
        """Get total token count."""
        return sum(msg.get("tokens", 0) for msg in self.messages)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoder.encode(text))
        except Exception:
            # Rough estimate if tiktoken fails
            return len(text) // 4

    def _trim_context(self):
        """Trim context to stay within token limit."""
        while self.get_token_count() > self.max_tokens and len(self.messages) > 1:
            # Keep system messages, remove oldest user/assistant messages
            if self.messages[0]["role"] != "system":
                self.messages.pop(0)
            else:
                self.messages.pop(1)

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return {
            "message_count": len(self.messages),
            "token_count": self.get_token_count(),
            "estimated_cost": self.get_token_count() * 0.000001,  # Rough estimate
            "duration": str(datetime.now() - self.session_start),
            "average_message_tokens": self.get_token_count() / max(len(self.messages), 1),
        }

    def save_to_file(self, path: Path):
        """Save conversation to a specific file."""
        data = {
            "messages": self.messages,
            "stats": self.get_stats(),
            "exported_at": datetime.now().isoformat(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, path: Path):
        """Load conversation from a specific file."""
        with open(path, "r") as f:
            data = json.load(f)
            self.messages = data.get("messages", [])
            self.session_start = datetime.now()  # Reset session start

    def clear(self):
        """Clear the conversation context, preserving system prompt."""
        # Keep system messages
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_messages
        self._save_context()


# Context Management:1 ends here
