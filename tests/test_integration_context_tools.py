#!/usr/bin/env python3
"""Integration tests for context management and tool usage."""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any, List

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gemini_repl.core.repl_structured import StructuredGeminiREPL
from gemini_repl.utils.context import ContextManager
from gemini_repl.tools.tool_decision import ToolDecision
from gemini_repl.tools.codebase_tools import (
    list_files,
    read_file, 
    write_file
)


class TestContextAndTools(unittest.TestCase):
    """Test context management and tool execution integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_dir = Path(self.temp_dir) / "workspace"
        self.workspace_dir.mkdir()
        
        # Create test files
        (self.workspace_dir / "test.txt").write_text("Hello World")
        (self.workspace_dir / "config.json").write_text('{"setting": "value"}')
        
        # Create a non-existent path for system prompt to prevent loading default
        fake_prompt_path = str(Path(self.temp_dir) / "nonexistent_prompt.txt")
        
        # Mock environment
        self.env_patcher = patch.dict("os.environ", {
            "GEMINI_API_KEY": "test-key",
            "WORKSPACE_DIR": str(self.workspace_dir),
            "CONTEXT_FILE": str(Path(self.temp_dir) / "context.json"),
            "LOG_FILE": str(Path(self.temp_dir) / "test.log"),
            "GEMINI_SYSTEM_PROMPT": fake_prompt_path  # Point to non-existent file
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)
        
    def test_system_prompt_loading(self):
        """Test that system prompt is loaded on fresh context."""
        # Create a system prompt file
        prompt_file = Path(self.temp_dir) / "system_prompt.txt"
        prompt_file.write_text("You are a helpful AI assistant.")
        
        with patch.dict("os.environ", {"GEMINI_SYSTEM_PROMPT": str(prompt_file)}):
            ctx = ContextManager(context_file=str(Path(self.temp_dir) / "fresh_context.json"))
            
            # Should have system message
            self.assertEqual(len(ctx.messages), 1)
            self.assertEqual(ctx.messages[0]["role"], "system")
            self.assertEqual(ctx.messages[0]["content"], "You are a helpful AI assistant.")
            
    def test_context_preservation_across_clear(self):
        """Test that system prompt persists after /clear."""
        prompt_file = Path(self.temp_dir) / "system_prompt.txt"
        prompt_file.write_text("System prompt content")
        
        with patch.dict("os.environ", {"GEMINI_SYSTEM_PROMPT": str(prompt_file)}):
            ctx = ContextManager(context_file=str(Path(self.temp_dir) / "test_context.json"))
            
            # Add some messages
            ctx.add_message("user", "Hello")
            ctx.add_message("assistant", "Hi there!")
            self.assertEqual(len(ctx.messages), 3)  # system + 2 messages
            
            # Clear context
            ctx.clear()
            
            # System prompt should remain
            self.assertEqual(len(ctx.messages), 1)
            self.assertEqual(ctx.messages[0]["role"], "system")
            
    def test_tool_execution_flow(self):
        """Test complete tool execution flow."""
        # Create a mock response that triggers tool use
        mock_response = Mock()
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].content.parts = [
            Mock(function_call=Mock(
                name="read_file",
                args={"file_path": "test.txt"}
            ))
        ]
        mock_response.text = "Here's the content of test.txt"
        
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.send_message.return_value = mock_response
            
            # Create REPL
            repl = StructuredGeminiREPL()
            
            # Simulate handling a request that needs tools
            with patch.object(repl.decision_engine, "analyze_query") as mock_analyze:
                mock_analyze.return_value = ToolDecision(
                    requires_tool_call=True,
                    tool_name="read_file",
                    reasoning="User wants to read a file",
                    file_path="test.txt"
                )
                
                # Capture output
                with patch("builtins.print") as mock_print:
                    repl._handle_api_request("show me test.txt")
                    
                    # Verify tool was executed
                    tool_calls = [call for call in mock_print.call_args_list 
                                 if "🔧" in str(call)]
                    self.assertTrue(len(tool_calls) > 0)
                    
    def test_tool_chaining(self):
        """Test that multiple tools can be chained."""
        # First response lists files
        list_response = Mock()
        list_response.text = "I'll list the files for you"
        list_response.candidates = []
        
        # Second response wants to read a file
        read_response = Mock()
        read_response.candidates = [Mock()]
        read_response.candidates[0].content.parts = [
            Mock(function_call=Mock(
                name="read_file",
                args={"file_path": "config.json"}
            ))
        ]
        
        # Final response with summary
        final_response = Mock()
        final_response.text = "The config file contains settings"
        final_response.candidates = []
        
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.send_message.side_effect = [list_response, read_response, final_response]
            
            repl = StructuredGeminiREPL()
            
            with patch.object(repl.decision_engine, "analyze_query") as mock_analyze:
                mock_analyze.return_value = ToolDecision(
                    requires_tool_call=True,
                    tool_name="list_files",
                    reasoning="Need to see files first",
                    pattern="*.json"
                )
                
                # Execute request
                repl._handle_api_request("summarize config files")
                
                # Verify multiple API calls were made
                self.assertEqual(mock_client.send_message.call_count, 3)
                
    def test_context_includes_tool_results(self):
        """Test that tool results are properly added to context."""
        ctx = ContextManager(context_file=str(Path(self.temp_dir) / "tool_context.json"))
        
        # Add user message
        ctx.add_message("user", "list files")
        
        # Simulate tool execution result being added
        tool_result = "file1.txt\nfile2.py\nconfig.json"
        enhanced_content = f"""list files

