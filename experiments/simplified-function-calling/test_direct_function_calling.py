#!/usr/bin/env python3
"""
Experiment: Simplified Function Calling Without Dispatch System
Based on Google's official Gemini API documentation for function calling
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from google import genai
from google.genai import types


class SimplifiedGeminiREPL:
    """Simplified REPL that follows Google's recommended function calling approach."""
    
    def __init__(self):
        # Initialize client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
            
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash-lite"
        self.conversation_history = []
        
        # Define tool functions
        self.tool_functions = {
            'list_files': self._list_files_impl,
            'read_file': self._read_file_impl,
            'write_file': self._write_file_impl,
        }
        
        # Define function declarations for Gemini
        self.function_declarations = [
            types.FunctionDeclaration(
                name="list_files",
                description="List files in a directory matching a pattern",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match files (e.g., '*.py', 'src/**/*.py')",
                            "default": "*"
                        }
                    },
                    "required": []
                }
            ),
            types.FunctionDeclaration(
                name="read_file",
                description="Read the contents of a file",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Write content to a file, creating directories as needed",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            )
        ]
        
        # Configure tools
        self.tools = types.Tool(function_declarations=self.function_declarations)
        self.config = types.GenerateContentConfig(
            tools=[self.tools],
            temperature=0.7
        )
        
        # Load system prompt
        self._load_system_prompt()
        
    def _load_system_prompt(self):
        """Load the aggressive system prompt."""
        prompt_path = Path(__file__).parent.parent.parent / "resources" / "system_prompt.txt"
        if prompt_path.exists():
            system_prompt = prompt_path.read_text()
            # Add system prompt as first message
            self.conversation_history.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })
            self.conversation_history.append({
                "role": "model",
                "parts": [{"text": "I understand. I have full read/write access and will use tools immediately when needed."}]
            })
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input and handle function calling."""
        
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "parts": [{"text": user_input}]
        })
        
        print(f"\n🤔 Processing: '{user_input}'")
        
        # Generate response with function calling enabled
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=self.conversation_history,
                config=self.config
            )
            
            # Handle the response (may include function calls)
            final_response = self._handle_response_with_tools(response)
            return final_response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _handle_response_with_tools(self, response) -> str:
        """Handle responses that may contain function calls."""
        
        if not response.candidates:
            return "No response generated"
        
        parts = response.candidates[0].content.parts
        text_parts = []
        function_calls_made = []
        
        # Process all parts
        for part in parts:
            if hasattr(part, 'function_call') and part.function_call:
                # Execute the function call
                print(f"🔧 Found function call: {part.function_call.name}")
                func_result = self._execute_function_call(part.function_call)
                function_calls_made.append((part.function_call, func_result))
                
            elif hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        # If we made function calls, send results back to model
        if function_calls_made:
            # Add the model's response (with function calls) to history
            self.conversation_history.append({
                "role": "model",
                "parts": response.candidates[0].content.parts
            })
            
            # Add function results
            for func_call, result in function_calls_made:
                self.conversation_history.append({
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": func_call.name,
                            "response": result
                        }
                    }]
                })
            
            # Get final response with function results
            print("📨 Getting final response with function results...")
            final_response = self.client.models.generate_content(
                model=self.model_name,
                contents=self.conversation_history,
                config=self.config
            )
            
            # Extract final text
            final_text = self._extract_text_from_response(final_response)
            
            # Add to history
            self.conversation_history.append({
                "role": "model",
                "parts": [{"text": final_text}]
            })
            
            return final_text
        else:
            # No function calls, just return text
            final_text = " ".join(text_parts)
            self.conversation_history.append({
                "role": "model",
                "parts": [{"text": final_text}]
            })
            return final_text
    
    def _extract_text_from_response(self, response) -> str:
        """Extract all text from a response."""
        if not response.candidates:
            return ""
            
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        return " ".join(text_parts)
    
    def _execute_function_call(self, function_call) -> Dict[str, Any]:
        """Execute a function call and return results."""
        func_name = function_call.name
        print(f"🔧 Executing: {func_name}")
        
        if func_name not in self.tool_functions:
            return {"error": f"Unknown function: {func_name}"}
        
        try:
            # Extract arguments
            args_dict = {}
            if hasattr(function_call, 'args'):
                # Handle different arg formats
                if hasattr(function_call.args, '_pb'):
                    # Protobuf object
                    args_dict = json.loads(type(function_call.args).to_json(function_call.args))
                elif isinstance(function_call.args, dict):
                    args_dict = function_call.args
                else:
                    # Try to extract attributes
                    for field in ['file_path', 'content', 'pattern', 'directory']:
                        if hasattr(function_call.args, field):
                            args_dict[field] = getattr(function_call.args, field)
            
            print(f"   Args: {args_dict}")
            
            # Execute the function
            result = self.tool_functions[func_name](**args_dict)
            print(f"   ✅ Result: {str(result)[:100]}...")
            return result
            
        except Exception as e:
            error_msg = f"Error executing {func_name}: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg}
    
    # Tool implementations (simplified, no sandboxing for this experiment)
    def _list_files_impl(self, pattern="*") -> Dict[str, Any]:
        """List files matching pattern."""
        import glob
        try:
            files = glob.glob(pattern, recursive=True)
            return {"files": files[:50]}  # Limit to 50 files
        except Exception as e:
            return {"error": str(e)}
    
    def _read_file_impl(self, file_path: str) -> Dict[str, Any]:
        """Read file contents."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return {"content": content[:5000]}  # Limit size
        except FileNotFoundError:
            return {"error": f"File not found: {file_path}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _write_file_impl(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file."""
        try:
            # Create directory if needed
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {"message": f"Successfully wrote to {file_path}"}
        except Exception as e:
            return {"error": str(e)}


def test_simplified_function_calling():
    """Test the simplified function calling approach."""
    
    print("=== Simplified Function Calling Experiment ===\n")
    
    repl = SimplifiedGeminiREPL()
    
    # Test cases that should trigger function calls
    test_cases = [
        # Test 1: "show fib in scheme" - should generate, not read
        {
            "input": "show fibonacci in scheme",
            "expected_behavior": "Should generate Scheme code, NOT try to read a file"
        },
        
        # Test 2: Create a file
        {
            "input": "create a TLA+ spec for fibonacci and add it to research/formal/",
            "expected_behavior": "Should use write_file to create the file"
        },
        
        # Test 3: Read the created file
        {
            "input": "show research/formal/Fibonacci.tla",
            "expected_behavior": "Should use read_file to show the content"
        },
        
        # Test 4: List files
        {
            "input": "what files are in research/",
            "expected_behavior": "Should use list_files to show directory contents"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['input']}")
        print(f"Expected: {test['expected_behavior']}")
        print(f"{'='*60}")
        
        response = repl.process_user_input(test['input'])
        
        print(f"\nResponse:\n{response}\n")
        
        # Check for bad patterns
        bad_patterns = [
            "please create",
            "create the folder", 
            "try again",
            "you need to",
            "you should"
        ]
        
        found_bad = [p for p in bad_patterns if p in response.lower()]
        if found_bad:
            print(f"⚠️  WARNING: Found advisory language: {found_bad}")
        else:
            print("✅ No advisory language detected")


def compare_with_current_implementation():
    """Compare simplified approach with current dispatch system."""
    
    print("\n\n=== Comparison with Current Implementation ===\n")
    
    print("Current Dispatch System:")
    print("- Uses ToolDecisionEngine to analyze queries")
    print("- Separate decision phase before tool execution")
    print("- Complex prompt engineering for decision making")
    print("- Two-stage process: decide → execute")
    
    print("\nSimplified Function Calling:")
    print("- Direct function calling as recommended by Google")
    print("- Model decides when to use tools naturally")
    print("- Single-stage process with built-in tool support")
    print("- Relies on system prompt for behavior guidance")
    
    print("\nKey Differences:")
    print("1. No separate decision engine needed")
    print("2. Function calls embedded in response.parts")
    print("3. Automatic handling of multiple tool calls")
    print("4. Simpler code, easier to debug")


if __name__ == "__main__":
    # Run the experiment
    test_simplified_function_calling()
    compare_with_current_implementation()
    
    print("\n\n=== Experiment Complete ===")
    print("\nKey Findings:")
    print("- Simplified approach follows Google's official patterns")
    print("- No need for complex dispatch system")
    print("- System prompt is crucial for behavior")
    print("- Function calling is handled natively by the API")
