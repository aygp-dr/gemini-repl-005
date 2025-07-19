# API Client


# [[file:../../../PYTHON-GEMINI-REPL.org::*API Client][API Client:1]]
"""Gemini API client implementation."""

import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types


class GeminiClient:
    """Client for interacting with Gemini API."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    def send_message(
        self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """Send message to Gemini API with full conversation history and optional tools."""
        if not messages:
            raise ValueError("No messages provided")

        # Convert messages to Gemini format
        contents = self._convert_messages_to_contents(messages)

        # Configure tools if provided
        config = None
        if tools:
            tool_declarations = types.Tool(function_declarations=tools)
            config = types.GenerateContentConfig(tools=[tool_declarations])

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return response

        except Exception as e:
            raise Exception(f"API request failed: {e}")

    def _convert_messages_to_contents(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """Convert message history to Gemini Content format."""
        contents = []
        
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
            contents.append(content)
        
        return contents

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
