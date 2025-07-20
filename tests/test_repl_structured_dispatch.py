"""Integration tests for structured tool dispatch in REPL."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from gemini_repl.core.repl_structured import StructuredGeminiREPL
from gemini_repl.tools.tool_decision import ToolDecision


class TestStructuredREPL:
    """Test structured REPL functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        workspace = Path(tempfile.mkdtemp())

        # Create test files
        (workspace / "test.txt").write_text("Test content")
        (workspace / "src").mkdir()
        (workspace / "src" / "main.py").write_text("print('Hello')")

        yield workspace

        # Cleanup
        shutil.rmtree(workspace)

    @pytest.fixture
    def mock_repl(self, temp_workspace):
        """Create mock REPL with structured dispatch."""
        with patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_STRUCTURED_DISPATCH": "true"}
        ):
            # Mock the decision engine
            with patch("gemini_repl.core.repl_structured.ToolDecisionEngine") as mock_engine:
                repl = StructuredGeminiREPL()
                repl.workspace = temp_workspace
                yield repl, mock_engine

    def test_structured_dispatch_enabled(self):
        """Test that structured dispatch is enabled by default."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            with patch("gemini_repl.core.repl_structured.ToolDecisionEngine"):
                repl = StructuredGeminiREPL()
                assert repl.structured_dispatch
                assert repl.decision_engine is not None

    def test_structured_dispatch_disabled(self):
        """Test disabling structured dispatch."""
        with patch.dict(
            "os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_STRUCTURED_DISPATCH": "false"}
        ):
            repl = StructuredGeminiREPL()
            assert not repl.structured_dispatch
            assert repl.decision_engine is None

    def test_tool_decision_list_files(self, mock_repl):
        """Test list_files tool decision and execution."""
        repl, mock_engine_class = mock_repl
        mock_engine = mock_engine_class.return_value

        # Mock decision
        mock_engine.analyze_query.return_value = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="User wants to see files",
            file_path="src/",
        )

        # Mock API response
        mock_response = MagicMock()
        mock_response.text = "Here are the files in src/"
        repl.client.send_message = Mock(return_value=mock_response)

        # Test
        repl._handle_api_request("What files are in src?")

        # Verify decision was made
        mock_engine.analyze_query.assert_called_once_with("What files are in src?")

        # Verify last decision stored
        assert repl.last_decision.tool_name == "list_files"

    def test_tool_decision_read_file(self, mock_repl):
        """Test read_file tool decision and execution."""
        repl, mock_engine_class = mock_repl
        mock_engine = mock_engine_class.return_value

        # Mock decision
        mock_engine.analyze_query.return_value = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="User wants to read test.txt",
            file_path="test.txt",
        )

        # Mock API response
        mock_response = MagicMock()
        mock_response.text = "The file contains test content"
        repl.client.send_message = Mock(return_value=mock_response)

        # Test
        repl._handle_api_request("Read test.txt")

        # Verify tool was decided
        assert repl.last_decision.tool_name == "read_file"
        assert repl.last_decision.file_path == "test.txt"

    def test_tool_decision_no_tool(self, mock_repl):
        """Test when no tool is needed."""
        repl, mock_engine_class = mock_repl
        mock_engine = mock_engine_class.return_value

        # Mock decision - no tool needed
        mock_engine.analyze_query.return_value = ToolDecision(
            requires_tool_call=False, reasoning="General explanation, no file access needed"
        )

        # Mock API response
        mock_response = MagicMock()
        mock_response.text = "Recursion is when a function calls itself"
        repl.client.send_message = Mock(return_value=mock_response)

        # Test
        repl._handle_api_request("Explain recursion")

        # Verify no tool was used
        assert not repl.last_decision.requires_tool_call
        assert repl.last_decision.tool_name is None

    def test_enhanced_prompt_creation(self, mock_repl):
        """Test enhanced prompt creation with tool results."""
        repl, _ = mock_repl

        # Test list_files
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="List files",
            file_path="src/",
        )

        enhanced = repl._create_tool_enhanced_prompt(
            "Show files in src", decision, "file1.py\nfile2.py"
        )
        assert "I've listed the files" in enhanced
        assert "file1.py" in enhanced

        # Test read_file
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read file",
            file_path="test.txt",
        )

        enhanced = repl._create_tool_enhanced_prompt("Read test.txt", decision, "File content here")
        assert "I've read the file" in enhanced
        assert "test.txt" in enhanced
        assert "File content here" in enhanced

    def test_tool_execution_error_handling(self, mock_repl):
        """Test handling of tool execution errors."""
        repl, mock_engine_class = mock_repl
        mock_engine = mock_engine_class.return_value

        # Mock decision for non-existent file
        mock_engine.analyze_query.return_value = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read non-existent file",
            file_path="doesnt_exist.txt",
        )

        # Mock API response (should proceed without tool result)
        mock_response = MagicMock()
        mock_response.text = "I couldn't find that file"
        repl.client.send_message = Mock(return_value=mock_response)

        # Test - should not raise exception
        repl._handle_api_request("Read doesnt_exist.txt")

        # Verify fallback behavior
        assert repl.last_decision.tool_name == "read_file"

    def test_stats_with_decision_engine(self, mock_repl):
        """Test stats display includes decision engine metrics."""
        repl, mock_engine_class = mock_repl
        mock_engine = mock_engine_class.return_value

        # Mock cache stats
        mock_engine.get_cache_stats.return_value = {
            "cache_size": 5,
            "cache_hits": 3,
            "cache_misses": 2,
            "hit_rate": 0.6,
            "total_queries": 5,
        }

        # Set a last decision
        repl.last_decision = ToolDecision(
            requires_tool_call=True, tool_name="list_files", reasoning="Test decision"
        )

        # Capture output
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            repl._handle_stats()
            output = captured_output.getvalue()

            # Verify decision stats shown
            assert "Tool Decision Stats" in output
            assert "Cache Size: 5" in output
            assert "Hit Rate: 60.0%" in output
            assert "Last Decision" in output
            assert "Tool: list_files" in output

        finally:
            sys.stdout = sys.__stdout__
