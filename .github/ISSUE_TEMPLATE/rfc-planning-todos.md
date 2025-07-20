---
name: "RFC: Planning and Todo Integration"
about: Proposal to add planning and todo tracking to tool dispatch
title: "RFC: Add planning and todo list generation to structured tool dispatch"
labels: enhancement, rfc, tools
assignees: ''
---

## Summary

Enhance the structured tool dispatch system to include automatic planning and todo list generation as part of the initial analysis phase. This would create a more transparent and traceable execution flow.

## Motivation

When the AI receives complex queries like "summarize this codebase", it currently jumps straight into tool execution. This RFC proposes adding a planning phase that would:

1. Generate a high-level plan
2. Create specific todos with tool calls
3. Execute todos with status tracking
4. Provide execution trace in response

## Proposed Changes

### 1. Enhanced ToolDecision Model
```python
class ToolDecision(BaseModel):
    # Existing fields...
    
    # New planning fields
    requires_planning: bool = False
    plan: Optional[List[str]] = None
    todos: Optional[List[TodoItem]] = None
```

### 2. Example Flow
```
> summarize this codebase

📋 Execution Plan:
  1. List all files to understand structure
  2. Read key documentation files
  3. Read main source files
  4. Generate comprehensive summary

📝 Todo List:
  □ List project files
  □ Read README if exists
  □ Read package configuration

▶️  Executing: List project files
✅ List project files - Complete

[... execution continues ...]
```

## Benefits

- **Transparency**: Users see the plan before execution
- **Debuggability**: Failed steps are clearly marked
- **Predictability**: AI's approach is explicit
- **Traceability**: Full execution history

## Implementation Approach

1. **Phase 1**: Basic planning with sequential execution
2. **Phase 2**: Enhanced tracking and failure handling  
3. **Phase 3**: Interactive plans and parallel execution

## Questions for Discussion

1. Should all tool usage include planning or only complex queries?
2. Should users be able to modify plans before execution?
3. How detailed should todos be?
4. Should plans be cached/reused?

## Related Issues

- #26 - Tool dispatch inconsistency (solved with structured dispatch)
- #28 - Tool chaining bug (fixed)

## Full RFC

See [docs/RFC-planning-todos-dispatch.md](../../docs/RFC-planning-todos-dispatch.md) for complete details.

---

**Note**: This is a proposal for discussion. Implementation should not begin until consensus is reached on the approach.
