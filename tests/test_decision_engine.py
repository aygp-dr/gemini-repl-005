"""Unit tests for decision engine."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from gemini_repl.tools.decision_engine import ToolDecisionEngine
from gemini_repl.tools.tool_decision import ToolDecision


class TestToolDecisionEngine:
    """Test the ToolDecisionEngine."""

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    def test_initialization(self):
        """Test engine initialization."""
        engine = ToolDecisionEngine()
        assert engine.api_key == "test-key"
        assert engine.model == "gemini-2.0-flash-lite"  # default
        assert engine.cache == {}
        assert engine.cache_hits == 0
        assert engine.cache_misses == 0

    def test_initialization_no_key(self):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
                ToolDecisionEngine()

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_analyze_query_success(self, mock_genai_client):
        """Test successful query analysis."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="User wants to read Makefile",
            file_path="Makefile",
        )
        mock_client.models.generate_content.return_value = mock_response

        # Test
        engine = ToolDecisionEngine(api_key="test-key")
        decision = engine.analyze_query("Read the Makefile")

        assert decision.requires_tool_call
        assert decision.tool_name == "read_file"
        assert decision.file_path == "Makefile"
        assert engine.cache_misses == 1
        assert engine.cache_hits == 0

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_cache_behavior(self, mock_genai_client):
        """Test caching functionality."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        test_decision = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="List files",
            file_path="src/",
        )
        mock_response.parsed = test_decision
        mock_client.models.generate_content.return_value = mock_response

        # Test
        engine = ToolDecisionEngine(api_key="test-key", cache_ttl_minutes=15)

        # First call - cache miss
        decision1 = engine.analyze_query("List files in src")
        assert engine.cache_misses == 1
        assert engine.cache_hits == 0
        assert len(engine.cache) == 1

        # Second call - cache hit
        decision2 = engine.analyze_query("List files in src")
        assert engine.cache_misses == 1
        assert engine.cache_hits == 1
        assert decision1 is decision2  # Same object

        # API should only be called once
        assert mock_client.models.generate_content.call_count == 1

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_cache_expiration(self, mock_genai_client):
        """Test cache TTL expiration."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = ToolDecision(requires_tool_call=False, reasoning="No tool needed")
        mock_client.models.generate_content.return_value = mock_response

        # Test with short TTL
        engine = ToolDecisionEngine(api_key="test-key", cache_ttl_minutes=1)

        # Add to cache with old timestamp
        old_time = datetime.now() - timedelta(minutes=2)
        engine.cache["old query"] = (mock_response.parsed, old_time)

        # Query should trigger cache miss due to expiration
        engine.analyze_query("old query")
        assert engine.cache_misses == 1
        assert "old query" in engine.cache

        # New timestamp should be recent
        _, timestamp = engine.cache["old query"]
        assert datetime.now() - timestamp < timedelta(seconds=1)

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_invalid_decision_handling(self, mock_genai_client):
        """Test handling of invalid decisions."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        # Invalid decision - read_file without path
        mock_response = MagicMock()
        mock_response.parsed = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read something",
            # Missing file_path!
        )
        mock_client.models.generate_content.return_value = mock_response

        # Test
        engine = ToolDecisionEngine(api_key="test-key")
        decision = engine.analyze_query("Read something")

        # Should return safe default
        assert not decision.requires_tool_call
        assert "Invalid tool configuration" in decision.reasoning

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_error_handling(self, mock_genai_client):
        """Test error handling in analysis."""
        # Setup mock to raise error
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API Error")

        # Test
        engine = ToolDecisionEngine(api_key="test-key")
        decision = engine.analyze_query("Test query")

        # Should return safe default
        assert not decision.requires_tool_call
        assert "Error in analysis" in decision.reasoning
        assert "API Error" in decision.reasoning

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_disable_cache(self, mock_genai_client):
        """Test disabling cache."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = ToolDecision(requires_tool_call=False, reasoning="No tool")
        mock_client.models.generate_content.return_value = mock_response

        # Test
        engine = ToolDecisionEngine(api_key="test-key")

        # First call with cache
        engine.analyze_query("Test", use_cache=True)
        assert len(engine.cache) == 1

        # Second call without cache
        engine.analyze_query("Test", use_cache=False)
        assert len(engine.cache) == 1  # Not added
        assert mock_client.models.generate_content.call_count == 2

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_cache_stats(self, mock_genai_client):
        """Test cache statistics."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = ToolDecision(requires_tool_call=False, reasoning="No tool")
        mock_client.models.generate_content.return_value = mock_response

        # Test
        engine = ToolDecisionEngine(api_key="test-key")

        # Initial stats
        stats = engine.get_cache_stats()
        assert stats["cache_size"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate"] == 0

        # Make some queries
        engine.analyze_query("Query 1")
        engine.analyze_query("Query 1")  # Hit
        engine.analyze_query("Query 2")
        engine.analyze_query("Query 2")  # Hit

        stats = engine.get_cache_stats()
        assert stats["cache_size"] == 2
        assert stats["cache_hits"] == 2
        assert stats["cache_misses"] == 2
        assert stats["hit_rate"] == 0.5
        assert stats["total_queries"] == 4

    @patch("gemini_repl.tools.decision_engine.genai.Client")
    def test_clear_cache(self, mock_genai_client):
        """Test cache clearing."""
        # Setup mock
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = ToolDecision(requires_tool_call=False, reasoning="No tool")
        mock_client.models.generate_content.return_value = mock_response

        # Test
        engine = ToolDecisionEngine(api_key="test-key")

        # Add to cache
        engine.analyze_query("Query 1")
        engine.analyze_query("Query 2")
        assert len(engine.cache) == 2

        # Clear cache
        engine.clear_cache()
        assert len(engine.cache) == 0
