# Control Flow Analysis & Automation Recommendations

**Date:** 2025-07-19  
**Observer:** Control Flow Analyst  
**Subject:** Deep dive into Gemini REPL control flow and tooling recommendations

## Control Flow Summary

### Main Execution Path
```
__main__.py → GeminiREPL.__init__() → repl.run() → Event Loop
                    ↓
    [Initialize: Logger, Context, Session, API Client, Tools]
                    ↓
    While running:
        → Get input → Route (command/API) → Process → Display → Log
```

### Critical Flow Points

1. **User Input → API Request**
   - `_handle_api_request()` - Main orchestrator
   - Context adds message → API call → Tool handling → Response processing

2. **Tool Execution Flow**
   - API returns function_call → `execute_tool()` → Sandboxed execution → Result

3. **Multi-Layer Logging**
   - Logger (JSON) → JSONLLogger (Session) → SessionManager (Threading)

## Automated Control Flow Analysis Tools

### 1. **Static Analysis Tools**

#### Python-Specific
```bash
# Call graph generation
pip install pyan3
pyan3 src/**/*.py --dot > callgraph.dot
dot -Tpng callgraph.dot -o callgraph.png

# Control flow visualization
pip install py2cfg
py2cfg src/gemini_repl/core/repl.py --cfg > repl_cfg.png

# Code complexity analysis
pip install mccabe
python -m mccabe --min 10 src/gemini_repl/**/*.py
```

#### Generic Tools
```bash
# Dependency cruiser (with Python plugin)
npm install -g dependency-cruiser
depcruise --include-only "^src" --output-type dot src | dot -T svg > dependencies.svg

# CodeQL for advanced analysis
# Create .github/codeql/queries/python/control-flow.ql
```

### 2. **Dynamic Analysis Tools**

#### Execution Tracing
```python
# Add to experiments/tracing/trace_execution.py
import sys
import trace

# Create a Trace object
tracer = trace.Trace(
    count=1,        # Count number of times each line is executed
    trace=1,        # Print each line as it's executed
    countfuncs=1,   # Count functions
    countcallers=1  # Track calling relationships
)

# Run the REPL with tracing
tracer.run('from gemini_repl.__main__ import main; main()')

# Generate report
r = tracer.results()
r.write_results(show_missing=True, coverdir='trace_results')
```

#### Coverage-Based Flow Analysis
```bash
# Generate coverage with branch tracking
pytest --cov=src --cov-branch --cov-report=html tests/

# Visualize with coverage.py
coverage run -m pytest tests/
coverage html --show-contexts
```

### 3. **Runtime Flow Monitoring**

#### OpenTelemetry Integration
```python
# Add to src/gemini_repl/utils/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add spans to key methods
@tracer.start_as_current_span("handle_api_request")
def _handle_api_request(self, user_input: str):
    span = trace.get_current_span()
    span.set_attribute("user_input_length", len(user_input))
    # ... rest of method
```

## Contract/Schema Drift Detection

### 1. **Static Type Checking**

```bash
# Strict mypy configuration
# mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True
```

### 2. **Runtime Contract Validation**

#### Pydantic Integration
```python
# Add to src/gemini_repl/models/contracts.py
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional

class GeminiResponse(BaseModel):
    candidates: List[Dict[str, Any]]
    usage_metadata: Optional[Dict[str, int]]
    
    @validator('candidates')
    def validate_candidates(cls, v):
        if not v:
            raise ValueError("Empty candidates list")
        return v

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]
    
    @validator('name')
    def validate_tool_name(cls, v):
        allowed = ['read_file', 'write_file', 'list_files', 'search_code']
        if v not in allowed:
            raise ValueError(f"Unknown tool: {v}")
        return v
```

#### JSON Schema Validation
```python
# Add to src/gemini_repl/utils/schema_validator.py
import jsonschema

MESSAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "enum": ["user", "assistant", "model"]},
        "content": {"type": "string"}
    },
    "required": ["role", "content"]
}

def validate_message(message: dict):
    jsonschema.validate(message, MESSAGE_SCHEMA)
```

### 3. **API Contract Testing**

```python
# Add to tests/test_api_contracts.py
import pytest
from schemathesis import from_dict

# Define API schema
api_schema = {
    "openapi": "3.0.0",
    "info": {"title": "Gemini API", "version": "1.0.0"},
    "paths": {
        "/generate": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "contents": {"type": "array"},
                                    "model": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

schema = from_dict(api_schema)

@schema.parametrize()
def test_api_contract(case):
    response = case.call()
    case.validate_response(response)
```

## Recommended Implementation Plan

### Phase 1: Immediate Additions
1. Add `py2cfg` to generate control flow graphs
2. Implement Pydantic models for API responses
3. Add correlation IDs to trace requests

### Phase 2: Monitoring
1. Add OpenTelemetry for distributed tracing
2. Implement Prometheus metrics for key operations
3. Create Grafana dashboard for flow visualization

### Phase 3: Advanced Analysis
1. Set up CodeQL for security and flow analysis
2. Implement property-based testing with Hypothesis
3. Add mutation testing to verify test coverage

## Key Insights

1. **Control Flow Complexity**: The main event loop is straightforward, but tool execution adds branching
2. **Schema Drift Risk**: High at API boundaries - no validation currently
3. **Observability Gap**: Limited visibility into actual execution paths
4. **Test Coverage**: Good unit tests but missing integration flow tests

## BPL Connection

The control flow analysis reveals we've built a practical "strange loop" - the REPL can modify its own code through tools, creating the self-reference that Hofstadter explores. The Observer analyzing the Builder analyzing the code is a real-world tangled hierarchy!
