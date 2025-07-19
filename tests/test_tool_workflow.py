#!/usr/bin/env python3
"""Test tool calling workflows that require multiple steps."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path

from gemini_repl.core.repl import GeminiREPL
from gemini_repl.tools.codebase_tools import CODEBASE_TOOL_DECLARATIONS


class TestToolWorkflow(unittest.TestCase):
    """Test multi-step tool calling workflows."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock Makefile content
        self.makefile_content = """# Gemini REPL Makefile

.PHONY: help setup lint test build repl

help:
\t@echo "Available targets:"
\t@echo "  make setup    - Install dependencies"
\t@echo "  make lint     - Run linters"
\t@echo "  make test     - Run tests"
\t@echo "  make repl     - Start the REPL"

setup:
\tuv pip install -e .

lint:
\truff check src/ tests/

test:
\tpytest tests/ -v

repl:
\tuv run python -m gemini_repl
"""

    @patch('gemini_repl.core.api_client.genai.Client')
    def test_list_makefile_targets_workflow(self, mock_genai):
        """Test the workflow: user asks to list Makefile targets."""
        # Mock the API client
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Create a sequence of responses simulating tool calls
        responses = []
        
        # First response: AI decides to read the Makefile
        response1 = MagicMock()
        response1.candidates = [MagicMock()]
        response1.candidates[0].content.parts = [MagicMock()]
        response1.candidates[0].content.parts[0].function_call = MagicMock(
            name="read_file",
            args={"file_path": "Makefile"}
        )
        responses.append(response1)
        
        # Second response: AI processes the Makefile content
        response2 = MagicMock()
        response2.candidates = [MagicMock()]
        response2.candidates[0].content.parts = [MagicMock()]
        response2.candidates[0].content.parts[0].function_call = None
        response2.candidates[0].content.parts[0].text = """
I found the following Makefile targets:

1. **help** - Displays available targets
2. **setup** - Installs dependencies using `uv pip install -e .`
3. **lint** - Runs ruff linter on src/ and tests/ directories
4. **test** - Runs pytest on the tests/ directory with verbose output
5. **repl** - Starts the Gemini REPL using `uv run python -m gemini_repl`

The default target is 'help' which shows all available commands.
"""
        responses.append(response2)
        
        # Set up the mock to return our responses
        mock_client.models.generate_content.side_effect = responses
        
        # Create REPL instance
        repl = GeminiREPL()
        
        # Simulate user request
        user_input = "Can you list all the Makefile targets and explain what each one does?"
        
        # Mock file reading
        with patch('gemini_repl.tools.codebase_tools.read_file') as mock_read:
            mock_read.return_value = self.makefile_content
            
            # This would normally be called through the REPL's _handle_api_request
            # but we'll test the components
            repl.context.add_message("user", user_input)
            
            # Verify tools are available
            self.assertTrue(repl.tools_enabled)
            self.assertIsNotNone(CODEBASE_TOOL_DECLARATIONS)
            
            # Verify the tool declarations include read_file
            tool_names = [tool['name'] for tool in CODEBASE_TOOL_DECLARATIONS]
            self.assertIn('read_file', tool_names)
            
    def test_tool_declarations_structure(self):
        """Test that tool declarations are properly structured."""
        # Verify we have the expected tools
        tool_names = [tool['name'] for tool in CODEBASE_TOOL_DECLARATIONS]
        expected_tools = ['read_file', 'write_file', 'list_files', 'search_code']
        
        for tool in expected_tools:
            self.assertIn(tool, tool_names)
            
        # Verify each tool has required fields
        for tool in CODEBASE_TOOL_DECLARATIONS:
            self.assertIn('name', tool)
            self.assertIn('description', tool)
            self.assertIn('parameters', tool)
            self.assertIn('type', tool['parameters'])
            self.assertEqual(tool['parameters']['type'], 'object')
            self.assertIn('properties', tool['parameters'])
            self.assertIn('required', tool['parameters'])
            
    @patch('subprocess.run')
    def test_search_makefile_targets(self, mock_subprocess):
        """Test using search_code to find Makefile targets."""
        # Mock ripgrep output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Makefile:5:.PHONY: help setup lint test build repl
Makefile:7:help:
Makefile:13:setup:
Makefile:16:lint:
Makefile:19:test:
Makefile:22:repl:"""
        mock_subprocess.return_value = mock_result
        
        # Import and test the search function
        from gemini_repl.tools.codebase_tools import search_code
        
        result = search_code("^[a-z]+:", "Makefile")
        
        # Verify ripgrep was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        self.assertEqual(call_args[0], "rg")
        self.assertIn("^[a-z]+:", call_args)
        
        # Verify result contains Makefile targets
        self.assertIn("help:", result)
        self.assertIn("setup:", result)
        self.assertIn("lint:", result)
        self.assertIn("test:", result)
        self.assertIn("repl:", result)


class TestToolChaining(unittest.TestCase):
    """Test scenarios where multiple tools need to be called in sequence."""
    
    def test_analyze_project_structure(self):
        """Test workflow: analyze project structure requires list + read operations."""
        # This would test:
        # 1. list_files("*.py") to find Python files
        # 2. read_file("pyproject.toml") to get project metadata
        # 3. search_code("class", "*.py") to find main classes
        pass  # Placeholder for more complex test
        
    def test_modify_and_verify(self):
        """Test workflow: modify a file then verify the change."""
        # This would test:
        # 1. read_file to get current content
        # 2. write_file to make changes
        # 3. read_file again to verify
        pass  # Placeholder for more complex test


if __name__ == '__main__':
    unittest.main()
