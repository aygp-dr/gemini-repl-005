# Gemini REPL Python Implementation

This is a Python port of the ClojureScript gemini-repl project.

## Key Features
- One-shot org-mode implementation
- Core REPL event loop with slash commands
- File and FIFO logging
- Context management for conversations
- Tool system for file operations
- Self-hosting capabilities

## Architecture
- Modular design: core/, utils/, tools/
- Event-driven REPL with slash commands
- Token-aware context with auto-trimming
- Sandboxed tool execution
- Structured JSON logging

## Development
- Built with uv package manager
- Makefile-driven workflow
- Org-babel tangle/detangle support
- Comprehensive test suite
