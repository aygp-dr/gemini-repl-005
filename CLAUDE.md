# CLAUDE.md - Project Context for Claude Code

This file provides guidance to Claude Code when working with this repository.
It tracks implementation decisions, patterns, and context for efficient development.

## Project Overview

**Gemini REPL** - A Python-based interactive REPL with Google Gemini AI integration
- Architecture: Literate programming with org-mode
- Main source: PYTHON-GEMINI-REPL.org
- Language: Python 3.11+
- SDK: google-genai (migrated from google-generativeai)

## Build & Test Commands

```bash
# Setup
gmake setup         # Initial setup with uv
source .env         # Load environment (API key)

# Development  
gmake run           # Run the REPL
gmake tangle        # Tangle org-mode to Python
gmake detangle      # Update org-mode from Python

# Quality
gmake lint          # Run ruff and mypy
gmake test          # Run pytest with coverage
gmake all           # Lint, test, build

# Utilities
gmake clean         # Clean generated files
gmake hooks         # Install pre-commit hooks
gmake README.md     # Generate from README.org
```

## Current State (2025-07-19)

- ✅ Basic REPL working ("2 + 2" returns "4")
- ✅ Clean exit with /exit command
- ✅ Logging functional (FIFO disabled)
- ✅ TTY interaction tested with expect
- ✅ Log processing verified through integration tests
- ⚠️ Tool system needs migration to new SDK
- ⚠️ Some unit tests failing (logger format, context isolation)
- 🔄 Experiments in experiments/repl-testing/

## Work Sessions

### 2025-07-19: SDK Migration Completion

**Starting Context:**
- Migrated from google-generativeai to google-genai SDK
- Basic REPL functionality restored
- Tool system still needs migration
- Tests failing due to logger format issues

**Prompts Received:**
1. "can you quickly add the files noted in issue 10 then continue work on the validation of the api calls and repl"
2. "remember at each step after a commit to include in git notes the prompts used..."
3. Initial: "gmake all linting, testing, integration (expect) tests and ensure that we have a minimally running repl that can do 2 + 2"

**Key Decisions:**
- Disabled FIFO logging temporarily (was causing hangs)
- Simplified response handling by removing tool processing
- Used `uv run` for all Python execution to ensure dependencies

**Problems Encountered:**
- Logger was writing JSON within JSON (double encoding)
- Tool system using old SDK's genai.Tool which doesn't exist
- Test isolation issues (context persisting between tests)
- FIFO at /tmp/gemini-repl.fifo blocking test execution

**Solutions Applied:**
- Commented out FIFO setup in logger.py
- Disabled tool handling in repl.py (TODO: re-enable)
- Fixed response extraction to use response.text directly
- Added debug logging to test scripts

**Testing Approach:**
1. Created minimal test script (experiments/repl-testing/test_minimal.py)
2. Debug script to understand new SDK response format
3. Unit tests for API client with mocking
4. Integration tests for REPL (some still failing)

**Timing:**
- SDK migration: ~2 hours
- Test fixing: ~1 hour
- Command integration: ~15 minutes

**Next Steps:**
- Fix remaining test failures
- Re-implement tool system with new SDK
- Add expect-based integration tests
- Document new SDK patterns

---

## Patterns and Learnings

### SDK Migration Pattern
When migrating between SDK versions:
1. Create isolated test script first
2. Debug actual API response format
3. Update code incrementally
4. Disable complex features temporarily
5. Add tests for new patterns

### Test Debugging Pattern
For hanging tests:
1. Check for blocking I/O (FIFOs, pipes)
2. Add timeout to subprocess calls
3. Use debug logging liberally
4. Isolate test environment (separate log/context files)

### Commit Pattern
Each commit should have:
1. Clear conventional commit message
2. Git notes with prompts and context
3. Reference to issues
4. Documentation of problems/solutions
5. Timing information for estimation

---

## Environment Setup

**Key Environment Variables:**
- `GEMINI_API_KEY`: Required for API calls
- `LOG_LEVEL`: Set to DEBUG for troubleshooting
- `LOG_FILE`: Path to log file (avoid /tmp for tests)
- `CONTEXT_FILE`: Conversation history storage

**Dependencies:**
- google-genai>=1.26.0 (new SDK)
- tiktoken (for token counting)
- pytest, pytest-cov (testing)
- ruff, mypy (linting)

**Common Commands:**
```bash
# Development
source .env
gmake run           # Run REPL
gmake test         # Run tests
gmake lint         # Run linters

# Testing specific files
uv run pytest tests/test_api_client.py -v
uv run python experiments/repl-testing/test_minimal.py

# Check logs
tail -f logs/gemini.log
```

---

*This file is updated by Builder mode to track implementation context*
