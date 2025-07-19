# Manual Testing Guide for Structured Tool Dispatch

## Bug Report #27: Missing log_tool_use Method

**Issue**: JSONLLogger is missing the `log_tool_use` method that the structured dispatch system expects.

**Error**:
```
'JSONLLogger' object has no attribute 'log_tool_use'
```

**Location**: src/gemini_repl/core/repl_structured.py:113-114

## Testing Examples

### 1. Enable Structured Dispatch

```bash
# Set environment variable
export GEMINI_STRUCTURED_DISPATCH=true

# Run the REPL
gmake run
```

### 2. Test Tool Detection

#### Should Trigger Tools:

```
# list_files tool
> what are the core config files for this repo
> show me all Python files in src/
> list the contents of the tests directory
> what files are in the current directory?

# read_file tool
> show me the contents of README.md
> what's in the Makefile?
> can you read pyproject.toml?
> let me see what's in src/gemini_repl/__init__.py

# write_file tool
> create a file called test.txt with "Hello World"
> write a Python script that prints the date
> save this code to example.py: def hello(): print("Hi")
```

#### Should NOT Trigger Tools:

```
> what is 2 + 2?
> explain how Python decorators work
> tell me a joke
> what's the capital of France?
> how do I use async/await in Python?
```

### 3. Verify Decision Engine

To see the decision reasoning, you can check the logs:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Watch the logs in another terminal
tail -f logs/gemini.log | jq '.'
```

### 4. Test Cache Behavior

```
# First query (should hit API)
> what files are in src/?

# Same query again (should use cache)
> what files are in src/?

# Check cache stats in logs
# Look for "Cache hit for query" or "Analyzing query" messages
```

### 5. Test Error Handling

```
# Try to read non-existent file
> read the file /does/not/exist.txt

# Try to write to protected location
> write to /etc/passwd

# Malformed queries
> read file but don't tell me which one
> write something somewhere
```

### 6. Feature Flag Testing

```bash
# Disable structured dispatch
export GEMINI_STRUCTURED_DISPATCH=false
gmake run
# Should fall back to standard REPL

# Enable structured dispatch
export GEMINI_STRUCTURED_DISPATCH=true
gmake run
# Should use two-stage dispatch
```

## Quick Fix for Bug #27

Add this method to `src/gemini_repl/utils/jsonl_logger.py`:

```python
def log_tool_use(self, tool_name: str, args: Dict[str, Any], result: Any):
    """Log tool usage."""
    self._write_log({
        "type": "tool_use",
        "tool": tool_name,
        "args": args,
        "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
        "session_id": self.session_manager.session_id,
        "timestamp": datetime.now().isoformat()
    })
```

## Expected Behavior

1. **With Structured Dispatch Enabled**:
   - Queries are analyzed first to determine if tools are needed
   - Only relevant queries trigger tool calls
   - Decision reasoning is logged
   - Cache reduces redundant API calls

2. **With Structured Dispatch Disabled**:
   - Falls back to standard REPL behavior
   - Direct tool calling without pre-analysis

## Debugging Tips

1. Check environment variables:
   ```bash
   env | grep GEMINI
   ```

2. Verify structured REPL is loaded:
   - Look for "Using StructuredGeminiREPL" in startup logs

3. Monitor decision engine:
   - Set LOG_LEVEL=DEBUG
   - Watch for "Analyzing query" messages

4. Test specific tools:
   ```python
   # In Python console
   from src.gemini_repl.tools.decision_engine import ToolDecisionEngine
   engine = ToolDecisionEngine()
   decision = engine.analyze_query("what files are in src?")
   print(decision)
   ```
