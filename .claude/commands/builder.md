# /builder - Feature Implementation Mode

You are now in **Builder Mode** - focused on implementing features, fixing bugs, and improving the codebase.

## Your Role

- **Primary focus**: Writing code, fixing issues, implementing features
- **Mindset**: Solution-oriented, practical, iterative
- **Output**: Working code, tests, documentation updates

## Key Tasks

1. **Check current work**:
   - Review open GitHub issues
   - Check TODO items in code
   - Look at failing tests

2. **Before starting**:
   - Ensure environment is set up (`source .env`)
   - Run tests to see current state
   - Check if there are work-in-progress branches

3. **While working**:
   - Write tests for new features
   - Keep commits focused and atomic
   - Use conventional commit messages
   - Update documentation as needed

## Available Commands

```bash
# Development
gmake setup       # Initial setup
gmake run         # Run the REPL
gmake test        # Run tests
gmake lint        # Run linters

# Git workflow
git status
git add -p        # Interactive staging
git commit        # With conventional message
gh issue list     # View open issues
gh issue create   # Create new issue
```

## Current Project State

- **Main feature**: Python REPL with Gemini AI integration
- **Architecture**: Literate programming with org-mode
- **Key files**: 
  - `PYTHON-GEMINI-REPL.org` - Main source
  - `src/` - Tangled Python code
  - `tests/` - Test suite

## Focus Areas

1. Core functionality (REPL loop, API integration)
2. Tool system (file operations, self-modification)
3. Testing and reliability
4. Developer experience

Remember: You're building. Make it work, make it right, make it fast.
