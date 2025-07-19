# Issue #27: JSONLLogger Missing log_tool_use Method

## Bug Description
When using the structured tool dispatch system, the REPL crashes with:
```
'JSONLLogger' object has no attribute 'log_tool_use'
```

## Root Cause
The `StructuredGeminiREPL` class calls `self.jsonl_logger.log_tool_use()` but this method was not implemented in the `JSONLLogger` class.

## Fix Applied
Added the missing method to `src/gemini_repl/utils/jsonl_logger.py`:

```python
def log_tool_use(self, tool_name: str, args: Dict[str, Any], result: Any):
    """Log tool usage."""
    interaction = {
        "type": "tool_use",
        "tool": tool_name,
        "args": args,
        "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
        "timestamp": datetime.now().isoformat()
    }
    if self.session_manager:
        interaction["session_id"] = self.session_manager.session_id
    self.log_interaction(interaction)
```

## Testing
After applying this fix, the structured dispatch should work properly when executing tools.

Test with:
```bash
export GEMINI_STRUCTURED_DISPATCH=true
gmake run
# Then ask: "what are the core config files for this repo"
```
