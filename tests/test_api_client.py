"""Tests for the Gemini API client."""

import pytest
from unittest.mock import Mock, patch
from gemini_repl.core.api_client import GeminiClient


class TestGeminiClient:
    """Test the Gemini API client."""

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("gemini_repl.core.api_client.genai")
    def test_client_initialization(self, mock_genai):
        """Test client initializes correctly."""
        client = GeminiClient()

        # Check that Client was created with API key
        mock_genai.Client.assert_called_once_with(api_key="test-key")
        assert client.model_name == "gemini-2.0-flash-exp"

    def test_client_requires_api_key(self):
        """Test client raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
                GeminiClient()

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("gemini_repl.core.api_client.genai")
    def test_send_message_simple(self, mock_genai):
        """Test sending a simple message."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "42"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Test
        client = GeminiClient()
        messages = [{"role": "user", "content": "What is 2 + 40?"}]
        response = client.send_message(messages)

        # Verify
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash-exp", contents="What is 2 + 40?"
        )
        assert response.text == "42"

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("gemini_repl.core.api_client.genai")
    def test_send_message_with_history(self, mock_genai):
        """Test sending message with conversation history."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Your name is Alice"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Test with history
        client = GeminiClient()
        messages = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Hello Alice!"},
            {"role": "user", "content": "What's my name?"},
        ]
        response = client.send_message(messages)

        # Should only use last user message for now
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash-exp", contents="What's my name?"
        )
        assert response.text == "Your name is Alice"

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch("gemini_repl.core.api_client.genai")
    def test_send_message_no_user_message(self, mock_genai):
        """Test error when no user message is found."""
        mock_genai.Client.return_value = Mock()

        client = GeminiClient()
        messages = [{"role": "assistant", "content": "Hello!"}]

        with pytest.raises(ValueError, match="No user message found"):
            client.send_message(messages)

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "custom-model"})
    @patch("gemini_repl.core.api_client.genai")
    def test_custom_model(self, mock_genai):
        """Test using custom model from environment."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        client = GeminiClient()
        assert client.model_name == "custom-model"

        # Send a message to verify model is used
        mock_response = Mock()
        mock_response.text = "Response"
        mock_client.models.generate_content.return_value = mock_response

        messages = [{"role": "user", "content": "Test"}]
        client.send_message(messages)

        mock_client.models.generate_content.assert_called_once_with(
            model="custom-model", contents="Test"
        )
