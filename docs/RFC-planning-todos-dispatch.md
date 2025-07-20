# RFC: Planning and Todo List Integration in Tool Dispatch System

## Summary

Enhance the structured tool dispatch system to include automatic planning and todo list generation as part of the initial analysis phase. This would create a more transparent and traceable execution flow.

## Motivation

Currently, when the AI receives a complex query like "summarize this codebase", it:
1. Analyzes if tools are needed
2. Executes tools one by one
3. Provides a response

This RFC proposes adding an intermediate planning step that would:
1. Analyze the query
2. **Generate a plan with todos**
3. Execute tools according to the plan
4. Track completion of todos
5. Provide a response with execution trace

## Proposed Implementation

### 1. Enhanced ToolDecision Model

```python
class ToolDecision(BaseModel):
    requires_tool_call: bool
    tool_name: Optional[str] = None
    reasoning: str
    
    # New fields for planning
    requires_planning: bool = False
    plan: Optional[List[str]] = None
    todos: Optional[List[TodoItem]] = None

class TodoItem(BaseModel):
    id: int
    description: str
    tool_name: Optional[str]
    args: Optional[Dict[str, Any]]
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result_summary: Optional[str] = None
```

### 2. Planning Prompt Enhancement

Update the decision engine prompt to include planning:

```python
DECISION_PROMPT = """You are a tool dispatch analyzer with planning capabilities.

When analyzing complex queries that require multiple steps:
1. Set requires_planning=true
2. Generate a plan list with high-level steps
3. Generate todos with specific tool calls

Example for "summarize this codebase":
{
    "requires_tool_call": true,
    "requires_planning": true,
    "tool_name": "list_files",
    "reasoning": "Need to understand project structure first",
    "plan": [
        "List all files to understand structure",
        "Read key documentation files (README, etc)",
        "Read main source files",
        "Analyze dependencies",
        "Generate comprehensive summary"
    ],
    "todos": [
        {
            "id": 1,
            "description": "List project files",
            "tool_name": "list_files",
            "args": {"pattern": "*"}
        },
        {
            "id": 2,
            "description": "Read README if exists",
            "tool_name": "read_file",
            "args": {"file_path": "README.md"}
        },
        {
            "id": 3,
            "description": "Read package configuration",
            "tool_name": "read_file",
            "args": {"file_path": "pyproject.toml"}
        }
    ]
}
"""
```

### 3. Global Context Integration

Add planning context to the REPL:

```python
class StructuredGeminiREPL(GeminiREPL):
    def __init__(self, ...):
        super().__init__(...)
        self.current_plan: Optional[List[str]] = None
        self.current_todos: List[TodoItem] = []
        self.execution_trace: List[Dict[str, Any]] = []
```

### 4. Execution Flow

```python
def _handle_api_request(self, user_input: str):
    # Step 1: Analyze and plan
    decision = self.decision_engine.analyze_query(user_input)
    
    if decision.requires_planning:
        self.current_plan = decision.plan
        self.current_todos = decision.todos
        
        # Display plan to user
        self._display_plan(decision.plan, decision.todos)
        
        # Execute todos in sequence
        for todo in self.current_todos:
            self._execute_todo(todo)
            
        # Generate final response with context of all executions
        response = self._generate_summary_response(user_input)
    else:
        # Simple single-tool execution (current behavior)
        ...
```

### 5. Visual Feedback

```python
def _display_plan(self, plan: List[str], todos: List[TodoItem]):
    print("\n📋 Execution Plan:")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step}")
    
    print("\n📝 Todo List:")
    for todo in todos:
        print(f"  □ {todo.description}")

def _execute_todo(self, todo: TodoItem):
    print(f"\n▶️  Executing: {todo.description}")
    todo.status = "in_progress"
    
    try:
        result = execute_tool(todo.tool_name, **todo.args)
        todo.status = "completed"
        todo.result_summary = self._summarize_result(result)
        print(f"✅ {todo.description} - Complete")
    except Exception as e:
        todo.status = "failed"
        print(f"❌ {todo.description} - Failed: {e}")
```

## Benefits

1. **Transparency**: Users see the execution plan before it happens
2. **Traceability**: Each step is tracked with status and results
3. **Debuggability**: Failed todos are clearly marked
4. **Predictability**: AI's approach is explicit and reviewable
5. **Interruptibility**: Could allow users to modify plan before execution

## Example Output

```
> summarize this codebase

📋 Execution Plan:
  1. List all files to understand structure
  2. Read key documentation files (README, etc)
  3. Read main source files
  4. Analyze dependencies
  5. Generate comprehensive summary

📝 Todo List:
  □ List project files
  □ Read README if exists
  □ Read package configuration
  □ Read main Python files
  □ Check for tests

▶️  Executing: List project files
🔧 Using tool: list_files
📂 Listing files...
✅ List project files - Complete

▶️  Executing: Read README if exists
🔧 Using tool: read_file
📄 Reading: README.md
✅ Read README if exists - Complete

[... continues through todos ...]

📊 Summary based on analysis:
This is a Python REPL project that integrates with Google's Gemini AI...
```

## Future Enhancements

1. **Interactive Planning**: Allow users to modify the plan before execution
2. **Parallel Execution**: Execute independent todos concurrently
3. **Plan Caching**: Cache plans for similar queries
4. **Plan Templates**: Pre-defined plans for common operations
5. **Execution History**: Store and replay successful plans

## Implementation Phases

### Phase 1: Basic Planning (MVP)
- Add planning fields to ToolDecision
- Update prompt to generate plans
- Display plan before execution
- Sequential todo execution

### Phase 2: Enhanced Tracking
- Add execution trace
- Status updates during execution
- Result summarization
- Failure handling

### Phase 3: Advanced Features
- Interactive plan modification
- Parallel execution
- Plan caching
- Templates

## Questions for Discussion

1. Should plans be generated for ALL tool usage or only complex multi-step operations?
2. Should users be able to approve/modify plans before execution?
3. How detailed should todos be? Every tool call or just major steps?
4. Should we persist plans for learning/improvement?
5. How do we handle dynamic plans that need adjustment based on results?

## Alternative Approaches

1. **Implicit Planning**: Keep plans internal, only show progress
2. **Post-Execution Trace**: Show what was done after completion
3. **Streaming Plans**: Generate todos as needed rather than upfront
4. **Plan-Free Progress**: Just show current operation without full plan

## Conclusion

Adding planning and todo tracking to the dispatch system would make the AI's problem-solving process more transparent and debuggable. It aligns with the tool-first philosophy while providing users with visibility into the execution strategy.
