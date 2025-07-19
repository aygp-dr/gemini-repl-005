# API Client


# [[file:../../../PYTHON-GEMINI-REPL.org::*API Client][API Client:1]]
"""Gemini API client implementation."""

import os
from typing import List, Dict, Any, Optional
from google import genai


class GeminiClient:
    """Client for interacting with Gemini API."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    def send_message(
        self, messages: List[Dict[str, str]], tools: Optional[List[Any]] = None
    ) -> Any:
        """Send message to Gemini API with optional tools."""
        # For now, we'll use a simple approach without conversation history
        # TODO: Research proper conversation handling in new SDK

        # Get the last user message
        last_user_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break

        if not last_user_message:
            raise ValueError("No user message found")

        # Send request (ignoring tools for now)
        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=last_user_message
            )
            return response

        except Exception as e:
            raise Exception(f"API request failed: {e}")

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[str]:
        """Convert internal message format to Gemini format."""
        gemini_messages = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # Gemini uses a simpler format
            if role == "user":
                gemini_messages.append(content)
            elif role == "assistant":
                gemini_messages.append(content)
            elif role == "tool":
                # Handle tool responses
                gemini_messages.append(f"Tool response: {content}")

        return gemini_messages


# API Client:1 ends here
