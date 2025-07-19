# Release Notes - v0.1.0

**Release Date:** January 19, 2025  
**Status:** Experimental / Educational  
**Python:** 3.11+  
**License:** MIT

## Overview

Initial release of Gemini REPL, a conversational AI REPL with basic tool support for educational and experimental use.

## What's Included

### Core Features
- ✅ Interactive REPL with Gemini AI integration
- ✅ Context management and conversation persistence
- ✅ Session management with UUID-based logging
- ✅ Rate limiting with visual feedback
- ✅ Basic file operation tools (read, write, list)
- ✅ Security sandboxing for file operations

### What's NOT Included
- ❌ Python code execution (removed for security)
- ❌ Reliable tool dispatch (known issue #26)
- ❌ Production-ready error handling
- ❌ Comprehensive test coverage
- ❌ Performance optimizations

## Known Limitations

1. **Tool Dispatch Inconsistency** - The AI doesn't reliably trigger tools when asked to analyze files
2. **Rate Limits** - Free tier limits can be hit quickly during testing
3. **Import Issues** - Some environments have issues with google-genai imports
4. **Not Production Ready** - This is an experimental release for learning and development

## Getting Started

```bash
# Install dependencies
make setup

# Set your API key
export GEMINI_API_KEY="your-key-here"

# Run the REPL
make repl
```

## Target Audience

This release is intended for:
- Students learning about AI integration
- Developers experimenting with Gemini API
- Contributors to the project
- Educational demonstrations

## Next Release (0.2.0)

The next release will focus on:
- Reliable tool dispatch
- Self-hosting capabilities
- Better error handling
- Improved test coverage

## Security Notice

The execute_python tool has been removed due to security concerns. File operations are sandboxed to the current directory.

## Contributing

See CONTRIBUTING.md for guidelines on how to contribute to this project.
