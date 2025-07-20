# API Client


# [[file:../../../PYTHON-GEMINI-REPL.org::*API Client][API Client:1]]
"""Gemini API client implementation."""

import os
import time
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from ..utils.rate_limiter import GlobalRateLimiter


class GeminiClient:
    """Client for interacting with Gemini API."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        self.client = genai.Client(api_key=api_key)
        # Use model with best rate limits for free tier (30 RPM)
        # See docs/RATE_LIMITS.md for details
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        
        # Initialize rate limiter
        self.rate_limiter = GlobalRateLimiter.get_limiter(self.model_name)

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

        # Check rate limit before making request
        self.rate_limiter.wait_with_display()
        
        # Retry logic for rate limits
        max_retries = 3
        retry_delay = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                # Record the request
                self.rate_limiter.record_request()
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
                return response

            except Exception as e:
                error_str = str(e)
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        print("⚠️  Rate limit hit despite protection!")
                        print(f"⏳ Waiting {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                        continue
                raise Exception(f"API request failed: {e}")

    def _convert_messages_to_contents(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """Convert message history to Gemini Content format."""
        contents = []
        
        # Prepend system messages to the first user message
        system_prompts = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompts.append(msg["content"])
        
        for msg in messages:
            if msg["role"] == "system":
                continue  # Skip system messages, they're handled above
                
            role = "user" if msg["role"] == "user" else "model"
            
            # Prepend system prompt to first user message
            if role == "user" and system_prompts and not contents:
                combined_content = "\n\n".join(system_prompts + [msg["content"]])
                content = types.Content(
                    role=role,
                    parts=[types.Part(text=combined_content)]
                )
                system_prompts = []  # Clear after using
            else:
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
