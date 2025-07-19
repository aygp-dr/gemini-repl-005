# Structured Dispatch Fixes Summary

## Issues Fixed

### 1. Bug #27: Missing log_tool_use Method
**Problem**: `JSONLLogger` was missing the `log_tool_use` method
**Fix**: Added method to `src/gemini_repl/utils/jsonl_logger.py:68-79`

### 2. AI Response Parameter Mismatch
**Problem**: AI returns `path` instead of `file_path` for read_file tool
**Fix**: 
- Updated decision prompt to emphasize correct parameter names
- Added `_fix_ai_response` method to handle common AI mistakes
- Fixed in `src/gemini_repl/tools/decision_engine.py:143-163`

### 3. Tool Parameter Mapping
**Problem**: ToolDecision was mapping to wrong parameter names
**Fix**: Updated `to_tool_args()` in `src/gemini_repl/tools/tool_decision.py:19-41`

### 4. Better Error Handling
**Problem**: Cryptic errors when parameters don't match
**Fix**: Added helpful error messages in `src/gemini_repl/core/repl_structured.py:139-156`

## How It Works Now

### Query Flow
1. User: "what's in the makefile"
2. Decision Engine analyzes query
3. AI might return: `{"path": "Makefile", ...}` (wrong!)
4. `_fix_ai_response` converts: `path` → `file_path`
5. ToolDecision validates and maps parameters correctly
6. Tool executes with correct arguments
7. Result logged without errors

### Robustness Features

#### AI Response Fixes
- `path` → `file_path` conversion
- Nested parameter flattening
- String boolean conversion
- Missing field detection

#### Parameter Validation
- Each tool validates required fields
- Clear error messages for mismatches
- Defensive parameter mapping

#### Logging
- Tool usage logged with JSONLLogger
- Debug logging for troubleshooting
- Session tracking

## Testing Instructions

### Enable Structured Dispatch
```bash
export GEMINI_STRUCTURED_DISPATCH=true
gmake run
```

### Test Queries

#### Should Use Tools:
```
> what are the core config files for this repo
> show me the contents of Makefile
> list all Python files
> create test.txt with "Hello World"
```

#### Should NOT Use Tools:
```
> what is 2 + 2?
> explain Python decorators
> how does async/await work?
```

### Verify Fixes

1. **Parameter Fix**: Query should work even if AI uses 'path'
2. **Error Messages**: Clear feedback if something goes wrong
3. **Logging**: Check `logs/gemini.log` for tool usage

## Files Modified

1. `src/gemini_repl/utils/jsonl_logger.py` - Added log_tool_use
2. `src/gemini_repl/tools/decision_engine.py` - Fixed prompt & AI response handling
3. `src/gemini_repl/tools/tool_decision.py` - Fixed parameter mapping
4. `src/gemini_repl/core/repl_structured.py` - Better error handling

## Known Limitations

- Still depends on AI following instructions (improved with prompt updates)
- MyPy has some type warnings (unrelated to functionality)
- Requires google-genai SDK properly configured

## Next Steps

1. Monitor AI responses to see if more parameter variations occur
2. Consider adding more tool types
3. Improve caching for repeated queries
4. Add metrics for tool usage patterns
