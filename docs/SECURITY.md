# Security Model for Gemini REPL Tool System

## Overview

The Gemini REPL implements a self-hosting capability where the AI can read, write, and modify files within its own codebase. This document describes the security model and boundaries.

## Security Principles

1. **Sandbox to Repository**: All file operations are restricted to the current working directory (pwd at startup)
2. **No Escape Mechanisms**: Parent directory references (..), absolute paths, and symlinks are blocked
3. **Minimal Operations**: Only read, write, and list operations are allowed
4. **Clear Boundaries**: "Only change files in this repo"

## Implementation

### Path Validation

Every file operation goes through `validate_path()` which ensures:

```python
def validate_path(file_path: str) -> Path:
    # Reject absolute paths
    if os.path.isabs(file_path):
        raise SecurityError(f"Absolute paths not allowed: {file_path}")
    
    # Reject parent directory references
    if ".." in file_path:
        raise SecurityError(f"Parent directory references not allowed: {file_path}")
    
    # Resolve and validate within sandbox
    full_path = (SANDBOX_DIR / file_path).resolve()
    full_path.relative_to(SANDBOX_DIR)  # Raises if outside
    
    # No symlinks allowed
    if full_path.is_symlink():
        raise SecurityError(f"Symlinks not allowed: {file_path}")
```

### Sandbox Directory

- Set at startup: `SANDBOX_DIR = Path.cwd().resolve()`
- Cannot be changed during execution
- All paths resolved relative to this directory

## Attack Vectors Blocked

### 1. Directory Traversal
```python
read_file("../../../etc/passwd")  # ❌ Blocked
read_file("src/../../etc/hosts")  # ❌ Blocked
```

### 2. Absolute Paths
```python
read_file("/etc/passwd")           # ❌ Blocked
write_file("/tmp/evil.txt", "...")  # ❌ Blocked
```

### 3. Symlink Attacks
```python
# Even if evil_link -> /etc
read_file("evil_link/passwd")      # ❌ Blocked
```

### 4. Path Normalization
```python
read_file(".//..//..//etc/passwd") # ❌ Blocked
```

## Allowed Operations

### ✅ Safe File Operations
```python
read_file("src/main.py")           # ✅ Within repo
write_file("output/data.txt", ...) # ✅ Within repo
list_files("src/**/*.py")          # ✅ Within repo
search_code("class.*REPL")         # ✅ Within repo
```

## Testing

Comprehensive test suite in `tests/test_path_traversal_security.py`:
- 7 attack vector tests (all must fail)
- 1 legitimate operation test (must pass)

Run security tests:
```bash
pytest tests/test_path_traversal_security.py -v
```

## Limitations

1. **No Updates**: The system cannot update dependencies or system files
2. **No Execution**: Cannot run arbitrary commands
3. **No Network**: Cannot make network requests
4. **Repository Only**: Cannot access files outside the repository

## Security Incident Response

If a security issue is discovered:

1. **Disable Tools**: Set `GEMINI_TOOLS_ENABLED=false`
2. **Report Issue**: Create a GitHub issue with security label
3. **Test Thoroughly**: Use the security test suite
4. **Document Fix**: Update this document and tests

## Rationale

This simple security model was chosen because:
- Clear boundaries are easier to understand and audit
- Self-hosting AI needs to modify its own code
- Complex permission systems add complexity without clear benefit
- "Only modify this repository" is a simple, understandable rule

## Future Considerations

- File type restrictions (e.g., only .py, .md files)
- Read-only mode for analysis without modification
- Audit logging of all file operations
- Size limits on file operations

---

**Remember**: The security model is "only change files in this repo and no symlinks, no updates, just list, read, write"
