# Python Gemini REPL

A self-hosting Python REPL with Gemini AI integration, featuring conversation context, tool use, and logging.

## Features

- ✅ **Core REPL Event Loop** - Interactive command-line interface with slash commands
- ✅ **Logging System** - JSON-formatted logs with file and FIFO output
- ✅ **Context Management** - Full conversation history with token tracking
- ✅ **Tool Use** - File I/O operations and Python code execution
- ✅ **Self-Hosting** - Can modify its own source code and restart

## Installation

1. Clone and setup:
```bash
make setup
source venv/bin/activate
make install
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. Run the REPL:
```bash
make run
```

## Usage

### Basic Commands
- `/help` - Show available commands
- `/exit` - Exit the REPL
- `/context` - View conversation history
- `/stats` - Show usage statistics
- `/tools` - List available tools

### Example Session
```
> Hello! Can you create a Python script that calculates fibonacci numbers?

[AI creates fibonacci.py in workspace/]

> Can you now modify it to use memoization?

[AI reads and updates the file]

> /stats
Messages: 4
Tokens: 1,250
Estimated cost: $0.0013
```

## Development

```bash
make dev    # Run with debug logging
make test   # Run tests
make lint   # Check code style
```

## Architecture

The system uses a modular architecture with:
- Event-driven REPL loop
- Pluggable tool system
- Persistent context management
- Structured logging
- Self-modification capabilities

See the org-mode source for detailed documentation and system diagrams.
