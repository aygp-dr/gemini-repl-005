"""Integration tests for the REPL."""

from unittest.mock import Mock, patch
from gemini_repl.core.repl import GeminiREPL


class TestREPLIntegration:
    """Test REPL integration with mocked API."""

    @patch.dict("os.environ", {"CONTEXT_FILE": "test_context.json"})
    @patch("gemini_repl.core.repl.GeminiClient")
    @patch("gemini_repl.core.repl.Logger")
    @patch("builtins.input")
    def test_simple_interaction(self, mock_input, mock_logger, mock_client_class):
        """Test a simple question-answer interaction."""
        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "2 + 40 equals 42"
        mock_client.send_message.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Simulate user input: ask a question then exit
        mock_input.side_effect = ["What is 2 + 40?", "/exit"]

        # Run REPL
        repl = GeminiREPL()
        repl.run()

        # Verify API was called
        mock_client.send_message.assert_called_once()
        messages = mock_client.send_message.call_args[0][0]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is 2 + 40?"

    @patch("gemini_repl.core.repl.GeminiClient")
    @patch("gemini_repl.core.repl.Logger")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_response_display(self, mock_print, mock_input, mock_logger, mock_client_class):
        """Test that responses are displayed correctly."""
        # Setup mocks
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "The answer is 42"
        mock_client.send_message.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Simulate user input
        mock_input.side_effect = ["2 + 40", "/exit"]

        # Run REPL
        repl = GeminiREPL()
        repl.run()

        # Check that response was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("The answer is 42" in call for call in print_calls)

    @patch("gemini_repl.core.repl.GeminiClient")
    @patch("gemini_repl.core.repl.Logger")
    @patch("builtins.input")
    def test_context_accumulation(self, mock_input, mock_logger, mock_client_class):
        """Test that context accumulates messages."""
        # Setup mocks
        mock_client = Mock()
        mock_response1 = Mock()
        mock_response1.text = "Hello! I'm Gemini."
        mock_response2 = Mock()
        mock_response2.text = "I said hello!"

        mock_client.send_message.side_effect = [mock_response1, mock_response2]
        mock_client_class.return_value = mock_client

        # Simulate conversation
        mock_input.side_effect = ["Hello", "What did you say?", "/exit"]

        # Run REPL
        repl = GeminiREPL()
        repl.run()

        # Verify context accumulation
        assert mock_client.send_message.call_count == 2

        # First call should have 1 message
        first_call_messages = mock_client.send_message.call_args_list[0][0][0]
        assert len(first_call_messages) == 1

        # Second call should have 3 messages (user, assistant, user)
        second_call_messages = mock_client.send_message.call_args_list[1][0][0]
        assert len(second_call_messages) == 3
        assert second_call_messages[0]["role"] == "user"
        assert second_call_messages[0]["content"] == "Hello"
        assert second_call_messages[1]["role"] == "assistant"
        assert second_call_messages[1]["content"] == "Hello! I'm Gemini."
        assert second_call_messages[2]["role"] == "user"
        assert second_call_messages[2]["content"] == "What did you say?"

    @patch("gemini_repl.core.repl.GeminiClient")
    @patch("gemini_repl.core.repl.Logger")
    @patch("builtins.input")
    def test_empty_input_ignored(self, mock_input, mock_logger, mock_client_class):
        """Test that empty input is ignored."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Simulate empty inputs
        mock_input.side_effect = ["", "  ", "Hello", "/exit"]

        # Run REPL
        repl = GeminiREPL()
        repl.run()

        # Should only call API once for "Hello"
        mock_client.send_message.assert_called_once()

    @patch("gemini_repl.core.repl.GeminiClient")
    @patch("gemini_repl.core.repl.Logger")
    @patch("builtins.input")
    def test_keyboard_interrupt(self, mock_input, mock_logger, mock_client_class):
        """Test handling of Ctrl-C."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Simulate Ctrl-C then exit
        mock_input.side_effect = [KeyboardInterrupt(), "/exit"]

        # Run REPL
        repl = GeminiREPL()
        repl.run()

        # Should not crash, API should not be called
        mock_client.send_message.assert_not_called()

    @patch("gemini_repl.core.repl.GeminiClient")
    @patch("gemini_repl.core.repl.Logger")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_api_error_handling(self, mock_print, mock_input, mock_logger, mock_client_class):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_client.send_message.side_effect = Exception("API Error: Rate limit exceeded")
        mock_client_class.return_value = mock_client

        # Simulate input
        mock_input.side_effect = ["Hello", "/exit"]

        # Run REPL
        repl = GeminiREPL()
        repl.run()

        # Check error was displayed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("API Error: Rate limit exceeded" in call for call in print_calls)
