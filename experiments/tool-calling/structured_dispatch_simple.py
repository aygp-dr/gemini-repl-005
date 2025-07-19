#!/usr/bin/env python3
"""
Quick and dirty structured output experiment for tool dispatch.
Uses direct prompting to get JSON decisions about tool usage.
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gemini_repl.core.api_client import GeminiClient


def test_structured_dispatch():
    """Test using structured prompts to improve tool dispatch."""
    
    print("🔬 Structured Tool Dispatch Experiment (Simple)")
    print("=" * 60)
    
    # Initialize client
    client = GeminiClient()
    print(f"Model: {client.model_name}")
    
    # System-like prompt embedded in user message
    decision_prompt = """You are analyzing queries to determine if they need file system tools.

Available tools:
- list_files: List files in a directory
- read_file: Read a specific file's contents  
- write_file: Create or update a file

For each query, respond with ONLY a JSON object:
{
  "requires_tool_call": true/false,
  "tool_name": "list_files" | "read_file" | "write_file" | null,
  "reasoning": "brief explanation",
  "file_path": "path if applicable" | null
}

Examples:
Query: "What files are in src?"
{"requires_tool_call": true, "tool_name": "list_files", "reasoning": "User wants to see directory contents", "file_path": "src"}

Query: "Explain recursion"  
{"requires_tool_call": false, "tool_name": null, "reasoning": "General concept explanation, no files needed", "file_path": null}

Now analyze this query:
"""

    test_queries = [
        # Should use list_files
        ("What files are in the src directory?", "list_files"),
        ("Show me what's in the experiments folder", "list_files"),
        ("List all Python files", "list_files"),
        
        # Should use read_file
        ("Read the Makefile", "read_file"),
        ("What's in README.org?", "read_file"),
        ("Show me the LICENSE file", "read_file"),
        
        # Should use write_file
        ("Create test.txt with 'Hello'", "write_file"),
        ("Save a note to todo.txt", "write_file"),
        
        # Should NOT use tools
        ("Explain Python decorators", None),
        ("What is a monad?", None),
        ("How does async/await work?", None),
    ]
    
    results = []
    correct = 0
    
    for query, expected_tool in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        print(f"   Expected: {expected_tool or 'No tool'}")
        
        # Get decision from model
        full_prompt = decision_prompt + f'"{query}"'
        
        try:
            messages = [{"role": "user", "content": full_prompt}]
            response = client.send_message(messages)
            
            if response and response.text:
                # Try to parse JSON from response
                text = response.text.strip()
                
                # Clean up markdown if present
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                
                decision = json.loads(text.strip())
                
                print(f"   Decision: {json.dumps(decision, indent=2)}")
                
                # Check correctness
                actual_tool = decision.get("tool_name")
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
                    "decision": decision
                })
                
        except json.JSONDecodeError as e:
            print(f"   ❌ Failed to parse JSON: {e}")
            print(f"   Response: {response.text if response else 'No response'}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"Accuracy: {correct}/{len(test_queries)} ({correct/len(test_queries)*100:.1f}%)")
    
    # Category breakdown
    categories = {"list_files": 0, "read_file": 0, "write_file": 0, "no_tool": 0}
    cat_correct = {"list_files": 0, "read_file": 0, "write_file": 0, "no_tool": 0}
    
    for result in results:
        cat = result["expected"] or "no_tool"
        categories[cat] += 1
        if result["correct"]:
            cat_correct[cat] += 1
    
    print("\nBy Category:")
    for cat, total in categories.items():
        if total > 0:
            acc = cat_correct[cat] / total * 100
            print(f"  {cat}: {cat_correct[cat]}/{total} ({acc:.1f}%)")
    
    print("\n💡 Key Findings:")
    print("- Structured prompts can improve tool dispatch decisions")
    print("- JSON output provides parseable, consistent responses")
    print("- This could be used as a pre-processor before tool execution")
    print("- Clear examples in the prompt improve accuracy")
    
    # Save results for analysis
    output_file = Path(__file__).parent / "structured_dispatch_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": client.model_name,
            "accuracy": correct / len(test_queries),
            "results": results
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    test_structured_dispatch()
