"""
Security tests for path traversal vulnerabilities.
These tests SHOULD FAIL with current implementation.
After security fix, these tests should PASS.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gemini_repl.tools.codebase_tools import read_file, write_file, list_files


class TestPathTraversalSecurity(unittest.TestCase):
    """Test cases for path traversal security."""
    
    def setUp(self):
        """Create a sandbox directory for testing."""
        self.sandbox = tempfile.mkdtemp(prefix="gemini_test_")
        self.original_cwd = os.getcwd()
        os.chdir(self.sandbox)
        
        # Create test files
        os.makedirs("src", exist_ok=True)
        with open("src/test.py", "w") as f:
            f.write("# Safe file")
        
        # Create a file outside sandbox for testing
        self.outside_file = tempfile.NamedTemporaryFile(delete=False)
        self.outside_file.write(b"Secret data")
        self.outside_file.close()
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        os.unlink(self.outside_file.name)
    
    def test_read_file_parent_directory_traversal(self):
        """Test that ../.. patterns are blocked."""
        attacks = [
            "../../../etc/passwd",
            ".." + os.sep + ".." + os.sep + "etc/passwd",
            "src/../../etc/passwd",
            "../" * 10 + "etc/passwd",
        ]
        
        for attack in attacks:
            with self.subTest(attack=attack):
                result = read_file(attack)
                # Should now return security error
                self.assertIn("error", result.lower(), f"Path traversal not blocked: {attack}")
    
    def test_read_file_absolute_paths(self):
        """Test that absolute paths are blocked."""
        attacks = [
            "/etc/passwd",
            "/home/user/.ssh/id_rsa",
            self.outside_file.name,  # Absolute path to temp file
        ]
        
        for attack in attacks:
            with self.subTest(attack=attack):
                result = read_file(attack)
                # CURRENTLY FAILS - reads the file!
                self.assertIn("error", result.lower(), f"Absolute path not blocked: {attack}")
    
    def test_write_file_parent_directory_traversal(self):
        """Test that write operations can't escape sandbox."""
        attacks = [
            ("../evil.txt", "Escaped!"),
            ("../../evil.txt", "Escaped!"),
            ("src/../../../evil.txt", "Escaped!"),
        ]
        
        for path, content in attacks:
            with self.subTest(path=path):
                result = write_file(path, content)
                # CURRENTLY FAILS - writes the file!
                self.assertIn("error", result.lower(), f"Write traversal not blocked: {path}")
                
                # Verify file wasn't created outside sandbox
                abs_path = os.path.abspath(path)
                self.assertFalse(
                    os.path.exists(abs_path) and not abs_path.startswith(self.sandbox),
                    f"File created outside sandbox: {abs_path}"
                )
    
    def test_write_file_absolute_paths(self):
        """Test that absolute write paths are blocked."""
        attacks = [
            ("/tmp/evil_absolute.txt", "Pwned!"),
            (os.path.join(tempfile.gettempdir(), "evil.txt"), "Pwned!"),
        ]
        
        for path, content in attacks:
            with self.subTest(path=path):
                result = write_file(path, content)
                # CURRENTLY FAILS - writes the file!
                self.assertIn("error", result.lower(), f"Absolute write not blocked: {path}")
    
    def test_list_files_parent_directory(self):
        """Test that list operations can't escape sandbox."""
        attacks = [
            "../*",
            "../../*",
            "../../../*",
            "/*",
            "/etc/*",
        ]
        
        for pattern in attacks:
            with self.subTest(pattern=pattern):
                result = list_files(pattern)
                # CURRENTLY FAILS - lists parent directories!
                self.assertTrue(
                    "No files found" in result or "error" in result.lower(),
                    f"List traversal not blocked: {pattern}"
                )
    
    def test_symlink_traversal(self):
        """Test that symlinks can't be used to escape."""
        # Create malicious symlink
        os.symlink("/etc", "evil_link")
        
        try:
            # Test read via symlink
            result = read_file("evil_link/passwd")
            # CURRENTLY FAILS - follows symlink!
            self.assertIn("error", result.lower(), "Symlink traversal not blocked")
            
            # Test list via symlink
            result = list_files("evil_link/*")
            self.assertTrue(
                "No files found" in result or "Error" in result,
                "Symlink listing not blocked"
            )
        finally:
            os.unlink("evil_link")
    
    def test_path_normalization_attacks(self):
        """Test various path normalization bypasses."""
        attacks = [
            ".//..//..//etc/passwd",  # Extra slashes
            "src/./../../etc/passwd",  # Current directory references
            "src/../src/../../../etc/passwd",  # Complex traversal
        ]
        
        for attack in attacks:
            with self.subTest(attack=attack):
                result = read_file(attack)
                # CURRENTLY FAILS - normalizes and reads!
                self.assertIn("error", result.lower(), f"Path normalization bypass: {attack}")
    
    def test_safe_operations_still_work(self):
        """Test that legitimate operations still work."""
        # These should work after security fix
        
        # Read existing file
        result = read_file("src/test.py")
        self.assertEqual(result, "# Safe file")
        
        # Write new file
        result = write_file("output.txt", "Safe content")
        self.assertIn("Successfully", result)
        self.assertTrue(os.path.exists("output.txt"))
        
        # List files
        result = list_files("src/*.py")
        self.assertIn("src/test.py", result)


if __name__ == "__main__":
    print("🔴 SECURITY TEST SUITE - Path Traversal")
    print("=" * 50)
    print("NOTE: These tests SHOULD FAIL with current implementation.")
    print("After security fix, all tests should PASS.")
    print("=" * 50)
    unittest.main(verbosity=2)
