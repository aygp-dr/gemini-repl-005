# Python Execution Security Analysis

## Current State

The `execute_python` tool in `tool_system.py` has basic sandboxing but lacks proper security measures.

## Security Risks

1. **Resource Exhaustion**
   - No CPU time limits
   - No memory limits
   - Could run infinite loops

2. **Python Internals Exploitation**
   - Restricted builtins but still in-process
   - Potential for exploiting Python internals

3. **No Process Isolation**
   - Runs in same process as REPL
   - Could affect REPL stability

## Recommended Solutions

### Option 1: Use E2B (Anthropic's Approach)

E2B provides containerized Python execution used by Anthropic:

```python
# Install: pip install e2b-code-interpreter
from e2b_code_interpreter import CodeInterpreter

def execute_python_safe(code: str) -> str:
    """Execute Python code in E2B sandbox."""
    sandbox = CodeInterpreter()
    try:
        execution = sandbox.run_python(code)
        return execution.text
    finally:
        sandbox.close()
```

**Benefits:**
- Container isolation
- Resource limits (1GB RAM, 5GB storage)
- No network access
- 1-hour timeout
- Used in production by Anthropic

### Option 2: Remove Python Execution

The safest option is to remove `execute_python` entirely:

```python
# In tool_system.py, remove:
# - execute_python function
# - EXECUTE_PYTHON_DECLARATION
# - Entry in TOOL_SYSTEM_FUNCTIONS
```

### Option 3: Basic Process Isolation (Not Recommended)

If you must implement your own:

```python
import subprocess
import tempfile
import resource

def execute_python_subprocess(code: str, timeout: int = 5) -> str:
    """Execute Python in subprocess with limits."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Run with strict limits
        result = subprocess.run(
            [sys.executable, '-u', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            preexec_fn=lambda: resource.setrlimit(
                resource.RLIMIT_AS, 
                (100 * 1024 * 1024, 100 * 1024 * 1024)  # 100MB
            )
        )
        return result.stdout + result.stderr
    finally:
        os.unlink(temp_file)
```

### Option 4: Pyodide in Deno (WebAssembly Isolation)

Simon Willison's approach using Pyodide provides WebAssembly-level isolation:

```javascript
// pyodide_sandbox.js
import { pyodide } from "npm:pyodide@0.26.4";

const py = await pyodide();

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }
  
  const { code } = await req.json();
  
  try {
    py.runPython(`
import sys
from io import StringIO
sys.stdout = StringIO()
sys.stderr = StringIO()
    `);
    
    const result = py.runPython(code);
    const stdout = py.runPython("sys.stdout.getvalue()");
    const stderr = py.runPython("sys.stderr.getvalue()");
    
    return Response.json({ 
      result: result?.toString(), 
      stdout, 
      stderr 
    });
  } catch (error) {
    return Response.json({ 
      error: error.message 
    }, { status: 400 });
  }
});
```

**Usage from Python:**
```python
import requests

def execute_python_pyodide(code: str) -> str:
    """Execute Python in Pyodide sandbox via Deno."""
    response = requests.post(
        "http://localhost:8000",
        json={"code": code}
    )
    result = response.json()
    return result.get("stdout", "") + result.get("stderr", "")
```

**Benefits:**
- WebAssembly isolation
- Runs in separate Deno process
- Built-in resource limits
- No filesystem access by default
- Can't escape to system

## Recommendation

**For production use**, in order of preference:
1. **Remove `execute_python`** - Simplest and safest
2. **Use E2B** - Battle-tested by Anthropic
3. **Use Pyodide in Deno** - Good WebAssembly isolation
4. **Basic subprocess** - Only for controlled environments

The current implementation is not safe for untrusted code execution.

## References

- [Anthropic Code Execution Tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/code-execution-tool)
- [E2B Documentation](https://e2b.dev/docs)
- [Running Untrusted Python Code](https://healeycodes.com/running-untrusted-python-code)
- [Pyodide Python Sandbox (Simon Willison)](https://til.simonwillison.net/deno/pyodide-sandbox)
- [HN Discussion on Python Sandboxing](https://news.ycombinator.com/item?id=43691230)
