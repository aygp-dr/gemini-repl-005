# Tool Dispatch Experiment Report

**Date**: 2025-01-19  
**Experiment**: Minimal Tool Dispatch Testing  
**Issue**: #26 - Tool dispatch inconsistency in REPL

## Executive Summary

Tested 45 queries across 4 categories to understand tool dispatch patterns with the minimal function set (list_files, read_file, write_file). Found 85.7% success rate for explicit file operations, 0% for ambiguous queries, and 20% for edge cases.

## Test Configuration

- **Model**: gemini-2.0-flash-exp
- **Temperature**: 0.1 (for consistency)
- **Rate Limiting**: 10 requests/minute with 6s delays
- **Tools**: list_files, read_file, write_file
- **Schema Type**: Pydantic models with `model_json_schema()`

## Results by Category

### 🔧 EXPECT TOOL (12/14 successful - 85.7%)

**Successful triggers**:
- "List all Python files" → `list_files`
- "Show me what's in the src directory" → `list_files`
- "Read the contents of README.org" → `read_file`
- "What's in the Makefile?" → `read_file`

**Failed to trigger**:
- "Show me the main entry point file" → No tool (too vague)
- "Read the changelog" → No tool (no explicit filename)

### ❓ AMBIGUOUS (0/5 successful - 0%)

All queries resulted in explanations without tool usage:
- "Explain the project structure"
- "What does this codebase do?"
- "How is logging implemented?"
- "What tools are available?"
- "Show me the error handling"

### ❌ NO TOOLS (0/10 successful - 0%)

Correctly avoided tools for pure generation:
- "Implement fibonacci in Scheme"
- "Explain monads"
- "Write a SQL query to find duplicate emails"
- "What's the time complexity of merge sort?"

### 🤔 EDGE CASES (2/10 successful - 20%)

**Successful**:
- "Save this code to experiments/temp/test.py: print('hello')" → `write_file`
- "Create a new file called experiments/temp/config.json with {}" → `write_file`

**Failed**:
- "Update README.md with installation instructions" → No tool
- "Add a comment to the main function" → No tool
- "Refactor the logger class" → No tool

## Key Findings

1. **Explicit is better**: Queries with exact file paths/names trigger tools reliably
2. **Pattern recognition**: The model looks for specific keywords like "list", "read", "show me", "what's in"
3. **Write operations need clarity**: Must include both filename AND content
4. **Ambiguity defaults to explanation**: When unsure, the model explains rather than explores

## Implementation Notes

### Pydantic vs FunctionDeclaration

Both approaches work:

```python
# Pydantic approach
class ReadFileParams(BaseModel):
    file_path: str = Field(description="Path to file")

tool_schema = ReadFileParams.model_json_schema()

# Direct approach
read_file_function = types.FunctionDeclaration(
    name="read_file",
    parameters={...}
)
```

The Pydantic approach is cleaner for validation but `FunctionDeclaration` is more direct.

## Recommendations

1. **Improve prompt engineering**: Add examples of when to use tools
2. **Tool descriptions**: Make them more explicit about trigger conditions
3. **System prompt**: Consider adding tool usage guidelines
4. **Fallback patterns**: When ambiguous, prompt for clarification

## Rate Limiting Observations

- Hit 10 req/min limit 4 times during testing
- 6-second delays between requests helped but still hit limits
- Consider implementing exponential backoff
- Migration to newer model suggested for higher quotas

## Next Steps

1. Test with improved tool descriptions
2. Implement system prompt for better tool usage
3. Add integration tests for common workflows
4. Document tool trigger patterns for users
