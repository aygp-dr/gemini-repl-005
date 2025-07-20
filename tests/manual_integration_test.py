#!/usr/bin/env python3
"""Manual integration test to verify context and tool usage."""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_context_with_system_prompt():
    """Test that system prompt is loaded and preserved."""
    print("=== Testing Context with System Prompt ===")
    
    # Set up temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create custom system prompt
        prompt_file = Path(temp_dir) / "test_prompt.txt"
        prompt_file.write_text("Test system prompt")
        
        os.environ["GEMINI_SYSTEM_PROMPT"] = str(prompt_file)
        os.environ["CONTEXT_FILE"] = str(Path(temp_dir) / "test_context.json")
        
        from gemini_repl.utils.context import ContextManager
        
        # Create context
        ctx = ContextManager()
        print(f"Initial messages: {len(ctx.messages)}")
        
        if ctx.messages and ctx.messages[0]["role"] == "system":
            print(f"✅ System prompt loaded: '{ctx.messages[0]['content'][:50]}...'")
        else:
            print("❌ No system prompt found!")
            
        # Add messages
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there!")
        print(f"After adding messages: {len(ctx.messages)}")
        
        # Clear context
        ctx.clear()
        print(f"After clear: {len(ctx.messages)}")
        
        if ctx.messages and ctx.messages[0]["role"] == "system":
            print("✅ System prompt preserved after clear")
        else:
            print("❌ System prompt lost after clear!")
            

def test_tool_execution():
    """Test tool execution and sandboxing."""
    print("\n=== Testing Tool Execution ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["WORKSPACE_DIR"] = temp_dir
        
        from gemini_repl.tools.codebase_tools import read_file, write_file, list_files
        
        # Test write
        result = write_file("test.txt", "Hello from test")
        print(f"Write result: {result}")
        
        # Test read
        result = read_file("test.txt")
        print(f"Read result: {result}")
        
        # Test list
        result = list_files("*.txt")
        print(f"List result: {result}")
        
        # Test security
        print("\n--- Security Tests ---")
        
        # Parent directory
        result = read_file("../../../etc/passwd")
        print(f"Parent dir attempt: {result[:50]}...")
        
        # Absolute path
        result = read_file("/etc/passwd") 
        print(f"Absolute path attempt: {result[:50]}...")
        

def test_tool_chaining_mock():
    """Test tool chaining with mocked API."""
    print("\n=== Testing Tool Chaining (Mocked) ===")
    
    from unittest.mock import Mock, patch
    
    # Mock the API client
    with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
        mock_client = MockClient.return_value
        
        # Create mock responses
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.candidates = []
        mock_response.usage_metadata = Mock(total_token_count=100)
        
        mock_client.send_message.return_value = mock_response
        
        # Create REPL
        from gemini_repl.core.repl_structured import StructuredGeminiREPL
        
        try:
            repl = StructuredGeminiREPL()
            print("✅ REPL created successfully")
            
            # Check if system prompt was loaded
            if repl.context.messages and repl.context.messages[0]["role"] == "system":
                print("✅ System prompt loaded in REPL")
            else:
                print("❌ No system prompt in REPL context")
                
        except Exception as e:
            print(f"❌ Error creating REPL: {e}")
            

if __name__ == "__main__":
    # Set API key for tests
    os.environ["GEMINI_API_KEY"] = "test-key"
    
    test_context_with_system_prompt()
    test_tool_execution()
    test_tool_chaining_mock()
    
    print("\n=== Integration Test Complete ===")
