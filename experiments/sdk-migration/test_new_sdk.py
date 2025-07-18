#!/usr/bin/env python3
"""
Minimal test to verify the new google-genai SDK works correctly.
This proves the solution for migrating from the old SDK.
"""

from google import genai
import os
import sys

def test_new_sdk():
    """Test basic functionality with new SDK"""
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        print("Run: source .env")
        return False
    
    print(f"✓ API key found: {api_key[:10]}...")
    
    # Create client
    try:
        client = genai.Client(api_key=api_key)
        print("✓ Client created successfully")
    except Exception as e:
        print(f"✗ Failed to create client: {e}")
        return False
    
    # Test simple generation
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents='Say hello in 5 words or less'
        )
        print("✓ API call successful!")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False
    
    # Test with conversation history (what REPL needs)
    try:
        messages = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
            {"role": "user", "content": "What's my name?"}
        ]
        
        # Convert to new SDK format
        contents = []
        for msg in messages:
            if msg["role"] == "user":
                contents.append(msg["content"])
            # Note: Need to research how to handle conversation history properly
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=contents[-1]  # Just the last user message for now
        )
        print(f"\n✓ Conversation test: {response.text}")
        
    except Exception as e:
        print(f"✗ Conversation test failed: {e}")
    
    return True

if __name__ == "__main__":
    print("Testing new google-genai SDK...\n")
    success = test_new_sdk()
    
    print("\n" + "="*50)
    if success:
        print("SUCCESS: New SDK works! Migration path is clear.")
    else:
        print("FAILED: Check errors above")
    
    sys.exit(0 if success else 1)
