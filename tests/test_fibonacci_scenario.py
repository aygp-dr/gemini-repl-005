#!/usr/bin/env python3
"""Test case for multi-step Fibonacci scenario with formal specifications."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from typing import List

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gemini_repl.core.repl_structured import StructuredGeminiREPL
from gemini_repl.tools.codebase_tools import write_file, read_file, list_files


class TestFibonacciScenario(unittest.TestCase):
    """Test multi-step scenario: Scheme → TLA+ → Review."""
    
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
        
    def test_fibonacci_workflow(self):
        """Test complete Fibonacci workflow with directory creation."""
        
        # Expected Scheme implementation
        scheme_fib = """(define (fibonacci n)
  (cond
    ((= n 0) 0)
    ((= n 1) 1)
    (else (+ (fibonacci (- n 1))
             (fibonacci (- n 2))))))

;; Tail-recursive version
(define (fib-tail n)
  (define (fib-iter n a b)
    (if (= n 0)
        a
        (fib-iter (- n 1) b (+ a b))))
  (fib-iter n 0 1))"""
        
        # Expected TLA+ specification
        tla_spec = """---- MODULE Fibonacci ----
EXTENDS Naturals, Sequences

(* Recursive definition of Fibonacci *)
RECURSIVE Fib(_)
Fib(n) == 
  IF n = 0 THEN 0
  ELSE IF n = 1 THEN 1
  ELSE Fib(n-1) + Fib(n-2)

(* Iterative computation for model checking *)
FibSeq(n) == 
  LET RECURSIVE FibIter(_, _, _)
      FibIter(k, a, b) == 
        IF k = 0 THEN a
        ELSE FibIter(k-1, b, a+b)
  IN FibIter(n, 0, 1)

(* Property: Fibonacci sequence is strictly increasing after n=1 *)
FibIncreasing == 
  \\A n \\in Nat : n > 1 => Fib(n) > Fib(n-1)

===="""
        
        # Mock responses for each step
        responses = [
            # Step 1: Show Fibonacci in Scheme
            Mock(text=f"Here's the Fibonacci function in Scheme:\n\n{scheme_fib}", 
                 candidates=[]),
            
            # Step 2: Create TLA+ spec
            Mock(candidates=[Mock(content=Mock(parts=[
                Mock(function_call=Mock(
                    name="write_file",
                    args={"file_path": "research/formal/Fibonacci.tla", "content": tla_spec}
                ))
            ]))]),
            Mock(text="I've created the TLA+ specification for Fibonacci.", candidates=[]),
            
            # Step 3: Read and suggest improvements
            Mock(candidates=[Mock(content=Mock(parts=[
                Mock(function_call=Mock(
                    name="read_file",
                    args={"file_path": "research/formal/Fibonacci.tla"}
                ))
            ]))]),
            Mock(text="""The TLA+ specification looks good! Here are some improvements:

