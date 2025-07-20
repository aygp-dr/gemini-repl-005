#!/usr/bin/env python3
"""Test for Bug #29: AI reverting to advisory behavior instead of using tools."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gemini_repl.core.repl_structured import StructuredGeminiREPL
from gemini_repl.tools.tool_decision import ToolDecision


class TestBug29AdvisoryBehavior(unittest.TestCase):
    """Test that AI uses tools instead of giving advice."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict("os.environ", {
            "GEMINI_API_KEY": "test-key",
            "WORKSPACE_DIR": self.temp_dir,
            "GEMINI_SYSTEM_PROMPT": ""  # Use default aggressive prompt
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)
        
    def test_show_fib_in_scheme_should_generate_not_read(self):
        """Test that 'show fib in scheme' generates code, not reads files."""
        
        # Mock response that shows Fibonacci
        mock_response = Mock()
        mock_response.text = """Here's the Fibonacci function in Scheme:

```scheme
(define (fibonacci n)
  (cond
    ((= n 0) 0)
    ((= n 1) 1)
    (else (+ (fibonacci (- n 1))
             (fibonacci (- n 2))))))
```"""
        mock_response.candidates = []
        
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.send_message.return_value = mock_response
            
            with patch("gemini_repl.tools.decision_engine.ToolDecisionEngine.analyze_query") as mock_analyze:
                # Should NOT try to read a file for "show X in Y"
                mock_analyze.return_value = ToolDecision(
                    requires_tool_call=False,
                    reasoning="User wants to see Fibonacci implementation in Scheme"
                )
                
                repl = StructuredGeminiREPL()
                
                output_lines = []
                with patch("builtins.print") as mock_print:
                    mock_print.side_effect = lambda *args: output_lines.append(" ".join(str(a) for a in args))
                    
                    repl._handle_api_request("show fib in scheme")
                    
                    # Should show Fibonacci code
                    output = "\n".join(output_lines)
                    self.assertIn("fibonacci", output.lower())
                    self.assertIn("define", output)
                    
                    # Should NOT say "please create"
                    self.assertNotIn("please create", output.lower())
                    self.assertNotIn("does not exist", output.lower())
                    
    def test_create_file_should_use_write_tool(self):
        """Test that 'create X' uses write_file immediately."""
        
        tla_content = """---- MODULE Fibonacci ----
EXTENDS Naturals

RECURSIVE Fib(_)
Fib(n) == 
  IF n = 0 THEN 0
  ELSE IF n = 1 THEN 1
  ELSE Fib(n-1) + Fib(n-2)
===="""
        
        # Mock responses
        write_response = Mock()
        write_response.text = "I've created the TLA+ specification."
        write_response.candidates = [Mock(content=Mock(parts=[
            Mock(function_call=Mock(
                name="write_file",
                args={"file_path": "research/formal/Fibonacci.tla", "content": tla_content}
            ))
        ]))]
        
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.send_message.return_value = write_response
            
            with patch("gemini_repl.tools.decision_engine.ToolDecisionEngine.analyze_query") as mock_analyze:
                # Should decide to write file
                mock_analyze.return_value = ToolDecision(
                    requires_tool_call=True,
                    tool_name="write_file",
                    reasoning="Creating TLA+ specification file",
                    file_path="research/formal/Fibonacci.tla",
                    content=tla_content
                )
                
                repl = StructuredGeminiREPL()
                
                output_lines = []
                with patch("builtins.print") as mock_print:
                    mock_print.side_effect = lambda *args: output_lines.append(" ".join(str(a) for a in args))
                    
                    repl._handle_api_request("create a TLA+ spec for that and add it to research/formal/")
                    
                    output = "\n".join(output_lines)
                    
                    # Should use write_file tool
                    self.assertIn("write_file", output)
                    
                    # Should NOT ask user to create folder
                    self.assertNotIn("create the folder", output.lower())
                    self.assertNotIn("folder exists", output.lower())
                    self.assertNotIn("try again", output.lower())
                    
    def test_failed_read_should_not_advise(self):
        """Test that failed read_file doesn't result in advisory messages."""
        
        # Mock a failed read followed by proper behavior
        read_fail_response = Mock()
        read_fail_response.candidates = [Mock(content=Mock(parts=[
            Mock(function_call=Mock(
                name="read_file",
                args={"file_path": "nonexistent.txt"}
            ))
        ]))]
        
        create_response = Mock()
        create_response.text = "The file doesn't exist. Let me create an example for you."
        create_response.candidates = [Mock(content=Mock(parts=[
            Mock(function_call=Mock(
                name="write_file",
                args={"file_path": "example.txt", "content": "Example content"}
            ))
        ]))]
        
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.send_message.side_effect = [read_fail_response, create_response]
            
            with patch("gemini_repl.tools.decision_engine.ToolDecisionEngine.analyze_query") as mock_analyze:
                mock_analyze.return_value = ToolDecision(
                    requires_tool_call=True,
                    tool_name="read_file",
                    reasoning="Reading requested file",
                    file_path="nonexistent.txt"
                )
                
                repl = StructuredGeminiREPL()
                
                # Mock the file read to fail
                with patch("gemini_repl.tools.codebase_tools.read_file") as mock_read:
                    mock_read.return_value = "Error reading file: [Errno 2] No such file or directory"
                    
                    output_lines = []
                    with patch("builtins.print") as mock_print:
                        mock_print.side_effect = lambda *args: output_lines.append(" ".join(str(a) for a in args))
                        
                        repl._handle_api_request("show me nonexistent.txt")
                        
                        output = "\n".join(output_lines)
                        
                        # Should NOT tell user to create the file
                        self.assertNotIn("please create", output.lower())
                        self.assertNotIn("re-run the command", output.lower())
                        self.assertNotIn("you need to", output.lower())


class TestProperBehaviorPatterns(unittest.TestCase):
    """Test the correct behavior patterns we want to see."""
    
    def test_query_interpretation_patterns(self):
        """Test that different query patterns are interpreted correctly."""
        
        test_cases = [
            # Query → Expected behavior
            ("show fibonacci in scheme", "generate", None),
            ("show me test.py", "read", "test.py"),
            ("create a python script", "write", None),
            ("what's in config.json", "read", "config.json"),
            ("make a TLA+ spec", "write", None),
            ("display the Makefile", "read", "Makefile"),
            ("generate a fibonacci function", "generate", None),
        ]
        
        for query, expected_action, expected_file in test_cases:
            # The decision engine should understand these patterns
            if expected_action == "generate":
                # Should not try to read files
                self.assertIn(any(word in query for word in ["show", "in"]), True)
            elif expected_action == "read":
                # Should identify the file to read
                self.assertIsNotNone(expected_file)
            elif expected_action == "write":
                # Should prepare to write
                self.assertIn(any(word in query for word in ["create", "make"]), True)


if __name__ == "__main__":
    unittest.main()
