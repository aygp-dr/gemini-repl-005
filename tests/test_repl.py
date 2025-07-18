# Testing Infrastructure


# [[file:../PYTHON-GEMINI-REPL.org::*Testing Infrastructure][Testing Infrastructure:1]]
"""Basic tests for Gemini REPL."""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from gemini_repl.core.repl import GeminiREPL
from gemini_repl.utils.context import ContextManager
from gemini_repl.utils.logger import Logger
from gemini_repl.tools.tool_system import ToolSystem


class TestGeminiREPL(unittest.TestCase):
    """Test cases for REPL functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_workspace = Path.cwd()
        Path(self.temp_dir).chmod(0o755)
        
        # Mock environment
        self.env_patcher = patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test-key',
            'WORKSPACE_DIR': str(Path(self.temp_dir) / 'workspace'),
            'LOG_FILE': str(Path(self.temp_dir) / 'test.log'),
            'CONTEXT_FILE': str(Path(self.temp_dir) / 'context.json')
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_context_management(self):
        """Test context manager functionality."""
        ctx = ContextManager()
        
        # Test adding messages
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there!")
        
        messages = ctx.get_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[0]['content'], 'Hello')
        
        # Test token counting
        tokens = ctx.get_token_count()
        self.assertGreater(tokens, 0)
        
        # Test stats
        stats = ctx.get_stats()
        self.assertEqual(stats['message_count'], 2)
        self.assertIn('token_count', stats)
    
    def test_logger(self):
        """Test logging functionality."""
        logger = Logger()
        
        # Test different log levels
        logger.debug("Debug message", {"test": True})
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Verify log file exists
        log_file = Path(self.temp_dir) / 'test.log'
        self.assertTrue(log_file.exists())
    
    def test_tool_system(self):
        """Test tool system functionality."""
        mock_repl = MagicMock()
        mock_repl.logger = Logger()
        
        tools = ToolSystem(mock_repl)
        
        # Test file operations
        result = tools.write_file("test.txt", "Hello, World!")
        self.assertTrue(result.get('success'))
        
        result = tools.read_file("test.txt")
        self.assertEqual(result.get('content'), "Hello, World!")
        
        result = tools.list_files(".")
        self.assertIn('files', result)
        self.assertEqual(len(result['files']), 1)
        
        # Test Python execution
        result = tools.execute_python("print('Hello')")
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('output').strip(), 'Hello')
    
    @patch('google.generativeai.GenerativeModel')
    def test_repl_commands(self, mock_model):
        """Test REPL slash commands."""
        # Mock API
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        
        repl = GeminiREPL()
        
        # Test help command
        with patch('builtins.print') as mock_print:
            repl.cmd_help("")
            mock_print.assert_called()
        
        # Test stats command
        repl.context.add_message("user", "test")
        with patch('builtins.print') as mock_print:
            repl.cmd_stats("")
            mock_print.assert_called()
        
        # Test exit command
        repl.cmd_exit()
        self.assertFalse(repl.running)


if __name__ == '__main__':
    unittest.main()
# Testing Infrastructure:1 ends here
