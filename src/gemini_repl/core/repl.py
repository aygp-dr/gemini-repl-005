# REPL Event Loop


# [[file:../../../PYTHON-GEMINI-REPL.org::*REPL Event Loop][REPL Event Loop:1]]
"""Core REPL implementation with event loop."""

import os
import readline
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ..utils.logger import Logger
from ..utils.context import ContextManager
from ..utils.paths import PathManager
from ..utils.jsonl_logger import JSONLLogger
from ..utils.session import SessionManager
from .api_client import GeminiClient
from ..tools.tool_system import ToolSystem


class GeminiREPL:
    """Main REPL class implementing the event loop."""

    def __init__(self, session_id: Optional[str] = None, resume_session: Optional[str] = None):
        # Initialize path manager first
        self.paths = PathManager()

        # Initialize session manager
        self.session_manager = SessionManager(self.paths.project_dir, session_id)

        # Handle session resumption
        if resume_session:
            try:
                messages = self.session_manager.load_session(resume_session)
                self.session_manager.session_id = resume_session
                print(f"Resumed session {resume_session} with {len(messages)} messages")
            except FileNotFoundError:
                print(f"Session {resume_session} not found, starting new session")

        # Initialize other components with paths
        self.logger = Logger(log_file=str(self.paths.get_log_file()))
        self.context = ContextManager(context_file=str(self.paths.context_file))
        self.jsonl_logger = JSONLLogger(self.paths.get_jsonl_file(), self.session_manager)
        self.client = GeminiClient()
        self.tools = ToolSystem(self)
        self.running = True
        self.commands = self._init_commands()

        # Initialize readline for better input handling
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode emacs")  # Ensure arrow keys work
        readline.set_history_length(1000)
        self._load_history()

        # Log startup with project info
        self.logger.info(
            "REPL started",
            {
                "timestamp": datetime.now().isoformat(),
                "project": self.paths.project_name,
                "project_dir": str(self.paths.project_dir),
            },
        )

    def _init_commands(self) -> Dict[str, Callable]:
        """Initialize slash commands."""
        return {
            "/help": self.cmd_help,
            "/exit": self.cmd_exit,
            "/quit": self.cmd_exit,
            "/clear": self.cmd_clear,
            "/context": self.cmd_context,
            "/stats": self.cmd_stats,
            "/save": self.cmd_save,
            "/load": self.cmd_load,
            "/tools": self.cmd_tools,
            "/workspace": self.cmd_workspace,
            "/debug": self.cmd_debug,
            "/project": self.cmd_project,
            "/sessions": self.cmd_sessions,
        }

    def _load_history(self):
        """Load command history from project-specific file."""
        try:
            readline.read_history_file(str(self.paths.history_file))
            self.logger.debug("Loaded history", {"file": str(self.paths.history_file)})
        except FileNotFoundError:
            self.logger.debug("No history file found", {"file": str(self.paths.history_file)})

    def _save_history(self):
        """Save command history to project-specific file."""
        try:
            readline.write_history_file(str(self.paths.history_file))
            self.logger.debug("Saved history", {"file": str(self.paths.history_file)})
        except Exception as e:
            self.logger.error("Failed to save history", {"error": str(e)})

    def _display_banner(self):
        """Display the REPL banner."""
        banner = """
╔══════════════════════════════════════╗
║        🌟 Gemini REPL v1.0 🌟        ║
║  Python-powered AI conversations     ║
║  Type /help for available commands   ║
╚══════════════════════════════════════╝
"""
        print(banner)
        print(f"Session ID: {self.session_manager.session_id}")

    def run(self):
        """Main event loop."""
        self._display_banner()
        self.logger.info("REPL started", {"timestamp": datetime.now().isoformat()})

        while self.running:
            try:
                # Get user input
                prompt = self._get_prompt()
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Log input
                self.logger.debug("User input", {"input": user_input})
                self.jsonl_logger.log_user_input(user_input)

                # Handle slash commands
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                else:
                    # Handle API request
                    self._handle_api_request(user_input)

            except EOFError:
                self.cmd_exit()
            except KeyboardInterrupt:
                print("\nUse /exit to quit")
                continue
            except Exception as e:
                self.logger.error("REPL error", {"error": str(e)})
                print(f"Error: {e}")

        self._save_history()
        self.logger.info("REPL stopped")

    def _get_prompt(self) -> str:
        """Generate the prompt string."""
        tokens = self.context.get_token_count()
        return f"\n[{tokens} tokens] > "

    def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in self.commands:
            self.commands[cmd](args)
            self.jsonl_logger.log_command(cmd, args)
        else:
            print(f"Unknown command: {cmd}")
            print("Type /help for available commands")
            self.jsonl_logger.log_command(cmd, args, "unknown_command")

    def _handle_api_request(self, user_input: str):
        """Handle API request with context and tools."""
        try:
            # Add to context
            self.context.add_message("user", user_input)

            # Get response (tools disabled for now until SDK support is complete)
            response = self.client.send_message(self.context.get_messages())

            # Handle tool calls if present (disabled for now)
            # TODO: Re-enable when tool support is properly implemented
            # if hasattr(response, "candidates") and response.candidates:
            #     candidate = response.candidates[0]
            #     if hasattr(candidate.content, "parts"):
            #         for part in candidate.content.parts:
            #             if hasattr(part, "function_call") and part.function_call:
            #                 # Execute tool
            #                 tool_response = self.tools.execute_tool(
            #                     part.function_call.name, part.function_call.args
            #                 )
            #                 # Add tool response to context
            #                 self.context.add_tool_response(part.function_call.name, tool_response)

            # Extract text response
            response_text = self._extract_response_text(response)

            # Add to context
            self.context.add_message("assistant", response_text)

            # Display response with metadata
            self._display_response(response_text, response)

            # Log response to JSONL
            metadata = self._extract_metadata(response)
            self.jsonl_logger.log_assistant_response(response_text, metadata)

        except Exception as e:
            self.logger.error("API request failed", {"error": str(e)})
            self.jsonl_logger.log_error(str(e), {"input": user_input})
            print(f"Error: {e}")

    def _extract_response_text(self, response) -> str:
        """Extract text from API response."""
        if hasattr(response, "text"):
            return response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate.content, "parts"):
                texts = []
                for part in candidate.content.parts:
                    if hasattr(part, "text"):
                        texts.append(part.text)
                return "\n".join(texts)
        return "No response text found"

    def _display_response(self, text: str, response):
        """Display response with metadata."""
        # Display the response text
        print(f"\n{text}")

        # Display metadata
        metadata = self._extract_metadata(response)
        if metadata:
            meta_str = f"[🟢 {metadata['tokens']} tokens | ${metadata['cost']:.4f} | {metadata['time']:.1f}s]"
            print(f"\n{meta_str}")

    def _extract_metadata(self, response) -> Optional[Dict[str, Any]]:
        """Extract metadata from response."""
        try:
            metadata = {}

            # Token usage
            if hasattr(response, "usage_metadata"):
                metadata["tokens"] = response.usage_metadata.total_token_count
                # Rough cost estimate (adjust based on actual pricing)
                metadata["cost"] = metadata["tokens"] * 0.000001
            else:
                metadata["tokens"] = 0
                metadata["cost"] = 0

            # Response time (would need to track this in api_client)
            metadata["time"] = 0.5  # Placeholder

            return metadata
        except Exception:
            return None

    # Command implementations
    def cmd_help(self, args: str):
        """Display help information."""
        help_text = """
Available Commands:
  /help         - Show this help message
  /exit, /quit  - Exit the REPL
  /clear        - Clear the screen
  /context      - Show conversation context
  /stats        - Show usage statistics
  /save [file]  - Save conversation to file
  /load [file]  - Load conversation from file
  /tools        - List available tools
  /workspace    - Show workspace contents
  /debug        - Toggle debug mode
  /project      - Show project information
  /sessions     - List available sessions

Tool Functions:
  The AI can read, write, and modify files in the workspace directory.
  Ask it to create, edit, or analyze files for you.
"""
        print(help_text)

    def cmd_exit(self, args: str = ""):
        """Exit the REPL."""
        print("\nGoodbye! 👋")
        self.running = False

    def cmd_clear(self, args: str):
        """Clear the screen."""
        os.system("clear" if os.name == "posix" else "cls")
        self._display_banner()

    def cmd_context(self, args: str):
        """Display conversation context."""
        messages = self.context.get_messages()
        print("\n=== Conversation Context ===")
        for msg in messages[-10:]:  # Show last 10 messages
            role = msg["role"].upper()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"{role}: {content}")
        print(f"\nTotal messages: {len(messages)}")
        print(f"Total tokens: {self.context.get_token_count()}")

    def cmd_stats(self, args: str):
        """Display usage statistics."""
        stats = self.context.get_stats()
        print("\n=== Usage Statistics ===")
        print(f"Messages: {stats['message_count']}")
        print(f"Tokens: {stats['token_count']}")
        print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
        print(f"Session duration: {stats['duration']}")

    def cmd_save(self, args: str):
        """Save conversation to file."""
        filename = args.strip() or f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = Path("workspace") / filename
        self.context.save_to_file(path)
        print(f"Conversation saved to: {path}")

    def cmd_load(self, args: str):
        """Load conversation from file."""
        if not args:
            print("Usage: /load <filename>")
            return
        path = Path("workspace") / args.strip()
        if path.exists():
            self.context.load_from_file(path)
            print(f"Conversation loaded from: {path}")
        else:
            print(f"File not found: {path}")

    def cmd_tools(self, args: str):
        """List available tools."""
        tools = self.tools.get_tool_definitions()
        print("\n=== Available Tools ===")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

    def cmd_workspace(self, args: str):
        """Show workspace contents."""
        workspace = Path("workspace")
        if not workspace.exists():
            print("Workspace directory does not exist")
            return

        print("\n=== Workspace Contents ===")
        for item in sorted(workspace.iterdir()):
            size = item.stat().st_size if item.is_file() else "-"
            print(f"{'📄' if item.is_file() else '📁'} {item.name:30} {size:>10}")

    def cmd_debug(self, args: str):
        """Toggle debug mode."""
        current = self.logger.logger.level
        new_level = "DEBUG" if current != 10 else "INFO"  # 10 is DEBUG level
        self.logger.set_level(new_level)
        print(f"Debug mode: {'ON' if new_level == 'DEBUG' else 'OFF'}")

    def cmd_project(self, args: str):
        """Show project information."""
        info = self.paths.info()
        print("\n=== Project Information ===")
        print(f"Project Name: {info['project_name']}")
        print(f"Project Dir:  {info['project_dir']}")
        print(f"History File: {info['history_file']}")
        print(f"Context File: {info['context_file']}")
        print(f"Logs Dir:     {info['logs_dir']}")
        print(f"Working Dir:  {info['cwd']}")
        print("\nShared context across sessions: YES")
        print("Session cache for Gemini API: ENABLED")

    def cmd_sessions(self, args: str):
        """Show available sessions."""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            print("No sessions found")
            return

        print("\n=== Available Sessions ===")
        print(f"Current session: {self.session_manager.session_id}\n")

        for session in sessions[:10]:  # Show last 10 sessions
            session_id = session["session_id"]
            is_current = " (current)" if session_id == self.session_manager.session_id else ""

            print(f"Session: {session_id}{is_current}")
            print(f"  Messages: {session['message_count']}")
            print(f"  Modified: {session['modified']}")

            if session["first_timestamp"] and session["last_timestamp"]:
                print(f"  Duration: {session['first_timestamp']} → {session['last_timestamp']}")
            print()

        if len(sessions) > 10:
            print(f"... and {len(sessions) - 10} more sessions")

        print("\nTo resume a session: gemini-repl --resume <session-id>")


# REPL Event Loop:1 ends here
