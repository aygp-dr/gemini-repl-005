#!/usr/bin/env python3
"""
Structured tool dispatch experiment using google-genai SDK.
Tests if structured output can improve tool dispatch reliability.
"""

import os
from google import genai
from pydantic import BaseModel
from typing import Optional, Literal

# Define structured output for tool decisions
class ToolDecision(BaseModel):
    """Decision about whether a query needs a tool call."""
    requires_tool_call: bool
    tool_name: Optional[Literal["list_files", "read_file", "write_file"]] = None
    reasoning: str
    file_path: Optional[str] = None
    pattern: Optional[str] = None


def test_tool_decision(query: str) -> ToolDecision:
    """Test if a query needs tool dispatch using structured output."""
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    system_context = """You are a tool dispatch analyzer for a file system REPL.

Available tools:
1. list_files - List files in a directory or matching a pattern
2. read_file - Read the contents of a specific file
3. write_file - Create or update a file with content

Analyze the user's query and determine if it requires a tool call.

Examples:
- "What files are in src?" → requires list_files tool
- "Explain recursion" → no tool needed, just explanation
- "Read the Makefile" → requires read_file tool
- "Create test.txt" → requires write_file tool
"""
    
    prompt = f"{system_context}\n\nUser query: {query}\n\nAnalyze this query:"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ToolDecision,
            "temperature": 0.1,  # Low temperature for consistency
        },
    )
    
    return response.parsed


def run_experiment():
    """Run the structured dispatch experiment."""
    
    print("🔬 Structured Tool Dispatch Experiment")
    print("=" * 60)
    print("Using google-genai with Pydantic structured output")
    print("=" * 60)
    
    # Test queries with expected outcomes
    test_cases = [
        # Should trigger list_files
        ("What files are in the src directory?", "list_files"),
        ("List all Python files in tests/", "list_files"),
        ("Show me what's in the experiments folder", "list_files"),
        ("ls -la src/", "list_files"),
        
        # Should trigger read_file
        ("Read the Makefile", "read_file"),
        ("What's in README.org?", "read_file"),
        ("Show me the contents of pyproject.toml", "read_file"),
        ("cat LICENSE", "read_file"),
        
        # Should trigger write_file
        ("Create a file called test.txt with 'Hello World'", "write_file"),
        ("Write 'TODO: fix this' to notes.txt", "write_file"),
        ("Save this to config.json: {}", "write_file"),
        
        # Should NOT trigger tools
        ("Explain how recursion works", None),
        ("What is the difference between map and filter?", None),
        ("Write a haiku about programming", None),
        ("How does Python's GIL work?", None),
    ]
    
    results = []
    correct = 0
    
    for query, expected_tool in test_cases:
        print(f"\n📝 Query: \"{query}\"")
        print(f"   Expected: {expected_tool or 'No tool'}")
        
        try:
            decision = test_tool_decision(query)
            
            print(f"   Decision: {'✅ Tool needed' if decision.requires_tool_call else '❌ No tool'}")
            if decision.tool_name:
                print(f"   Tool: {decision.tool_name}")
            print(f"   Reasoning: {decision.reasoning}")
            
            # Check correctness
            actual_tool = decision.tool_name if decision.requires_tool_call else None
            is_correct = actual_tool == expected_tool
            
            if is_correct:
                print("   ✅ Correct!")
                correct += 1
            else:
                print(f"   ❌ Incorrect - got {actual_tool}")
            
            results.append({
                "query": query,
                "expected": expected_tool,
                "actual": actual_tool,
                "correct": is_correct,
                "decision": decision.dict()
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "query": query,
                "expected": expected_tool,
                "actual": None,
                "correct": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    accuracy = correct / len(test_cases) * 100
    print(f"Overall Accuracy: {correct}/{len(test_cases)} ({accuracy:.1f}%)")
    
    # Category breakdown
    for tool in ["list_files", "read_file", "write_file", None]:
        tool_cases = [r for r in results if r["expected"] == tool]
        tool_correct = sum(1 for r in tool_cases if r["correct"])
        if tool_cases:
            tool_acc = tool_correct / len(tool_cases) * 100
            tool_name = tool or "no_tool"
            print(f"{tool_name}: {tool_correct}/{len(tool_cases)} ({tool_acc:.1f}%)")
    
    print("\n💡 Implementation Idea:")
    print("1. Add this structured decision step before tool execution")
    print("2. If requires_tool_call=true, dispatch to appropriate tool")
    print("3. This could significantly improve tool dispatch reliability")
    print("4. Can be cached for similar queries to reduce API calls")
    
    return results


def demo_integration():
    """Demo how this could integrate with the REPL."""
    
    print("\n\n🔧 Integration Demo")
    print("=" * 60)
    
    query = "Read the Makefile and explain what the test target does"
    print(f"User: {query}")
    
    # Step 1: Analyze if tool is needed
    decision = test_tool_decision(query)
    print(f"\n1️⃣ Tool Analysis:")
    print(f"   Needs tool: {decision.requires_tool_call}")
    print(f"   Tool: {decision.tool_name}")
    print(f"   File: {decision.file_path}")
    
    # Step 2: Execute tool if needed
    if decision.requires_tool_call and decision.tool_name == "read_file":
        print(f"\n2️⃣ Executing: read_file('{decision.file_path}')")
        print("   [Tool would read Makefile contents here]")
        
        # Step 3: Process with context
        print(f"\n3️⃣ Processing with file contents...")
        print("   [AI would explain the test target based on actual file]")
    else:
        print("\n2️⃣ No tool needed, generating response directly")


if __name__ == "__main__":
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        exit(1)
    
    try:
        results = run_experiment()
        demo_integration()
        
        # Save results
        import json
        with open("structured_decision_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n\nResults saved to structured_decision_results.json")
        
    except Exception as e:
        print(f"\n❌ Experiment failed: {e}")
        import traceback
        traceback.print_exc()