I've listed the files for you. Here's what I found:

{tool_result}

Based on these files, here's my response:"""
        
        # Update the last message with enhanced content
        ctx.messages[-1]["content"] = enhanced_content
        
        # Verify the context includes tool results
        messages = ctx.get_messages()
        self.assertIn("I've listed the files", messages[-1]["content"])
        self.assertIn("file1.txt", messages[-1]["content"])
        
    def test_tool_security_sandbox(self):
        """Test that tools respect security boundaries."""
        # Test path traversal prevention
        result = read_file(file_path="../../../etc/passwd")
        self.assertIn("Security error", result)
        self.assertIn("Parent directory", result)
        
        # Test absolute path prevention  
        result = read_file(file_path="/etc/passwd")
        self.assertIn("Security error", result)
        self.assertIn("Absolute path", result)
        
        # Test safe operations work
        result = write_file(file_path="safe_test.txt", content="Safe content")
        self.assertIn("Successfully wrote", result)
        
        result = read_file(file_path="safe_test.txt")
        self.assertEqual(result, "Safe content")


class TestIntegrationScenarios(unittest.TestCase):
    """Test complete user scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict("os.environ", {
            "GEMINI_API_KEY": "test-key",
            "WORKSPACE_DIR": str(Path(self.temp_dir) / "workspace"),
            "GEMINI_SYSTEM_PROMPT": ""
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)
        
    def test_summarize_codebase_flow(self):
        """Test the 'summarize this codebase' flow."""
        # Create mock codebase structure
        workspace = Path(self.temp_dir) / "workspace"
        workspace.mkdir()
        (workspace / "main.py").write_text("def main(): pass")
        (workspace / "utils.py").write_text("def helper(): pass")
        (workspace / "README.md").write_text("# My Project")
        
        # Mock the complete flow
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            
            # Setup response sequence
            responses = [
                # First: list files response
                Mock(text="I'll analyze your codebase", candidates=[]),
                # Second: wants to read README
                Mock(candidates=[Mock(content=Mock(parts=[
                    Mock(function_call=Mock(name="read_file", args={"file_path": "README.md"}))
                ]))]),
                # Third: wants to read main.py
                Mock(candidates=[Mock(content=Mock(parts=[
                    Mock(function_call=Mock(name="read_file", args={"file_path": "main.py"}))
                ]))]),
                # Final: summary
                Mock(text="This is a Python project with a main module", candidates=[])
            ]
            
            mock_client.send_message.side_effect = responses
            
            # Create REPL and simulate request
            repl = StructuredGeminiREPL()
            
            with patch.object(repl.decision_engine, "analyze_query") as mock_analyze:
                mock_analyze.return_value = ToolDecision(
                    requires_tool_call=True,
                    tool_name="list_files",
                    reasoning="Need to see project structure",
                    pattern="*"
                )
                
                # Capture all output
                output_lines = []
                with patch("builtins.print") as mock_print:
                    mock_print.side_effect = lambda *args: output_lines.append(" ".join(str(a) for a in args))
                    
                    repl._handle_api_request("summarize this codebase")
                    
                # Verify the flow
                tool_indicators = [line for line in output_lines if "🔧" in line]
                self.assertTrue(len(tool_indicators) >= 3)  # list + 2 reads
                
                # Verify final summary was displayed
                summary_found = any("Python project" in line for line in output_lines)
                self.assertTrue(summary_found)


if __name__ == "__main__":
    unittest.main()
