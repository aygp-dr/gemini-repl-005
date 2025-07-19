#!/usr/bin/env python3
"""
Direct API test to understand tool calling behavior
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types
from gemini_repl.tools.codebase_tools import CODEBASE_TOOL_DECLARATIONS

def test_direct_tool_call():
    """Test tool calling directly with the API."""
    print("🧪 Direct API Tool Calling Test")
    print("=" * 50)
    
    # Initialize client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Configure tools
    tools = types.Tool(function_declarations=CODEBASE_TOOL_DECLARATIONS)
    config = types.GenerateContentConfig(tools=[tools])
    
    # Test queries
    queries = [
        "List all Python files in the src directory",
        "Read the Makefile and tell me the available commands",
        "What's in the README.org file?",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=query,
                config=config,
            )
            
            # Check response structure
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate.content, "parts"):
                    print(f"Parts: {len(candidate.content.parts)}")
                    for i, part in enumerate(candidate.content.parts):
                        print(f"  Part {i}: {type(part).__name__}")
                        if hasattr(part, "function_call") and part.function_call:
                            print(f"    ✅ Function call: {part.function_call.name}")
                            print(f"    Args: {dict(part.function_call.args)}")
                        elif hasattr(part, "text"):
                            print(f"    Text: {part.text[:100]}...")
                else:
                    print("No parts in content")
            else:
                print("No candidates in response")
                
            # Also check direct text
            if hasattr(response, "text"):
                print(f"\nDirect text response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n✅ Test complete")

if __name__ == "__main__":
    test_direct_tool_call()