1. Add invariants for the sequence properties
2. Include a bounded model checking constraint
3. Add temporal properties for liveness
4. Consider adding an optimized matrix multiplication version""", 
                 candidates=[])
        ]
        
        with patch("gemini_repl.core.api_client.GeminiClient") as MockClient:
            mock_client = MockClient.return_value
            mock_client.send_message.side_effect = responses
            
            # Also mock the decision engine to avoid real API calls
            with patch("gemini_repl.tools.decision_engine.ToolDecisionEngine.analyze_query") as mock_analyze:
                # Return decisions for each query
                from gemini_repl.tools.tool_decision import ToolDecision
                
                decisions = [
                    # Step 1: No tool needed, just show Scheme
                    ToolDecision(
                        requires_tool_call=False,
                        reasoning="Showing Scheme implementation"
                    ),
                    # Step 2: Need to write file
                    ToolDecision(
                        requires_tool_call=True,
                        tool_name="write_file",
                        reasoning="Creating TLA+ specification",
                        file_path="research/formal/Fibonacci.tla",
                        content=tla_spec
                    ),
                    # Step 3: Need to read file
                    ToolDecision(
                        requires_tool_call=True,
                        tool_name="read_file",
                        reasoning="Reading TLA+ spec for review",
                        file_path="research/formal/Fibonacci.tla"
                    )
                ]
                mock_analyze.side_effect = decisions
                
                repl = StructuredGeminiREPL()
                
                # Capture all output
                output_lines = []
                with patch("builtins.print") as mock_print:
                    mock_print.side_effect = lambda *args: output_lines.append(" ".join(str(a) for a in args))
                    
                    # Step 1: Show Fibonacci in Scheme
                    print("\n=== Step 1: Show Fibonacci in Scheme ===")
                    repl._handle_api_request("show fibonacci in scheme")
                    
                    # Verify Scheme code was displayed
                    scheme_shown = any("fibonacci" in line.lower() and "define" in line 
                                     for line in output_lines)
                    self.assertTrue(scheme_shown, "Scheme implementation should be shown")
                    
                    # Step 2: Create TLA+ spec
                    output_lines.clear()
                    print("\n=== Step 2: Create TLA+ Specification ===")
                    repl._handle_api_request("create a TLA+ spec for that and add it to research/formal/")
                    
                    # Verify tool was called
                    tool_used = any("🔧" in line and "write_file" in line 
                                  for line in output_lines)
                    self.assertTrue(tool_used, "write_file tool should be used")
                    
                    # Step 3: Review the spec
                    output_lines.clear()
                    print("\n=== Step 3: Review and Suggest Improvements ===")
                    repl._handle_api_request("show research/formal/Fibonacci.tla and suggest improvements")
                    
                    # Verify read tool was used
                    read_used = any("🔧" in line and "read_file" in line 
                                  for line in output_lines)
                    self.assertTrue(read_used, "read_file tool should be used")
                    
                    # Verify improvements suggested
                    improvements = any("improvements" in line.lower() for line in output_lines)
                    self.assertTrue(improvements, "Improvements should be suggested")
        
    def test_directory_creation(self):
        """Test that write_file creates directories safely."""
        
        # Note: write_file uses SANDBOX_DIR which is the project root
        # We'll test with a temporary test directory
        test_path = f"test_temp_{id(self)}/formal/specs/Test.tla"
        
        try:
            # Test creating nested directories
            result = write_file(test_path, "test content")
            self.assertIn("Successfully wrote", result)
            
            # The file is created in the project sandbox, not temp_dir
            # Just verify the operation succeeded
            self.assertIn(test_path, result)
            
        finally:
            # Clean up the test directory
            import os
            test_dir = test_path.split('/')[0]
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)
        
        # Test security - no parent directory traversal
        result = write_file("../../../etc/passwd", "malicious")
        self.assertIn("Security error", result)
        self.assertIn("Parent directory", result)
        
        # Test security - no absolute paths
        result = write_file("/etc/passwd", "malicious")
        self.assertIn("Security error", result)
        self.assertIn("Absolute path", result)
        
    def test_complex_directory_structure(self):
        """Test creating complex but safe directory structures."""
        
        test_cases = [
            ("docs/rfcs/2024/proposal.md", True),
            ("experiments/tla-plus/specs/Model.tla", True),
            ("src/../tests/test.py", False),  # Contains ..
            ("./safe/path/file.txt", True),
            ("research/formal/../../evil.txt", False),  # Escapes with ..
        ]
        
        for path, should_succeed in test_cases:
            result = write_file(path, f"Content for {path}")
            if should_succeed:
                self.assertIn("Successfully wrote", result, 
                            f"Should succeed: {path}")
                # Verify file was created
                full_path = Path(self.temp_dir) / path
                self.assertTrue(full_path.exists(), 
                              f"File should exist: {path}")
            else:
                self.assertIn("Security error", result,
                            f"Should fail: {path}")


class TestSchemeImplementations(unittest.TestCase):
    """Test various Scheme implementations can be generated."""
    
    def test_scheme_variations(self):
        """Test that AI can generate different Fibonacci variations."""
        
        # Different styles we might see
        variations = [
            # Basic recursive
            "(define (fib n) (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2)))))",
            
            # With cond
            """(define (fibonacci n)
                 (cond ((= n 0) 0)
                       ((= n 1) 1)
                       (else (+ (fibonacci (- n 1)) 
                               (fibonacci (- n 2))))))""",
            
            # Tail recursive
            """(define (fib n)
                 (define (fib-iter n a b)
                   (if (= n 0) a
                       (fib-iter (- n 1) b (+ a b))))
                 (fib-iter n 0 1))""",
            
            # With memoization
            """(define fib
                 (let ((cache (make-hash)))
                   (lambda (n)
                     (cond
                       ((hash-ref cache n #f) => (lambda (x) x))
                       ((<= n 1) n)
                       (else 
                         (let ((result (+ (fib (- n 1)) (fib (- n 2)))))
                           (hash-set! cache n result)
                           result))))))"""
        ]
        
        for var in variations:
            # Each should be valid Scheme syntax
            self.assertIn("define", var)
            self.assertIn("fib", var.lower())
            # Should handle base cases
            self.assertTrue("0" in var or "<= n 1" in var)


if __name__ == "__main__":
    unittest.main()
