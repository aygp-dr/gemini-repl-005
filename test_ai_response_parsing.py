#!/usr/bin/env python3
"""Test how AI responses are parsed and handle common mistakes."""

import os
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🧪 Testing AI Response Parsing Issues")
print("=" * 50)

# Common AI response mistakes
ai_response_mistakes = [
    # Using 'path' instead of 'file_path'
    {
        "test": "AI uses 'path' instead of 'file_path'",
        "response": '{"requires_tool_call": true, "tool_name": "read_file", "path": "Makefile", "reasoning": "Reading Makefile"}'
    },
    # Missing required fields
    {
        "test": "Missing file_path for read_file",
        "response": '{"requires_tool_call": true, "tool_name": "read_file", "reasoning": "Reading file"}'
    },
    # Extra fields that might confuse
    {
        "test": "Extra fields in response",
        "response": '{"requires_tool_call": true, "tool_name": "read_file", "file_path": "test.txt", "path": "wrong.txt", "reasoning": "Which one?"}'
    },
    # Wrong types
    {
        "test": "Wrong type for boolean",
        "response": '{"requires_tool_call": "true", "tool_name": "read_file", "file_path": "test.txt", "reasoning": "String bool"}'
    },
    # Nested structure (AI might do this)
    {
        "test": "Nested parameters",
        "response": '{"requires_tool_call": true, "tool_name": "read_file", "parameters": {"file_path": "test.txt"}, "reasoning": "Nested params"}'
    },
]

print("\n1. Testing Pydantic parsing of AI responses...")
try:
    from gemini_repl.tools.tool_decision import ToolDecision
    
    for test_case in ai_response_mistakes:
        print(f"\n  Test: {test_case['test']}")
        print(f"  Response: {test_case['response'][:60]}...")
        
        try:
            # Parse JSON
            data = json.loads(test_case['response'])
            
            # Try to create ToolDecision
            decision = ToolDecision(**data)
            print(f"  ✅ Parsed successfully")
            print(f"     Valid: {decision.is_valid()}")
            print(f"     Args: {decision.to_tool_args()}")
            
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON error: {e}")
        except Exception as e:
            print(f"  ❌ Validation error: {type(e).__name__}: {str(e)[:80]}...")

except Exception as e:
    print(f"❌ Import failed: {e}")

print("\n2. Creating a robust parser...")

def parse_ai_tool_response(response_data: dict) -> dict:
    """Fix common AI response mistakes."""
    fixed = response_data.copy()
    
    # Fix path → file_path
    if 'path' in fixed and 'file_path' not in fixed:
        fixed['file_path'] = fixed.pop('path')
        print(f"  Fixed: 'path' → 'file_path'")
    
    # Handle nested parameters
    if 'parameters' in fixed and isinstance(fixed['parameters'], dict):
        params = fixed.pop('parameters')
        fixed.update(params)
        print(f"  Fixed: Flattened nested parameters")
    
    # Fix string booleans
    if 'requires_tool_call' in fixed and isinstance(fixed['requires_tool_call'], str):
        fixed['requires_tool_call'] = fixed['requires_tool_call'].lower() == 'true'
        print(f"  Fixed: String boolean → {fixed['requires_tool_call']}")
    
    # Ensure required fields exist
    if fixed.get('requires_tool_call') and fixed.get('tool_name'):
        tool = fixed['tool_name']
        
        if tool == 'read_file' and 'file_path' not in fixed:
            # Try to extract from reasoning or other fields
            if 'reasoning' in fixed:
                import re
                match = re.search(r'(?:read|show|display|get)\s+(?:the\s+)?(\S+)', fixed['reasoning'], re.I)
                if match:
                    fixed['file_path'] = match.group(1)
                    print(f"  Fixed: Extracted file_path from reasoning: {fixed['file_path']}")
    
    return fixed

print("\n3. Testing the robust parser...")
for test_case in ai_response_mistakes:
    print(f"\n  Test: {test_case['test']}")
    try:
        data = json.loads(test_case['response'])
        fixed_data = parse_ai_tool_response(data)
        
        decision = ToolDecision(**fixed_data)
        print(f"  ✅ Fixed and parsed successfully")
        print(f"     Args: {decision.to_tool_args()}")
        
    except Exception as e:
        print(f"  ❌ Still failed: {type(e).__name__}: {str(e)[:60]}...")

print("\n4. Proposed fix for decision_engine.py...")
print("""
Add this to _get_structured_decision method:

def _fix_ai_response(self, response_data: dict) -> dict:
    \"\"\"Fix common AI response mistakes.\"\"\"
    fixed = response_data.copy()
    
    # Fix path → file_path
    if 'path' in fixed and 'file_path' not in fixed:
        fixed['file_path'] = fixed.pop('path')
        logger.debug("Fixed AI response: 'path' → 'file_path'")
    
    # Handle nested parameters
    if 'parameters' in fixed and isinstance(fixed['parameters'], dict):
        params = fixed.pop('parameters')
        fixed.update(params)
        logger.debug("Fixed AI response: Flattened parameters")
    
    return fixed

Then in _get_structured_decision:
    # Parse response
    response_data = response.parsed
    
    # Fix common mistakes
    if isinstance(response_data, dict):
        response_data = self._fix_ai_response(response_data)
    
    return ToolDecision(**response_data)
""")
