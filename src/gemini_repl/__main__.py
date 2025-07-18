# Main Entry Point


# [[file:../../PYTHON-GEMINI-REPL.org::*Main Entry Point][Main Entry Point:1]]
#!/usr/bin/env python3
"""Main entry point for Gemini REPL."""
import sys
from gemini_repl.core.repl import GeminiREPL

def main():
    repl = GeminiREPL()
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
