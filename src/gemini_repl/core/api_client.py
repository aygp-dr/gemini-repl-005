# API Client


# [[file:../../../PYTHON-GEMINI-REPL.org::*API Client][API Client:1]]
"""Gemini API client implementation."""

import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse


class GeminiClient:
    """Client for interacting with Gemini API."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        genai.configure(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
        )

    def send_message(
        self, messages: List[Dict[str, str]], tools: Optional[List[Any]] = None
    ) -> GenerateContentResponse:
        """Send message to Gemini API with optional tools."""
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)

        # Configure model with tools if provided
        if tools:
            self.model = genai.GenerativeModel(
                self.model_name,
                tools=tools,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                },
            )

        # Send request
        try:
            if len(gemini_messages) == 1:
                response = self.model.generate_content(gemini_messages[0])
            else:
                # Use chat for multi-turn conversations
                chat = self.model.start_chat(history=gemini_messages[:-1])
                response = chat.send_message(gemini_messages[-1])

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
