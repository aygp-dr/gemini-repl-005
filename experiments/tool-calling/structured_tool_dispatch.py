#!/usr/bin/env python3
"""
Experiment: Use structured output to determine if tool calls are needed.
Quick and dirty test to see if we can improve tool dispatch reliability.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types


class ToolDecision(BaseModel):
    """Structured response for tool call decisions."""
    requires_tool_call: bool
    tool_name: Optional[str] = None
    reasoning: str
    file_path: Optional[str] = None
    pattern: Optional[str] = None


class ToolDispatchExperiment:
    """Test structured output for tool dispatch decisions."""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-lite"  # Fast model for experiments
        
        # System prompt for tool decision making
        self.system_prompt = """You are a tool dispatch assistant for a file system REPL.

Available tools:
1. list_files - List files in a directory or matching a pattern
2. read_file - Read the contents of a specific file
3. write_file - Create or update a file with content

Your task: Analyze the user's request and determine if it requires a tool call.

Return a structured response with:
- requires_tool_call: true if a tool is needed, false otherwise
- tool_name: which tool to use (if any)
- reasoning: brief explanation of your decision
- file_path: the file/directory path (if applicable)
- pattern: file pattern for list_files (if applicable)

Examples:
- "What files are in src?" → requires_tool_call: true, tool_name: "list_files", file_path: "src"
- "Explain recursion" → requires_tool_call: false, reasoning: "General explanation, no file access needed"
- "Read the Makefile" → requires_tool_call: true, tool_name: "read_file", file_path: "Makefile"
"""

    def test_tool_decision(self, user_query: str) -> ToolDecision:
        """Test if a query needs tool dispatch using structured output."""
        
        prompt = f"{self.system_prompt}\n\nUser query: {user_query}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": ToolDecision,
                    "temperature": 0.1,  # Low temperature for consistency
                }
            )
            
            return response.parsed
            
        except Exception as e:
            print(f"Error: {e}")
            return ToolDecision(
                requires_tool_call=False,
                reasoning=f"Error in decision: {str(e)}"
            )

    def run_experiments(self):
        """Run experiments on various queries."""
        
        test_queries = [
            # Should trigger list_files
            "What files are in the src directory?",
            "List all Python files in src/",
            "Show me what's in the experiments folder",
            "Can you check what files exist in tests?",
            "ls -la src/",
            
            # Should trigger read_file
            "Read the Makefile",
            "What's in README.org?",
            "Show me the contents of pyproject.toml",
            "Can you read the LICENSE file?",
            "cat Makefile",
            
            # Should trigger write_file
            "Create a file called test.txt with 'Hello World'",
            "Write 'TODO: fix this' to notes.txt",
            "Save this haiku to poem.txt: 'Code flows like water'",
            
            # Should NOT trigger tools
            "Explain how recursion works",
            "What is the difference between map and filter?",
            "Write a haiku about programming",
            "How does Python's GIL work?",
        ]
        
        print("🔬 Structured Tool Dispatch Experiment")
        print("=" * 60)
        print(f"Model: {self.model}")
        print(f"Using structured output with Pydantic schema")
        print("=" * 60)
        
        results = {
            "correct": 0,
            "incorrect": 0,
            "by_category": {
                "list_files": {"correct": 0, "total": 0},
                "read_file": {"correct": 0, "total": 0},
                "write_file": {"correct": 0, "total": 0},
                "no_tool": {"correct": 0, "total": 0},
            }
        }
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: \"{query}\"")
            
            # Determine expected result
            expected_tool = None
            if any(x in query.lower() for x in ["list", "what files", "show me what's in", "ls"]):
                expected_tool = "list_files"
            elif any(x in query.lower() for x in ["read", "what's in", "contents of", "cat"]):
                expected_tool = "read_file"
            elif any(x in query.lower() for x in ["create", "write", "save"]):
                expected_tool = "write_file"
            
            expected_category = expected_tool if expected_tool else "no_tool"
            results["by_category"][expected_category]["total"] += 1
            
            # Get decision
            decision = self.test_tool_decision(query)
            
            # Print results
            print(f"  Decision: {'✅ Tool needed' if decision.requires_tool_call else '❌ No tool'}")
            if decision.tool_name:
                print(f"  Tool: {decision.tool_name}")
            print(f"  Reasoning: {decision.reasoning}")
            
            # Check correctness
            is_correct = False
            if expected_tool and decision.requires_tool_call and decision.tool_name == expected_tool:
                is_correct = True
                results["correct"] += 1
                results["by_category"][expected_category]["correct"] += 1
            elif not expected_tool and not decision.requires_tool_call:
                is_correct = True
                results["correct"] += 1
                results["by_category"]["no_tool"]["correct"] += 1
            else:
                results["incorrect"] += 1
            
            print(f"  Result: {'✅ Correct' if is_correct else '❌ Incorrect'}")
            
        # Summary
        print("\n" + "=" * 60)
        print("📊 Results Summary:")
        print(f"\nOverall Accuracy: {results['correct']}/{len(test_queries)} ({results['correct']/len(test_queries)*100:.1f}%)")
        
        print("\nBy Category:")
        for category, stats in results["by_category"].items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"] * 100
                print(f"  {category}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
        
        print("\n💡 Insights:")
        print("- Structured output provides consistent, parseable decisions")
        print("- Can be used as a pre-processor to improve tool dispatch")
        print("- Low temperature helps with consistency")
        print("- Clear system prompt with examples improves accuracy")


def main():
    """Run the experiment."""
    experiment = ToolDispatchExperiment()
    experiment.run_experiments()


if __name__ == "__main__":
    main()
