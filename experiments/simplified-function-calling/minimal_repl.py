#!/usr/bin/env python3
"""
Minimal REPL implementation using direct function calling.
This shows the simplest possible approach that should work.
"""

import os
from google import genai
from google.genai import types


def create_minimal_repl():
    """Create a minimal REPL with function calling."""
    
    # Initialize client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Tool implementations
    def read_file(file_path: str) -> dict:
        try:
            with open(file_path, 'r') as f:
                return {"content": f.read()}
        except Exception as e:
            return {"error": str(e)}
    
    def write_file(file_path: str, content: str) -> dict:
        try:
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            return {"success": True, "message": f"Created {file_path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def list_files(pattern: str = "*") -> dict:
        import glob
        files = glob.glob(pattern)
        return {"files": files}
    
    # Tool registry
    tools = {
        "read_file": read_file,
        "write_file": write_file,
        "list_files": list_files
    }
    
    # Function declarations
    tool_config = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="read_file",
                description="Read a file",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"}
                    },
                    "required": ["file_path"]
                }
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Write a file",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["file_path", "content"]
                }
            ),
            types.FunctionDeclaration(
                name="list_files",
                description="List files",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "default": "*"}
                    }
                }
            )
        ]
    )
    
    # Conversation history
    messages = []
    
    # Add system prompt
    system_prompt = """You have write_file, read_file, and list_files tools.
When asked to create something, USE write_file immediately.
Never tell users to create files themselves."""
    
    messages.append({"role": "user", "parts": [{"text": system_prompt}]})
    messages.append({"role": "model", "parts": [{"text": "Understood. I'll use my tools."}]})
    
    def chat(user_input: str) -> str:
        # Add user message
        messages.append({"role": "user", "parts": [{"text": user_input}]})
        
        # Generate response
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=messages,
            config=types.GenerateContentConfig(tools=[tool_config])
        )
        
        # Process response
        if not response.candidates:
            return "No response"
        
        parts = response.candidates[0].content.parts
        function_calls = []
        text_parts = []
        
        # Extract function calls and text
        for part in parts:
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                print(f"🔧 Tool: {fc.name}")
                
                # Execute function
                args = {}
                # Handle different argument formats
                if hasattr(fc, 'args'):
                    if hasattr(fc.args, '_pb'):
                        # Protobuf format
                        import json
                        args = json.loads(type(fc.args).to_json(fc.args))
                    elif isinstance(fc.args, dict):
                        args = fc.args
                    else:
                        # Direct attribute access
                        for field in ['file_path', 'content', 'pattern']:
                            if hasattr(fc.args, field):
                                args[field] = getattr(fc.args, field)
                
                print(f"   Args: {args}")
                
                result = tools[fc.name](**args)
                function_calls.append((fc, result))
                
            elif hasattr(part, 'text'):
                text_parts.append(part.text)
        
        # If we made function calls, continue conversation
        if function_calls:
            # Add model's response (with function calls)
            messages.append({"role": "model", "parts": parts})
            
            # Add function results
            for fc, result in function_calls:
                messages.append({
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": fc.name,
                            "response": result
                        }
                    }]
                })
            
            # Get final response
            final_response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=messages,
                config=types.GenerateContentConfig(tools=[tool_config])
            )
            
            # Extract text from final response
            final_text = ""
            if final_response.candidates:
                for part in final_response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        final_text += part.text
            
            messages.append({"role": "model", "parts": [{"text": final_text}]})
            return final_text
        else:
            # No function calls
            text = " ".join(text_parts)
            messages.append({"role": "model", "parts": [{"text": text}]})
            return text
    
    return chat


def test_minimal_repl():
    """Test the minimal REPL."""
    print("=== Minimal REPL Test ===\n")
    
    chat = create_minimal_repl()
    
    # Test creating a file
    print("User: create test.txt with 'Hello World'")
    response = chat("create test.txt with 'Hello World'")
    print(f"Assistant: {response}\n")
    
    # Check for bad patterns
    if "please create" in response.lower() or "you need to" in response.lower():
        print("❌ FAIL: Advisory language detected!")
    else:
        print("✅ PASS: No advisory language")
    
    # Test reading the file
    print("\nUser: show test.txt")
    response = chat("show test.txt")
    print(f"Assistant: {response}\n")
    
    # Clean up
    if os.path.exists("test.txt"):
        os.remove("test.txt")
        print("🧹 Cleaned up test.txt")


if __name__ == "__main__":
    test_minimal_repl()
