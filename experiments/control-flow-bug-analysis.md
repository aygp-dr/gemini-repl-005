# Control Flow Bug Analysis: Tool Call Chain Breaking

## Bug Description

**Issue #28**: Structured REPL only executes first tool, doesn't chain subsequent tool calls

When asked to "summarize this codebase", the structured REPL would:
1. Correctly identify that `list_files` tool is needed
2. Execute `list_files` and get results
3. Send results to AI
4. AI responds with instructions for user instead of executing more tools

## Root Cause

The structured REPL was missing the `_handle_tool_calls` check after receiving the AI response. The base REPL has this logic, but it wasn't included in the structured version.

### Broken Flow (Before Fix)

```python
# In StructuredGeminiREPL._handle_api_request()
if decision.requires_tool_call:
    tool_result = self._execute_structured_tool(decision)  # ✅ Executes first tool
    enhanced_prompt = self._create_tool_enhanced_prompt(...)
    self.context.messages[-1]["content"] = enhanced_prompt
    response = self.client.send_message(self.context.get_messages())
    
    # ❌ Missing: Check if response contains more tool calls!
    # Just extracts and displays the text
    response_text = self._extract_response_text(response)
```

### Fixed Flow (After Fix)

```python
# In StructuredGeminiREPL._handle_api_request()
if decision.requires_tool_call:
    tool_result = self._execute_structured_tool(decision)  # ✅ Executes first tool
    enhanced_prompt = self._create_tool_enhanced_prompt(...)
    self.context.messages[-1]["content"] = enhanced_prompt
    response = self.client.send_message(self.context.get_messages())
    
    # ✅ NEW: Check for additional tool calls
    final_response = self._handle_tool_calls(response, user_input)
    
    response_text = self._extract_response_text(final_response)
```

## Example Trace

### User Input
```
> summarize this codebase
```

### Before Fix (Broken Behavior)
```
1. ToolDecisionEngine.analyze_query() → requires list_files
2. Execute list_files → returns file list
3. Send to AI with file list
4. AI responds: "To gain a deeper understanding, you should now:
   1. Read the README.org file...
   2. Read the Makefile..."
5. ❌ Stops here - user must manually request each file
```

### After Fix (Correct Behavior)
```
1. ToolDecisionEngine.analyze_query() → requires list_files
2. Execute list_files → returns file list
3. Send to AI with file list
4. AI responds with function_call for read_file("README.org")
5. _handle_tool_calls() executes read_file
6. AI responds with function_call for read_file("pyproject.toml")
7. _handle_tool_calls() executes read_file
8. AI responds with function_call for read_file("src/gemini_repl/core/repl.py")
9. _handle_tool_calls() executes read_file
10. AI generates final summary: "This codebase is a Python REPL that integrates..."
```

## Testing the Fix

To verify the fix works:

```bash
# Test that should now work automatically
$ python -m gemini_repl
> summarize this codebase

# Should see:
🔧 Using tool: list_files
📂 Listing files...
🔧 Executing tool: read_file
✅ Tool result: # Gemini REPL...
🔧 Executing tool: read_file
✅ Tool result: [project]...
🔧 Executing tool: read_file
✅ Tool result: class GeminiREPL...

# Final summary appears without user intervention
```

## Key Lessons

1. **Tool Chaining is Critical**: LLMs often need multiple tool calls to complete complex tasks
2. **Test End-to-End Flows**: Unit tests passed but the integration flow was broken
3. **Check Base Class Logic**: When extending classes, ensure all critical logic is preserved
4. **User Experience**: The difference between "telling what to do" vs "doing it" is huge

## Implementation Details

The `_handle_tool_calls` method (inherited from base REPL) handles:
- Checking response for function_call parts
- Executing each tool call
- Sending results back to AI
- Repeating until no more tool calls

This creates a "trampoline" effect where the AI can chain multiple operations together to accomplish complex tasks.
