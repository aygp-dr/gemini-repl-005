#!/usr/bin/env python3
"""
Demonstrate the full tool calling flow for Makefile analysis.
This shows how Gemini decides which tools to call and in what order.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types
from gemini_repl.tools.codebase_tools import CODEBASE_FUNCTIONS, CODEBASE_TOOL_DECLARATIONS


def visualize_function_call(function_call):
    """Pretty print function call details."""
    print(f"\n🔧 TOOL CALL: {function_call.name}")
    print("─" * 50)
    args = dict(function_call.args)
    print(f"📋 Arguments:")
    for key, value in args.items():
        print(f"   {key}: {repr(value)}")
    return args


def execute_tool(name: str, **kwargs) -> str:
    """Execute a tool and return result."""
    if name in CODEBASE_FUNCTIONS:
        print(f"\n🔄 EXECUTING: {name}")
        result = CODEBASE_FUNCTIONS[name](**kwargs)
        print(f"📤 Result preview: {result[:200]}{'...' if len(result) > 200 else ''}")
        return result
    else:
        return f"Unknown tool: {name}"


def demonstrate_tool_flow():
    """Show the complete flow of tool calling for Makefile analysis."""
    print("🎯 Tool Calling Flow Demonstration")
    print("=" * 60)
    print("Request: Analyze the Makefile and explain what each target does")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        return False
    
    # Configure client with tools
    client = genai.Client()
    tools = types.Tool(function_declarations=CODEBASE_TOOL_DECLARATIONS)
    config = types.GenerateContentConfig(tools=[tools])
    
    # Initial request - let the model decide what tools to use
    request = "I need to analyze the Makefile in this project. Can you list all the targets and explain what each one does?"
    
    print(f"\n👤 USER: {request}")
    print("\n🤖 GEMINI THINKING...")
    
    # Track conversation for multi-turn
    conversation = []
    conversation.append(types.Content(parts=[types.Part.from_text(request)]))
    
    try:
        # First API call - model should decide to list files or read Makefile
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=conversation,
            config=config,
        )
        
        # Process response - may contain multiple tool calls
        turn_count = 1
        max_turns = 5  # Prevent infinite loops
        
        while turn_count <= max_turns:
            print(f"\n{'='*20} TURN {turn_count} {'='*20}")
            
            # Check if response has function calls
            if response.candidates[0].content.parts[0].function_call:
                # Model wants to call a function
                function_call = response.candidates[0].content.parts[0].function_call
                
                # Visualize what the model wants to do
                args = visualize_function_call(function_call)
                
                # Execute the function
                result = execute_tool(function_call.name, **args)
                
                # Add model's request to conversation
                conversation.append(response.candidates[0].content)
                
                # Create function response
                function_response = types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": result}
                )
                conversation.append(types.Content(parts=[function_response]))
                
                # Get next response from model
                print(f"\n🤖 GEMINI PROCESSING RESULT...")
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=conversation,
                    config=config,
                )
                
                turn_count += 1
            else:
                # Model provided final answer
                print(f"\n✅ FINAL ANSWER:")
                print("─" * 50)
                print(response.text)
                break
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print(f"\n\n📊 FLOW SUMMARY:")
    print(f"Total turns: {turn_count}")
    print(f"Tools called: Check conversation above")
    
    return True


def test_simple_flow():
    """Test a simple single-tool flow."""
    print("\n\n🧪 SIMPLE TEST: Direct file read")
    print("=" * 40)
    
    client = genai.Client()
    tools = types.Tool(function_declarations=CODEBASE_TOOL_DECLARATIONS)
    config = types.GenerateContentConfig(tools=[tools])
    
    # Simple request that should trigger read_file
    request = "Read the pyproject.toml file and tell me the project name"
    print(f"👤 USER: {request}")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=request,
            config=config,
        )
        
        if response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call
            args = visualize_function_call(function_call)
            result = execute_tool(function_call.name, **args)
            
            # Send result back
            function_response = types.Part.from_function_response(
                name=function_call.name,
                response={"result": result}
            )
            
            final_response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[
                    types.Content(parts=[types.Part.from_text(request)]),
                    response.candidates[0].content,
                    types.Content(parts=[function_response])
                ],
                config=config,
            )
            
            print(f"\n✅ ANSWER: {final_response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run both demonstrations
    demonstrate_tool_flow()
    test_simple_flow()
