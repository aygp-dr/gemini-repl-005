# Main Entry Point


# [[file:../../PYTHON-GEMINI-REPL.org::*Main Entry Point][Main Entry Point:1]]
#!/usr/bin/env python3
"""Main entry point for Gemini REPL."""

import sys
import argparse
from gemini_repl.core.repl import GeminiREPL
from gemini_repl.utils.session import (
    add_session_args,
    SessionManager,
    name_to_uuid,
    find_session_by_name_or_id,
)
from gemini_repl.utils.paths import PathManager


def main():
    parser = argparse.ArgumentParser(description="Gemini REPL - AI-powered conversation interface")
    add_session_args(parser)
    args = parser.parse_args()

    # Handle --list-sessions
    if args.list_sessions:
        paths = PathManager()
        session_manager = SessionManager(paths.project_dir)
        sessions = session_manager.list_sessions()

        if not sessions:
            print("No sessions found")
            return

        print("Available sessions:")
        for session in sessions:
            print(f"\n{session['session_id']}")
            print(f"  Messages: {session['message_count']}")
            print(f"  Modified: {session['modified']}")
        return

    # Handle session resolution
    session_id = None
    resume_session = None

    if args.name:
        # Create deterministic UUID from name
        session_id = name_to_uuid(args.name)
        print(f"Using named session '{args.name}' (ID: {session_id})")

    if args.resume:
        # Find session by name or UUID
        paths = PathManager()
        found_session = find_session_by_name_or_id(paths.project_dir, args.resume)
        if found_session:
            resume_session = found_session
            if args.resume != found_session:
                print(f"Resuming session '{args.resume}' (ID: {found_session})")
        else:
            print(f"Session '{args.resume}' not found")
            sys.exit(1)

    # Create REPL with optional session
    repl = GeminiREPL(session_id=session_id, resume_session=resume_session)
    try:
        repl.run()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
# Main Entry Point:1 ends here
