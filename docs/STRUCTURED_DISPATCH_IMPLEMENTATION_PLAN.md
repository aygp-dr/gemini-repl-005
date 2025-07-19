# Structured Tool Dispatch Implementation Plan

## Overview

Implement a two-stage tool dispatch system using structured output to achieve reliable tool calling in the Gemini REPL.

## Architecture

```
User Query → Decision Engine → Tool Execution → Response Generation
                ↓
         ToolDecision (Pydantic)
              ↓
         Cache Layer (optional)
```

## Implementation Phases

### Phase 1: Core Components

#### 1.1 ToolDecision Model (`src/gemini_repl/tools/tool_decision.py`)
```python
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

class ToolDecision(BaseModel):
    """Structured decision about tool usage."""
    requires_tool_call: bool
    tool_name: Optional[Literal["list_files", "read_file", "write_file"]] = None
    reasoning: str
    file_path: Optional[str] = None
    pattern: Optional[str] = None
    content: Optional[str] = None  # For write_file
    
    def to_tool_args(self) -> Dict[str, Any]:
        """Convert decision to tool arguments."""
        args = {}
        if self.file_path:
            args["path"] = self.file_path
        if self.pattern:
            args["pattern"] = self.pattern
        if self.content:
            args["content"] = self.content
        return args
```

#### 1.2 Decision Engine (`src/gemini_repl/tools/decision_engine.py`)
```python
class ToolDecisionEngine:
    """Analyzes queries to determine tool usage."""
    
    def __init__(self, client: GeminiClient):
        self.client = client
        self.cache = {}  # Simple in-memory cache
        
    def analyze_query(self, query: str) -> ToolDecision:
        """Analyze if query needs tools."""
        # Check cache first
        if query in self.cache:
            return self.cache[query]
            
        # Use structured output
        decision = self._get_structured_decision(query)
        
        # Cache for similar queries
        self.cache[query] = decision
        return decision
```

#### 1.3 Updated REPL Integration
- Modify `_handle_api_request` in `repl.py`
- Add decision step before tool execution
- Fall back to direct response if no tools needed

### Phase 2: Unit Tests

#### 2.1 Test ToolDecision (`tests/test_tool_decision.py`)
```python
def test_tool_decision_validation():
    """Test ToolDecision model validation."""
    # Valid decisions
    decision = ToolDecision(
        requires_tool_call=True,
        tool_name="read_file",
        reasoning="User wants to read a file",
        file_path="test.txt"
    )
    assert decision.tool_name == "read_file"
    
def test_to_tool_args():
    """Test conversion to tool arguments."""
    decision = ToolDecision(
        requires_tool_call=True,
        tool_name="write_file",
        reasoning="Creating file",
        file_path="test.txt",
        content="Hello"
    )
    args = decision.to_tool_args()
    assert args == {"path": "test.txt", "content": "Hello"}
```

#### 2.2 Test Decision Engine (`tests/test_decision_engine.py`)
```python
@patch('gemini_repl.core.api_client.GeminiClient')
def test_analyze_query(mock_client):
    """Test query analysis."""
    engine = ToolDecisionEngine(mock_client)
    
    # Mock structured response
    mock_response = MagicMock()
    mock_response.parsed = ToolDecision(
        requires_tool_call=True,
        tool_name="read_file",
        reasoning="User wants to read Makefile",
        file_path="Makefile"
    )
    mock_client.models.generate_content.return_value = mock_response
    
    decision = engine.analyze_query("Read the Makefile")
    assert decision.requires_tool_call
    assert decision.tool_name == "read_file"

def test_cache_behavior():
    """Test caching of decisions."""
    engine = ToolDecisionEngine(mock_client)
    
    # First call
    decision1 = engine.analyze_query("Read test.txt")
    
    # Second call should use cache
    decision2 = engine.analyze_query("Read test.txt")
    assert decision1 is decision2  # Same object
```

### Phase 3: Integration Tests

#### 3.1 REPL Integration (`tests/test_repl_structured_dispatch.py`)
```python
def test_repl_with_structured_dispatch():
    """Test REPL using structured dispatch."""
    repl = GeminiREPL()
    
    # Test file reading
    response = repl._handle_user_query("Read the README.org file")
    assert "tool: read_file" in repl.last_decision.reasoning
    
def test_no_tool_queries():
    """Test queries that don't need tools."""
    repl = GeminiREPL()
    
    response = repl._handle_user_query("Explain recursion")
    assert not repl.last_decision.requires_tool_call
```

#### 3.2 End-to-End Tests (`tests/test_e2e_structured.py`)
```python
def test_e2e_file_operations():
    """Test complete file operation workflow."""
    # Start REPL
    # Send "List files in src/"
    # Verify tool decision
    # Verify tool execution
    # Verify response formatting
```

### Phase 4: Performance & Reliability

#### 4.1 Cache Management
- LRU cache with size limit
- TTL for cached decisions
- Clear cache on context changes

#### 4.2 Error Handling
- Fallback to original behavior if decision fails
- Log decision failures for debugging
- Retry logic for transient errors

#### 4.3 Metrics
- Track decision accuracy
- Monitor cache hit rate
- Log decision latency

## Testing Strategy

### Unit Test Coverage
- [ ] ToolDecision model validation
- [ ] Decision engine logic
- [ ] Cache behavior
- [ ] Error handling
- [ ] Argument conversion

### Integration Test Coverage
- [ ] REPL integration
- [ ] Tool execution flow
- [ ] Multiple tool scenarios
- [ ] Error recovery
- [ ] Performance under load

### Manual Testing Checklist
- [ ] All README example queries work
- [ ] Complex multi-step queries
- [ ] Edge cases (empty queries, typos)
- [ ] Performance is acceptable
- [ ] No regressions in existing features

## Sign-off Criteria

### Functional Requirements
- [ ] 95%+ accuracy on test queries (up from ~20%)
- [ ] All three tools (list, read, write) work reliably
- [ ] No false positives (tools called when not needed)
- [ ] Graceful fallback on errors

### Non-Functional Requirements
- [ ] Decision latency < 2 seconds
- [ ] Cache hit rate > 50% for common queries
- [ ] No memory leaks from cache
- [ ] Clear logging for debugging

### Documentation
- [ ] API documentation updated
- [ ] User guide includes examples
- [ ] Architecture diagram added
- [ ] Troubleshooting guide

### Code Quality
- [ ] All tests passing
- [ ] Code coverage > 90%
- [ ] Type hints complete
- [ ] Linting clean
- [ ] Security review passed

## Rollout Plan

1. **Feature Flag**: Add `GEMINI_STRUCTURED_DISPATCH` env var
2. **Canary Testing**: Enable for development first
3. **Gradual Rollout**: Monitor metrics, adjust as needed
4. **Full Release**: Update default behavior in v0.2.0

## Risk Mitigation

1. **Performance Impact**: Cache layer minimizes API calls
2. **API Changes**: Abstract decision logic for easy updates
3. **Backwards Compatibility**: Feature flag for rollback
4. **User Confusion**: Clear documentation and examples

## Success Metrics

- Tool dispatch success rate: 20% → 95%+
- User satisfaction: Fewer "tool not triggered" complaints
- Developer confidence: Reliable self-hosting capability
- Performance: Minimal latency increase (<500ms)
